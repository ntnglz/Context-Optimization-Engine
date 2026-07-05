# Estado del proyecto (maintainers)

> **Maintainers (ES).** For visitors and integrators: [getting-started.md](getting-started.md) (EN) · [FAQ.md](FAQ.md) (EN)  
> Plan de trabajo: [execution-plan.md](execution-plan.md)

**Producto v1:** fases 0–18 ✅ · **Fase 20** docs visitante ✅ · **Fase 19:** omitida

## Componentes

| Componente | Spec | Implementación |
|------------|------|----------------|
| [Visión fundacional](Context%20Optimization%20Engine%20(COE).md) | ✅ | — |
| [Diseño global](architecture.md) | ✅ | L0→N5, MCP, HTTP, CIR, PCM |
| [Plan de ejecución](execution-plan.md) | ✅ | Fases 0–18 cerradas |
| [Pipeline L0 → N1–N5](levels.md) | ✅ | Completo |
| [Multilingüe (i18n)](i18n.md) | ✅ | EN / ES / ZH |
| [L0 Ingest](l0-ingest.md) | ✅ | v2 |
| [Context Ingest](ingest.md) | ✅ | structured / code / glossary |
| [Renderer](renderer.md) | ✅ | prosa vía `renderer/assembly.py` |
| [CIR v1.0](cir-v1.md) | ✅ | grafo + envelope N5 |
| [Benchmarks](benchmarks.md) | ✅ | KPIs + harness |
| [Harness](benchmark-harness.md) | ✅ | H1–H5 · 10 smokes CI |
| [Nivel 1](level1.md) – [Nivel 5](level5.md) | ✅ | ✅ |
| **Gateway** | ✅ | `optimize_context` |
| **MCP** | ✅ | stdio |
| **HTTP API** | ✅ | FastAPI |
| **Model Adapter** | ✅ | default / mistral / openai |

## CI local

```bash
python run.py --ci   # pytest + 10 perfiles benchmark smoke
```

GitHub Actions desactivado — ver [.github/workflows/README.md](../.github/workflows/README.md).

## Commits de cierre (fases 14–18)

| Fase | Commit |
|------|--------|
| 14 N5 TTL | `76c3683` |
| 15 fuzzy linking | `e8b45d5` |
| 16 SQLite store | `8d23a72` |
| 17 locale zh | `6ec6435` |
| 18 ingest structured | `2c91a7e` |
