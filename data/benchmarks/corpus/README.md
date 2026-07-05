# Corpus local (transcripciones)

Transcripts crudos de conversaciones con agentes **no** van a git. Déjalos en:

```
data/benchmarks/corpus/transcripts/
```

(cualquier subcarpeta o archivo dentro; el directorio existe en el repo pero su contenido está en `.gitignore`).

## Fuente

- Export Cursor / markdown de chat → recortar y anonimizar → casos en `../cases/dev_agent/`.
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

1. Copiar exports o `.md` de chat a `transcripts/` (p. ej. `transcripts/cursor/warnings.md`).
2. Recortar a 2–4 turnos con bloques `tool` / `prose`.
3. Anotar `question` + `expected_facts` por turno.
4. Guardar JSON anonimizado en `../cases/dev_agent/` (o subcarpeta por tag).
5. Añadir fixture mock si el evaluador es `mock`.

Solo este `README.md` y `transcripts/.gitkeep` se versionan bajo `corpus/`.
