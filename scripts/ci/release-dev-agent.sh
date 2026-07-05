#!/usr/bin/env bash
# Release tier — dev_agent cases with Ollama (local, manual; not part of run.py --ci)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3:8b}"
PROFILE="${PROFILE:-n5_graph_session}"
RUNS="${RUNS:-3}"

step() {
  echo ""
  echo "==> $*"
}

step "release tier — dev_agent cases (Ollama ${OLLAMA_MODEL}, ${RUNS} runs)"
"$PYTHON" scripts/benchmark/run.py \
  --tier release \
  --profile "$PROFILE" \
  --tags dev_agent \
  --evaluator "ollama:${OLLAMA_MODEL}" \
  --runs "$RUNS"

echo ""
echo "Release dev_agent: PASS (see data/benchmarks/runs/ for report)"
