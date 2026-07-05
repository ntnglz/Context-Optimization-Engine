#!/usr/bin/env bash
# Iteración rápida dev_agent — Ollama con modelos ligeros (Granite, Gemma).
# No sustituye al gate release (qwen3:4b). Imprime KPIs aunque falle el gate.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

OLLAMA_MODEL="${OLLAMA_MODEL:-granite4.1:3b}"
PROFILE="${PROFILE:-n5_graph_session_release}"
RUNS="${RUNS:-1}"

step() {
  echo ""
  echo "==> $*"
}

step "fast dev_agent — Ollama ${OLLAMA_MODEL} (${RUNS} run, profile ${PROFILE})"
set +e
"$PYTHON" scripts/benchmark/run.py \
  --tier release \
  --profile "$PROFILE" \
  --tags dev_agent \
  --evaluator "ollama:${OLLAMA_MODEL}" \
  --runs "$RUNS"
exit_code=$?
set -e

echo ""
if [[ "$exit_code" -eq 0 ]]; then
  echo "Fast dev_agent: gate PASS (informative; ver docs/benchmark-ollama.md)"
else
  echo "Fast dev_agent: gate FAIL (esperado con Granite/Gemma — usar release-dev-agent.sh para gate de calidad)"
  echo "Ver report en data/benchmarks/runs/"
fi
exit 0
