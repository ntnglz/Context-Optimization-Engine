"""Informes y gate de benchmarks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import BenchmarkReport, PipelineProfile


def evaluate_gate(
    report: BenchmarkReport,
    profile: PipelineProfile,
) -> tuple[bool, list[str]]:
    failures: list[str] = []
    gate = profile.gate
    summary = report.summary

    if any(not r.passed for r in report.results):
        failed_ids = [r.case_id for r in report.results if not r.passed]
        failures.append(f"cases failed: {', '.join(failed_ids)}")

    if gate.t_coe_p95_ms is not None:
        p95 = summary.get("t_coe_p95_ms", 0)
        if p95 > gate.t_coe_p95_ms:
            failures.append(f"t_coe_p95 {p95}ms > {gate.t_coe_p95_ms}ms")

    max_artifact = gate.artifact_leak_rate_max
    if max_artifact is not None:
        rate = summary.get("artifact_leak_rate", 0)
        if rate > max_artifact:
            failures.append(f"artifact_leak_rate {rate} > {max_artifact}")

    if gate.factual_recall is not None:
        mean_recall = summary.get("factual_recall_mean", 0)
        if mean_recall < gate.factual_recall:
            failures.append(
                f"factual_recall_mean {mean_recall} < {gate.factual_recall}"
            )

    return len(failures) == 0, failures


def render_markdown_report(report: BenchmarkReport) -> str:
    lines = [
        "# COE Benchmark Report",
        "",
        f"- **Profile:** `{report.profile_id}`",
        f"- **Tier:** `{report.tier}`",
        f"- **Evaluator:** `{report.evaluator}`",
        f"- **Harness:** `{report.harness_version}`",
        f"- **Gate:** {'PASS' if report.gate_passed else 'FAIL'}",
        "",
        "## Summary",
        "",
    ]
    for key, value in report.summary.items():
        lines.append(f"- `{key}`: {value}")
    if report.gate_failures:
        lines.extend(["", "## Gate failures", ""])
        for item in report.gate_failures:
            lines.append(f"- {item}")
    lines.extend(["", "## Cases", ""])
    for result in report.results:
        status = "OK" if result.passed else "FAIL"
        lines.append(f"### {result.case_id} — {status}")
        lines.append(f"- t_coe_ms: {result.metrics.t_coe_ms:.2f}")
        if result.metrics.factual_recall is not None:
            lines.append(f"- factual_recall: {result.metrics.factual_recall:.2f}")
        if result.failures:
            for f in result.failures:
                lines.append(f"- failure: {f}")
        lines.append("")
    return "\n".join(lines)


def save_report(report: BenchmarkReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    md_path = output_dir / "report.md"
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown_report(report), encoding="utf-8")
    return json_path, md_path


def compare_reports(
    current: dict[str, Any],
    baseline: dict[str, Any],
) -> list[str]:
    """Regresiones: KPI summary empeora respecto al baseline."""
    regressions: list[str] = []
    cur_s = current.get("summary") or {}
    base_s = baseline.get("summary") or {}

    if cur_s.get("factual_recall_mean", 0) < base_s.get("factual_recall_mean", 0):
        regressions.append("factual_recall_mean regressed")

    if cur_s.get("t_coe_p95_ms", 0) > base_s.get("t_coe_p95_ms", float("inf")):
        regressions.append("t_coe_p95_ms regressed")

    if cur_s.get("artifact_leak_rate", 1) > base_s.get("artifact_leak_rate", 0):
        regressions.append("artifact_leak_rate regressed")

    return regressions
