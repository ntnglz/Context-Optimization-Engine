# Context Optimization Engine (COE)

> **Legacy Spanish user docs.** Canonical documentation is English at the repo root.

Motor de optimización de **contexto** para LLM: RAG, historial, tools, código. Complementa a [PCM](https://github.com/ntnglz/Prompt-Compression-Middleware) (instrucciones).

```
Bloques crudos  →  COE  →  Prosa compacta  →  LLM
```

COE **no resume**: reorganiza y deduplica sin perder hechos medibles en benchmarks.

## Probar ahora

```bash
git clone https://github.com/ntnglz/Context-Optimization-Engine.git
cd Context-Optimization-Engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src

python run.py --demo          # dedup ACME (N1)
python run.py --test          # 234 tests
```

## Ejemplo (antes → después)

**Entrada** — tres chunks RAG con repetición:

```
[A] Company: ACME / Juan works at ACME.
[B] Company: ACME / Budget: 50k / Juan approved the budget.
[C] Company: ACME / Pedro works at ACME.
```

**Salida** (`levels=[1, 2]`, `locale="en"`) — una línea por entidad, hechos compartidos fusionados:

```
Company: ACME
Client: Globex
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
# ~44 → ~29 tokens típico en smoke benchmark
```

## Tres formas de integrar

| Camino | Cuándo | Arranque |
|--------|--------|----------|
| **Python** | Pipelines, notebooks | `from coe import optimize_context` |
| **MCP** | Cursor, Claude Desktop | `python scripts/mcp/run_server.py` |
| **HTTP** | RAG / microservicios | `python scripts/http/run_server.py` → `:8080` |

Guía paso a paso: **[docs/getting-started.md](docs/getting-started.md)**  
Preguntas frecuentes: **[docs/FAQ.md](docs/FAQ.md)**  
Ejemplos JSON: **[data/examples/](data/examples/)**

### MCP en Cursor

```json
{
  "mcpServers": {
    "coe": {
      "command": "/ruta/.venv/bin/python",
      "args": ["/ruta/Context-Optimization-Engine/scripts/mcp/run_server.py"]
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

## Opciones habituales

| Parámetro | Uso |
|-----------|-----|
| `levels=[1, 2]` | RAG narrativo (dedup + factorización) |
| `levels` con `5` + `session_id` | Chat multi-turno con memoria |
| `locale` | `"en"`, `"es"`, `"zh"` |
| `l0=True` + `target_lang` | Unificar idioma del contexto |
| `source_type` | `rag`, `code`, `structured`, `glossary`, … |

## Documentación

| Para… | Documento |
|-------|-----------|
| **Integrar sin leer el pipeline** | [getting-started.md](docs/getting-started.md) |
| FAQ | [FAQ.md](docs/FAQ.md) |
| Visión y comparativa v1 | [vision.md](docs/vision.md) |
| Diseño (N1–N5, CIR) | [architecture.md](docs/architecture.md) |
| **Maintainers** (estado, fases) | [STATUS.md](docs/STATUS.md) · [execution-plan.md](docs/execution-plan.md) |

## PCM + COE

```
Usuario → PCM (instrucción) → COE (contexto) → Model Adapter → LLM
```

| Proyecto | Optimiza |
|----------|----------|
| [PCM](https://github.com/ntnglz/Prompt-Compression-Middleware) | Instrucciones |
| **COE** (este repo) | Conocimiento / contexto |

## Estructura del repo

```
src/coe/          # gateway, ingest, level1–5, mcp, http
docs/             # specs + getting-started
data/examples/    # payloads demo
tests/            # pytest
scripts/          # mcp, http, benchmark, ci
```

## Licencia

MIT — ver [LICENSE](LICENSE). Cambios: [CHANGELOG.md](CHANGELOG.md).
