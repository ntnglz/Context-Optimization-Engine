# Benchmark results — token savings

> Auto-generated from `data/benchmarks/baselines/`. Do not edit by hand — run `python scripts/benchmark/generate_savings_report.py`.

COE optimizes **context** you already retrieved. Savings depend on repetition and structure; these smoke cases use narrative RAG with duplicated facts across chunks.

## Summary

- **Typical token reduction** (recommended `levels=[1, 2]`): **~32–46%**
- **No extra LLM** — deterministic pipeline; savings are measured, not generated
- **Quality preserved** — smoke gate requires high factual recall and comprehension similarity

## Results by profile

### `n1_n2_en`

Dedup + entity grouping (EN) — **default for narrative RAG**

- `factual_recall_mean`: 1.00
- `comprehension_similarity_mean`: 1.00

| Case | Before | After | Tokens saved | Reduction |
|------|--------|-------|--------------|-----------|
| `acme_budget_v1` | 43 | 28 | 15 | 35% |
| `acme_team_v1` | 19 | 13 | 6 | 32% |

### `n1_n2_es`

Dedup + entity grouping (ES)

- `factual_recall_mean`: 1.00
- `comprehension_similarity_mean`: 1.00

| Case | Before | After | Tokens saved | Reduction |
|------|--------|-------|--------------|-----------|
| `acme_budget_es_v1` | 44 | 29 | 15 | 34% |

### `n1_n2_zh`

Dedup + entity grouping (ZH)

- `factual_recall_mean`: 1.00
- `comprehension_similarity_mean`: 1.00

| Case | Before | After | Tokens saved | Reduction |
|------|--------|-------|--------------|-----------|
| `acme_budget_zh_v1` | 24 | 13 | 11 | 46% |

## Illustrative monthly cost

Using `acme_budget_v1` (`43` → `28` tokens):

| Assumption | Value |
|------------|-------|
| Requests per day | 10,000 |
| Input price | $2.50 / 1M tokens |
| Tokens saved per request | 15 |
| **Estimated monthly savings** | **~$11** |

Adjust inputs for your model pricing and traffic. COE adds negligible latency (smoke p95 &lt; 1 ms on these cases).

## Try on your data

**Python** — check `out.metrics` after `optimize_context(...)`:

```python
from coe import optimize_context
out = optimize_context(blocks, levels=[1, 2], locale="en")
print(out.metrics.original_tokens, out.metrics.optimized_tokens)
```

**MCP / HTTP** — `estimate_savings` returns metrics without optimized prose:

```bash
curl -s -X POST http://127.0.0.1:8080/estimate \
  -H 'Content-Type: application/json' \
  -d @data/examples/acme_rag_en.json
```

## Reproduce

Smoke benchmarks (mock evaluator, no Ollama):

```bash
python run.py --ci
# or a single profile:
python scripts/benchmark/run.py --tier smoke --profile n1_n2_en \
  --compare-baseline data/benchmarks/baselines/n1_n2_en_smoke.json
```

Refresh baselines after intentional pipeline changes — see `data/benchmarks/baselines/README.md`.

Regenerate this page:

```bash
python scripts/benchmark/generate_savings_report.py
```

