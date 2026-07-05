# Lagunas de especificación — checklist de cierre

> Revisión crítica previa a dar por cerradas las specs N1–N5.  
> Última actualización: 2026-07-05 (Fase 7 — sincronización documental).

**Objetivo:** resolver decisiones **bloqueantes** antes de codificar Gateway, N2+ y benchmarks E2E.

---

## Estado de cierre

| # | Tema | Decisión / doc | Estado |
|---|------|----------------|--------|
| 1 | Política render hacia LLM (N1–N5) | [renderer.md](renderer.md) | ✅ Cerrado |
| 2 | Context Ingest + Normalizer | [ingest.md](ingest.md) | ✅ Cerrado |
| 3 | Baseline única benchmarks | [benchmarks.md](benchmarks.md) §1 | ✅ Cerrado |
| 4 | Doc fundacional vs specs operativas | Nota de evolución en [COE].md | ✅ Cerrado |
| 5 | N5: vista sin duplicar turno | [level5.md](level5.md) | ✅ Cerrado |
| 6 | N5: entity linking inter-turno v1 | [level5.md](level5.md) | ✅ Cerrado |
| 7 | N5: conflictos y retracts en prosa | [level5.md](level5.md) | ✅ Cerrado |
| 8 | Principio «sin pérdida» acotado (N5) | [levels.md](levels.md) | ✅ Cerrado |
| 9 | CIR formal (gramática, versión) | Fase 6 · [cir-v1.md](cir-v1.md) Opción A | ✅ Cerrado |
| 10 | Model Adapter spec | [architecture.md](architecture.md) §3.4 | ⏳ Fase 13 |
| 11 | Presupuesto tokens global (COE+PCM) | [ingest.md](ingest.md) + Gateway | ⏳ Fases 10–11 |
| 12 | Robustez estadística benchmarks | [benchmarks.md](benchmarks.md) §9 | ✅ Cerrado |
| 13 | Aprobar N5 + benchmarks | ✅ Cerrado |

[COE]: Context%20Optimization%20Engine%20(COE).md

---

## 1. Política render (cerrado)

**Decisión:** hacia el LLM destino **solo prosa en lenguaje natural**. Representaciones compactas (`Empresa=ACME`, `entity:`, grafo) son **internas** o de depuración.

| Nivel | Hacia LLM | Interno / debug |
|-------|-----------|-----------------|
| N1 | `render_prose()` vía Renderer | `render_compact()` (actual `render()`) |
| N2 | `render_prose()` — default `prose_compact` | `render_structured()` |
| N3–N4 | `render_prose()` | `render_debug()` / `serialize_internal()` |
| N5 | `StateView.render()` | trace, store |

Ver [renderer.md](renderer.md).

**Migración código:** renombrar/refactorizar `DeduplicationResult.render()` → compat alias hasta Gateway; etiquetas i18n en Renderer, no hardcode ES.

---

## 2. Ingest + Normalizer (cerrado)

**Decisión:** Ingest produce `ContextBundle`; Normalizer es **sub-etapa** de Ingest (no pieza suelta post-L0).

- `source_type` determina niveles activables — matriz en [ingest.md](ingest.md).
- Segmentación (líneas, oraciones `zh`) en Normalizer antes de N1.

---

## 3. Baseline benchmarks (cerrado)

**Decisión única:**

- **Respuesta A** = contexto **original crudo** (pre-L0, pre-COE) + `response_lang` del caso.
- **Respuesta B** = mismo evaluador + pipeline COE **completo configurado** para el despliegue.

Comparaciones secundarias (N3 vs N4, turno vs N5) son diagnóstico, no gate de aprobación.

---

## 4. N5 vista vs turno (cerrado)

**Decisión:** tras merge+commit, **solo** `StateView.render()`. No concatenar `turn_bundle.render_prose()` si ya está en `head`.

Excepción v1: flag `include_pending_turn=true` si merge difiere de commit (working tree); por defecto **false**.

---

## 5. Entity linking inter-turno v1 (cerrado)

**Decisión v1 (conservadora):**

- Fusión solo con **mismo `id` canónico** (normalización casefold + strip del label N3/N4).
- Alias explícitos vía metadato `entity_aliases[]` en Ingest o en turno (sin inferencia LLM).
- Sin fuzzy matching ni coreferencia automática en v1.

---

## 6. Conflictos y retracts (cerrado)

- Nodo con `conflict: true` → `render_prose()` enumera **ambas** versiones con fuentes.
- `retracts: commit_id` → hecho previo marcado como superseded; prosa: «Previously X; corrected to Y (source …)».

---

## 7. Deuda → fase ([execution-plan.md](execution-plan.md) 6–18)

| Tema | Fase |
|------|------|
| Gramática CIR formal (Opción A) | 6 |
| `case.schema.json` + corpus ampliado | 8 |
| L0 detección + traducción robusta | 9 |
| Presupuesto tokens COE | 10 |
| Presupuesto ventana COE+PCM | 11 |
| HTTP API | 12 |
| Model Adapter | 13 |
| N5 TTL / archivado | 14 |
| Entity linking fuzzy | 15 |
| Store distribuido | 16 |
| Normalizer zh + locale pack | 17 |
| Ingest `structured` / `code` | 18 |
| CIR v1.1 Opción B (`stage` N1–N3) | 19 (opcional) |

---

## 8. Acciones de implementación (orden en execution-plan.md)

| # | Acción | Fase |
|---|--------|------|
| 1 | Ampliar `ContextBlock` + `ContextBundle` según [ingest.md](ingest.md) | 1 ✅ |
| 2 | `ingest_context()` + matriz `source_type` | 1 ✅ |
| 3 | Refactor N1 render → Renderer prosa + ensamblaje Gateway | 2 ✅ |
| 4 | N5 producción: auto-store, retención, conflictos | 3 ✅ |
| 5 | Casos `dev_agent` + tier release Ollama | 4 ✅ |
| 6 | MCP `optimize_context` / `estimate_savings` | 5 ✅ |
| 7 | CIR v1.0 grafo + schema + envelope N5 | 6 ✅ |
| 8 | README + architecture §9 + vision al día | 7 ✅ |
| 9 | `case.schema.json` + ≥4 casos nuevos | 8 |
| 10 | L0 v2 (detección, `TranslationBackend`) | 9 |
| 11 | `max_context_tokens` en Gateway | 10 |
| 12 | Composición PCM+COE + harness `coe+pcm` | 11 |
| 13 | HTTP `/optimize` + `/estimate` | 12 |
| 14 | Model Adapter + `target_model` | 13 |
| 15 | N5 TTL + archivado | 14 |
| 16 | Entity linking fuzzy | 15 |
| 17 | `SQLiteStateStore` | 16 |
| 18 | Locale pack `zh` | 17 |
| 19 | Ingest structured/code/glossary | 18 |

Checklist spec:

- [x] Usuario revisa N5, benchmarks, ingest, renderer, spec-gaps
- [x] Plan fases 0–5 cerrado
- [x] Plan fases 6–18 priorizado (2026-07-05)
- [ ] Producto v1 completo (fases 6–18 ✅)

---

## Documentos relacionados

| Documento | Rol |
|-----------|-----|
| [ingest.md](ingest.md) | ContextBundle, source_type, Normalizer |
| [renderer.md](renderer.md) | Prosa obligatoria hacia LLM |
| [benchmarks.md](benchmarks.md) | KPIs y baseline |
| [review-checklist.md](review-checklist.md) | Revisión al aprobar |
| [levels.md](levels.md) | Contratos pipeline |
