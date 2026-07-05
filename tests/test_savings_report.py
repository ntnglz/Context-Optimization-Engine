"""Tests for visitor-facing savings report generator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark" / "generate_savings_report.py"
README = ROOT / "README.md"
RESULTS = ROOT / "docs" / "benchmark-results.md"


def test_savings_report_script_runs():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Wrote docs/benchmark-results.md" in proc.stdout


def test_savings_report_check_passes():
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "up to date" in proc.stdout


def test_readme_has_generated_savings_section():
    text = README.read_text(encoding="utf-8")
    assert "<!-- coe-savings:start -->" in text
    assert "## Savings at a glance" in text
    assert "n1_n2_en" in text
    assert "docs/benchmark-results.md" in text


def test_benchmark_results_doc_exists_and_has_cases():
    assert RESULTS.exists()
    text = RESULTS.read_text(encoding="utf-8")
    assert "acme_budget_v1" in text
    assert "generate_savings_report.py" in text


def test_visitor_profiles_have_positive_savings():
    baselines = ROOT / "data" / "benchmarks" / "baselines"
    for name in ("n1_n2_en_smoke.json", "n1_n2_es_smoke.json", "n1_n2_zh_smoke.json"):
        data = json.loads((baselines / name).read_text(encoding="utf-8"))
        saved = [
            r["metrics"]["original_tokens"] - r["metrics"]["optimized_tokens"]
            for r in data["results"]
        ]
        assert any(s > 0 for s in saved), name
