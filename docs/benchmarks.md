# Benchmarks y KPIs de calidad

> Harness previsto: `scripts/comprehension_benchmark.py` · datos: `data/comprehension_cases.json`  
> Índice pipeline: [levels.md](levels.md) · métricas transversales: [architecture.md](architecture.md) §8

**Estado:** ✅ Spec aprobada · **harness implementado** (`scripts/benchmark/`, `src/coe/benchmark/`)

COE debe demostrar dos cosas distintas antes de producción:

1. **Comprensión** — el LLM responde tan bien (o mejor) con contexto optimizado que con el original.
2. **Operabilidad** — el pipeline no degrada la experiencia del diálogo por latencia ni por respuestas ilegibles para el usuario final.

El **ratio de tokens** se documenta pero **no bloquea** si falla comprensión, redacción o latencia.

---

## 1. Línea base de comparación

**Regla única (gate de aprobación):**

| Brazo | Contenido |
|-------|-----------|
| **A (referencia)** | Contexto **original crudo** — pre-L0, pre-COE — + pregunta + instrucción `response_lang` |
| **B (pipeline)** | Mismo evaluador + **misma pregunta e instrucción** + contexto tras pipeline COE **completo** del despliegue |

Comparaciones **diagnósticas** (no sustituyen A/B anterior):

| Referencia | Qué es | Cuándo usarla |
|------------|--------|---------------|
| **Historial completo sin N5** | Todos los turnos concatenados sin State Store | Techo multi-turno |
| **N3 `render_prose()` vs N4** | Regresión entre niveles | Tuning N4 slice/plantillas |
| **Turno aislado N4 vs N5 vista** | Regresión N5 | Tuning materialize view |

Ejecutar casos en **`target_lang`** cuando L0 esté activo; casos adicionales con original en **idioma fuente** del usuario.

---

## 2. Protocolo E2E (por caso de test)

Para cada `(contexto, pregunta)` del dataset:

1. Fijar pregunta respondible **solo** con el contexto.
2. **Respuesta A** — LLM evaluador + contexto **original crudo** + instrucción PCM/system con **`response_lang` explícito** (idioma del mensaje del usuario en el caso, no idioma del contexto).
3. **Respuesta B** — mismo LLM, misma instrucción + contexto **optimizado** (pipeline COE activo).
4. Calcular KPIs de las secciones 3–4 sobre A y B.
5. Registrar latencia COE (sección 5) en la misma ejecución.

Requisito: **mismo modelo evaluador, temperatura y prompt de usuario** en A y B por caso.

---

## 3. KPIs de comprensión (factual)

Ya definidos desde N2; aplican a N2–N5 sobre `render_prose()` / `StateView.render()`.

| KPI | Cómo se mide | Umbral v1 (B vs. original) |
|-----|--------------|----------------------------|
| **`comprehension_similarity`** | Similitud semántica embedding entre respuesta A y B | Media ≥ **0,90** |
| **`factual_recall`** | F1 sobre hechos/entidades clave esperados en B | ≥ **0,95** |
| **`comprehension_delta`** | `similarity(B,A) − 1.0` | ≥ **−0,10** (B no más de 10 pp peor que A) |

Si no se cumple → reducir agresividad (passthrough parcial, vista ampliada N5, desactivar nivel).

---

## 4. KPI de redacción (calidad de la respuesta al usuario)

Además de si B es **correcta**, medir si es **legible y apropiada para el usuario final**, que no participó en la optimización del contexto.

### Problema

El LLM tiende a **imitar** densidad, jerga y convenciones del contexto del prompt. COE puede producir respuestas factualmente correctas pero telegráficas, con abreviaturas internas o tono inadecuado.

### KPIs propuestos

