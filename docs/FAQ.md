# Preguntas frecuentes (COE)

Respuestas cortas para integradores. Detalle técnico en [getting-started.md](getting-started.md) y specs en `docs/level*.md`.

## ¿COE resume o elimina información?

**No.** Reorganiza y deduplica; los benchmarks exigen `factual_recall` alto. No es un resumidor generativo.

## ¿COE reemplaza mi vector DB o RAG?

**No.** Optimiza el **texto** que ya recuperaste (chunks, historial, salidas de tools) antes de enviarlo al LLM.

## ¿Qué diferencia hay con PCM?

| | PCM | COE |
|---|-----|-----|
| Optimiza | Instrucciones / system prompt | Contexto (conocimiento) |
| Repo | [Prompt-Compression-Middleware](https://github.com/ntnglz/Prompt-Compression-Middleware) | este repo |

Se pueden usar juntos: [getting-started.md § PCM+COE](getting-started.md#pcm--coe).

## ¿MCP o HTTP?

| | MCP | HTTP |
|---|-----|-----|
| Uso típico | Cursor, Claude Desktop, agentes locales | Pipelines RAG, microservicios |
| Arranque | `python scripts/mcp/run_server.py` | `python scripts/http/run_server.py` |

Mismo contrato JSON de bloques y opciones.

## ¿Qué pongo en `levels`?

| `levels` | Efecto típico |
|----------|----------------|
| `[1]` | Dedup de líneas repetidas |
| `[1, 2]` | + factorización por entidad (recomendado EN/ES/ZH) |
| `[1, 2, 3, 4]` | + relaciones y grafo del turno |
| incluye `5` | Estado de sesión persistente (`session_id` obligatorio) |

Empieza con `[1, 2]` para RAG narrativo. La matriz `source_type` puede limitar niveles — ver [ingest.md](ingest.md).

## ¿Cuándo necesito `session_id`?

Cuando uses **N5**: conversaciones multi-turno donde el agente acumula estado en lugar de reenviar todo el historial crudo.

## ¿Qué es `locale` vs `target_lang`?

- **`target_lang`** + **`l0=True`**: idioma del **contexto** hacia el LLM (traducción pre-N1).
- **`locale`**: patrones N2/N3 y plantillas de prosa (EN, ES, ZH).
- **`response_lang`**: idioma de respuesta al usuario (lo usa PCM/system; COE no traduce la respuesta).

Ver [i18n.md](i18n.md).

## ¿El LLM recibe grafos o CIR?

**No en producción.** COE proyecta a **prosa natural** vía Renderer. CIR/grafo es interno y para N5 store.

## ¿Qué limitaciones tiene v1?

- N2/N3: heurísticas + locale packs (no parser semántico universal).
- L0 en CI: stub ES→EN / EN→ZH; producción puede inyectar `DeepTranslatorBackend`.
- Store: filesystem o SQLite local (no Redis/cloud en v1).
- Idiomas N2 completos: EN, ES, ZH.

## ¿Cómo sé que no rompí nada?

```bash
python run.py --ci
```

## ¿Dónde está el diseño interno?

[architecture.md](architecture.md), [levels.md](levels.md), [execution-plan.md](execution-plan.md).
