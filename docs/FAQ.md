# Frequently asked questions (COE)

Short answers for integrators. Technical detail in [getting-started.md](getting-started.md) and specs in `docs/level*.md` *(ES)*.

## Does COE summarize or drop information?

**No.** It reorganizes and deduplicates; benchmarks require high `factual_recall`. COE is not a generative summarizer.

## When should I **not** use COE?

- Context is already tiny (<~200 tokens) with no repetition.
- You need abstractive summarization, not deterministic compaction.
- You want raw JSON/CSV/tables unchanged in the prompt.
- You have not retrieved context yet — COE optimizes text you already have.

## Does COE replace my vector DB or RAG retriever?

**No.** It optimizes the **text** you already retrieved (chunks, history, tool outputs) before sending it to the LLM.

## How is COE different from PCM?

| | PCM | COE |
|---|-----|-----|
| Optimizes | Instructions / system prompt | Context (knowledge) |
| Repo | [Prompt-Compression-Middleware](https://github.com/ntnglz/Prompt-Compression-Middleware) | this repo |

Use together: [getting-started.md § PCM+COE](getting-started.md#pcm--coe).

## MCP or HTTP?

| | MCP | HTTP |
|---|-----|-----|
| Typical use | Cursor, Claude Desktop, local agents | RAG pipelines, microservices |
| Start | `python scripts/mcp/run_server.py` | `python scripts/http/run_server.py` |

Same JSON contract for blocks and options.

## What should I put in `levels`?

| `levels` | Typical effect |
|----------|----------------|
| `[1]` | Deduplicate repeated lines |
| `[1, 2]` | + group facts by entity (**recommended for narrative RAG**) |
| `[1, 2, 3, 4]` | + relations and turn graph |
| includes `5` | Persistent session state (`session_id` required) |

Start with `[1, 2]` for narrative RAG. The `source_type` matrix may limit levels — see [ingest.md](ingest.md) *(ES)*.

## What savings should I expect?

Smoke benchmarks on narrative RAG (`levels=[1, 2]`) show **~32–46%** fewer context tokens — see [benchmark-results.md](benchmark-results.md) for reproducible tables. Actual savings depend on repetition and structure — run `estimate_savings` or check `out.metrics` on your data. Not a guarantee.

## Do I need MCP in `requirements.txt` for library-only use?

**No.** Use optional extras: `pip install -e ".[dev]"` for the library; add `[mcp]` or `[http]` only when you need those servers.

## When do I need `session_id`?

When you enable **session memory** (level 5): multi-turn conversations where the agent accumulates state instead of resending raw history.

## What is `locale` vs `target_lang`?

- **`target_lang`** + **`l0=True`**: language of **context** toward the LLM (pre-processing translation).
- **`locale`**: prose patterns for entity grouping and relations (EN, ES, ZH).
- **`response_lang`**: user-facing reply language (PCM/system; COE does not translate the response).

See [i18n.md](i18n.md) *(ES)*.

## Does the LLM receive graphs or CIR?

**Not in production.** COE projects to **natural prose** via the Renderer. CIR/graph is internal and used for session store.

## What are v1 limitations?

- Entity grouping / relations: heuristics + locale packs (not a universal semantic parser).
- L0 in CI: stub ES→EN / EN→ZH; production can inject `DeepTranslatorBackend`.
- Store: local filesystem or SQLite (no Redis/cloud in v1).
- Full locale packs: EN, ES, ZH.

## How do I verify nothing broke?

```bash
python run.py --ci
```

CI runs locally (GitHub Actions disabled). See [.github/workflows/README.md](../.github/workflows/README.md).

## Where is the internal design?

[architecture.md](architecture.md), [levels.md](levels.md), [execution-plan.md](execution-plan.md) *(ES)*.
