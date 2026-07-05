# Plan de ejecución COE — fuente única de verdad

> **Vigente desde:** 2026-07-05  
> **Regla:** no se implementa nada fuera de la fase activa sin enmienda explícita de este documento.  
> **Gate por fase:** `python run.py --ci` PASS + actualizar tabla de progreso abajo.

---

## Por qué este documento existe

`architecture.md` §9 quedó obsoleto: marca N3–N5 como «investigación» y Gateway/MCP como futuro, pero el código ya tiene L0, N1–N5, harness H1–H5 y `FilesystemStateStore`. El trabajo reciente (casos `dev_agent`, baseline DevSSD, store en disco) fue útil pero **fuera de orden** respecto a las dependencias del diseño (Ingest → Renderer → Gateway → integración).

Este plan **reemplaza** `architecture.md` §9 como orden de trabajo. La arquitectura de piezas sigue en `architecture.md` §§1–8; el **orden de implementación** vive aquí.

---

## Estado real (foto 2026-07-05)

| Pieza | Spec | Código | Notas |
|-------|------|--------|-------|
| N1–N4 | ✅ | ✅ | Gates smoke en CI |
| N5 merge + commits | ✅ | ✅ | `n5_session`, `n5_graph_session` |
| State Store | ✅ | ✅ | `FilesystemStateStore` + auto-wire Gateway; retención `max_commits`; conflictos/retracts en prosa |
| Gateway `optimize_context` | ✅ | ✅ | Acepta `ContextBundle` y `list[ContextBlock]` |
| L0 | ✅ | ⚠️ parcial | ES→EN heurístico; con bundle |
| Context Ingest | ✅ | ✅ | `ingest_context`, `source_type`, matriz niveles |
| Renderer unificado | ✅ | ✅ | Ensamblaje Gateway según `renderer.md` |
| Harness capa 0–1 | ✅ | ✅ | 8 perfiles smoke mock |
| Harness capa 2 (Ollama) | ✅ | ✅ | `scripts/ci/release-dev-agent.sh`; fuera de `--ci` |
| MCP | ✅ acotado | ✅ | `optimize_context`, `estimate_savings` vía stdio |
| CIR formal | 📝 diferido | ❌ | Fase 6 Opción A — solo grafo; ver [cir-v1-draft.md](cir-v1-draft.md) |
| Casos benchmark | — | 6 | 2 core, 1 ES, 1 multi_turn, 2 dev_agent |

---

## Reglas de ejecución estricta

1. **Una fase activa.** La fase actual es la primera fila con estado `🔄` o `⏳` en la tabla de progreso.
2. **Sin saltos.** No empezar tareas de fases posteriores aunque parezcan pequeñas.
3. **Cierre de fase** = todos los entregables ✅ + CI PASS + fila actualizada a `✅` + commit con `CI: PASS antes de push`.
4. **Enmiendas.** Si hace falta desviarse, primero se edita este archivo (sección «Enmiendas») y el usuario aprueba.
5. **Specs > código.** Si código y spec discrepan, el trabajo de la fase alinea código a spec (no al revés), salvo enmienda documentada.

---

## Fases (orden obligatorio)

### Fase 0 — Sincronizar documentación ⏳

**Objetivo:** Una sola narrativa de «dónde estamos y qué sigue».

| Entregable | Criterio de hecho |
|------------|-------------------|
| `docs/execution-plan.md` | Este archivo aprobado por el usuario |
| `docs/architecture.md` §9 | Sustituido por referencia a este plan + tabla de fases actualizada |
| `docs/vision.md` | Gateway y niveles reflejan implementación real |
| `docs/spec-gaps.md` §8 | Checklist implementación actualizado |

**No incluye código de producto.**

---

### Fase 1 — Context Ingest + ContextBundle

**Objetivo:** Entrada uniforme según `ingest.md` antes de tocar más integración.

| Entregable | Criterio de hecho |
|------------|-------------------|
| `ContextBundle`, `IngestOptions`, `SourceType` | Modelos en `src/coe/ingest/` |
| `ingest_context()` | Normalizer v1 (CRLF, fences), asigna `id`/`source_type` |
| `ContextBlock` ampliado | `source_type`, `detected_lang`, metadata acordada |
| Matriz niveles | Filtrado por `source_type` antes del pipeline |
| Gateway | Acepta `ContextBundle` además de `list[ContextBlock]` (compat) |
| Tests | `tests/test_ingest.py` cubre matriz + normalizer |
| CI | PASS sin regresión de perfiles smoke |

**Bloquea:** Fase 2 (Renderer ensamblaje necesita bundle ordenado y tipado).

---

### Fase 2 — Renderer + ensamblaje Gateway

**Objetivo:** Cumplir `renderer.md` — solo prosa hacia el LLM, plantillas locale.

| Entregable | Criterio de hecho |
|------------|-------------------|
| N1 `render_prose()` | Plantillas `en`/`es`; `render_compact()` solo debug |
| Ensamblaje Gateway | Orden: N5 `StateView` → turno (sin duplicar si merge en head) |
| i18n etiquetas | Sin hardcode ES en renderer |
| Tests | Prosa sin `entity:`/`node:`; casos ES/EN en pytest |
| CI | PASS; `artifact_leak_rate` sin regresión |

