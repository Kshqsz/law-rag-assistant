#!/usr/bin/env python3
# coding: utf-8
"""
RAG vs Base LLM A/B 评测脚本

功能：
1) 读取测试集（JSONL）
2) 同题跑两组：
   - baseline: 仅大模型（不走RAG）
   - rag: 走现有 law_qa_service.ask_question
3) 自动计算基础指标（命中率/引用/拒答/时延）
4) 导出明细 CSV + 汇总 JSON

用法示例：
python scripts/evaluate_rag_vs_base.py \
  --dataset tests/ab_eval_dataset.sample.jsonl \
  --output-dir evaluation_results \
  --limit 30
"""

import os
import re
import csv
import json
import time
import argparse
import asyncio
import sys
from datetime import datetime
from typing import Any, Dict, List

# 允许在 scripts/ 目录直接运行
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# 固定工作目录到项目根，避免相对路径导致向量库/数据集加载失败
os.chdir(PROJECT_ROOT)

from law_ai.utils import get_model
from backend.law_service import law_qa_service

# ──────────────────────────────────────────────
# Qwen3.5-plus 担任 LLM 裁判
# ──────────────────────────────────────────────

_JUDGE_SYSTEM_PROMPT = """\
你是一位专业的中国法律AI回答质量评审专家。
你将收到：一个法律问题、可选的检索上下文（RAG召回的法律原文片段），以及待评估的AI回答。
请从以下四个维度对回答进行综合评分（总分100分）：

1. Context Relevance 内容相关性（25分）
   - 若提供了检索上下文：上下文中的法律原文是否与问题高度相关，有无冗余或偏题内容。
   - 若无检索上下文（Baseline）：回答所援引的法律知识点是否与问题直接相关，无跑题。

2. Groundedness 真实性/忠实度（25分）
   - 若提供了检索上下文：回答中的法律事实与结论是否忠实于检索上下文，不捏造或曲解原文。
   - 若无检索上下文（Baseline）：回答中的法律事实是否与中国现行法律一致，无明显杜撰。

3. Answer Relevance 回答相关性（25分）
   - 回答是否直接、有针对性地解答了用户的问题，没有答非所问或过度发散。

4. Legal Citation Quality 法律引用质量（25分）
   - 是否正确引用了相关法律名称及条文（格式：《法律名称》第X条）。
   - 引用是否准确、恰当，与回答内容相符。

评分规则：
- 每个维度独立打分（0-25），最终输出四项之和（0-100的整数）。
- 最终只输出一个整数（0-100），不要输出分析过程、分项分数或其他任何内容。
"""


async def llm_judge_score(
    question: str,
    answer: str,
    context: str = "",  # RAG 检索上下文；Baseline 传空字符串
) -> float:
    """调用 Qwen3.5-plus 对单条回答按四维度进行 0-100 评分。"""
    if not answer or not answer.strip():
        return 0.0

    context_block = (
        f"【检索上下文（RAG召回法律原文）】\n{context.strip()}\n\n"
        if context and context.strip()
        else "【检索上下文】无（Baseline裸答模式）\n\n"
    )
    user_content = (
        f"【问题】\n{question}\n\n"
        f"{context_block}"
        f"【待评估回答】\n{answer}\n\n"
        "请按四个维度（Context Relevance / Groundedness / Answer Relevance / Legal Citation Quality）"
        "各打0-25分，输出四项之和（仅输出0-100的整数）："
    )

    # 直接调用 get_model 获取 ChatOpenAI 模型
    judge_model = get_model(model="qwen3.5-plus", streaming=False)
    
    try:
        # 使用 LangChain ChatOpenAI 的 invoke 方法
        from langchain.schema import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=_JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: judge_model.invoke(messages)
        )
        raw = response.content if hasattr(response, "content") else str(response)
        raw = raw.strip()
        # 提取第一个数字作为分数
        m = re.search(r"\d+", raw)
        if m:
            score = float(min(100, max(0, int(m.group()))))
        else:
            score = 0.0
    except Exception as exc:
        print(f"  [LLM裁判] 调用失败：{exc}")
        score = -1.0
    
    return score

REFUSAL_PATTERNS = [
    "不好意思，我是法律AI助手",
    "请提问和法律有关的问题",
    "无法回答",
    "无法提供",
]

LAW_CITATION_PATTERN = re.compile(r"第[一二三四五六七八九十百千万0-9]+条|《[^》]{1,30}》")

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.isabs(path):
        path = os.path.join(PROJECT_ROOT, path)
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(json.loads(line))
    return rows


def contains_refusal(text: str) -> int:
    t = text or ""
    return int(any(p in t for p in REFUSAL_PATTERNS))


