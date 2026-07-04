# Nivel 1 — Eliminación de redundancias

> Definición conceptual (ejemplo ACME, niveles superiores, CIR): ver el [documento de visión en PCM](https://github.com/ntnglz/Prompt-Compression-Middleware/blob/main/Context%20Optimization%20Engine%20(COE).md#nivel-1--eliminación-de-redundancias).

## Objetivo en este repo

Implementación determinista del Nivel 1: detectar líneas idénticas (tras normalización) que aparecen en **≥2 bloques de contexto** y extraerlas a hechos compartidos con referencias, sin eliminar información.

## Entrada / salida

**Entrada:** lista de `ContextBlock(id, content)`.

**Salida:** `DeduplicationResult` con:

- `shared_facts` — líneas repetidas en formato compacto (`clave=valor` si la línea usa `:`)
- `unique_blocks` — contenido que solo aparece en un bloque
- métricas de tokens estimados

Ejemplo (mismo caso que en PCM):

| Bloque | Contenido |
|--------|-----------|
| A | `Empresa: ACME` / `Cliente: Globex` |
| B | `Empresa: ACME` / `Presupuesto: 50k` |
| C | `Empresa: ACME` / `Cliente: Globex` |

```
Empresa=ACME
Referencias: A, B, C

Cliente=Globex
Referencias: A, C

[B]
Presupuesto: 50k
```

## API

```python
from coe.level1 import deduplicate_context
from coe.models import ContextBlock

result = deduplicate_context([
    ContextBlock(id="A", content="..."),
    ContextBlock(id="B", content="..."),
])
result.render()           # texto para LLM
result.compression_ratio    # ahorro estimado
result.to_json()            # depuración / pipelines
```

Parámetro `min_occurrences=2` (por defecto): mínimo de bloques distintos donde debe aparecer una línea para extraerla.

## Reglas de matching

- Comparación **case-insensitive** tras normalizar espacios.
- Una línea repetida solo dentro del **mismo** bloque no se extrae (no es redundancia inter-bloque).
- Si no hay hechos compartidos, la salida conserva el contexto original sin reformatear.

## Límites del prototipo

- Solo duplicados **exactos** a nivel de línea (no similitud semántica).
- Sin integración MCP ni pipeline PCM todavía.
- Conteo de tokens aproximado (`len(text) // 4`).

## Próximos pasos (COE)

1. Nivel 2 — factorización por entidad
2. Integración MCP (`optimize_context`)
3. Benchmark con contextos RAG reales
