# Nivel 1 — Eliminación de redundancias

> Definición conceptual (ejemplo ACME, niveles superiores, CIR): ver el [documento fundacional](Context%20Optimization%20Engine%20(COE).md#nivel-1--eliminación-de-redundancias).

## Objetivo en este repo

Implementación determinista del Nivel 1: detectar líneas idénticas (tras normalización) que aparecen en **≥2 bloques de contexto** y extraerlas a hechos compartidos con referencias, sin eliminar información.

> **Render hacia el LLM:** solo prosa vía `render_prose()` ([renderer.md](renderer.md)). El formato compacto actual (`Empresa=ACME`, `Referencias:`) es **`render_compact()`** — interno/legacy hasta migración Gateway.

## Alineación con la visión fundacional

| Principio ([COE].md) | Cómo lo cumple N1 |
|----------------------|-------------------|
| Optimizar contexto, no resumir | Extrae duplicados inter-bloque; reconstrucción total |
| Matching sintáctico | Línea idéntica tras normalización; sin semántica |
| Camino hacia pipeline | Entrada `ContextBlock[]` post-[Ingest](ingest.md) |

[COE]: Context%20Optimization%20Engine%20(COE).md

## Naturaleza del procesado

| Aspecto | Nivel 1 |
|---------|---------|
| **Persistencia** | No. Stateless: procesa la entrada del turno y devuelve salida al pipeline. No guarda estado entre invocaciones. |
| **Tipo de matching** | **Sintáctico**, no semántico — **independiente del idioma** (Unicode; normalización neutral) |
| **Unidad** | Línea completa (no párrafos ni frases sueltas) |
| **Idioma** | Si [L0](l0-ingest.md) está activo, N1 recibe bloques ya en `target_lang`; ver [i18n.md](i18n.md) |

El matching es **sintáctico**: dos líneas se consideran duplicadas solo si, tras normalizar espacios y mayúsculas, son **idénticas carácter a carácter**. No se detecta la misma idea expresada con otras palabras, ni variaciones leves del texto.

**Sí se deduplica** (misma línea, distinto bloque):

```
Empresa: ACME     ↔     empresa: acme
```

**No se deduplica** (equivalente semántico, texto distinto):

```
Empresa: ACME     ✗     La empresa es ACME
Cliente: Globex   ✗     Cliente = Globex
Presupuesto: 50k  ✗     Presupuesto de 50.000 €
```

La deduplicación semántica o por similitud queda fuera del alcance de N1; niveles posteriores o técnicas distintas podrían abordarla.

## Entrada / salida

**Entrada:** lista de `ContextBlock(id, content)`.

**Salida:** `DeduplicationResult` con:

- `shared_facts` — líneas repetidas en formato compacto (`clave=valor` si la línea usa `:`)
- `unique_blocks` — contenido que solo aparece en un bloque
- métricas de tokens estimados

Ejemplo (mismo caso que en el documento fundacional):

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
result.render_prose()       # → LLM (vía Renderer; por implementar)
result.render_compact()     # legacy; alias render()
result.compression_ratio
result.to_json()
```

Parámetro `min_occurrences=2` (por defecto): mínimo de bloques distintos donde debe aparecer una línea para extraerla.

## Reglas de matching

- Comparación **sintáctica**: igualdad de línea tras `strip`, colapso de espacios y **case-insensitive** (`casefold`).
- Una línea repetida solo dentro del **mismo** bloque no se extrae (no es redundancia inter-bloque).
- Si no hay hechos compartidos, la salida conserva el contexto original sin reformatear.

## Límites del prototipo

- Solo duplicados **exactos** a nivel de línea; **sin** similitud semántica, embeddings ni fuzzy matching.
- Sin persistencia ni estado entre peticiones (stateless).
- Sin integración MCP ni pipeline PCM todavía.
- Conteo de tokens aproximado (`len(text) // 4`).

## Siguiente nivel

→ [level2.md](level2.md) — factorización por entidad ✅ spec aprobada

Índice del pipeline: [levels.md](levels.md)
