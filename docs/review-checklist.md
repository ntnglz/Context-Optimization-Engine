# Checklist de revisión al aprobar specs

Usar **después** de revisar una spec de nivel, **L0**, o documento transversal (**i18n**) y **antes** del commit de aprobación. Objetivo: detectar desviaciones de la [visión fundacional](Context%20Optimization%20Engine%20(COE).md) por centrarse en soluciones puntuales.

## Preguntas obligatorias

1. **¿Sigue siendo optimización de contexto y no resumen?** — Reorganización / representación; información necesaria preservada (salvo N5 vista al LLM, explícito).
2. **¿Encaja en el pipeline?** — Entrada/salida coherente con [levels.md](levels.md) y nivel anterior/siguiente.
3. **¿Respeta [architecture.md](architecture.md)?** — Stateless/stateful, Ingest, Metrics, Renderer, sin mezclar responsabilidades de PCM.
4. **¿El consumidor es un LLM en lenguaje natural?** — Desde N2: benchmark de comprensión; no formatos opacos sin validación.
5. **¿KPIs de calidad y latencia?** — Ver [benchmarks.md](benchmarks.md).
6. **¿Render hacia LLM solo prosa?** — Ver [renderer.md](renderer.md).
7. **¿Ingest / source_type coherente?** — Ver [ingest.md](ingest.md).
8. **¿Lagunas cerradas o documentadas?** — Ver [spec-gaps.md](spec-gaps.md).

## Acciones si algo falla

- Ajustar la spec **antes** de marcar aprobada.
- Si la idea es válida pero es otro nivel → moverla a la spec correcta o a “refinamiento posterior”.
- Documentar en la spec una tabla **Alineación con la visión** (ver [level2.md](level2.md)).

## Estado en docs tras aprobar

- Spec: `✅ Spec aprobada · sin implementar`
- [levels.md](levels.md), [vision.md](vision.md), [README.md](../README.md), [architecture.md](architecture.md) si aplica
