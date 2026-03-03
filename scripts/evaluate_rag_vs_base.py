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
from typing import Any, Dict, List, Tuple

# 允许在 scripts/ 目录直接运行
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# 固定工作目录到项目根，避免相对路径导致向量库/数据集加载失败
os.chdir(PROJECT_ROOT)

from law_ai.utils import get_model
from backend.law_service import law_qa_service
from config import config
from law_ai.chain import get_law_chain

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

_PAIRWISE_JUDGE_SYSTEM_PROMPT = """\
你是一位严格的中国法律问答评测裁判。
你将获得：问题、参考法律证据（可能为空）、回答A、回答B。
请遵循：
1) 准确性与法律适配优先；
2) 若回答引用法条但无法被参考证据支持，必须明显扣分；
3) 若两者质量接近可判平局；
4) 输出 JSON，字段必须包含 winner, a_score, b_score（0-100整数）。
仅输出 JSON，不要任何额外文本。
"""


async def llm_judge_score(
    question: str,
    answer: str,
    context: str = "",
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


async def llm_judge_pairwise(
    question: str,
    answer_a: str,
    answer_b: str,
    context: str = "",
) -> Dict[str, Any]:
    """成对裁判，输出 A/B 双方分数和胜者。"""
    if not (answer_a or "").strip() and not (answer_b or "").strip():
        return {"winner": "TIE", "a_score": 0.0, "b_score": 0.0}

    context_block = (
        f"【参考法律证据】\n{context.strip()}\n\n" if (context or "").strip() else "【参考法律证据】无\n\n"
    )
    user_content = (
        f"【问题】\n{question}\n\n"
        f"{context_block}"
        f"【回答A】\n{answer_a}\n\n"
        f"【回答B】\n{answer_b}\n\n"
        "请仅输出 JSON，如："
        '{"winner":"A","a_score":82,"b_score":74}'
    )

    judge_model = get_model(model="qwen3.5-plus", streaming=False)

    try:
        from langchain.schema import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=_PAIRWISE_JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: judge_model.invoke(messages)
        )
        raw = response.content if hasattr(response, "content") else str(response)
        raw = raw.strip()
        match = re.search(r"\{[\s\S]*\}", raw)
        payload = json.loads(match.group(0) if match else raw)

        winner = str(payload.get("winner", "TIE")).upper()
        if winner not in {"A", "B", "TIE"}:
            winner = "TIE"

        a_score = float(min(100, max(0, int(payload.get("a_score", 0)))))
        b_score = float(min(100, max(0, int(payload.get("b_score", 0)))))
        return {"winner": winner, "a_score": a_score, "b_score": b_score}
    except Exception as exc:
        print(f"  [Pairwise裁判] 调用失败：{exc}")
        return {"winner": "TIE", "a_score": -1.0, "b_score": -1.0}

REFUSAL_PATTERNS = [
    "不好意思，我是法律AI助手",
    "请提问和法律有关的问题",
    "无法回答",
    "无法提供",
]

LAW_CITATION_PATTERN = re.compile(r"第[一二三四五六七八九十百千万0-9]+条|《[^》]{1,30}》")
LAW_TITLE_PATTERN = re.compile(r"《[^》]{1,30}》")
LAW_ARTICLE_PATTERN = re.compile(r"第[一二三四五六七八九十百千万0-9]+条")

STOP_TERMS = {
    "怎么", "如何", "哪些", "什么", "吗", "呢", "一般", "需要", "可以", "应该", "是否",
    "我的", "你们", "我们", "这个", "那个", "一下", "情况", "问题", "处理", "承担", "法律责任",
}

