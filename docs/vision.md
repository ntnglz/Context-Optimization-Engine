# Visión de COE

La visión conceptual, los niveles de optimización (1–5), CIR, métricas y la analogía con compiladores están documentados en el **repositorio predecesor PCM**, no se duplican aquí.

## Documento canónico

→ [Context Optimization Engine (COE).md](https://github.com/ntnglz/Prompt-Compression-Middleware/blob/main/Context%20Optimization%20Engine%20(COE).md) en [Prompt-Compression-Middleware](https://github.com/ntnglz/Prompt-Compression-Middleware)

Copia local (si clonaste ambos repos en paralelo):

```
../Prompt-Compression-Middleware/Context Optimization Engine (COE).md
```

## Qué vive en este repositorio

| Contenido | Ubicación |
|-----------|-----------|
| Visión y roadmap global | PCM (enlace arriba) |
| Prototipo **Nivel 1** — deduplicación | `src/coe/level1/` |
| Especificación operativa Nivel 1 | [level1.md](level1.md) |
| Ejemplo de referencia | `data/examples/level1_acme.json` |

## Pipeline

```
Usuario → PCM (instrucción) → COE (contexto) → LLM
```

PCM y COE son complementarios. Cada uno mantiene su código y su documentación conceptual en su propio repositorio.
