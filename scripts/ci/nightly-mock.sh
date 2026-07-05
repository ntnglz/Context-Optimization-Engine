#!/usr/bin/env bash
# Nightly mock local — sustituto del antiguo benchmark-nightly.yml (sin Ollama)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

step() {
  echo ""
  echo "==> $*"
}

step "nightly tier — profile n1 (mock)"
"$PYTHON" scripts/benchmark/run.py --tier nightly --profile n1 --evaluator mock

step "nightly multilingual — profile n1_es (mock)"
"$PYTHON" scripts/benchmark/run.py --tier nightly --profile n1_es --tags multilingual --evaluator mock

step "multi-turn N5 session smoke + baseline"
"$PYTHON" scripts/benchmark/run.py --tier smoke --profile n5_session \
  --tags multi_turn --evaluator mock \
  --compare-baseline data/benchmarks/baselines/n5_session_smoke.json

echo ""
echo "CI nightly (mock): PASS"
