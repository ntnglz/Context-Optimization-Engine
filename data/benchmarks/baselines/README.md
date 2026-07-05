# Baselines de benchmark (versionados)

Informes de referencia para `compare.py` en PR. **No** gitignore — forman parte del contrato de no-regresión.

| Fichero | Perfil | Tier | Cuándo refrescar |
|---------|--------|------|------------------|
| `n1_smoke.json` | `n1` | smoke | Tras cambiar N1 o umbral del perfil |
| `n1_n2_en_smoke.json` | `n1_n2_en` | smoke | Tras cambiar N2 o casos `core` |

## Refrescar baseline (proceso)

1. En rama de mejora intencional, ejecutar:  
   `python scripts/benchmark/run.py --tier smoke --profile n1_n2_en --out /tmp/report.json`
2. Verificar que el gate mejora o se mantiene por razones documentadas.
3. Copiar a `data/benchmarks/baselines/{profile}_smoke.json`.
4. PR dedicado: título `benchmark: refresh baseline n1_n2_en`.

Los baselines incluyen `harness_version`, `embedding_model`, `embedding_backend` y `git_sha` en `metadata` / `config.json`.
