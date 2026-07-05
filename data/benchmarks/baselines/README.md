# Baselines de benchmark (versionados)

Informes de referencia para `compare.py` en PR. **No** gitignore — forman parte del contrato de no-regresión.

| Fichero | Perfil | Tier / tags | Cuándo refrescar |
|---------|--------|-------------|------------------|
| `n1_smoke.json` | `n1` | smoke · `core` | Tras cambiar N1 o umbral del perfil |
| `n1_n2_en_smoke.json` | `n1_n2_en` | smoke · `core` | Tras cambiar N2 EN o casos `core` |
| `n1_n2_es_smoke.json` | `n1_n2_es` | smoke · `multilingual` | Tras cambiar N2 ES o casos ES |
| `l0_n1_en_smoke.json` | `l0_n1_en` | smoke · `multilingual` | Tras cambiar L0 o perfil L0→N1 |
| `n5_session_smoke.json` | `n5_session` | smoke · `multi_turn` | Tras cambiar N5 o casos sesión |
| `n1_n2_n3_en_smoke.json` | `n1_n2_n3_en` | smoke · `core` | Tras cambiar N3 o casos `core` |

## CI local

**GitHub Actions está desactivado** (sin coste en la nube). El gate de calidad se ejecuta en local antes de push:

```bash
python run.py --ci
```

Equivale a `pytest` + los seis perfiles smoke con `--compare-baseline` (evaluador mock, sin Ollama). Ver [`.github/workflows/README.md`](../../.github/workflows/README.md).

Nightly mock opcional: `bash scripts/ci/nightly-mock.sh`.

## Refrescar baseline (proceso)

1. En rama de mejora intencional, ejecutar p. ej.:  
   `python scripts/benchmark/run.py --tier smoke --profile n1_n2_en --compare-baseline data/benchmarks/baselines/n1_n2_en_smoke.json`
2. Verificar que el gate mejora o se mantiene por razones documentadas.
3. Si el reporte es la nueva referencia, copiar `report.json` a `data/benchmarks/baselines/{profile}_smoke.json`.
4. PR dedicado: título `benchmark: refresh baseline n1_n2_en`.

Los baselines incluyen `harness_version`, `embedding_model`, `embedding_backend` y `git_sha` en `metadata` / `config.json`.
