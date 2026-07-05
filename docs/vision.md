# Visión de COE

## Documento fundacional

→ **[Context Optimization Engine (COE).md](Context%20Optimization%20Engine%20(COE).md)**

Es la fuente canónica de la visión de este proyecto: motivación, objetivo, niveles de optimización (1–5), CIR, métricas, relación con PCM e hipótesis de investigación. **Se mantiene en este repositorio.**

En [Prompt-Compression-Middleware](https://github.com/ntnglz/Prompt-Compression-Middleware) hay una copia histórica como referencia en la visión global del ecosistema; no se actualiza allí.

## Resto de la documentación

| Documento | Contenido |
|-----------|-----------|
| [Context Optimization Engine (COE).md](Context%20Optimization%20Engine%20(COE).md) | Visión fundacional (canónica) |
| [architecture.md](architecture.md) | Diseño global: piezas, relaciones, roadmap de implementación |
| [i18n.md](i18n.md) | Multilingüe: `target_lang`, locale packs ✅ aprobado |
| [l0-ingest.md](l0-ingest.md) | Spec L0 — normalización de idioma ✅ aprobada |
| [benchmarks.md](benchmarks.md) | KPIs comprensión, redacción, latencia COE ✅ aprobado |
| [benchmark-harness.md](benchmark-harness.md) | Harness de calidad ✅ implementado |
| [spec-gaps.md](spec-gaps.md) | Checklist cierre pre-implementación ✅ |
| [ingest.md](ingest.md) | Context Ingest + Normalizer ✅ |
| [renderer.md](renderer.md) | Prosa hacia LLM ✅ |
| [levels.md](levels.md) | Índice del pipeline L0 → N1–N5 |
| [review-checklist.md](review-checklist.md) | Revisión cruzada al aprobar specs |
| [level1.md](level1.md) | Spec N1 ✅ · `src/coe/level1/` |
| [level2.md](level2.md) | Spec N2 ✅ · `src/coe/level2/` |
| [level3.md](level3.md) | Spec N3 ✅ |
| [level4.md](level4.md) | Spec N4 ✅ |
| [level5.md](level5.md) | Spec N5 ✅ · `src/coe/level5/` |
| `src/coe/gateway.py` | `optimize_context` — L0, N1, N2, N5 |
| `src/coe/ingest/` | L0 `normalize_language` |
| `scripts/benchmark/run.py` | CLI harness + gates |
| `data/examples/level1_acme.json` | Ejemplo ACME |

## Pipeline con PCM

```
Usuario → PCM (instrucción) → COE (contexto) → LLM
```

PCM y COE son complementarios. Cada uno mantiene su código en su repositorio; la visión de COE vive aquí.
