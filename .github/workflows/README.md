# GitHub Actions — desactivado

Los workflows de CI (`benchmark.yml`, `benchmark-nightly.yml`) **no se ejecutan** en este repositorio para evitar coste de GitHub Actions.

## CI local (procedimiento habitual)

Antes de push o merge:

```bash
python run.py --ci
# equivalente:
bash scripts/ci/smoke.sh
```

Nightly mock (opcional, sin Ollama):

```bash
bash scripts/ci/nightly-mock.sh
```

Detalle de perfiles, baselines y refresco: [data/benchmarks/baselines/README.md](../../data/benchmarks/baselines/README.md) · [docs/benchmark-harness.md](../../docs/benchmark-harness.md#10-ci--tiers-y-comandos).
