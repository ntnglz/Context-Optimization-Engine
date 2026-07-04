# Context Optimization Engine (COE)

Motor de optimización de contexto para sistemas basados en LLM. Complementa a [PCM](https://github.com/ntnglz/Prompt-Compression-Middleware): mientras PCM comprime **instrucciones**, COE optimiza el **conocimiento** (RAG, historial, herramientas, código).

```
Contexto bruto (N bloques)  →  COE  →  Representación compacta  →  LLM
```

## Estado

| Componente | Estado |
|------------|--------|
| [Visión fundacional](docs/Context%20Optimization%20Engine%20(COE).md) | ✅ |
| [Índice docs](docs/vision.md) | ✅ |
| [Diseño global](docs/architecture.md) | ✅ |
| [Pipeline N1–N5](docs/levels.md) | 📝 Specs en revisión |
| [L0 + i18n](docs/l0-ingest.md) | 📝 Spec (sin implementar) |
| [Nivel 1 — spec](docs/level1.md) | ✅ Aprobado |
| Nivel 1 — implementación | ✅ Prototipo |
| N2–N5 — specs | 📝 Sin implementar |

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
│   ├── level1.md … level5.md
├── src/coe/
│   ├── models.py             # ContextBlock, DeduplicationResult
│   └── level1/
│       ├── deduplicator.py   # Nivel 1: eliminación de redundancias
│       └── render.py         # Serialización legible para LLM
├── data/examples/
│   └── level1_acme.json      # Ejemplo ACME (documento fundacional)
├── tests/
│   └── test_level1.py
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
