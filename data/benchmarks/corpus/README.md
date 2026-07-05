# Corpus local (no versionado)

Transcripts crudos de conversaciones con agentes **no** van a git.

## Fuente

- Export Cursor anonimizado manualmente → casos en `../cases/dev_agent/`.
- Ejemplo: chat «analizar warnings» → `dev_warnings_session_v1.json`.

## Reglas de anonimización

| Original | Sustituto |
|----------|-----------|
| Nombre de app / proyecto | `ExampleApp` |
| Modelos de dominio (`Visit`, etc.) | `RecordItem`, `RecordType` |
| Rutas locales (`/Users/…`, `/Volumes/…`) | omitidas o `/workspace/app/…` |
| Commits / hashes reales | ficticios o omitidos |
| PII, tokens, URLs con credenciales | `[REDACTED]` |

## Workflow

1. Descomprimir exports en carpeta **fuera del repo** (p. ej. `~/coe-benchmark-corpus/raw/`).
2. Recortar a 2–4 turnos con bloques `tool` / `prose`.
3. Anotar `question` + `expected_facts` por turno.
4. Guardar JSON en `../cases/dev_agent/`.
5. Añadir fixture mock si el evaluador es `mock`.

Este directorio (`corpus/`) solo documenta el proceso; los `.md` crudos pueden vivir aquí localmente si añades `data/benchmarks/corpus/raw/` al `.gitignore`.
