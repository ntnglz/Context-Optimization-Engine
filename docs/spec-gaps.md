# Lagunas de especificación — checklist de cierre

> Revisión crítica previa a dar por cerradas las specs N1–N5.  
> Última actualización: tras auditoría documental pre-implementación.

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
| 9 | CIR formal (gramática, versión) | Fase D roadmap; borrador N3 | 📝 Diferido |
| 10 | Model Adapter spec | [architecture.md](architecture.md) §3.4 | ✅ Acotado |
| 11 | Presupuesto tokens global (COE+PCM) | [ingest.md](ingest.md) + Gateway futuro | 📝 Parcial |
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

## 7. Diferido (no bloquea N1–N2)

| Tema | Cuándo |
|------|--------|
| Gramática CIR formal | Fase D ([architecture.md](architecture.md) roadmap) |
| Presupuesto tokens ventana completa | Al integrar Gateway + PCM |
| Entity linking fuzzy / LLM | Post-v1 N5 |
| Normalizer zh segmentador | Con locale pack `zh` |

---

## 8. Acciones antes de commit «specs cerradas»

- [ ] Usuario revisa N5, benchmarks, ingest, renderer, spec-gaps
- [x] Marcar N5 ✅ + benchmarks ✅ en índices
- [ ] (Implementación) Refactor N1 render → Renderer prosa
- [ ] (Implementación) Ampliar `ContextBlock` según ingest.md

---

## Documentos relacionados

| Documento | Rol |
|-----------|-----|
| [ingest.md](ingest.md) | ContextBundle, source_type, Normalizer |
| [renderer.md](renderer.md) | Prosa obligatoria hacia LLM |
| [benchmarks.md](benchmarks.md) | KPIs y baseline |
| [review-checklist.md](review-checklist.md) | Revisión al aprobar |
| [levels.md](levels.md) | Contratos pipeline |