| KPI | Cómo se mide | Umbral v1 |
|-----|--------------|-----------|
| **`readability_score`** | Juez LLM (rúbrica 1–5): claridad, lenguaje natural, ausencia de jerga COE, adecuación al usuario | **B ≥ 3,5** absoluto **y** **B ≥ A − 0,3** |
| **`artifact_leak_rate`** | % de respuestas B con patrones prohibidos (`entity:`, `node:`, `[E1]`, diffs tipo `+edge`, JSON de grafo) | ≤ **2%** del corpus |
| **`user_language_match`** | ¿La respuesta B está en **`response_lang`** del turno (idioma del **mensaje del usuario** / PCM), no en el idioma del contexto ni en `target_lang`? | ≥ **0,95** casos OK |
| **`prose_naturalness`** | Juez LLM binario: «¿Suena como texto escrito para un humano, no como dump de contexto?» | ≥ **0,90** «sí» en B |

### Rúbrica orientativa para `readability_score` (juez LLM)

Evaluar la **respuesta B** (y opcionalmente comparar con A):

| Puntuación | Criterio |
|------------|----------|
| **5** | Clara, fluida, sin jerga interna; un usuario no técnico la entiende sin contexto previo |
| **4** | Correcta y legible; leves repeticiones o densidad aceptables |
| **3** | Comprensible con esfuerzo; alguna abreviatura o estilo «de prompt» |
| **2** | Densa, listas crípticas, mezcla de notación y prosa |
| **1** | Ilegible o indistinguible de un volcado de contexto optimizado |

El juez recibe la **pregunta del usuario** y la **instrucción de tono/idioma** (PCM), **no** el contexto completo — para evaluar presentación, no fact checking.

### Detección automática de `artifact_leak_rate` (complemento al juez)

Regex / heurísticas sobre respuesta B (barato, en CI):

- Patrones `node:`, `edge:`, `entity{`, `orphan:`, `commit_id`, `# delta`
- Ratio palabras/abreviaturas vs. oraciones completas (umbral configurable)

Discrepancia juez vs. heurística → revisión manual del caso.

### Criterio de aprobación del pipeline

Además de comprensión (§3), el despliegue **no activa** un nivel o configuración si:

- `readability_score` medio cae bajo **3,5**, o
- **B** pierde más de **0,3** puntos respecto a **A** en media, o
- `artifact_leak_rate` > **2%**

---

## 5. KPIs de latencia COE (presupuesto de retardo)

### Definición

```
t_dialog_e2e     = t_usuario_envía → t_usuario_recibe_respuesta
t_llm          = inferencia del LLM destino (TTFT + generación, medido en cliente)
t_coe          = t_dialog_e2e − t_llm − t_red_cliente   (ideal: medir envolviendo optimize_context)
```

**Objetivo:** `t_coe` acotado. COE no debe hacer inservible el chat por espera perceptible.

Medir **P50** y **P95** por configuración de pipeline; alertar si P95 supera umbral **hard**.

### Presupuestos v1 propuestos (revisar con mediciones reales)

| Configuración pipeline | P50 `t_coe` | P95 `t_coe` | Hard fail P95 |
|------------------------|-------------|-------------|---------------|
| **N1** solo | ≤ 30 ms | ≤ **80 ms** | 150 ms |
| **N1 + N2** | ≤ 50 ms | ≤ **120 ms** | 250 ms |
| **L0 + N1–N4** (chat interactivo) | ≤ 80 ms | ≤ **200 ms** | 400 ms |
| **+ N5** (store local SQLite/fs) | ≤ 120 ms | ≤ **350 ms** | 600 ms |
| **L0 con MT externo** (batch) | medir aparte | ≤ **500 ms** P95 | 1 s |

Desglose orientativo por etapa (para diagnóstico en `result.metrics.latency_ms`):

| Etapa | P95 interno v1 |
|-------|----------------|
| L0 autodetect (sin traducción) | 15 ms |
| L0 traducción MT | 200–500 ms (async recomendado si supera 200 ms) |
| N1 dedup | 20 ms |
| N2 factorización | 40 ms |
| N3 parse + render_prose | 60 ms |
| N4 grafo + render_prose | 80 ms |
| N5 load + merge + materialize | 150 ms |