**Bloquea:** Fase 3 (N5 producción asume ensamblaje correcto).

---

### Fase 3 — N5 producción

**Objetivo:** State Store usable en despliegue local según `level5.md`.

| Entregable | Criterio de hecho |
|------------|-------------------|
| Gateway auto-store | Si `session_id` y sin `state_store` → `FilesystemStateStore("./data/sessions")` |
| Retención v1 | `max_commits` configurable; poda `history` sin perder head |
| Conflictos / retracts | Flags en merge + prosa en `StateView.render()` |
| Tests | Persistencia entre procesos + retención + conflicto mínimo |
| CI | PASS incl. `n5_session` y `n5_graph_session` |

**Nota:** `FilesystemStateStore` (commit `4eee06f`) cuenta como avance adelantado; esta fase lo **completa** (wire + retención + conflictos).

---

### Fase 4 — Harness madurez + casos reales

**Objetivo:** Validar COE con conversaciones reales y evaluador LLM.

| Entregable | Criterio de hecho |
|------------|-------------------|
| Casos `dev_agent` | ≥2 casos JSON en `cases/dev_agent/` desde `corpus/transcripts/` |
| Perfil `release` | Documentado en `benchmark-harness.md` |
| Tier release local | Script/comando reproducible con Ollama sobre `--tags dev_agent` |
| Gate | Documentar umbrales; no obligatorio en `run.py --ci` (solo smoke en CI) |

**Bloquea:** Fase 5 (MCP debe exponer pipeline ya validado en casos reales).

---

### Fase 5 — MCP COE

**Objetivo:** Integración agentes según `architecture.md` §7.2.

| Entregable | Criterio de hecho |
|------------|-------------------|
| Herramienta `optimize_context` | Entrada bundle/bloques + opciones; salida prosa + métricas |
| Herramienta `estimate_savings` | Tokens ahorrados sin ejecutar LLM evaluador |
| Tests | Smoke MCP o integración mínima documentada |
| Docs | Sección en `architecture.md` §7.2 con ejemplo |

---

### Fase 6 — CIR formal (diferido)

**Objetivo:** Contrato interno del grafo (Opción A). **Solo tras Fase 5 ✅.**

**Decisión de diseño:** formalizar **solo `stage=graph`**; N1–N3 siguen como tipos Python en memoria (sin serialización CIR intermedia). Ver [cir-v1-draft.md](cir-v1-draft.md).

| Entregable | Criterio de hecho |
|------------|-------------------|
| Spec CIR v1.0 | `docs/cir-v1.md` congelado desde borrador (grafo, envelope, enums) |
| JSON Schema | `data/benchmarks/schema/cir-1.0.schema.json` |
| Builder N4 | `document`/`chunk`, aristas `action`/`contains`/`reference` |
| Envelope N5 | `semantic_state_to_dict` con `cir_version` + `graph` |
| Tests | Roundtrip JSON, merge conflictos, proyección prosa sin regresión |
| **Fuera de alcance** | CIR `stage=fact|entity|tree`; refactor de `DeduplicationResult` / `FactorizationResult` |

**No iniciar hasta re-priorización explícita del usuario.**

---

## Progreso

| Fase | Nombre | Estado | Commit cierre |
|------|--------|--------|---------------|
| 0 | Sincronizar documentación | ✅ cerrada | — |
| 1 | Context Ingest + ContextBundle | ✅ cerrada | — |
| 2 | Renderer + ensamblaje Gateway | ✅ cerrada | — |
| 3 | N5 producción | ✅ cerrada | d733bb7 |
| 4 | Harness madurez + casos reales | ✅ cerrada | b8de213 |
| 5 | MCP COE | ✅ cerrada | bf9ddf2 |
| 6 | CIR formal | 📝 diferido | — |

**Leyenda:** ⏳ pendiente · 🔄 en curso · ✅ cerrada · 📝 diferido

---

## Enmiendas

| Fecha | Cambio | Motivo |
|-------|--------|--------|
| 2026-07-05 | Plan inicial | Desvío respecto a `architecture.md` §9; acuerdo de seguimiento estricto |
| 2026-07-05 | CIR v1.0 diseño | Opción A: solo grafo serializado; N1–N3 en Python; `document`/`chunk`; `action` arista |

---

## Documentos relacionados

| Documento | Rol |
|-----------|-----|
| [architecture.md](architecture.md) | Piezas y relaciones (qué construimos) |
| [execution-plan.md](execution-plan.md) | **Orden de trabajo (cuándo y en qué secuencia)** |
| [spec-gaps.md](spec-gaps.md) | Decisiones de diseño cerradas |
| [ingest.md](ingest.md) | Spec Fase 1 |
| [renderer.md](renderer.md) | Spec Fase 2 |
| [level5.md](level5.md) | Spec Fase 3 |
| [benchmark-harness.md](benchmark-harness.md) | Spec Fase 4 |
| [cir-v1-draft.md](cir-v1-draft.md) | Borrador CIR v1.0 (Fase 6, Opción A) |
