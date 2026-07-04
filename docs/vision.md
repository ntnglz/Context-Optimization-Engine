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
| [level1.md](level1.md) | Spec operativa del Nivel 1 |
| `src/coe/level1/` | Implementación Nivel 1 |
| `data/examples/level1_acme.json` | Ejemplo ACME |

## Pipeline con PCM

```
Usuario → PCM (instrucción) → COE (contexto) → LLM
```

PCM y COE son complementarios. Cada uno mantiene su código en su repositorio; la visión de COE vive aquí.
