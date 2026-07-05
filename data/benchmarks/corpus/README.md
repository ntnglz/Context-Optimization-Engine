# Corpus local (transcripciones)

Transcripts crudos **no** van a git. Detalle del workflow completo: [benchmark-harness.md §13](../../docs/benchmark-harness.md).

## Ubicación

```
data/benchmarks/corpus/transcripts/
```

(cualquier subcarpeta; el contenido está en `.gitignore` — solo `.gitkeep` se versiona).

## Resumen rápido

1. Export Cursor / chat → `transcripts/`
2. Anonimizar (ver tabla en harness §13)
3. JSON en `../cases/` con validación schema
4. `python3 -m pytest tests/test_benchmark_schema.py -q`
5. Casos `dev_agent`: quality → `python run.py --release-dev-agent` · fast → `python run.py --benchmark-dev-agent-fast` — [benchmark-ollama.md](../../docs/benchmark-ollama.md)
