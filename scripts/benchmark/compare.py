#!/usr/bin/env python3
"""Compara dos report.json de benchmark y detecta regresiones."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from coe.benchmark.report import compare_reports_detailed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare COE benchmark reports")
    parser.add_argument("current", type=Path, help="Current report.json")
    parser.add_argument("baseline", type=Path, help="Baseline report.json")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable regression list",
    )
    args = parser.parse_args()

    try:
        current = json.loads(args.current.read_text(encoding="utf-8"))
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    regressions = compare_reports_detailed(current, baseline)
    if args.json:
        print(json.dumps(regressions, indent=2, ensure_ascii=False))
    else:
        if not regressions:
            print("Baseline compare: PASS")
        else:
            print("Baseline compare: FAIL")
            for item in regressions:
                print(f"  - {item['message']}")

    return 0 if not regressions else 1


if __name__ == "__main__":
    raise SystemExit(main())
