#!/usr/bin/env bash
# CI smoke local — equivalente al antiguo .github/workflows/benchmark.yml
# Ejecutar antes de push: bash scripts/ci/smoke.sh  ·  python run.py --ci
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

run_benchmark() {
  local profile=$1
  local baseline=$2
  shift 2
  "$PYTHON" scripts/benchmark/run.py --tier smoke --profile "$profile" \
    --compare-baseline "$baseline" "$@"
}

step "pytest (capa 0)"
"$PYTHON" -m pytest tests/ -q

step "benchmark smoke n1"
run_benchmark n1 data/benchmarks/baselines/n1_smoke.json

step "benchmark smoke n1_n2_en"
run_benchmark n1_n2_en data/benchmarks/baselines/n1_n2_en_smoke.json

step "benchmark smoke n1_n2_es (multilingual)"
run_benchmark n1_n2_es data/benchmarks/baselines/n1_n2_es_smoke.json --tags multilingual

step "benchmark smoke l0_n1_en (multilingual)"
run_benchmark l0_n1_en data/benchmarks/baselines/l0_n1_en_smoke.json --tags multilingual

step "benchmark smoke n5_session (multi_turn)"
run_benchmark n5_session data/benchmarks/baselines/n5_session_smoke.json --tags multi_turn

step "benchmark smoke n1_n2_n3_en"
run_benchmark n1_n2_n3_en data/benchmarks/baselines/n1_n2_n3_en_smoke.json

step "benchmark smoke n1_n2_n3_n4_en"
run_benchmark n1_n2_n3_n4_en data/benchmarks/baselines/n1_n2_n3_n4_en_smoke.json

step "benchmark smoke n5_graph_session (multi_turn)"
run_benchmark n5_graph_session data/benchmarks/baselines/n5_graph_session_smoke.json --tags multi_turn

step "benchmark smoke coe_pcm_n1_en (coe+pcm)"
run_benchmark coe_pcm_n1_en data/benchmarks/baselines/coe_pcm_n1_en_smoke.json --tags coe_pcm

echo ""
echo "CI smoke: PASS"