def citation_present(text: str) -> int:
    return int(bool(LAW_CITATION_PATTERN.search(text or "")))


def keyword_hit_ratio(text: str, keywords: List[str]) -> float:
    if not keywords:
        return 0.0
    t = text or ""
    hit = sum(1 for kw in keywords if kw and kw in t)
    return hit / len(keywords)


def law_hit(text: str, expected_laws: List[str]) -> int:
    if not expected_laws:
        return 0
    t = text or ""
    return int(any(law in t for law in expected_laws if law))


def calc_score(result_text: str, row: Dict[str, Any]) -> float:
    """简单可解释评分（0-100）"""
    expected_keywords = row.get("expected_keywords", [])
    expected_laws = row.get("expected_laws", [])
    is_law_related = bool(row.get("is_law_related", True))

    refusal = contains_refusal(result_text)
    kw_ratio = keyword_hit_ratio(result_text, expected_keywords)
    law_ref = law_hit(result_text, expected_laws)
    cite = citation_present(result_text)

    if not is_law_related:
        # 非法律问题：拒答更优
        score = 100.0 if refusal else 40.0
        return round(score, 2)

    # 法律问题：拒答扣分
    score = (
        50.0 * kw_ratio +
        25.0 * law_ref +
        15.0 * cite +
        10.0 * (1 - refusal)
    )
    return round(score, 2)


async def run_rag(question: str) -> Dict[str, Any]:
    start = time.perf_counter()
    answer, law_context, web_context = await law_qa_service.ask_question(
        question=question,
        use_document_content=None,
        history=None,
    )
    latency_ms = (time.perf_counter() - start) * 1000
    return {
        "answer": answer,
        "law_context": law_context,
        "web_context": web_context,
        "latency_ms": round(latency_ms, 2),
    }


def run_baseline(question: str, model_name: str) -> Dict[str, Any]:
    """Baseline: 同模型裸问答（不使用RAG，不使用项目内Prompt模板）"""
    model = get_model(model=model_name, streaming=False)
    prompt = question

    start = time.perf_counter()
    resp = model.invoke(prompt)
    latency_ms = (time.perf_counter() - start) * 1000

    if hasattr(resp, "content"):
        answer = resp.content
    else:
        answer = str(resp)

    return {
        "answer": answer,
        "latency_ms": round(latency_ms, 2),
        "input_text": prompt,
    }


def estimate_chars_cost(text: str) -> int:
    """粗略成本代理指标：输出字符数（非真实计费）"""
    return len(text or "")


