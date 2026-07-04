# Renderer — serialización hacia el LLM

> Política transversal acordada en [spec-gaps.md](spec-gaps.md) §1 · Ensamblaje con PCM: [architecture.md](architecture.md) §2

**Estado:** spec transversal ✅ cerrada · implementación parcial (`level1/render.py`)

## Regla central

**El LLM destino solo recibe prosa en lenguaje natural** en `target_lang` (post-L0). Cualquier notación compacta (`clave=valor`, `entity:`, `node:`, JSON de grafo) es **interna** o de **depuración**, salvo pasar benchmark E2E completo incluyendo `readability_score` — en v1 **no se usa** como atajo.

```
Pipeline interno (compacto)  →  Renderer.render_prose()  →  LLM
```

---

## Responsabilidades

| Hace | No hace |
|------|---------|
| Proyectar salida de cada nivel a **oraciones completas** | Traducir idioma (L0) |
| Concatenar bloques en orden acordado | Comprimir instrucción PCM |
| Aplicar plantillas por `locale` | Elegir retrieval RAG |
| Etiquetas de sección i18n (`target_lang`) | Resolver conflictos semánticos (N5 merge) |

---

## API por nivel (convención)

| Nivel | Método hacia LLM | Interno / debug |
|-------|------------------|-----------------|
| **N1** | `render_prose()` | `render_compact()` — alias legacy `render()` |
| **N2** | `render_prose(mode="prose_compact")` **default** | `render_structured()` |
| **N3** | `render_prose()` | `render_debug()`, `to_cir_draft()` |
| **N4** | `ContextGraph.render_prose()` | `serialize_internal()` |
| **N5** | `StateView.render()` | trace, diff interno |

**Default N2:** `prose_compact`. Modo `structured` solo en logs/tests internos hasta revalidación benchmark.

### N1 — migración

Implementación actual (`Empresa=ACME`, `Referencias:`) pasa a **`render_compact()`**. Nuevo **`render_prose()`**:

```
The following facts are shared across sources A, B, and C: ACME is the company. …
Unique content from source B: …
```

Etiquetas («Shared facts», «Source B») vienen de **plantillas locale**, no hardcode en español.

---

## Ensamblaje Gateway (`optimize_context`)

Orden de concatenación v1:

```
1. [Opcional] StateView.render()           # solo si N5 activo
2. Bloques del turno en orden Ingest       # render_prose() por cadena N1–N4
3. Sin duplicar: si N5 merge incluyó turno en head → omitir paso 2
```

Delimitadores entre secciones (configurable):

```
--- session state ---
… prosa estado …

--- context ---
… prosa turno …
```

Separador default: `\n\n---\n\n` · desactivable (`options.section_delimiters=false`).

---

## Integración PCM / messages[]

COE entrega **`optimized_context: str`**. El **cliente** monta:

| Rol | Contenido típico |
|-----|------------------|
| `system` | Instrucción PCM + «Responde en `{response_lang}`» + aviso si contexto ≠ idioma usuario |
| `user` | Pregunta del usuario |
| `user` o `system` | Bloque `optimized_context` (convención de producto; COE no impone) |

Recomendación v1: contexto optimizado en **mensaje separado** antes del user turn, para no mezclar con compresión PCM de la pregunta.

---

## Política de prohibiciones en prosa

Igual que N2/N3 — prohibido en salida Renderer hacia LLM:

- `entity:`, `node:`, `edge:`, `[E1]`, diffs `+edge(…)`
- Pronombres ambiguos con varias entidades en scope
- JSON/array crudo salvo `source_type: structured` en passthrough literal

Validación: [benchmarks.md](benchmarks.md) `artifact_leak_rate`.

---

## Model Adapter (después del Renderer)

Orden del pipeline completo:

```
COE Renderer → optimized_context (prosa)
      ↓
Model Adapter (opcional) → ajuste formato/tokenizer del modelo destino
      ↓
LLM
```

Model Adapter **no** cambia idioma ni estructura semántica; puede reordenar bullets, preferir markdown vs plain, etc. Spec detallada: fase posterior; ver [architecture.md](architecture.md) §3.4.

---

## Documentos relacionados

| Documento | Relación |
|-----------|----------|
| [ingest.md](ingest.md) | Orden de bloques, provenance |
| [level2.md](level2.md) | Modos factorización |
| [level5.md](level5.md) | StateView sin duplicar turno |
| [benchmarks.md](benchmarks.md) | Legibilidad y fugas |