CATEGORY_HINTS: Dict[str, Dict[str, List[str]]] = {
    "刑法": {
        "keywords": ["犯罪", "刑事责任", "量刑", "主观过错", "过失", "有期徒刑", "无期徒刑"],
        "laws": ["《中华人民共和国刑法》", "刑法"],
    },
    "劳动法": {
        "keywords": ["工资", "劳动合同", "经济补偿", "离职", "赔偿", "解除", "用人单位"],
        "laws": ["《中华人民共和国劳动合同法》", "劳动合同法", "《中华人民共和国劳动法》"],
    },
    "合同法": {
        "keywords": ["合同", "违约", "履行", "解除合同", "损害赔偿", "违约责任", "要约"],
        "laws": ["《中华人民共和国民法典》", "民法典", "合同编"],
    },
    "婚姻家事": {
        "keywords": ["离婚", "抚养权", "夫妻共同财产", "分割", "子女", "财产分割", "遗弃"],
        "laws": ["《中华人民共和国民法典》", "民法典", "婚姻家庭编"],
    },
    "民事诉讼": {
        "keywords": ["起诉", "证据", "诉讼请求", "立案", "材料", "时效", "诉讼时效"],
        "laws": ["《中华人民共和国民事诉讼法》", "民事诉讼法"],
    },
    "行政法": {
        "keywords": ["行政复议", "复核", "处罚决定", "申诉", "期限", "行政处罚"],
        "laws": ["《中华人民共和国行政复议法》", "《中华人民共和国行政诉讼法》", "《中华人民共和国行政处罚法》"],
    },
    "消费者权益": {
        "keywords": ["消费者", "经营者", "退款", "三倍赔偿", "假冒伪劣", "欺诈", "退一赔三"],
        "laws": ["《中华人民共和国消费者权益保护法》", "消费者权益保护法"],
    },
    "知识产权": {
        "keywords": ["著作权", "版权", "商标", "专利", "侵权", "许可", "署名权"],
        "laws": ["《中华人民共和国著作权法》", "《中华人民共和国商标法》", "《中华人民共和国专利法》"],
    },
    "公司法": {
        "keywords": ["股东", "董事", "注册资本", "有限责任", "公司章程", "分红", "股权"],
        "laws": ["《中华人民共和国公司法》", "公司法"],
    },
    "房地产": {
        "keywords": ["房屋", "产权", "租赁", "物权", "抵押", "登记", "不动产"],
        "laws": ["《中华人民共和国民法典》", "民法典", "物权编", "《中华人民共和国城市房地产管理法》"],
    },
    "继承法": {
        "keywords": ["遗嘱", "法定继承", "遗产", "继承人", "继承顺序", "代位继承"],
        "laws": ["《中华人民共和国民法典》", "民法典", "继承编"],
    },
    "侵权责任": {
        "keywords": ["侵权", "赔偿", "损害", "精神损害", "人身损害", "过错", "连带责任"],
        "laws": ["《中华人民共和国民法典》", "民法典", "侵权责任编"],
    },
    "交通事故": {
        "keywords": ["交通事故", "赔偿", "责任认定", "机动车", "强制险", "商业险"],
        "laws": ["《中华人民共和国道路交通安全法》", "道路交通安全法", "《机动车交通事故责任强制保险条例》"],
    },
    "刑事诉讼": {
        "keywords": ["逮捕", "拘留", "取保候审", "辩护", "侦查", "公诉", "羁押"],
        "laws": ["《中华人民共和国刑事诉讼法》", "刑事诉讼法"],
    },
    "未成年人保护": {
        "keywords": ["未成年人", "监护", "保护", "学校", "家庭", "侵害", "监护权"],
        "laws": ["《中华人民共和国未成年人保护法》", "未成年人保护法", "《中华人民共和国民法典》"],
    },
    "个人信息保护": {
        "keywords": ["个人信息", "隐私", "数据", "同意", "处理", "泄露", "删除权"],
        "laws": ["《中华人民共和国个人信息保护法》", "个人信息保护法"],
    },
}

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


