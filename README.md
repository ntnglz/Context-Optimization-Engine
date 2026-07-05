# Context Optimization Engine (COE)

Motor de optimización de contexto para sistemas basados en LLM. Complementa a [PCM](https://github.com/ntnglz/Prompt-Compression-Middleware): mientras PCM comprime **instrucciones**, COE optimiza el **conocimiento** (RAG, historial, herramientas, código).

```
Contexto bruto (N bloques)  →  COE  →  Representación compacta  →  LLM
```

## Estado

> Orden de trabajo: [execution-plan.md](docs/execution-plan.md) · **Fases 0–13 ✅** · activa: **Fase 14**

| Componente | Spec | Implementación |
|------------|------|----------------|
| [Visión fundacional](docs/Context%20Optimization%20Engine%20(COE).md) | ✅ | — |
| [Diseño global](docs/architecture.md) | ✅ | ✅ núcleo v1 (L0→N5, MCP, CIR) · integración v1 en curso (fases 8–18) |
| [Plan de ejecución](docs/execution-plan.md) | ✅ | Fases 0–6 cerradas |
| [Pipeline L0 → N1–N5](docs/levels.md) | ✅ | L0 v1 · N1 · N2 · N3 · N4 · N5 |
| [Multilingüe (i18n)](docs/i18n.md) | ✅ | Locale packs N2 EN/ES |
| [L0 Ingest](docs/l0-ingest.md) | ✅ | v2 (langdetect + TranslationBackend) |
| [Context Ingest](docs/ingest.md) | ✅ | ✅ `ingest_context`, `ContextBundle`, matriz `source_type` |
| [Renderer](docs/renderer.md) | ✅ | ✅ prosa N1–N5 vía `renderer/assembly.py` |
| [CIR v1.0](docs/cir-v1.md) | ✅ | ✅ grafo + envelope N5 (`src/coe/cir/`) |
| [Benchmarks y KPIs](docs/benchmarks.md) | ✅ | — |
| [Harness de benchmarks](docs/benchmark-harness.md) | ✅ | ✅ H1–H5 · CI smoke |
| [Evaluadores Ollama](docs/benchmark-ollama.md) | ✅ | Granite/Gemma fast · Qwen release |
| [Nivel 1](docs/level1.md) | ✅ | ✅ |
| [Nivel 2](docs/level2.md) | ✅ | ✅ (EN/ES) |
| [Nivel 3](docs/level3.md) | ✅ | ✅ (relaciones tipadas) |
| [Nivel 4](docs/level4.md) | ✅ | ✅ (`ContextGraph`, CIR materializado) |
| [Nivel 5](docs/level5.md) | ✅ | ✅ (graph merge, commits, `FilesystemStateStore`) |
| **Gateway** (`optimize_context`) | ✅ | ✅ L0 + N1–N5 + métricas |
| **MCP** (agentes) | ✅ | ✅ `optimize_context`, `estimate_savings` (stdio) |
| **HTTP API** (RAG / despliegue) | ✅ | ✅ `POST /optimize`, `POST /estimate`, `GET /health` |
| **Model Adapter** (`target_model`) | ✅ | ✅ `default`, `mistral`, `openai` post-renderer |

## Inicio rápido

```bash
git clone https://github.com/ntnglz/Context-Optimization-Engine.git
cd Context-Optimization-Engine

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Demo con el ejemplo de la visión (documentos A, B, C)
python run.py --demo

# Tests
python run.py --test

# CI local (pytest + 8 perfiles smoke, compare baseline — antes de push)
python run.py --ci
# equivalente: bash scripts/ci/smoke.sh

# Servidor MCP para agentes (Cursor, Claude Desktop)
pip install -r requirements-mcp.txt
python scripts/mcp/run_server.py

# Servidor HTTP (pipelines RAG, mismo contrato que MCP)
pip install -r requirements-http.txt
python scripts/http/run_server.py
# http://127.0.0.1:8080 — ver architecture.md §7.3
```

Ver configuración MCP en [architecture.md §7.2](docs/architecture.md) · HTTP en [§7.3](docs/architecture.md).

## Gateway (pipeline composable)

```python
from coe import optimize_context
from coe.models import ContextBlock

blocks = [
    ContextBlock(id="A", content="Juan works at ACME."),
    ContextBlock(id="B", content="Juan approved the budget."),
]

# N1 + N2 factorización (EN)
out = optimize_context(blocks, levels=[1, 2], locale="en")
print(out.text)

# L0 ES→EN + N1
out = optimize_context(
    blocks,
    levels=[1],
    locale="en",
    target_lang="en",
    l0=True,
)
```

## Nivel 1 — Deduplicación

Detecta líneas repetidas entre bloques de contexto y las extrae a hechos compartidos con referencias, sin eliminar información.

```python
from coe.level1 import deduplicate_context
from coe.models import ContextBlock

blocks = [
    ContextBlock(id="A", content="Empresa: ACME\nCliente: Globex"),
    ContextBlock(id="B", content="Empresa: ACME\nPresupuesto: 50k"),
    ContextBlock(id="C", content="Empresa: ACME\nCliente: Globex"),
]

result = deduplicate_context(blocks)
print(result.render())
print(f"Ahorro: {result.compression_ratio:.1%}")
```

Salida:

```
Empresa=ACME
Referencias: A, B, C

Cliente=Globex
Referencias: A, C

[B]
Presupuesto: 50k
```

## Estructura

```
Context-Optimization-Engine/
├── docs/
│   ├── Context Optimization Engine (COE).md   # Visión fundacional (canónica)
│   ├── vision.md           # Índice de documentación
│   ├── architecture.md     # Diseño global: piezas y relaciones
│   ├── levels.md           # Índice pipeline L0 → N1–N5
│   ├── i18n.md             # Multilingüe, target_lang, locale packs
│   ├── l0-ingest.md        # Spec L0 (pre-N1)
│   ├── execution-plan.md   # Orden de trabajo (fases 0–18)
│   ├── cir-v1.md           # CIR v1.0 congelado
│   ├── spec-gaps.md        # Checklist cierre + deuda → fase
│   ├── ingest.md           # Context Ingest + Normalizer
│   ├── renderer.md         # Prosa hacia LLM
│   ├── level1.md … level5.md
├── src/coe/
│   ├── gateway.py            # optimize_context — L0, N1–N5
│   ├── models.py             # ContextBlock, ContextGraph, resultados por nivel
│   ├── cir/                  # CIR v1.0 envelope (serialización N5)
│   ├── ingest/               # ingest_context, L0, normalizer
│   ├── level1/ … level5/
│   ├── mcp/                  # Servidor MCP (stdio)
│   ├── renderer/             # Ensamblaje prosa hacia LLM
│   └── benchmark/            # Harness H1–H5
├── scripts/
│   ├── benchmark/            # run.py, compare.py
│   ├── mcp/                  # run_server.py (stdio MCP)
│   └── ci/                   # smoke.sh, nightly-mock.sh, release-dev-agent.sh
├── data/
│   ├── examples/             # Demo N1 (ACME)
│   └── benchmarks/           # Casos, perfiles, baselines, runs
├── tests/                    # pytest (169 tests)
└── run.py
```

## Relación con PCM

La visión de COE vive en [Context Optimization Engine (COE).md](docs/Context%20Optimization%20Engine%20(COE).md) (este repo). PCM es el proyecto complementario de compresión de instrucciones.

| Proyecto | Repo | Optimiza |
|----------|------|----------|
| **PCM** | [Prompt-Compression-Middleware](https://github.com/ntnglz/Prompt-Compression-Middleware) | Instrucción (`TASK=review …`) |
| **COE** | este repo | Contexto (`Empresa=ACME` + refs) |

## Licencia

MIT (pendiente de formalizar)
