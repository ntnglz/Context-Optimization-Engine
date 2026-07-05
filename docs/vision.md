# Visión de COE

> **Integradores:** guía en inglés → [getting-started.md](getting-started.md) · [FAQ.md](FAQ.md)

## Documento fundacional

→ **[Context Optimization Engine (COE).md](Context%20Optimization%20Engine%20(COE).md)**

Es la fuente canónica de la visión de este proyecto: motivación, objetivo, niveles de optimización (1–5), CIR, métricas, relación con PCM e hipótesis de investigación. **Se mantiene en este repositorio.**

En [Prompt-Compression-Middleware](https://github.com/ntnglz/Prompt-Compression-Middleware) hay una copia histórica como referencia en la visión global del ecosistema; no se actualiza allí.

---

## Producto v1 — cerrado (2026-07-05)

**Plan de ejecución:** [execution-plan.md](execution-plan.md) · **Fases 0–18 ✅** · **Fase 20 ✅** · **Fase 19 🚫 omitida**

| Área | Estado | Notas |
|------|--------|-------|
| Pipeline L0 → N5 + Gateway | ✅ | `optimize_context`, trace por nivel |
| Renderer prosa hacia LLM | ✅ | CIR/árboles no salen al modelo |
| Context Ingest + matriz `source_type` | ✅ | structured / code / glossary (Fase 18) |
| L0 v2 (detección + traducción) | ✅ | `TranslationBackend`, mixed bundle |
| Locale packs N2 (EN / ES / ZH) | ✅ | Segmentación `zh` en Normalizer |
| CIR v1.0 (grafo + envelope N5) | ✅ | Opción A — solo `stage=graph` |
| State Store (filesystem + SQLite) | ✅ | TTL, archivado, métricas store |
| N5 merge + fuzzy linking | ✅ | Alias + umbral configurable |
| MCP stdio + HTTP API | ✅ | `/optimize`, `/estimate`, `/health` |
| Integración PCM+COE | ✅ | Presupuesto ventana conjunto |
| Model Adapter | ✅ | `target_model`: default / mistral / openai |
| Harness smoke + tier release | ✅ | 234 tests · 10 perfiles CI |
| Docs visitante e integrador | ✅ | Fase 20 — README, getting-started, FAQ, STATUS |
| CIR v1.1 (stages N1–N3) | 🚫 | Sin demanda concreta — ver Fase 19 |

**Gate habitual:** `python run.py --ci`

---

## Visión fundacional vs producto v1

| Tema (doc fundacional) | Producto v1 |
|------------------------|-------------|
| Optimizar **contexto**, no prompt | ✅ Pipeline + benchmarks A/B |
| **Cambiar representación**, no resumir | ✅ N1–N5 deterministas; N5 vista acotada |
| Niveles 1–5 | ✅ Implementados y composables |
| CIR intermedia optimizable | ✅ Grafo N4+ persistido; N1–N3 en RAM |
| Salida al LLM | **Prosa natural** (spec operativa prevalece) |
| PCM + COE + Model Adapter | ✅ Fases 11–13 |
| Parser semántico upstream | ⏸ Pista I — investigación |
| CIR directa al LLM (no prosa) | ⏸ Pista I — sin benchmark favorable |
| ML / capa universal industria | ⏸ Pista I — fuera de alcance v1 |

La fundacional describe el **horizonte**; las specs en `level1.md`–`level5.md`, [renderer.md](renderer.md) e [ingest.md](ingest.md) acotan el **producto entregado**.

---

## Pipeline con PCM

```
Usuario → PCM (instrucción) → COE (contexto) → Model Adapter → LLM
```

PCM y COE son complementarios (repos independientes). Integración runtime: [execution-plan.md](execution-plan.md) Fase 11.

---

## Siguiente trabajo (post-v1)

| Vía | Contenido |
|-----|-----------|
| **[getting-started.md](getting-started.md)** | Integrar COE (Python, MCP, HTTP) |
| **Pista I** | ML, CIR→LLM — benchmark A/B favorable |
| **Enmienda al plan** | Nuevo trabajo producto |

---

## Resto de la documentación

| Documento | Contenido |
|-----------|-----------|
| [Context Optimization Engine (COE).md](Context%20Optimization%20Engine%20(COE).md) | Visión fundacional (canónica) |
| [architecture.md](architecture.md) | Diseño global: piezas, relaciones, roadmap §9 |
| [execution-plan.md](execution-plan.md) | Plan de ejecución (fases 0–20 cerradas) |
| [getting-started.md](getting-started.md) | Guía integrador (visitante) |
| [FAQ.md](FAQ.md) | Preguntas frecuentes adopción |
| [STATUS.md](STATUS.md) | Tabla spec/implementación (maintainers) |
| [cir-v1.md](cir-v1.md) | CIR v1.0 congelado — grafo N4+, envelope N5 |
| [i18n.md](i18n.md) | Multilingüe: `target_lang`, locale packs |
| [l0-ingest.md](l0-ingest.md) | Spec L0 — normalización de idioma |
| [benchmarks.md](benchmarks.md) | KPIs comprensión, redacción, latencia COE |
| [benchmark-harness.md](benchmark-harness.md) | Harness de calidad H1–H5 |
| [spec-gaps.md](spec-gaps.md) | Checklist cierre + deuda → fase |
| [ingest.md](ingest.md) | Context Ingest + Normalizer |
| [renderer.md](renderer.md) | Prosa hacia LLM |
| [levels.md](levels.md) | Índice del pipeline L0 → N1–N5 |
| [level1.md](level1.md) … [level5.md](level5.md) | Specs por nivel |

---

## Código principal

| Ruta | Rol |
|------|-----|
| `src/coe/gateway.py` | `optimize_context` — L0, N1–N5 |
| `src/coe/ingest/` | `ingest_context`, L0, normalizer, structured/code |
| `src/coe/cir/` | Envelope CIR v1.0 (persistencia N5) |
| `src/coe/mcp/` | Servidor MCP (`optimize_context`, `estimate_savings`) |
| `src/coe/http/` | FastAPI — mismo contrato que MCP |
| `src/coe/pcm/` | Composición PCM+COE |
| `src/coe/locales/zh/` | Locale pack chino |
| `src/coe/level5/` | State Store (fs/SQLite), merge, glossary, `StateView` |
| `scripts/benchmark/run.py` | CLI harness + gates |
| `scripts/mcp/run_server.py` | Arranque MCP stdio |
| `scripts/http/run_server.py` | Arranque HTTP |
