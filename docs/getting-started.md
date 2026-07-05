# Guía de inicio — integrar COE sin conocer el pipeline

Esta guía es para **usar** COE (RAG, agentes, HTTP). No necesitas saber qué es N3 o CIR.

- FAQ: [FAQ.md](FAQ.md)
- Estado del proyecto (maintainers): [STATUS.md](STATUS.md)
- Diseño profundo: [architecture.md](architecture.md)

## Instalación

```bash
git clone https://github.com/ntnglz/Context-Optimization-Engine.git
cd Context-Optimization-Engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Añade el código al path de Python (desde la raíz del repo):

```bash
export PYTHONPATH=src
```

## Probar en 30 segundos

```bash
python run.py --demo
```

Verás deduplicación N1 sobre el ejemplo ACME (documentos A, B, C).

---

## Librería Python

### RAG one-shot (recomendado: N1 + N2)

```python
from coe import optimize_context
from coe.models import ContextBlock

blocks = [
    ContextBlock(id="A", content="Company: ACME\nJuan works at ACME.", source_type="rag"),
    ContextBlock(id="B", content="Company: ACME\nBudget: 50k\nJuan approved the budget.", source_type="rag"),
    ContextBlock(id="C", content="Company: ACME\nPedro works at ACME.", source_type="rag"),
]

out = optimize_context(blocks, levels=[1, 2], locale="en")
print(out.text)
print(out.metrics.compression_ratio, out.metrics.original_tokens, out.metrics.optimized_tokens)
```

Ejemplo JSON de bloques: [../data/examples/http_optimize_rag.json](../data/examples/http_optimize_rag.json)

### Sesión multi-turno (N5)

Turno 1 y turno 2 comparten `session_id`; COE acumula estado en store (filesystem por defecto).

```python
from coe import optimize_context
from coe.models import ContextBlock

session = "my-agent-session"

# Turno 1
optimize_context(
    [ContextBlock(id="t1-A", content="Company: ACME\nJuan works at ACME.", source_type="rag")],
    levels=[1, 4, 5],
    locale="en",
    session_id=session,
)

# Turno 2 — el estado previo se fusiona
out = optimize_context(
    [ContextBlock(id="t2-A", content="Company: ACME\nJuan approved the budget.", source_type="rag")],
    levels=[1, 4, 5],
    locale="en",
    session_id=session,
)
print(out.text)
```

Store SQLite (opcional):

```python
optimize_context(
    blocks,
    levels=[1, 5],
    session_id=session,
    state_store_backend="sqlite",
    state_store_path="data/sessions/agent.db",
)
```

### L0 — contexto en otro idioma (ES → EN)

```python
out = optimize_context(
    [
        ContextBlock(id="A", content="Empresa: ACME\nJuan trabaja en ACME."),
        ContextBlock(id="B", content="Empresa: ACME\nJuan aprobó el presupuesto."),
    ],
    levels=[1, 2],
    locale="en",
    target_lang="en",
    l0=True,
)
```

### Bloques `structured`, `code`, `glossary`

Use `ingest_context` o pasa bloques con `source_type`:

```python
from coe import ingest_context, optimize_context

ingested = ingest_context([
    {"id": "json-1", "source_type": "structured", "content": '{"company": "ACME", "budget": "50k"}'},
])
out = optimize_context(ingested.bundle, levels=[1])
```

Ejemplos: [../data/examples/structured_block.json](../data/examples/structured_block.json), [code_blocks.json](../data/examples/code_blocks.json), [glossary_block.json](../data/examples/glossary_block.json).

---

## MCP (Cursor, Claude Desktop)

### Arranque

```bash
pip install -r requirements-mcp.txt
python scripts/mcp/run_server.py
```

### Configuración Cursor

Ajustes → MCP → añadir servidor, o `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "coe": {
      "command": "/ruta/a/.venv/bin/python",
      "args": ["/ruta/absoluta/Context-Optimization-Engine/scripts/mcp/run_server.py"],
      "env": {}
    }
  }
}
```

### Herramientas

| Tool | Devuelve |
|------|----------|
| `optimize_context` | `text` (prosa) + `metrics` |
| `estimate_savings` | solo `metrics` (sin prosa) |

Payload de ejemplo: [../data/examples/mcp_optimize_rag.json](../data/examples/mcp_optimize_rag.json)

---

## HTTP API

### Arranque

```bash
pip install -r requirements-http.txt
python scripts/http/run_server.py
# http://127.0.0.1:8080
```

### Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio |
| POST | `/optimize` | Contexto optimizado + métricas |
| POST | `/estimate` | Solo métricas |

### Ejemplo curl

```bash
curl -s http://127.0.0.1:8080/health

curl -s -X POST http://127.0.0.1:8080/optimize \
  -H 'Content-Type: application/json' \
  -d @data/examples/http_optimize_rag.json
```

Cuerpo mínimo:

```json
{
  "blocks": [
    {"id": "A", "source_type": "rag", "content": "Company: ACME\nJuan works at ACME."},
    {"id": "B", "source_type": "rag", "content": "Company: ACME\nBudget: 50k\nJuan approved the budget."}
  ],
  "levels": [1, 2],
  "locale": "en"
}
```

Detalle en [architecture.md §7.3](architecture.md).

---

## PCM + COE

COE optimiza el **contexto**; PCM la **instrucción**. Composición en un solo flujo:

```python
from coe import optimize_with_pcm

result = optimize_with_pcm(
    context_blocks=[...],
    instruction="TASK=answer ...",
    levels=[1, 2],
    locale="en",
    max_window_tokens=8192,
)
# result.context_text, result.instruction_text, result.metrics
```

Requiere PCM instalado/configurado según [Fase 11](execution-plan.md) del plan.

---

## Opciones que más importan

| Parámetro | Cuándo usarlo |
|-----------|----------------|
| `levels` | `[1,2]` RAG; añade `5` + `session_id` para chat |
| `locale` | `"en"`, `"es"`, `"zh"` — patrones N2+ |
| `l0` + `target_lang` | Unificar idioma del contexto antes de N1 |
| `session_id` | Obligatorio con nivel 5 |
| `max_context_tokens` | Truncar salida si supera tope |
| `target_model` | Ajuste post-renderer (mistral, openai, …) |
| `query_context` | Slice N4/N5 hacia la pregunta actual |
| `source_type` | `rag`, `code`, `structured`, `glossary`, … — ver [ingest.md](ingest.md) |

### Métricas (`out.metrics`)

| Campo | Significado |
|-------|-------------|
| `original_tokens` | Entrada estimada |
| `optimized_tokens` | Salida prosa |
| `compression_ratio` | Ahorro relativo |
| `latency_ms` | Tiempo total |
| `truncated` | Se aplicó tope de tokens |

---

## Siguiente lectura

| Si quieres… | Lee |
|-------------|-----|
| Decidir niveles e ingest | [ingest.md](ingest.md), [levels.md](levels.md) |
| Multilingüe | [i18n.md](i18n.md), [l0-ingest.md](l0-ingest.md) |
| Benchmarks / calidad | [benchmarks.md](benchmarks.md) |
| Contribuir / roadmap | [execution-plan.md](execution-plan.md) |
