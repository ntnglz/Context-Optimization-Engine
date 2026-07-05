# Benchmark datasets

Diseño del harness: [docs/benchmark-harness.md](../docs/benchmark-harness.md).

| Directorio | Contenido |
|------------|-----------|
| `cases/` | Casos de test (JSON por caso o suite) |
| `cases/dev_agent/` | Casos derivados de transcripts de agente (anonimizados) |
| `corpus/transcripts/` | Transcripts locales para derivar casos (gitignored) · ver `corpus/README.md` |
| `profiles/` | Perfiles pipeline + umbrales gate |
| `fixtures/` | Respuestas mock para CI capa 2 |
| `runs/` | Informes generados (gitignored) |
| `baselines/` | Referencia compare PR (versionado) |

Casos etiquetados con `tags` — filtrar en CLI: `--tags core`.
