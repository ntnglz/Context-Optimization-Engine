# L0 — Normalización de idioma (Context Ingest)

> Principios multilingües: [i18n.md](i18n.md).  
> **No es un nivel de optimización** (no es N0 que compite con N1–N5): es una etapa **pre-N1** dentro de **Context Ingest**.

**Estado:** spec en revisión · sin implementar

## Objetivo

Alinear el idioma del bundle de contexto con el **`target_lang`** del despliegue **antes** de aplicar N1–N5, traduciendo solo cuando hace falta y siempre sobre **texto natural**, no sobre representaciones comprimidas.

## Naturaleza del procesado

| Aspecto | L0 |
|---------|-----|
| **Persistencia** | No. Stateless. |
| **Tipo** | Detección de idioma + traducción opcional |
| **Posición** | `Context Ingest` → **L0** → Normalizer → N1 → … |
| **Numeración** | **L0** (letra L de *language*) para no confundir con N1–N5 |

L0 **no** elimina redundancias ni cambia estructura semántica; solo unifica idioma (y opcionalmente script/locale de surface form).

## Flujo

```mermaid
flowchart LR
    RAW[ContextBlock[] bruto]
    DET[Detectar idioma]
    CMP{¿= target_lang?}
    TR[Traducir a target_lang]
    OUT[ContextBlock[] normalizado]

    RAW --> DET --> CMP
    CMP -->|sí| OUT
    CMP -->|no| TR --> OUT
    OUT --> N1
```

## Entrada / salida

**Entrada:**

- `ContextBlock[]` — texto en uno o varios idiomas
- `target_lang` — p. ej. `en`, `zh` (requerido si L0 activo)
- `source_lang` — opcional; si omitido, autodetect por bloque o bundle
- `translate_code_blocks` — default `false` (no traducir fences de código sin opt-in)

**Salida:**

- `ContextBlock[]` — mismo `id` y metadatos; `content` en `target_lang` cuando hubo traducción
- `ingest_trace` — idioma detectado, bloques traducidos, motor usado, skip reasons
- `original_content` — opcional en metadatos para auditoría/reversión (no enviado al LLM)

## Reglas

1. **Skip si ya coincide** — no traducir bloques ya en `target_lang` (detección por bloque).
2. **Traducir antes de comprimir** — L0 es **obligatoriamente anterior** a N1 en el pipeline cuando está habilitado.
3. **Preservar identificadores** — nombres propios, URLs, UUIDs, paths: lista de exclusión; no traducir dentro de backticks/fences salvo flag explícito.
4. **Un solo idioma de salida** — todo el bundle queda en `target_lang` para niveles posteriores y Renderer.
5. **Sin compresión** — L0 no acorta texto; puede **aumentar** tokens si traduce de un idioma compacto a uno más verboso (métricas deben registrarlo).

## API prevista

```python
from coe.ingest import normalize_language

result = normalize_language(
    blocks=[...],
    target_lang="en",
    source_lang=None,           # autodetect
    translate_code_blocks=False,
)
result.blocks                   # → N1
result.ingest_trace
```

Integración en Gateway objetivo:

```python
optimize_context(
    blocks=[...],
    target_lang="en",
    levels=[1, 2],
    locale="en",                 # locale pack para N2+ (patrones)
)
```

`target_lang` (L0) y `locale` (patrones N2/N3) pueden coincidir pero son **conceptos distintos**: uno unifica idioma del texto; el otro selecciona reglas de parsing.

## Motor de traducción (implementación futura)

| Modo | Uso |
|------|-----|
| **MT dedicado** | LibreTranslate local, Argos, etc. — batch, sin inferencia del LLM destino |
| **LLM auxiliar barato** | Ollama local para L0 solo si MT insuficiente |
| **Passthrough** | `target_lang` omitido o L0 desactivado |

L0 **no** usa el mismo criterio de calidad que el LLM de producción; basta coherencia factual. Validación en benchmarks E2E posteriores (N2+).

## Métricas

- Bloques traducidos / omitidos
- Idiomas detectados
- Delta de tokens pre/post L0
- Latencia L0

## Límites previstos (v1)

- Un `target_lang` por petición (no mezcla en salida).
- Autodetect por bloque con biblioteca estándar (p. ej. `langdetect` / fastText); revisión humana en casos `confidence < umbral` → passthrough + warning en trace.
- Sin traducción de JSON estructurado interno (solo valores string human-readable).

## Relación con otros componentes

| Componente | Relación |
|------------|----------|
| **N1** | Recibe bloques ya en `target_lang`; deduplicación sintáctica sigue siendo Unicode-neutral |
| **N2–N3** | Consumen **locale pack** alineado con `target_lang` (p. ej. `locale=en` + `target_lang=en`) |
| **Model Adapter** | **No** traduce al final si L0 ya normalizó; Adapter ajusta formato/tokenizer, no idioma |
| **PCM** | Independiente; instrucción del usuario puede seguir otro idioma |

## Preguntas abiertas

- [ ] ¿Umbral de confianza de autodetect para traducir automáticamente?
- [ ] ¿Traducir metadatos (`source_type` labels) o solo `content`?
- [ ] ¿Política para bundles multilingües intencionados (p. ej. glosario bilingüe)?

## Riesgos

- **Error de traducción temprano** se propaga a todo el pipeline → tests de comprensión deben incluir casos multilingües con L0 activo.
- **Código mezclado con prosa** — requiere segmentación cuidadosa y `translate_code_blocks=false` por defecto.
