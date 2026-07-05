# Visión de COE

## Documento fundacional

→ **[Context Optimization Engine (COE).md](Context%20Optimization%20Engine%20(COE).md)**

Es la fuente canónica de la visión de este proyecto: motivación, objetivo, niveles de optimización (1–5), CIR, métricas, relación con PCM e hipótesis de investigación. **Se mantiene en este repositorio.**

En [Prompt-Compression-Middleware](https://github.com/ntnglz/Prompt-Compression-Middleware) hay una copia histórica como referencia en la visión global del ecosistema; no se actualiza allí.

## Estado producto v1 (2026-07-05)

| Área | Estado | Siguiente fase |
|------|--------|----------------|
| Pipeline L0 → N5 + Gateway | ✅ | — |
| Renderer prosa hacia LLM | ✅ | — |
| State Store filesystem + N5 merge | ✅ | Fase 16 (distribuido) |
| CIR v1.0 (grafo + envelope) | ✅ | Fase 19 opcional (v1.1) |
| MCP stdio para agentes | ✅ | Fase 12 (HTTP) |
| Harness smoke + tier release Ollama | ✅ | Fase 8 (schema + corpus) |
| L0 robusto, PCM+COE, HTTP, i18n zh | ⏳ | Fases 9–18 |

**Orden de trabajo:** [execution-plan.md](execution-plan.md) (fases 0–18 + pista investigación).

## Resto de la documentación

| Documento | Contenido |
|-----------|-----------|
| [Context Optimization Engine (COE).md](Context%20Optimization%20Engine%20(COE).md) | Visión fundacional (canónica) |
| [architecture.md](architecture.md) | Diseño global: piezas, relaciones, roadmap §9 |
| [execution-plan.md](execution-plan.md) | **Orden de trabajo estricto** (fases 0–18) |
| [cir-v1.md](cir-v1.md) | CIR v1.0 congelado — grafo N4+, envelope N5 |
| [i18n.md](i18n.md) | Multilingüe: `target_lang`, locale packs |
| [l0-ingest.md](l0-ingest.md) | Spec L0 — normalización de idioma |
| [benchmarks.md](benchmarks.md) | KPIs comprensión, redacción, latencia COE |
| [benchmark-harness.md](benchmark-harness.md) | Harness de calidad H1–H5 |
| [spec-gaps.md](spec-gaps.md) | Checklist cierre + deuda → fase |
| [ingest.md](ingest.md) | Context Ingest + Normalizer |
| [renderer.md](renderer.md) | Prosa hacia LLM |
| [levels.md](levels.md) | Índice del pipeline L0 → N1–N5 |
| [review-checklist.md](review-checklist.md) | Revisión cruzada al aprobar specs |
| [level1.md](level1.md) … [level5.md](level5.md) | Specs por nivel |

## Código principal

| Ruta | Rol |
|------|-----|
| `src/coe/gateway.py` | `optimize_context` — L0, N1–N5 |
| `src/coe/ingest/` | `ingest_context`, L0, normalizer |
| `src/coe/cir/` | Envelope CIR v1.0 (persistencia N5) |
| `src/coe/mcp/` | Servidor MCP (`optimize_context`, `estimate_savings`) |
| `src/coe/level5/` | State Store, merge, `StateView` |
| `scripts/benchmark/run.py` | CLI harness + gates |
| `scripts/mcp/run_server.py` | Arranque MCP stdio |
| `data/examples/level1_acme.json` | Ejemplo ACME |

## Pipeline con PCM

```
Usuario → PCM (instrucción) → COE (contexto) → LLM
```

PCM y COE son complementarios. Integración runtime en código: **Fase 11** del [execution-plan.md](execution-plan.md). Cada proyecto mantiene su código en su repositorio; la visión de COE vive aquí.
