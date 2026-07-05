# Niveles de optimización — índice

> Definición conceptual de los cinco niveles: [documento fundacional](Context%20Optimization%20Engine%20(COE).md#niveles-de-optimización).  
> Diseño global de piezas: [architecture.md](architecture.md).  
> Multilingüe / L0: [i18n.md](i18n.md) · [l0-ingest.md](l0-ingest.md).

COE aplica **transformaciones composables** sobre el contexto. **L0** (Ingest) precede a los niveles N1–N5 y **no es un nivel de optimización**: unifica idioma antes de comprimir.

## Specs transversales

| Documento | Contenido | Estado |
|-----------|-----------|--------|
| [i18n.md](i18n.md) | Principios multilingües, locale packs | ✅ Aprobado |
| [l0-ingest.md](l0-ingest.md) | Normalización de idioma (Ingest) | ✅ Aprobado · **v1 implementado** |
| [benchmarks.md](benchmarks.md) | KPIs comprensión, redacción, latencia COE | ✅ Aprobado · **harness implementado** |
| [benchmark-harness.md](benchmark-harness.md) | Diseño harness (capas, CI, schema) | ✅ Implementado (H1–H5) |
| [spec-gaps.md](spec-gaps.md) | Checklist cierre pre-implementación | ✅ Cerrado |
| [ingest.md](ingest.md) | Context Ingest + Normalizer | ✅ Cerrado |
| [renderer.md](renderer.md) | Prosa obligatoria hacia LLM | ✅ Cerrado |

## Specs operativas N1–N5

| Nivel | Nombre | Spec | Implementación |
|-------|--------|------|----------------|
| **1** | Eliminación de redundancias | [level1.md](level1.md) | ✅ Completo |
| **2** | Factorización | [level2.md](level2.md) | ✅ v1 (locale EN/ES) |
| **3** | Representación estructurada | [level3.md](level3.md) | ✅ v1 (relaciones `knows`, proyección prosa) |
| **4** | Grafo de conocimiento | [level4.md](level4.md) | ✅ v1 (ContextGraph, slice, proyección prosa) |
| **5** | Estado semántico | [level5.md](level5.md) | ✅ v2 (graph merge, StateView, store in-memory) |

## Pipeline

```mermaid
flowchart LR
    IN[ContextBlock[]]
    L0[L0 Idioma\nopcional]
    N1[N1 Deduplicación]
    N2[N2 Factorización]
    N3[N3 Estructura]
    N4[N4 Grafo]
    N5[N5 Estado]
    OUT[Salida optimizada]

    IN --> L0 --> N1 --> N2 --> N3 --> N4 --> N5 --> OUT
```

- **L0** se omite si `target_lang` no se configura o el bundle ya está en idioma base.
- Se puede activar un subconjunto de **N1–N5** (p. ej. `[1]`, `[1,2]`).

## Contrato entre etapas

| Etapa | Entrada | Salida |
|-------|---------|--------|
| **L0** | `ContextBlock[]` (+ `target_lang`) | `ContextBlock[]` en idioma unificado |
| **1** | `ContextBlock[]` | `DeduplicationResult` |
| **2** | `DeduplicationResult` | `FactorizationResult` |
| **3** | `FactorizationResult` | `StructuredContext` |
| **4** | `StructuredContext` | `ContextGraph` |
| **5** | `ContextGraph` + `SemanticState` + delta | `StateView` |

## Persistencia

| Etapas | Persistencia |
|--------|--------------|
| **L0, 1 – 4** | **Stateless** por invocación |
| **5** | **Stateful** — State Store entre turnos |

## Tipo de procesado

| Etapa | Transformación |
|-------|----------------|
| **L0** | Detección de idioma + traducción opcional a `target_lang` |
| **1** | Sintáctico — líneas idénticas tras normalización | Integridad sintáctica |
| **2** | Estructural — locale pack; misma entidad como sujeto | Comprensión LLM (benchmark A/B) |
| **3** | Relacional — locale pack | Comprensión LLM |
| **4** | Topológico — grafo del bundle | Comprensión LLM + slice |
| **5** | Temporal — diffs sobre estado | Comprensión LLM + store |

## Principios comunes

### N1–N4 (+ L0 traduce, no elimina)

1. **Sin pérdida en la salida del nivel** — reorganización; no resumir.
2. **Traducción antes de compresión** — L0 siempre antes de N1 cuando está activo.
3. **Determinismo preferido** — heurísticas y MT configurables antes que LLM auxiliar opaco.
4. **Trazabilidad** — `ingest_trace` (L0) + `trace` por nivel.

### N5 (distinto)

5. **Store sin pérdida** — commits conservan historial completo.
6. **Vista al LLM puede omitir** — subconjunto materializado **solo** si benchmarks OK ([benchmarks.md](benchmarks.md)).
7. **Prosa obligatoria** — [renderer.md](renderer.md).

## Orden de aprobación sugerido

1. ✅ N1 — aprobado  
2. ✅ N2 — aprobado  
3. ✅ [i18n.md](i18n.md) — aprobado  
4. ✅ [l0-ingest.md](l0-ingest.md) — aprobado  
5. ✅ N3 — aprobado  
6. ✅ N4 — aprobado  
7. ✅ N5 — aprobado  
8. ✅ [benchmarks.md](benchmarks.md) — aprobado  
9. ✅ Revisión cruzada + [spec-gaps.md](spec-gaps.md)  
10. Implementación etapa a etapa  