### Reglas operativas

1. **Chat interactivo síncrono** — configuración por defecto: L0 sin MT lento en hot path, o L0 async con contexto en cache del turno anterior.
2. **Hard fail** — si P95 supera la columna «Hard fail», el nivel responsable se desactiva automáticamente (feature flag) hasta optimización.
3. **No confundir** latencia del **harness de benchmark** (LLM juez) con `t_coe`; el juez corre offline/CI, no en el camino del usuario.
4. **Reporting** — Gateway expone `metrics.latency_ms.{total,l0,n1,…,n5}` y `metrics.latency_budget_ok: bool`.

### Relación con ahorro de tokens

Un pipeline puede cumplir ratio excelente y **fallar** latencia o redacción. La decisión de activar niveles es **conjunción** de KPIs, no solo compresión.

---

## 6. Matriz resumen de aprobación

| Dimensión | KPI principal | Umbral v1 |
|-----------|---------------|-----------|
| Comprensión | `comprehension_similarity` | ≥ 0,90 |
| Hechos | `factual_recall` | ≥ 0,95 |
| Redacción | `readability_score` | B ≥ 3,5 y B ≥ A − 0,3 |
| Sin fugas COE | `artifact_leak_rate` | ≤ 2% |
| Idioma usuario | `user_language_match` | ≥ 0,95 |
| Latencia chat | `t_coe` P95 (L0+N1–N4) | ≤ **200 ms** |
| Latencia + N5 | `t_coe` P95 | ≤ **350 ms** |

---

## 7. Implementación

**Diseño completo del harness:** [benchmark-harness.md](benchmark-harness.md) (capas, módulos, schema, CI, roadmap H1–H5).

Resumen:

| Pieza | Ubicación |
|-------|-----------|
| Librería | `src/coe/benchmark/` |
| CLI | `scripts/benchmark/run.py` |
| Casos | `data/benchmarks/cases/` |
| Perfiles | `data/benchmarks/profiles/` |
| Informes | `data/benchmarks/runs/` (gitignored) |

Gate de aprobación: umbrales §6 aplicados por **perfil YAML**, no hardcode en script.

---

## 8. Tiers CI (referencia rápida)

Ver [benchmark-harness.md](benchmark-harness.md) §10.

| Tier | LLM | Cuándo |
|------|-----|--------|
| `smoke` | mock | PR |
| `ci` | mock | main |
| `nightly` | ollama | cron |
| `release` | ollama ×3 runs | tag |

---

## 9. Robustez estadística (juez LLM)

El evaluador LLM es **no determinista**. v1:

| Práctica | Valor |
|----------|-------|
| Corridas por caso en CI | **1** (rápido) |
| Corridas pre-release | **3**; media de KPIs |
| Gate | Umbrales §6 sobre **media** pre-release |
| Temperatura evaluador | **0** o fija documentada |
| Discrepancia alta entre corridas | Flag manual; ampliar corpus |

Heurísticas (`artifact_leak_rate`, latencia) son deterministas y corren en cada CI.

---

## 10. Documentos relacionados

| Documento | Relación |
|-----------|----------|
| [level2.md](level2.md) | Primer nivel con benchmark de comprensión obligatorio |
| [level5.md](level5.md) | Multi-turno, línea base pre-L0, riesgo de estilo |
| [architecture.md](architecture.md) | Metrics transversal, Gateway |
| [i18n.md](i18n.md) | Tres ejes de idioma; casos multilingües |
| [renderer.md](renderer.md) | Prosa hacia LLM; artifact_leak |
| [benchmark-harness.md](benchmark-harness.md) | Diseño harness (capas, código, CI, schema) |
| [spec-gaps.md](spec-gaps.md) | Checklist cierre pre-implementación |
| [ingest.md](ingest.md) | ContextBundle, casos multilingües |
