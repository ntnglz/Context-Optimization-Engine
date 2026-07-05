# Evaluadores Ollama — fast path vs quality path

> Medición en **DevSSD** · 2026-07-05 · Perfil `n5_graph_session_release` · 2 casos `dev_agent` · 1 run salvo donde se indica.

El harness E2E compara **respuesta A** (contexto crudo) vs **respuesta B** (contexto COE) con el mismo LLM. La métrica clave del gate release es **`comprehension_similarity`** (embedding local entre A y B): mide si optimizar el contexto **no cambia** lo que el modelo responde.

---

## Dos caminos

| Camino | Cuándo | Modelo típico | Script | ¿Bloquea merge? |
|--------|--------|---------------|--------|-----------------|
| **Quality (release)** | Antes de merge grande, validar COE | `qwen3:4b` (o `qwen3:8b` estricto) | `python run.py --release-dev-agent` | Sí (exit ≠ 0 si gate falla) |
| **Fast (exploración)** | Iterar casos, probar pipeline, feedback rápido | `granite4.1:3b`, `gemma3:4b` | `bash scripts/ci/benchmark-dev-agent-fast.sh` | No (exit 0; gate informativo) |
| **CI smoke** | Cada push | **mock** (sin Ollama) | `python run.py --ci` | Sí |

---

## Matriz de modelos (DevSSD, jul 2025)

Perfil **`n5_graph_session_release`**: `comprehension_similarity` ≥ **0.86**, `comprehension_delta_min` ≥ **−0.14**, `factual_recall` ≥ **0.95**.

| Modelo | Wall (1 run, 2 casos) | similitud media | factual recall | Gate release | Notas |
|--------|----------------------|-----------------|----------------|--------------|-------|
| **qwen3:4b** | ~130 s | **0.894** | 1.0 | **PASS** | Default release; lento, semántica estable |
| **qwen3:4b** ×3 runs | ~390 s | 0.894 | 1.0 | **PASS** | Gate oficial `release-dev-agent.sh` |
| **granite4.1:3b** | **~12 s** | 0.413 | 0.75 | FAIL | Rápido; respuestas A/B muy distintas |
| **pcm-granite:latest** | ~17 s | 0.532 | 0.50 | FAIL | Modelo PCM; no calibrado para evaluación chat |
| **gemma3:4b** | ~18 s | 0.474 | 0.50 | FAIL | Rápido; similar a Granite en gate |
| **qwen3.5:9b** | ~20 min / 3 runs | 0.489 | 0.50 | FAIL | Más capaz en otros tasks; peor en este benchmark |

Perfil estricto **`n5_graph_session`** (similitud ≥ 0.90): **qwen3:4b** falla por 0.894 — usar **`qwen3:8b`** tras `ollama pull` si se exige gate estricto.

---

## Detalle por caso — granite4.1:3b (fast)

| Caso | similitud | factual | readability |
|------|-----------|---------|-------------|
| `dev_pytest_failure_session_v1` | 0.602 | 1.0 | 5.0 |
| `dev_warnings_session_v1` | 0.223 | 0.50 | 4.0 |

El caso en **español** (`dev_warnings_session_v1`) penaliza más a Granite/Gemma: respuestas A/B divergen y baja `factual_recall`.

---

## Detalle por caso — qwen3:4b (quality)

| Caso | similitud | factual | readability |
|------|-----------|---------|-------------|
| `dev_pytest_failure_session_v1` | 0.861 | 1.0 | 5.0 |
| `dev_warnings_session_v1` | 0.927 | 1.0 | 4.0 |

---

## Comandos

### Gate de calidad (obligatorio antes de merge grande)

```bash
python run.py --release-dev-agent
# = OLLAMA_MODEL=qwen3:4b PROFILE=n5_graph_session_release RUNS=3
```

Gate estricto (cuando tengas el modelo):

```bash
ollama pull qwen3:8b
OLLAMA_MODEL=qwen3:8b PROFILE=n5_graph_session RUNS=3 \
  bash scripts/ci/release-dev-agent.sh
```

### Iteración rápida (Granite / Gemma)

```bash
bash scripts/ci/benchmark-dev-agent-fast.sh
# Granite por defecto

OLLAMA_MODEL=gemma3:4b bash scripts/ci/benchmark-dev-agent-fast.sh
OLLAMA_MODEL=granite4.1:3b RUNS=1 bash scripts/ci/benchmark-dev-agent-fast.sh
```

Manual equivalente:

```bash
python scripts/benchmark/run.py --tier release \
  --profile n5_graph_session_release --tags dev_agent \
  --evaluator ollama:granite4.1:3b --runs 1
```

### Requisitos

- Ollama en marcha: `ollama ps` / `curl -s http://localhost:11434/api/tags`
- Modelo instalado: `ollama list`
- Venv del repo: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Si el modelo no existe: error explícito *«Check model name with ollama list»*

---

## Perfiles YAML

| Perfil | Uso | `comprehension_similarity` |
|--------|-----|----------------------------|
| `n5_graph_session` | Gate documentado / modelos grandes | 0.90 |
| `n5_graph_session_release` | DevSSD, qwen3:4b calibrado | 0.86 |

No crear perfil «fast» con umbrales bajos para Granite: el gate perdería significado. Fast path = **informative only**.

---

## Recomendación operativa

1. **Desarrollo diario:** `python run.py --ci` (mock, segundos).
2. **Probar casos dev_agent con feedback LLM:** `benchmark-dev-agent-fast.sh` + Granite o Gemma (~10–20 s).
3. **Antes de push/merge con cambios en pipeline o casos:** `python run.py --release-dev-agent` con Qwen (~7 min, 3 runs).
4. **Modelos PCM** (`pcm-granite`, `pcm-compressor`): reservados para compresión de instrucciones; no usar como evaluador E2E del harness COE.

---

## Documentos relacionados

| Documento | Rol |
|-----------|-----|
| [benchmark-harness.md](benchmark-harness.md) | Diseño harness, tiers, gates |
| [execution-plan.md](execution-plan.md) | Fase 8 release gate |
| `scripts/ci/release-dev-agent.sh` | Quality path |
| `scripts/ci/benchmark-dev-agent-fast.sh` | Fast path |
