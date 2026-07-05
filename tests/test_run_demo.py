"""Tests for run.py visitor entry points."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "data" / "examples" / "acme_rag_en.json"


def _run_run_py(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**__import__("os").environ}
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if "PYTHONPATH" not in env else f"{src}:{env['PYTHONPATH']}"
    return subprocess.run(
        [sys.executable, str(ROOT / "run.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_demo_uses_optimize_context_en():
    proc = _run_run_py("--demo")
    assert proc.returncode == 0, proc.stderr
    assert "Company: ACME" in proc.stdout
    assert "Juan works at ACME and approved the budget." in proc.stdout
    assert "Globex" not in proc.stdout
    assert "## Input" in proc.stdout
    assert "## Optimized output" in proc.stdout


def test_quickstart_includes_snippet():
    proc = _run_run_py("--quickstart")
    assert proc.returncode == 0, proc.stderr
    assert "from coe import optimize_context" in proc.stdout
    assert 'optimize_context(blocks, levels=[1, 2], locale="en")' in proc.stdout


def test_canonical_example_file_matches_contract():
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert data["levels"] == [1, 2]
    assert data["locale"] == "en"
    assert len(data["blocks"]) == 3
    assert all(b["source_type"] == "rag" for b in data["blocks"])
