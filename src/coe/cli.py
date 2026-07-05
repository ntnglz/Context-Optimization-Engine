"""Console entry point for editable installs (`coe-demo`)."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    from run import main as run_main

    raise SystemExit(run_main(["--demo"]))
