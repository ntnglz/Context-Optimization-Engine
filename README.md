# Context Optimization Engine (COE)

Motor de optimización de contexto para sistemas basados en LLM. Complementa a [PCM](https://github.com/ntnglz/Prompt-Compression-Middleware): mientras PCM comprime **instrucciones**, COE optimiza el **conocimiento** (RAG, historial, herramientas, código).

```
Contexto bruto (N bloques)  →  COE  →  Representación compacta  →  LLM
```

## Estado

| Componente | Spec | Implementación |
|------------|------|----------------|
| [Visión fundacional](docs/Context%20Optimization%20Engine%20(COE).md) | ✅ | — |
| [Diseño global](docs/architecture.md) | ✅ | Parcial |
| [Pipeline L0 → N1–N5](docs/levels.md) | ✅ | L0 v1 · N1 · N2 · N5 v1 · N3/N4 pendientes |
| [Multilingüe (i18n)](docs/i18n.md) | ✅ | Locale packs N2 EN/ES en código |
| [L0 Ingest](docs/l0-ingest.md) | ✅ | v1 (heurística + ES→EN) |
| [Context Ingest](docs/ingest.md) | ✅ | Parcial (`ContextBlock` + L0) |
| [Renderer](docs/renderer.md) | ✅ | N1/N2 `render_prose` |
| [Benchmarks y KPIs](docs/benchmarks.md) | ✅ | — |
| [Harness de benchmarks](docs/benchmark-harness.md) | ✅ | ✅ H1–H5 · CI smoke (5 perfiles) |
| [Nivel 1](docs/level1.md) | ✅ | ✅ |
| [Nivel 2](docs/level2.md) | ✅ | ✅ v1 (EN/ES) |
| [Nivel 3](docs/level3.md) | ✅ | ✅ v1 (relaciones tipadas) |
| [Nivel 4](docs/level4.md) | ✅ | Pendiente |
| [Nivel 5](docs/level5.md) | ✅ | v1 (`StateView`, store in-memory) |
| **Gateway** (`optimize_context`) | — | L0 + N1 + N2 + N3 + N5 |

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

# Benchmark smoke (mock, compare baselines)
python scripts/benchmark/run.py --tier smoke --profile n1_n2_en \
  --compare-baseline data/benchmarks/baselines/n1_n2_en_smoke.json
```

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
│   ├── benchmarks.md       # KPIs comprensión, redacción, latencia
│   ├── spec-gaps.md        # Checklist cierre pre-implementación
│   ├── ingest.md           # Context Ingest + Normalizer
│   ├── renderer.md         # Prosa hacia LLM
│   ├── level1.md … level5.md
├── src/coe/
│   ├── gateway.py            # optimize_context — L0, N1, N2, N5
│   ├── models.py             # ContextBlock, resultados por nivel
│   ├── ingest/               # L0 normalize_language
│   ├── level1/               # Deduplicación
│   ├── level2/               # Factorización (locale EN/ES)
│   ├── level3/               # Estructuración relacional
│   ├── level5/               # StateView, sesión multi-turno
│   ├── renderer/             # Plantillas prosa N1
│   └── benchmark/            # Harness H1–H5
├── scripts/benchmark/        # run.py, compare.py
├── data/
│   ├── examples/             # Demo N1 (ACME)
│   └── benchmarks/           # Casos, perfiles, baselines, runs
├── tests/                    # pytest (~82 tests)
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