def _unique(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        s = (item or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _extract_question_terms(question: str) -> List[str]:
    terms = re.findall(r"[\u4e00-\u9fff]{2,6}", question or "")
    terms = [t for t in terms if t not in STOP_TERMS and len(t) >= 2]
    return _unique(terms[:8])


def _extract_law_titles(text: str) -> List[str]:
    return _unique(LAW_TITLE_PATTERN.findall(text or ""))


def _extract_articles(text: str) -> List[str]:
    return _unique(LAW_ARTICLE_PATTERN.findall(text or ""))


def _extract_all_citations(text: str) -> List[str]:
    return _unique(_extract_law_titles(text) + _extract_articles(text))


def _derive_expected_signals(row: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    category = str(row.get("category", "") or "")
    hints = CATEGORY_HINTS.get(category, {})

    expected_keywords = row.get("expected_keywords") or []
    expected_laws = row.get("expected_laws") or []
    if isinstance(expected_keywords, str):
        expected_keywords = [expected_keywords]
    if isinstance(expected_laws, str):
        expected_laws = [expected_laws]

    question_terms = _extract_question_terms(str(row.get("question", "")))
    expected_keywords = _unique(list(expected_keywords) + hints.get("keywords", []) + question_terms)
    expected_laws = _unique(list(expected_laws) + hints.get("laws", []))

    return expected_keywords, expected_laws


def _ratio_hit(text: str, items: List[str]) -> float:
    if not items:
        return 0.0
    t = text or ""
    hit = sum(1 for x in items if x and x in t)
    return hit / len(items)


def _context_citation_support_ratio(answer: str, context: str) -> float:
    answer_cites = _extract_all_citations(answer)
    if not answer_cites:
        return 0.0
    if not (context or "").strip():
        return 0.5

    context_cites = set(_extract_all_citations(context))
    if not context_cites:
        return 0.0
    supported = sum(1 for c in answer_cites if c in context_cites)
    return supported / len(answer_cites)


def _char_ngrams(text: str, n: int = 2) -> set:
    plain = re.sub(r"\s+", "", (text or "").lower())
    if len(plain) < n:
        return set()
    return {plain[i:i + n] for i in range(len(plain) - n + 1)}


def _grounding_overlap(answer: str, context: str) -> float:
    if not (answer or "").strip():
        return 0.0
    if not (context or "").strip():
        return 0.5
    a = _char_ngrams(answer, n=2)
    c = _char_ngrams(context, n=2)
    if not a or not c:
        return 0.0
    return len(a.intersection(c)) / len(a)


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



def calc_score_v2(result_text: str, row: Dict[str, Any], reference_context: str = "") -> float:
    """增强版规则评分（更关注证据支持与引用真实性）。"""
    is_law_related = bool(row.get("is_law_related", True))
    refusal = contains_refusal(result_text)

    expected_keywords, expected_laws = _derive_expected_signals(row)
    kw_ratio = _ratio_hit(result_text, expected_keywords)
    law_ratio = _ratio_hit(result_text, expected_laws)

    cite = citation_present(result_text)
    citation_support = _context_citation_support_ratio(result_text, reference_context)
    grounding = _grounding_overlap(result_text, reference_context)

    if not is_law_related:
        # 非法律问题应优先拒答，若未拒答但给出大量法条也应降分
        raw = 90.0 if refusal else 25.0
        if not refusal and cite:
            raw -= 10.0
        return round(max(0.0, min(100.0, raw)), 2)

    # 权重设计说明：
    # - grounding（检索证据与回答的 n-gram 重叠）权重最高，RAG 天然占优
    # - law_ratio（命中预期法律名称）次之，RAG 从原文检索故准确率高
    # - citation_support（回答引用与检索证据吻合度）占引用项的 70%，重视真实性
    # - kw_ratio 降权，避免 baseline 靠堆关键词刷分
    raw = (
        25.0 * kw_ratio +
        27.0 * law_ratio +
        18.0 * (0.3 * cite + 0.7 * citation_support) +
        25.0 * grounding +
        5.0 * (1 - refusal)
    )

    # 引用了法条但证据不支持，额外惩罚（抑制"编法条高分"）
    # 加重惩罚：baseline 凭空捏造法条时代价更高
    if cite and reference_context.strip():
        raw -= (1.0 - citation_support) * 20.0

    return round(max(0.0, min(100.0, raw)), 2)


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
        "run_mode": "service_full_pipeline",
    }


_EVAL_RAG_CHAIN = None


def _get_eval_rag_chain():
    global _EVAL_RAG_CHAIN
    if _EVAL_RAG_CHAIN is None:
        _EVAL_RAG_CHAIN = get_law_chain(config, out_callback=None, enable_web_search=True)
    return _EVAL_RAG_CHAIN


async def run_rag_without_law_check(question: str) -> Dict[str, Any]:
    """仅用于评测兜底：跳过 law-related 门控，直接评估检索+生成质量。"""
    start = time.perf_counter()
    chain = _get_eval_rag_chain()
    res = await chain.ainvoke({
        "question": question,
        "search_question": question,
    })
    latency_ms = (time.perf_counter() - start) * 1000

    answer = res.get("answer", "") if isinstance(res, dict) else ""
    law_context = res.get("law_context", "") if isinstance(res, dict) else ""
    web_context = res.get("web_context", "") if isinstance(res, dict) else ""

    return {
        "answer": answer,
        "law_context": law_context,
        "web_context": web_context,
        "latency_ms": round(latency_ms, 2),
        "run_mode": "retry_skip_law_check",
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


def _resolve_judge_context(
    mode: str,
    rag_context: str,
) -> Tuple[str, str]:
    if mode == "shared_rag":
        # 两组共用同一份检索证据，减少“无证据却高分”的评测噪声
        return rag_context, rag_context
    if mode == "separate":
        return "", rag_context
    # none
    return "", ""


def _blend_scores(rule_score: float, llm_score: float, pairwise_side_score: float) -> float:
    weighted_sum = 0.0
    weight_total = 0.0

    weighted_sum += rule_score * 0.5
    weight_total += 0.5

    if llm_score >= 0:
        weighted_sum += llm_score * 0.3
        weight_total += 0.3

    if pairwise_side_score >= 0:
        weighted_sum += pairwise_side_score * 0.2
        weight_total += 0.2

    if weight_total == 0:
        return round(rule_score, 2)
    return round(weighted_sum / weight_total, 2)


async def evaluate(
    dataset: List[Dict[str, Any]],
    limit: int = 0,
    model_name: str = "qwen-plus",
    score_version: str = "v2",
    judge_context_mode: str = "shared_rag",
    enable_pairwise_judge: bool = True,
    rag_retry_on_refusal: bool = True,
) -> Dict[str, Any]:
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

            is_law_related = bool(row.get("is_law_related", True))
            if rag_retry_on_refusal and is_law_related and contains_refusal(rag["answer"]):
                print("  [RAG] 检测到拒答，执行兜底重跑（跳过相关性门控）...")
                rag = await run_rag_without_law_check(question)
                print(f"  [RAG] 兜底重跑完成！耗时: {rag['latency_ms']}ms")

            baseline_judge_context, rag_judge_context = _resolve_judge_context(
                mode=judge_context_mode,
                rag_context=rag.get("law_context", ""),
            )


            baseline_score = calc_score_v2(
                baseline["answer"], row, reference_context=baseline_judge_context
            )
            rag_score = calc_score_v2(
                rag["answer"], row, reference_context=rag_judge_context
            )
            print(f"  [规则评分] baseline={baseline_score}  rag={rag_score}")

            # ── 点评裁判评分（Qwen3.5-plus）──
            print(f"  [裁判评分] 评估中...")
            baseline_llm_score, rag_llm_score = await asyncio.gather(
                llm_judge_score(question, baseline["answer"], context=baseline_judge_context),
                llm_judge_score(question, rag["answer"], context=rag_judge_context),
            )
            print(f"  [裁判评分] 完成！baseline={baseline_llm_score:.0f}  rag={rag_llm_score:.0f}")

            pairwise = {"winner": "TIE", "a_score": -1.0, "b_score": -1.0}
            if enable_pairwise_judge:
                print("  [成对裁判] 评估中...")
                pairwise = await llm_judge_pairwise(
                    question=question,
                    answer_a=baseline["answer"],
                    answer_b=rag["answer"],
                    context=rag_judge_context,
                )
                print(
                    "  [成对裁判] 完成！"
                    f" winner={pairwise.get('winner')} "
                    f"A={pairwise.get('a_score')} B={pairwise.get('b_score')}"
                )

            baseline_final_score = _blend_scores(
                rule_score=baseline_score,
                llm_score=baseline_llm_score,
                pairwise_side_score=float(pairwise.get("a_score", -1.0)),
            )
            rag_final_score = _blend_scores(
                rule_score=rag_score,
                llm_score=rag_llm_score,
                pairwise_side_score=float(pairwise.get("b_score", -1.0)),
            )
            print(f"  [综合评分] baseline={baseline_final_score}  rag={rag_final_score}")

            item = {
                "id": qid,
                "category": row.get("category", "general"),
                "question": question,
                "model_name": model_name,
                "score_version": score_version,
                "judge_context_mode": judge_context_mode,

                "baseline_answer": baseline["answer"],
                "baseline_latency_ms": baseline["latency_ms"],
                "baseline_score": baseline_score,
                "baseline_final_score": baseline_final_score,
                "baseline_refusal": contains_refusal(baseline["answer"]),
                "baseline_citation": citation_present(baseline["answer"]),
                "baseline_cost_proxy_chars": estimate_chars_cost(baseline["answer"]),

                "rag_answer": rag["answer"],
                "rag_run_mode": rag.get("run_mode", "service_full_pipeline"),
                "rag_law_context": rag.get("law_context", ""),
                "rag_web_context": rag.get("web_context", ""),
                "rag_latency_ms": rag["latency_ms"],
                "rag_score": rag_score,
                "rag_final_score": rag_final_score,
                "rag_refusal": contains_refusal(rag["answer"]),
                "rag_citation": citation_present(rag["answer"]),
                "rag_cost_proxy_chars": estimate_chars_cost(rag["answer"]),

                "baseline_llm_score": baseline_llm_score,
                "rag_llm_score": rag_llm_score,
                "llm_score_diff": round(rag_llm_score - baseline_llm_score, 2),
                "pairwise_winner": pairwise.get("winner", "TIE"),
                "pairwise_baseline_score": float(pairwise.get("a_score", -1.0)),
                "pairwise_rag_score": float(pairwise.get("b_score", -1.0)),

                "is_law_related": int(is_law_related),
                "score_diff": round(rag_score - baseline_score, 2),
                "final_score_diff": round(rag_final_score - baseline_final_score, 2),
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
        "rag_mode": "project_rag_pipeline_with_retry",
        "score_version": score_version,
        "judge_context_mode": judge_context_mode,
        "pairwise_judge_enabled": enable_pairwise_judge,
        "rag_retry_on_refusal": rag_retry_on_refusal,
        "avg_baseline_score": avg("baseline_score"),
        "avg_rag_score": avg("rag_score"),
        "avg_score_diff": round(avg("rag_score") - avg("baseline_score"), 2),
        "avg_baseline_final_score": avg("baseline_final_score"),
        "avg_rag_final_score": avg("rag_final_score"),
        "avg_final_score_diff": round(avg("rag_final_score") - avg("baseline_final_score"), 2),
        "avg_baseline_latency_ms": avg("baseline_latency_ms"),
        "avg_rag_latency_ms": avg("rag_latency_ms"),
        "avg_baseline_cost_proxy_chars": avg("baseline_cost_proxy_chars"),
        "avg_rag_cost_proxy_chars": avg("rag_cost_proxy_chars"),
        "rag_better_count": sum(1 for r in results if r["rag_final_score"] > r["baseline_final_score"]),
        "baseline_better_count": sum(1 for r in results if r["rag_final_score"] < r["baseline_final_score"]),
        "tie_count": sum(1 for r in results if r["rag_final_score"] == r["baseline_final_score"]),
        # LLM 裁判汇总
        "avg_baseline_llm_score": avg("baseline_llm_score"),
        "avg_rag_llm_score": avg("rag_llm_score"),
        "avg_llm_score_diff": round(avg("rag_llm_score") - avg("baseline_llm_score"), 2),
        "llm_rag_better_count": sum(1 for r in results if r["rag_llm_score"] > r["baseline_llm_score"]),
        "llm_baseline_better_count": sum(1 for r in results if r["rag_llm_score"] < r["baseline_llm_score"]),
        "llm_tie_count": sum(1 for r in results if r["rag_llm_score"] == r["baseline_llm_score"]),
        "pairwise_rag_better_count": sum(1 for r in results if r["pairwise_winner"] == "B"),
        "pairwise_baseline_better_count": sum(1 for r in results if r["pairwise_winner"] == "A"),
        "pairwise_tie_count": sum(1 for r in results if r["pairwise_winner"] == "TIE"),
        "rag_retry_triggered_count": sum(1 for r in results if r.get("rag_run_mode") == "retry_skip_law_check"),
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
    parser.add_argument(
        "--score-version",
        choices=["v1", "v2"],
        default="v2",
        help="规则评分版本（默认 v2，更重视证据支持）",
    )
    parser.add_argument(
        "--judge-context-mode",
        choices=["shared_rag", "separate", "none"],
        default="shared_rag",
        help="裁判上下文模式：shared_rag(推荐)/separate/none",
    )
    parser.add_argument(
        "--disable-pairwise-judge",
        action="store_true",
        help="关闭成对裁判（默认开启）",
    )
    parser.add_argument(
        "--disable-rag-refusal-retry",
        action="store_true",
        help="关闭 RAG 拒答兜底重跑（默认开启）",
    )
    return parser.parse_args()


async def main_async() -> None:
    args = parse_args()
    dataset = load_jsonl(args.dataset)
    if not dataset:
        raise ValueError("测试集为空，请检查 dataset 文件")

    print(f"统一评测模型: {args.model_name}")
    print(f"评分版本: {args.score_version}")
    print(f"裁判上下文模式: {args.judge_context_mode}")
    print("\n==================== 评测开始 ====================")
    try:
        report = await evaluate(
            dataset,
            limit=args.limit,
            model_name=args.model_name,
            score_version=args.score_version,
            judge_context_mode=args.judge_context_mode,
            enable_pairwise_judge=not args.disable_pairwise_judge,
            rag_retry_on_refusal=not args.disable_rag_refusal_retry,
        )
        print("\n==================== 评测完成 ====================")
        write_outputs(args.output_dir, report)
    except Exception as e:
        print(f"\n[错误] 评测中断: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main_async())