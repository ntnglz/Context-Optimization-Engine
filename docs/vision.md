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
| [i18n.md](i18n.md) | Multilingüe: `target_lang`, locale packs, traducción pre-N1 |
| [l0-ingest.md](l0-ingest.md) | Spec L0 — normalización de idioma (Ingest) |
| [levels.md](levels.md) | Índice del pipeline L0 → N1–N5 |
| [review-checklist.md](review-checklist.md) | Revisión cruzada al aprobar specs |
| [level1.md](level1.md) | Spec N1 ✅ aprobado |
| [level2.md](level2.md) | Spec N2 ✅ aprobado |
| [level3.md](level3.md) – [level5.md](level5.md) | Specs N3–N5 (en revisión) |
| `src/coe/level1/` | Implementación Nivel 1 |
| `data/examples/level1_acme.json` | Ejemplo ACME |

## Pipeline con PCM

```
Usuario → PCM (instrucción) → COE (contexto) → LLM
```

PCM y COE son complementarios. Cada uno mantiene su código en su repositorio; la visión de COE vive aquí.
