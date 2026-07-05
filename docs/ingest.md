# Context Ingest — modelo de entrada

> L0 idioma: [l0-ingest.md](l0-ingest.md) · Normalizer · matriz niveles · [architecture.md](architecture.md) §3

**Estado:** spec transversal ✅ cerrada · **v1 implementado** (`src/coe/ingest/` · `ingest_context`, `ContextBundle`)

## Objetivo

Convertir fuentes heterogéneas (RAG, historial, tools, código…) en un **`ContextBundle`** uniforme que el pipeline L0→N1–N5 pueda procesar con trazabilidad y reglas por tipo de contenido.

```
Fuentes → Ingest (+ Normalizer) → [L0 opcional] → N1 → …
```

---

## ContextBundle

Contenedor de una petición de optimización:

```
ContextBundle
├── blocks: ContextBlock[]
├── target_lang: str | None          # L0
├── locale: str | None               # locale pack N2+ (default alineado con target_lang)
├── query_context: str | None        # consulta actual (slice N4/N5); ver § query_context
├── response_lang: str | None        # idioma respuesta usuario (PCM); no lo traduce COE
├── session_id: str | None           # obligatorio si levels incluye 5
└── options: IngestOptions
```

### ContextBlock

```
ContextBlock
├── id: str                          # estable en el bundle; usado en source_refs
├── content: str                     # texto bruto post-normalizer
├── source_type: SourceType          # ver matriz §
├── detected_lang: str | None        # post-L0 autodetect
├── token_estimate: int | None       # opcional; si no, Metrics estima
└── metadata: dict
      ├── preserve_lang: bool        # L0: no traducir
      ├── entity_aliases: str[]      # N5: alias → id canónico
      ├── source_uri: str | None     # proveniencia RAG (URL, path)
      ├── source_label: str | None   # «Documento A» para citas en prosa
      └── levels_override: int[] | None  # anular matriz global por bloque
```

**Orden:** los bloques conservan el orden de Ingest; el Renderer respeta ese orden al concatenar prosa (salvo N5 state primero — ver [renderer.md](renderer.md)).

---

## Normalizer (sub-etapa de Ingest)

Ejecuta **después** de asignar `id` y `source_type`, **antes** de L0 y N1.

| Función | v1 |
|---------|-----|
| Colapsar `\r\n` → `\n` | Sí |
| Segmentar en **líneas** para N1 | Default (`en`, `es`, …) |
| Segmentar en **oraciones** | Locale `zh` (fase locale pack) |
| Respetar fences ``` … ``` | No partir deduplicación N1 **dentro** de un fence |
| JSON pretty-print | Mantener como bloque `structured`; matriz limita niveles |

Normalizer **no** traduce ni comprime; solo prepara unidades atómicas.

---

## source_type — matriz de niveles activables

Niveles no listados heredan la config global del Gateway (`levels=[…]`). La matriz define **máximo** permitido por tipo; el cliente puede pedir menos.

| source_type | Descripción | L0 | N1 | N2 | N3 | N4 | N5 | Notas |
|-------------|-------------|----|----|----|----|----|-----|-------|
| `prose` | Texto natural, RAG narrativo | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Caso principal |
| `history` | Turnos conversación | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `session_id` si N5 |
| `rag` | Chunks recuperados | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `source_uri` recomendado |
| `tool` | Salida herramienta (texto) | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | N3/N4 si parseable como prosa |
| `structured` | JSON, logs, CSV | ⚠️ | ✅ | ❌ | ❌ | ❌ | ⚠️ | Solo N1 dedup líneas o passthrough |
| `code` | Código fuente | ❌* | ✅ | ❌ | ❌ | ❌ | ❌ | *L0 off; `translate_code_blocks=false` |
| `glossary` | Glosario bilingüe | ⚠️ | ✅ | ❌ | ❌ | ❌ | ✅ | `preserve_lang: true` típico |
| `memory` | Memoria agente externa | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Mismo contrato que `prose` |

Leyenda: ✅ permitido · ❌ no aplicar · ⚠️ degradación esperada / passthrough parcial.

Si un bloque pide un nivel no permitido → **skip nivel** para ese bloque + entrada en `trace` (no fallo fatal v1).

---

## query_context

Campo del bundle, **no** del mensaje PCM comprimido:

| Origen típico | Uso |
|---------------|-----|
| Último mensaje del usuario (texto) | Slice N4 / materialize N5 |
| Query explícita del agente | RAG re-ranking interno upstream |

Si está vacío: N4 usa grafo completo (si cabe en presupuesto); N5 materializa subgrafo por heurística recencia + `max_view_tokens`.

---

## Provenance (citas)

Para RAG y documentos:

1. Ingest rellena `metadata.source_label` y/o `source_uri`.
2. N1 `SharedFact.source_ids` referencia `block.id`.
3. N3+ propagan `source_refs[]` en entidades/nodos.
4. **`render_prose()`** puede incluir citas breves: «(source: doc-A)» si `options.cite_sources=true` (default **false** v1).

COE no sustituye al sistema de citas del agente; solo preserva ids para reconstrucción.

---

## Presupuesto de tokens (v1)

| Campo | Rol |
|-------|-----|
| `options.max_context_tokens` | Tope soft salida COE hacia LLM (post-Renderer) |
| N4/N5 slice | Recortan antes de superar tope (`build_context_graph_within_budget`, `query_slice`) |
| Ventana modelo (PCM + instrucción + respuesta) | Responsabilidad **cliente** hasta Gateway unificado (Fase 11) |

Si tras optimizar se supera `max_context_tokens` → truncar por prioridad: **turno reciente / query slice** > **vista de estado N5**; registrar `metrics.truncated: true` y `pre_truncation_tokens`.

Implementación: `src/coe/budget/` · Gateway `max_context_tokens` · MCP `estimate_savings` expone `truncated`.

---

## API prevista

```python
from coe.ingest import ingest_context

bundle = ingest_context(
    raw_blocks=[{"id": "doc-a", "text": "...", "source_type": "rag", "uri": "..."}],
    target_lang="en",
    locale="en",
    query_context="What is the ACME budget?",
    response_lang="es",   # para PCM; COE no traduce respuesta
)
bundle.blocks   # → L0 o N1
```

---

## Relación con otros docs

| Documento | Relación |
|-----------|----------|
| [l0-ingest.md](l0-ingest.md) | Traducción por bloque; `preserve_lang` |
| [i18n.md](i18n.md) | `target_lang`, `locale`, `response_lang` |
| [renderer.md](renderer.md) | Orden y prosa final |
| [level1.md](level1.md) | Unidad línea post-normalizer |

## Preguntas abiertas (no bloqueantes v1)

- [ ] ¿Ingest HTTP/MCP propio o solo librería?
- [ ] ¿Normalizar HTML/Markdown a texto plano en Ingest o upstream?
