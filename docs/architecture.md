# Diseño global de alto nivel — COE

> Documento de arquitectura de **este repositorio**. La motivación, los niveles de optimización y CIR como concepto están en el [documento fundacional](Context%20Optimization%20Engine%20(COE).md). Aquí se describe **cómo lo implementamos**: piezas, responsabilidades y relaciones.

## 1. Propósito

COE es un **compilador de contexto**: recibe información heterogénea (RAG, historial, herramientas, código…) y produce una representación más compacta orientada al LLM, **sin resumir ni eliminar información necesaria**.

Analogía:

```
Texto / JSON / logs  →  [COE]  →  Contexto optimizado  →  LLM
     (fuentes)           IR +         (menos tokens,           (inferencia)
                      optimizadores    misma semántica)
```

---

## 2. Posición en el ecosistema

COE no sustituye a PCM; lo complementa en el pipeline de una petición:

```mermaid
flowchart LR
    U[Usuario / Agente]
    PCM[PCM\ncompresor de instrucciones]
    COE[COE\noptimizador de contexto]
    MA[Model Adapter\nopcional]
    LLM[LLM destino]

    U --> PCM
    U -->|contexto bruto| COE
    PCM -->|instrucción compacta| LLM
    COE --> MA
    MA --> LLM
```

| Componente | Repo | Entrada | Salida |
|------------|------|---------|--------|
| **PCM** | [Prompt-Compression-Middleware](https://github.com/ntnglz/Prompt-Compression-Middleware) | Prompt en lenguaje natural | Instrucción compacta (`TASK=…`) |
| **COE** | este repo | Bloques de contexto | Contexto optimizado |
| **Model Adapter** | futuro / externo | Contexto optimizado | Formato preferido del modelo |

PCM y COE pueden usarse de forma independiente. El pipeline completo maximiza el ahorro cuando conviven.

### 3.4 Model Adapter (acotado)

Componente **opcional externo** post-Renderer:

| Hace | No hace |
|------|---------|
| Ajustar formato al gusto del modelo (markdown, bullets) | Traducir idioma (L0) |
| Tokenizer-specific layout si aplica | Cambiar hechos ni omitir contenido |
| | Sustituir benchmarks de comprensión |

Entrada: `optimized_context` en prosa (`target_lang`). Spec detallada en fase posterior; ver [renderer.md](renderer.md).

---

## 3. Piezas principales

COE se organiza en **capas** con interfaces claras. Cada pieza tiene una responsabilidad única.

```mermaid
flowchart TB
    subgraph externo [Mundo exterior]
        SRC[Fuentes de contexto]
        CLI[Cliente / Agente / MCP]
    end

    subgraph coe [Context Optimization Engine]
        GW[Gateway\nAPI / MCP / CLI]
        ING[Context Ingest\nmodelo de entrada]
        L0[L0 Language norm.\ntarget_lang]
        NORM[Normalizer\nsegmentación]
        PIPE[Optimization Pipeline\nN1 → N2 → … → N5]
        CIR[CIR\nrepresentación intermedia]
        REN[Renderer\nserialización para LLM]
        MET[Metrics\nmedición y validación]
        ST[(State Store\nNivel 5)]
    end

    SRC --> ING
    CLI --> GW
    GW --> ING
    ING --> L0
    L0 --> NORM
    NORM --> PIPE
    PIPE <--> CIR
    PIPE --> REN
    PIPE --> MET
    ST <--> PIPE
    REN --> GW
    MET --> GW
```

### 3.1 Tabla de piezas

| Pieza | Responsabilidad | Entrada | Salida | Estado |
|-------|-----------------|---------|--------|--------|
| **Gateway** | Punto de entrada unificado (librería, CLI, MCP, HTTP futuro) | Petición del cliente | Contexto optimizado + métricas | ✅ `optimize_context` (L0, N1, N2, N3, N4, N5) |
| **Context Ingest** | Normalizar fuentes heterogéneas a un modelo común; Normalizer; opcional **L0** | Texto, chunks RAG, tool output, etc. | `ContextBundle` / `ContextBlock[]` | Parcial · spec [ingest.md](ingest.md) |
| **L0 (Language norm.)** | Detectar idioma; traducir a `target_lang` **antes de N1** si hace falta | `ContextBlock[]` | `ContextBlock[]` en idioma base | v1 [l0-ingest.md](l0-ingest.md) · `src/coe/ingest/` |
| **Normalizer** | Sub-etapa de Ingest: segmentación (líneas, oraciones `zh`), respeto fences | Bloques crudos | Unidades normalizadas | Parcial · `level1/normalize.py` |
| **Optimization Pipeline** | Aplicar niveles de optimización en cadena configurable | Unidades + metadatos | Estructura optimizada | N1 ✅ · N2 ✅ · N3 v1 · N4 v1 · N5 v1 |
| **CIR** | Representación intermedia estable, optimizable y serializable | Salida de parser / pipeline | Árbol o grafo de contexto | Diseño (sin implementar) |
| **Renderer** | Proyección **prosa** hacia LLM; ensamblaje final | Resultado del pipeline | String / messages[] | N1/N2 `render_prose` · spec [renderer.md](renderer.md) |
| **Metrics** | Tokens, ratio, latencia, integridad semántica | Antes / después del pipeline | Informe de métricas | Gateway + harness |
| **State Store** | Mantener estado semántico entre turnos (Nivel 5) | Diffs de contexto | Vista materializada | v1 filesystem JSON + in-memory · `src/coe/level5/` |

---

## 4. Relaciones entre piezas

### 4.1 Flujo principal (happy path)

1. **Gateway** recibe contexto bruto y opciones (`target_lang`, `locale`, `levels=[1,2]`, presupuesto de tokens).
2. **Context Ingest** asigna `id`, `source_type` y metadatos a cada bloque.
3. **L0** (opcional) detecta idioma y traduce a `target_lang` sobre prosa natural — ver [l0-ingest.md](l0-ingest.md), [i18n.md](i18n.md).
4. **Normalizer** prepara unidades atómicas (sub-etapa Ingest) — ver [ingest.md](ingest.md).
5. **Optimization Pipeline** ejecuta niveles habilitados en orden creciente de complejidad.
6. En fases avanzadas, el pipeline lee/escribe **CIR** como artefacto central (fase D).
7. **Renderer** materializa **prosa** para el LLM — ver [renderer.md](renderer.md).
8. **Metrics** compara entrada y salida y adjunta el informe al Gateway.

### 4.2 Dependencias

```
Gateway
  └── Context Ingest
        └── L0 Language normalization (opcional) → [l0-ingest.md](l0-ingest.md)
        └── Normalizer
              └── Optimization Pipeline
                    ├── Level 1 (deduplicación)
                    ├── Level 2 (factorización)
                    ├── Level 3 (estructuración)
                    ├── Level 4 (grafo)
                    └── Level 5 (estado) ← State Store
              └── CIR (objetivo: contrato entre niveles)
        └── Renderer
  └── Metrics (observa todo el flujo)
```

- **CIR** será el contrato interno (fase D): cada nivel transforma hacia tipos encadenados hasta grafo — ver [levels.md](levels.md). Hoy: `DeduplicationResult` → … → `ContextGraph`.
- **Renderer** consume la salida del último nivel activo y produce **prosa** — [renderer.md](renderer.md).
- **Metrics** no modifica datos; es transversal (observabilidad + benchmarks).
- **State Store** solo interviene en Nivel 5; los niveles 1–4 son stateless sobre el bundle de entrada.

### 4.3 Qué NO hace COE

| Fuera de alcance | Dónde vive |
|------------------|------------|
| Comprimir instrucciones del usuario | PCM |
| Elegir qué documentos recuperar (retrieval) | Sistema RAG / agente |
| Inferencia del LLM | Cliente upstream |
| Resumir eliminando información | Explícitamente rechazado por diseño |

---

## 5. Pipeline de optimización (niveles)

Los [cinco niveles](Context%20Optimization%20Engine%20(COE).md#niveles-de-optimización) son **etapas composables**, no modos excluyentes.

```mermaid
flowchart LR
    IN[Contexto bruto]
    N1[N1\nRedundancias]
    N2[N2\nFactorización]
    N3[N3\nEstructura]
    N4[N4\nGrafo]
    N5[N5\nEstado]
    OUT[Salida optimizada]

    IN --> N1 --> N2 --> N3 --> N4 --> N5 --> OUT
```

| Nivel | Transformación | Tipo | Implementación COE |
|-------|------------------|------|-------------------|
| **1** | Extraer duplicados exactos inter-bloque | Determinista | `src/coe/level1/` ✅ |
| **2** | Agrupar hechos bajo entidades (`Juan → acciones`) | Heurística + locale pack | `src/coe/level2/` ✅ v1 |
| **3** | Natural → estructura compacta + `render_prose()` | Parser / plantillas + proyección LN | `src/coe/level3/` v1 · [level3.md](level3.md) |
| **4** | Grafo del bundle + `render_prose()` | Topológico; cero pérdida vs N3 | `src/coe/level4/` v1 · [level4.md](level4.md) |
| **5** | Estado semántico + diff (modelo Git) | Store persistente | `src/coe/level5/` v1 · [level5.md](level5.md) |

**Regla de composición:** cada nivel asume que el anterior ya eliminó la redundancia obvia de su capa. Se pueden activar subconjuntos (p. ej. solo N1, o N1+N2).

Specs operativas: [levels.md](levels.md) · [level1.md](level1.md) ✅ · [level2.md](level2.md) ✅ · [level3.md](level3.md) ✅ · [level4.md](level4.md) ✅ · [level5.md](level5.md)

---

## 6. Modelo de datos (visión)

Evolución prevista del modelo interno:

```
ContextBundle
├── blocks: ContextBlock[]
│     ├── id: str
│     ├── source_type: rag | history | tool | code | memory
│     ├── content: str
│     ├── detected_lang: str | None    # post-L0
│     └── metadata: dict
├── target_lang: str | None            # L0: en, zh, …
├── locale: str | None                 # locale pack N2+ (en, zh, …)
├── query_context: str | None
└── options: OptimizeOptions

OptimizeResult
├── optimized_text: str
├── cir: CIR | None                # cuando exista
├── shared_facts: SharedFact[]     # N1
├── metrics: OptimizationMetrics
└── trace: LevelTrace[]            # depuración por nivel
```

Hoy solo existen `ContextBlock`, `SharedFact` y `DeduplicationResult` (`src/coe/models.py`). El resto se introducirá al integrar Gateway + CIR.

---

## 7. Interfaces previstas

### 7.1 Librería (actual y objetivo)

```python
# Hoy
from coe.level1 import deduplicate_context

# Objetivo
from coe import optimize_context

result = optimize_context(
    blocks=[...],
    target_lang="en",      # L0: normalizar idioma antes de N1
    locale="en",           # patrones N2+ (locale pack)
    levels=[1, 2],
    target_model="mistral-large",
)
result.text          # para el LLM
result.metrics       # ahorro, latencia
result.to_json()     # pipelines / logs
```

### 7.2 Servicios (futuro)

| Interfaz | Uso |
|----------|-----|
| **CLI** | `run.py --demo`, benchmarks locales |
| **MCP** | Herramientas `optimize_context`, `estimate_savings` para agentes |
| **HTTP** | Middleware transparente en pipelines RAG |

PCM ya expone MCP/HTTP para compresión; COE seguirá el mismo patrón de integración cuando el pipeline esté maduro.

---

## 8. Métricas y calidad

Transversal a todo el diseño. **Especificación completa:** [benchmarks.md](benchmarks.md).

| Métrica | Uso |
|---------|-----|
| **Ratio de compresión** | Documentado; no bloquea si fallan KPIs de calidad |
| **Tokens ahorrados** | ROI económico |
| **`t_coe` (latencia COE)** | P95 ≤ **200 ms** (L0+N1–N4 chat); ≤ **350 ms** con N5; ver presupuestos por etapa |
| **Integridad (N1–N4)** | Cero pérdida por nivel; N4: grafo ∪ orphans ⊇ entrada N3 |
| **Comprensión (N2–N5)** | `comprehension_similarity` ≥ 0,90; `factual_recall` ≥ 0,95 vs original pre-L0 |
| **Redacción E2E** | `readability_score` ≥ 3,5; `artifact_leak_rate` ≤ 2%; respuesta legible para usuario final |
| **Calidad de respuesta (E2E)** | Benchmark A/B: original crudo vs optimizado + juez LLM |

Los benchmarks vivirán en `data/` + `tests/` + `scripts/comprehension_benchmark.py` (por crear).

---

## 9. Roadmap de implementación

> **Fuente única de verdad del orden de trabajo:** [execution-plan.md](execution-plan.md)  
> Las fases A–F de abajo son **histórico**; el plan vigente usa Fases 0–6 con gates estrictos.

### Estado por bloques (foto 2026-07-05)

| Bloque | Contenido | Estado código |
|--------|-----------|---------------|
| **A** | Ingest mínimo + N1 + Renderer + Metrics | ✅ N1 + Metrics; Ingest/Renderer parciales |
| **B** | Gateway `optimize_context` | ✅ L0, N1–N5 |
| **C** | N2 factorización | ✅ |
| **D** | CIR + refactor pipeline | 📝 Fase 6 — diferido |
| **E** | MCP + benchmark RAG | ⏳ Fase 5 |
| **F** | N3–N5 + State Store | ✅ N3–N5 v1; Store parcial (Fase 3 cierra producción) |

### Orden vigente (resumen)

Ver [execution-plan.md](execution-plan.md) para entregables, criterios de hecho y reglas estrictas.

| Fase | Nombre | Estado |
|------|--------|--------|
| 0 | Sincronizar documentación | ✅ |
| 1 | Context Ingest + ContextBundle | ⏳ |
| 2 | Renderer + ensamblaje Gateway | ⏳ |
| 3 | N5 producción | ⏳ |
| 4 | Harness madurez + casos reales | ⏳ |
| 5 | MCP COE | ⏳ |
| 6 | CIR formal | 📝 diferido |

### Histórico (fases A–F originales)

| Fase | Bloques | Entregable |
|------|---------|------------|
| **A** ✅ | Ingest mínimo + N1 + Renderer + Metrics básicas | Prototipo deduplicación |
| **B** ✅ | Gateway unificado (`optimize_context`) + tests de integración | API estable |
| **C** ✅ | N2 factorización + ampliación de `ContextBlock` | Pipeline N1+N2 |
| **D** | Esbozo CIR + refactor pipeline sobre CIR | Contrato interno |
| **E** | MCP + benchmark RAG | Integración agentes |
| **F** ✅ | N3–N5 + State Store | Pipeline completo v1 |

---

## 10. Principios de diseño

1. **Sin pérdida en niveles tempranos** — N1 y N2 reorganizan; no resumen.
2. **Composición** — Niveles independientes, activables por configuración.
3. **Determinismo primero** — heurísticas exactas antes de LLM auxiliar.
4. **Separación PCM / COE** — visión fundacional aquí, compresión de instrucciones en PCM; repos independientes.
5. **Observabilidad** — cada nivel reporta qué cambió (`trace`).
6. **Renderer desacoplado** — el LLM no impone la estructura interna.

---

## 11. Documentos relacionados

| Documento | Contenido |
|-----------|-----------|
| [vision.md](vision.md) | Índice de documentación |
| [Context Optimization Engine (COE).md](Context%20Optimization%20Engine%20(COE).md) | Visión fundacional (canónica) |
| [levels.md](levels.md) | Pipeline L0 → N1–N5: contratos e integración |
| [i18n.md](i18n.md) | Principios multilingües, locale packs ✅ aprobado |
| [benchmarks.md](benchmarks.md) | KPIs comprensión, redacción, latencia COE |
| [spec-gaps.md](spec-gaps.md) | Checklist cierre pre-implementación |
| [ingest.md](ingest.md) | Context Ingest + Normalizer |
| [renderer.md](renderer.md) | Prosa hacia LLM |
| [l0-ingest.md](l0-ingest.md) | Spec L0 — normalización de idioma (pre-N1) ✅ aprobada |
| [level1.md](level1.md) – [level5.md](level5.md) | Spec operativa por nivel |
