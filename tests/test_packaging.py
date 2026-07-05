"""Packaging smoke tests."""

from __future__ import annotations

import subprocess
import sys


def test_import_optimize_context_without_pythonpath():
    proc = subprocess.run(
        [sys.executable, "-c", "from coe import optimize_context; print('ok')"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "ok"
