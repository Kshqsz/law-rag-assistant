# RAG A/B 评测使用说明

## 1) 目标
同一批问题，比较：
- A 组：不使用 RAG（同一模型，直接输入用户问题，不使用项目检索与Prompt链路）
- B 组：使用当前系统 RAG（`law_qa_service.ask_question`，保持项目现有逻辑）

> 关键约束：A/B 两组强制使用同一个 `model_name`，仅是否启用 RAG 不同。

输出可用于论文与答辩的对比数据：
- 平均得分
- 得分差值（RAG - Baseline）
- 时延
- 近似成本（输出字符数代理）

## 2) 运行命令
在项目根目录执行：

```bash
python scripts/evaluate_rag_vs_base.py \
  --dataset tests/ab_eval_dataset.sample.jsonl \
  --output-dir evaluation_results \
  --model-name qwen-plus \
  --limit 0
```

说明：
- `--limit 0` 表示跑全部题目
- 先用 `--limit 5` 做冒烟测试再跑全量

## 3) 数据集格式（JSONL）
每行一个 JSON 对象：

```json
{
  "id": "LAW-001",
  "category": "刑法",
  "question": "不小心把人撞死了需要承担什么法律责任？",
  "expected_keywords": ["过失致人死亡", "刑事责任", "赔偿"],
  "expected_laws": ["刑法", "第233条"],
  "is_law_related": true
}
```

## 4) 输出文件
- `evaluation_results/ab_summary_*.json`：汇总指标
- `evaluation_results/ab_details_*.csv`：逐题明细

## 5) 指标口径（当前脚本）
- 法律问题：关键词命中、法律名命中、是否含法条引用、是否拒答
- 非法律问题：拒答为高分

> 该评分是“自动粗评”，建议再做一轮人工盲评（至少 30 题），将主观质量纳入论文结果。
