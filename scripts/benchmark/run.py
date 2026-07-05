#!/usr/bin/env python3
"""CLI del harness de benchmarks COE."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from coe.benchmark.report import compare_reports, save_report  # noqa: E402
from coe.benchmark.runner import default_benchmark_root, run_suite_from_ids  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="COE benchmark harness")
    parser.add_argument("--profile", default="n1", help="Profile id (YAML stem)")
    parser.add_argument(
        "--tier",
        default="smoke",
        choices=["smoke", "ci", "nightly", "release"],
    )
    parser.add_argument("--tags", help="Comma-separated case tags filter")
    parser.add_argument(
        "--benchmark-root",
        type=Path,
        default=None,
        help="Path to data/benchmarks",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for report (default: data/benchmarks/runs/...)",
    )
    parser.add_argument(
        "--compare-baseline",
        type=Path,
        default=None,
        help="Baseline report.json; fail if KPIs regress",
    )
    parser.add_argument(
        "--embedding-backend",
        default=None,
        choices=["auto", "simple", "sentence_transformers"],
        help="Backend for comprehension_similarity (default: simple / COE_EMBEDDING_BACKEND)",
    )
    args = parser.parse_args()

    root = args.benchmark_root or default_benchmark_root()
    tags = set(args.tags.split(",")) if args.tags else None

    try:
        report = run_suite_from_ids(
            profile_id=args.profile,
            tier=args.tier,
            tags=tags,
            benchmark_root=root,
            embedding_backend=args.embedding_backend,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.out:
        out_dir = args.out
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = root / "runs" / f"{args.profile}_{args.tier}_{ts}"

    json_path, md_path, config_path = save_report(report, out_dir)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {config_path}")
    print(f"Gate: {'PASS' if report.gate_passed else 'FAIL'}")
    if report.gate_failures:
        for item in report.gate_failures:
            print(f"  - {item}")

    exit_code = 0 if report.gate_passed else 1

    if args.compare_baseline:
        baseline = json.loads(args.compare_baseline.read_text(encoding="utf-8"))
        regressions = compare_reports(report.to_dict(), baseline)
        if regressions:
            print("Baseline compare: FAIL")
            for r in regressions:
                print(f"  - {r}")
            exit_code = 1
        else:
            print("Baseline compare: PASS")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
