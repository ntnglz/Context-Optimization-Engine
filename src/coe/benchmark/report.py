"""Informes, gate y comparación de regresiones."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .schema import BenchmarkReport, PipelineProfile
from .scorers.embedding import DEFAULT_BACKEND, DEFAULT_MODEL


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


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

    if gate.comprehension_similarity is not None:
        mean_sim = summary.get("comprehension_similarity_mean")
        if mean_sim is None:
            failures.append("comprehension_similarity_mean missing from summary")
        elif mean_sim < gate.comprehension_similarity:
            failures.append(
                f"comprehension_similarity_mean {mean_sim} < {gate.comprehension_similarity}"
            )

    delta_min = gate.comprehension_delta_min
    if delta_min is not None:
        mean_delta = summary.get("comprehension_delta_mean")
        if mean_delta is None:
            failures.append("comprehension_delta_mean missing from summary")
        elif mean_delta < delta_min:
            failures.append(
                f"comprehension_delta_mean {mean_delta} < {delta_min}"
            )

    if gate.readability_score_min is not None:
        mean_read = summary.get("readability_score_mean")
        if mean_read is not None and mean_read < gate.readability_score_min:
            failures.append(
                f"readability_score_mean {mean_read} < {gate.readability_score_min}"
            )

    if gate.user_language_match is not None:
        rate = summary.get("user_language_match_rate")
        if rate is None:
            failures.append("user_language_match_rate missing from summary")
        elif rate < gate.user_language_match:
            failures.append(
                f"user_language_match_rate {rate} < {gate.user_language_match}"
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
    if report.metadata:
        lines.extend(["", "## Metadata", ""])
        for key, value in report.metadata.items():
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
        if result.metrics.comprehension_similarity is not None:
            lines.append(
                f"- comprehension_similarity: {result.metrics.comprehension_similarity:.4f}"
            )
        if result.metrics.readability_score is not None:
            lines.append(
                f"- readability_score: {result.metrics.readability_score:.2f}"
            )
        if result.failures:
            for f in result.failures:
                lines.append(f"- failure: {f}")
        lines.append("")
    return "\n".join(lines)


def build_report_metadata(
    *,
    embedding_backend: str,
    embedding_model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    return {
        "git_sha": git_sha(),
        "embedding_backend": embedding_backend,
        "embedding_model": embedding_model,
    }


def save_report(
    report: BenchmarkReport,
    output_dir: Path,
    *,
    config: dict[str, Any] | None = None,
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    md_path = output_dir / "report.md"
    config_path = output_dir / "config.json"

    payload = report.to_dict()
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown_report(report), encoding="utf-8")

    config_payload = {
        "harness_version": report.harness_version,
        "profile_id": report.profile_id,
        "tier": report.tier,
        "evaluator": report.evaluator,
        **(config or {}),
        **report.metadata,
    }
    config_path.write_text(
        json.dumps(config_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return json_path, md_path, config_path


_HIGHER_IS_BETTER = {
    "factual_recall_mean",
    "comprehension_similarity_mean",
    "comprehension_delta_mean",
    "readability_score_mean",
    "user_language_match_rate",
}

_LOWER_IS_BETTER = {
    "t_coe_p95_ms",
    "artifact_leak_rate",
}


def compare_reports(
    current: dict[str, Any],
    baseline: dict[str, Any],
) -> list[str]:
    """Regresiones: KPI summary empeora respecto al baseline."""
    return [item["message"] for item in compare_reports_detailed(current, baseline)]


def compare_reports_detailed(
    current: dict[str, Any],
    baseline: dict[str, Any],
) -> list[dict[str, Any]]:
    regressions: list[dict[str, Any]] = []
    cur_s = current.get("summary") or {}
    base_s = baseline.get("summary") or {}

    for key in _HIGHER_IS_BETTER:
        cur_val = cur_s.get(key)
        base_val = base_s.get(key)
        if cur_val is None or base_val is None:
            continue
        if cur_val < base_val:
            regressions.append(
                {
                    "metric": key,
                    "current": cur_val,
                    "baseline": base_val,
                    "message": f"{key} regressed ({cur_val} < {base_val})",
                }
            )

    for key in _LOWER_IS_BETTER:
        cur_val = cur_s.get(key)
        base_val = base_s.get(key)
        if cur_val is None or base_val is None:
            continue
        if cur_val > base_val:
            if key == "t_coe_p95_ms" and (cur_val - base_val) <= 0.05:
                continue
            regressions.append(
                {
                    "metric": key,
                    "current": cur_val,
                    "baseline": base_val,
                    "message": f"{key} regressed ({cur_val} > {base_val})",
                }
            )

    return regressions


def aggregate_reports(reports: list[BenchmarkReport]) -> BenchmarkReport:
    """Promedia summaries de varias ejecuciones (tier release ×N)."""
    if not reports:
        raise ValueError("aggregate_reports requires at least one report")
    if len(reports) == 1:
        return reports[0]

    base = reports[0]
    numeric_keys = set()
    for report in reports:
        numeric_keys.update(report.summary.keys())

    merged_summary: dict[str, Any] = {}
    for key in sorted(numeric_keys):
        values = [r.summary[key] for r in reports if key in r.summary]
        if not values:
            continue
        if isinstance(values[0], (int, float)):
            merged_summary[key] = round(sum(values) / len(values), 4)
        else:
            merged_summary[key] = values[0]

    gate_passed = all(r.gate_passed for r in reports)
    gate_failures: list[str] = []
    if not gate_passed:
        failed = sum(1 for r in reports if not r.gate_passed)
        gate_failures.append(f"{failed}/{len(reports)} runs failed gate")

    metadata = dict(base.metadata)
    metadata["runs"] = len(reports)

    return BenchmarkReport(
        harness_version=base.harness_version,
        profile_id=base.profile_id,
        tier=base.tier,
        evaluator=base.evaluator,
        cases_run=base.cases_run,
        cases_passed=min(r.cases_passed for r in reports),
        gate_passed=gate_passed,
        gate_failures=gate_failures,
        results=base.results,
        summary=merged_summary,
        metadata=metadata,
    )