async def evaluate(dataset: List[Dict[str, Any]], limit: int = 0, model_name: str = "qwen-plus") -> Dict[str, Any]:
    # 强制 RAG 与 Baseline 使用同一个模型
    original_model_name = os.environ.get("MODEL_NAME")
    os.environ["MODEL_NAME"] = model_name

    results: List[Dict[str, Any]] = []
    data = dataset[:limit] if limit and limit > 0 else dataset

    try:
        for idx, row in enumerate(data, 1):
            qid = row.get("id", idx)
            question = row["question"]

            print(f"\n[{idx}/{len(data)}] 评测问题 {qid}: {question[:80]}")

            print(f"  [Baseline] 执行裸问答...")
            baseline = run_baseline(question, model_name=model_name)
            print(f"  [Baseline] 完成！耗时: {baseline['latency_ms']}ms")
            
            print(f"  [RAG] 执行检索增强问答...")
            rag = await run_rag(question)
            print(f"  [RAG] 完成！耗时: {rag['latency_ms']}ms")

            baseline_score = calc_score(baseline["answer"], row)
            rag_score = calc_score(rag["answer"], row)
            print(f"  [规则评分] baseline={baseline_score}  rag={rag_score}")

            # ── LLM 裁判评分（Qwen3.5-plus）──
            # baseline 无检索上下文，rag 传入召回的法律原文供裁判评估 Groundedness
            print(f"  [裁判评分] 评估中...")
            baseline_llm_score, rag_llm_score = await asyncio.gather(
                llm_judge_score(question, baseline["answer"], context=""),
                llm_judge_score(question, rag["answer"], context=rag.get("law_context", "")),
            )
            print(f"  [裁判评分] 完成！baseline={baseline_llm_score:.0f}  rag={rag_llm_score:.0f}")

            item = {
                "id": qid,
                "category": row.get("category", "general"),
                "question": question,
                "model_name": model_name,

                "baseline_answer": baseline["answer"],
                "baseline_latency_ms": baseline["latency_ms"],
                "baseline_score": baseline_score,
                "baseline_refusal": contains_refusal(baseline["answer"]),
                "baseline_citation": citation_present(baseline["answer"]),
                "baseline_cost_proxy_chars": estimate_chars_cost(baseline["answer"]),

                "rag_answer": rag["answer"],
                "rag_law_context": rag.get("law_context", ""),
                "rag_web_context": rag.get("web_context", ""),
                "rag_latency_ms": rag["latency_ms"],
                "rag_score": rag_score,
                "rag_refusal": contains_refusal(rag["answer"]),
                "rag_citation": citation_present(rag["answer"]),
                "rag_cost_proxy_chars": estimate_chars_cost(rag["answer"]),

                "baseline_llm_score": baseline_llm_score,
                "rag_llm_score": rag_llm_score,
                "llm_score_diff": round(rag_llm_score - baseline_llm_score, 2),

                "is_law_related": int(bool(row.get("is_law_related", True))),
                "score_diff": round(rag_score - baseline_score, 2),
            }
            results.append(item)
    finally:
        if original_model_name is None:
            os.environ.pop("MODEL_NAME", None)
        else:
            os.environ["MODEL_NAME"] = original_model_name

    def avg(key: str) -> float:
        return round(sum(float(r[key]) for r in results) / max(len(results), 1), 2)

    summary = {
        "samples": len(results),
        "model_name": model_name,
        "baseline_mode": "raw_question_only",
        "rag_mode": "project_rag_pipeline",
        "avg_baseline_score": avg("baseline_score"),
        "avg_rag_score": avg("rag_score"),
        "avg_score_diff": round(avg("rag_score") - avg("baseline_score"), 2),
        "avg_baseline_latency_ms": avg("baseline_latency_ms"),
        "avg_rag_latency_ms": avg("rag_latency_ms"),
        "avg_baseline_cost_proxy_chars": avg("baseline_cost_proxy_chars"),
        "avg_rag_cost_proxy_chars": avg("rag_cost_proxy_chars"),
        "rag_better_count": sum(1 for r in results if r["rag_score"] > r["baseline_score"]),
        "baseline_better_count": sum(1 for r in results if r["rag_score"] < r["baseline_score"]),
        "tie_count": sum(1 for r in results if r["rag_score"] == r["baseline_score"]),
        # LLM 裁判汇总
        "avg_baseline_llm_score": avg("baseline_llm_score"),
        "avg_rag_llm_score": avg("rag_llm_score"),
        "avg_llm_score_diff": round(avg("rag_llm_score") - avg("baseline_llm_score"), 2),
        "llm_rag_better_count": sum(1 for r in results if r["rag_llm_score"] > r["baseline_llm_score"]),
        "llm_baseline_better_count": sum(1 for r in results if r["rag_llm_score"] < r["baseline_llm_score"]),
        "llm_tie_count": sum(1 for r in results if r["rag_llm_score"] == r["baseline_llm_score"]),
    }

    return {"summary": summary, "details": results}


def write_outputs(output_dir: str, report: Dict[str, Any]) -> None:
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(PROJECT_ROOT, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    summary_path = os.path.join(output_dir, f"ab_summary_{ts}.json")
    details_path = os.path.join(output_dir, f"ab_details_{ts}.csv")

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(report["summary"], f, ensure_ascii=False, indent=2)

    details = report["details"]
    if details:
        fieldnames = list(details[0].keys())
        with open(details_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(details)

    print("\n=== 评测完成 ===")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"\n明细文件: {details_path}")
    print(f"汇总文件: {summary_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RAG vs Base LLM A/B 评测")
    parser.add_argument(
        "--dataset",
        default="tests/ab_eval_dataset.sample.jsonl",
        help="JSONL 测试集路径（默认: tests/ab_eval_dataset.sample.jsonl）",
    )
    parser.add_argument("--output-dir", default="evaluation_results", help="输出目录")
    parser.add_argument("--limit", type=int, default=0, help="只评测前 N 条，0 表示全部")
    parser.add_argument("--model-name", default=os.getenv("MODEL_NAME", "qwen-plus"), help="同一模型名（Baseline 与 RAG 共用）")
    return parser.parse_args()


async def main_async() -> None:
    args = parse_args()
    dataset = load_jsonl(args.dataset)
    if not dataset:
        raise ValueError("测试集为空，请检查 dataset 文件")

    print(f"统一评测模型: {args.model_name}")
    print("\n==================== 评测开始 ====================")
    try:
        report = await evaluate(dataset, limit=args.limit, model_name=args.model_name)
        print("\n==================== 评测完成 ====================")
        write_outputs(args.output_dir, report)
    except Exception as e:
        print(f"\n[错误] 评测中断: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main_async())
