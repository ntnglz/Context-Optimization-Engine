# Context Optimization Engine (COE)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-238-green.svg)](#try-it-now)
[![Version](https://img.shields.io/badge/version-1.0.2-blue.svg)](CHANGELOG.md)

**Compact LLM context without losing facts.** COE reorganizes and deduplicates RAG chunks, chat history, tools, and code before they reach the model. It complements [PCM](https://github.com/ntnglz/Prompt-Compression-Middleware) (instructions).

```
Raw blocks  →  COE  →  compact prose  →  LLM
```

COE **does not summarize**. It removes redundancy and groups facts — measurable in benchmarks.

## Try it now

```bash
git clone https://github.com/ntnglz/Context-Optimization-Engine.git
cd Context-Optimization-Engine
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python run.py --demo          # canonical EN RAG example
python run.py --quickstart    # demo + copy-paste Python snippet
python run.py --test          # pytest suite
```

No editable install? Use `pip install -r requirements.txt` and `export PYTHONPATH=src` instead.

## Example (before → after)

**Input** — three RAG chunks with repetition:

```
[A] Company: ACME / Juan works at ACME.
[B] Company: ACME / Budget: 50k / Juan approved the budget.
[C] Company: ACME / Pedro works at ACME.
```

**Output** (`levels=[1, 2]`, `locale="en"`) — one line per entity, shared facts merged:

```
Company: ACME
Juan works at ACME and approved the budget.
Budget: 50k
Pedro works at ACME.
```

```python
from coe import optimize_context
from coe.models import ContextBlock

out = optimize_context(
    [
        ContextBlock(id="A", content="Company: ACME\nJuan works at ACME.", source_type="rag"),
        ContextBlock(id="B", content="Company: ACME\nBudget: 50k\nJuan approved the budget.", source_type="rag"),
        ContextBlock(id="C", content="Company: ACME\nPedro works at ACME.", source_type="rag"),
    ],
    levels=[1, 2],
    locale="en",
)
print(out.text)
# ~33 → ~22 tokens in smoke benchmarks
```

## Three ways to integrate

| Path | When | Quick start |
|------|------|-------------|
| **Python** | Pipelines, notebooks | `from coe import optimize_context` |
| **MCP** | Cursor, Claude Desktop | `python scripts/mcp/run_server.py` |
| **HTTP** | RAG / microservices | `python scripts/http/run_server.py` → `:8080` |

Step-by-step guide: **[docs/getting-started.md](docs/getting-started.md)**  
FAQ: **[docs/FAQ.md](docs/FAQ.md)**  
JSON examples: **[data/examples/](data/examples/)**

### MCP in Cursor

```bash
python scripts/mcp/print_cursor_config.py   # prints JSON with absolute paths
```

Or manually in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "coe": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/Context-Optimization-Engine/scripts/mcp/run_server.py"]
    }
  }
}
```

### HTTP

```bash
curl -s -X POST http://127.0.0.1:8080/optimize \
  -H 'Content-Type: application/json' \
  -d @data/examples/http_optimize_rag.json
```

## Choosing options (plain language)

| `levels` | What it does | When |
|----------|--------------|------|
| `[1]` | Line deduplication | Repeated lines across chunks |
| `[1, 2]` | Dedup + entity grouping | **Default for narrative RAG** |
| `[1, 2, 3, 4]` | + relations & graph slice | Complex multi-entity context |
| includes `5` + `session_id` | Session memory | Multi-turn agents |

| Parameter | Use |
|-----------|-----|
| `locale` | `"en"`, `"es"`, `"zh"` — prose patterns |
| `l0=True` + `target_lang` | Unify context language before processing |
| `source_type` | `rag`, `code`, `structured`, `glossary`, … |

Technical reference (ES): [docs/levels.md](docs/levels.md) · [docs/ingest.md](docs/ingest.md)

## When not to use COE

- Context is already under ~200 tokens with no repetition.
- You need a **generative summary** (COE is deterministic, not abstractive).
- Payload is purely tabular and you want raw JSON/CSV unchanged.
- You have not retrieved context yet — COE optimizes text you already have.

## Documentation

| For… | Document |
|------|----------|
| **Integrate without reading the pipeline** | [getting-started.md](docs/getting-started.md) |
| FAQ | [FAQ.md](docs/FAQ.md) |
| Vision & v1 comparison | [vision.md](docs/vision.md) |
| Design (pipeline internals) | [architecture.md](docs/architecture.md) *(ES)* |
| **Maintainers** | [STATUS.md](docs/STATUS.md) · [execution-plan.md](docs/execution-plan.md) *(ES)* |

Spanish user docs (archive): [docs/es/](docs/es/)

## PCM + COE

```
User → PCM (instruction) → COE (context) → Model Adapter → LLM
```

| Project | Optimizes |
|---------|-----------|
| [PCM](https://github.com/ntnglz/Prompt-Compression-Middleware) | Instructions |
| **COE** (this repo) | Knowledge / context |

## Repository layout

```
src/coe/          # gateway, ingest, levels, mcp, http
docs/             # specs + getting-started
data/examples/    # demo payloads
tests/            # pytest
scripts/          # mcp, http, benchmark, ci
```

## License

MIT — see [LICENSE](LICENSE). Changes: [CHANGELOG.md](CHANGELOG.md).
