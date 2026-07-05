"""Orquestación de suites de benchmark."""

from __future__ import annotations

from pathlib import Path

from . import HARNESS_VERSION
from .dataset import load_cases
from .evaluators.mock import mock_responses
from .pipeline_runner import run_pipeline_on_case
from .profile import load_profile_by_id
from .report import evaluate_gate
from .schema import BenchmarkCase, BenchmarkReport, CaseMetrics, CaseResult, PipelineProfile
from .scorers.artifacts import detect_artifact_leak
from .scorers.factual import factual_recall
from .scorers.latency import latency_ok


def run_suite(
    *,
    profile: PipelineProfile,
    cases_dir: Path,
    tier: str = "smoke",
    tags: set[str] | None = None,
    evaluator: str = "mock",
) -> BenchmarkReport:
    cases = load_cases(cases_dir, tags=tags)
    if not cases:
        raise ValueError(f"No cases found in {cases_dir} with tags={tags}")

    results: list[CaseResult] = []
    for case in cases:
        results.append(_run_case(case, profile, tier=tier, evaluator=evaluator))

    report = BenchmarkReport(
        harness_version=HARNESS_VERSION,
        profile_id=profile.id,
        tier=tier,
        evaluator=evaluator,
        cases_run=len(results),
        cases_passed=sum(1 for r in results if r.passed),
        gate_passed=False,
        gate_failures=[],
        results=results,
    )
    report.summary = _build_summary(results)
    report.gate_passed, report.gate_failures = evaluate_gate(report, profile)
    return report


def _run_case(
    case: BenchmarkCase,
    profile: PipelineProfile,
    *,
    tier: str,
    evaluator: str,
) -> CaseResult:
    pipeline = run_pipeline_on_case(case, profile)
    prose_ratio = (
        pipeline.optimized_tokens / pipeline.original_tokens
        if pipeline.original_tokens
        else 1.0
    )
    artifact = detect_artifact_leak(pipeline.optimized_text)

    failures: list[str] = []
    if not latency_ok(pipeline.t_coe_ms, profile.gate.t_coe_p95_ms):
        failures.append(
            f"t_coe {pipeline.t_coe_ms:.1f}ms > budget {profile.gate.t_coe_p95_ms}ms"
        )
    if artifact:
        failures.append("artifact_leak in optimized context")

    recall: float | None = None
    arm_a = ""
    arm_b = ""
    if tier in ("smoke", "ci", "nightly", "release"):
        if evaluator == "mock":
            mock = mock_responses(case)
            arm_a = mock.arm_a_response
            arm_b = mock.arm_b_response
            recall = factual_recall(arm_b, case.expected_facts)
            if profile.gate.factual_recall is not None and recall < profile.gate.factual_recall:
                failures.append(
                    f"factual_recall {recall:.2f} < {profile.gate.factual_recall}"
                )
        elif evaluator != "mock":
            failures.append(f"evaluator {evaluator!r} not implemented in H1")

    metrics = CaseMetrics(
        t_coe_ms=pipeline.t_coe_ms,
        optimized_tokens=pipeline.optimized_tokens,
        original_tokens=pipeline.original_tokens,
        prose_ratio=prose_ratio,
        artifact_leak=artifact,
        factual_recall=recall,
    )
    return CaseResult(
        case_id=case.id,
        passed=len(failures) == 0,
        failures=failures,
        metrics=metrics,
        optimized_context_preview=pipeline.optimized_text[:200],
        mock_arm_a=arm_a,
        mock_arm_b=arm_b,
    )


def _build_summary(results: list[CaseResult]) -> dict:
    if not results:
        return {}
    n = len(results)
    return {
        "factual_recall_mean": round(
            sum(r.metrics.factual_recall or 0 for r in results) / n, 4
        ),
        "t_coe_p95_ms": round(
            sorted(r.metrics.t_coe_ms for r in results)[max(0, int(n * 0.95) - 1)],
            2,
        ),
        "artifact_leak_rate": round(
            sum(1 for r in results if r.metrics.artifact_leak) / n, 4
        ),
        "prose_ratio_mean": round(
            sum(r.metrics.prose_ratio for r in results) / n, 4
        ),
    }


def default_benchmark_root() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "benchmarks"


def run_suite_from_ids(
    *,
    profile_id: str,
    tier: str = "smoke",
    tags: set[str] | None = None,
    benchmark_root: Path | None = None,
) -> BenchmarkReport:
    root = benchmark_root or default_benchmark_root()
    profile = load_profile_by_id(root / "profiles", profile_id)
    tag_filter = tags
    if tier == "smoke" and tags is None:
        tag_filter = {"core"}
    return run_suite(
        profile=profile,
        cases_dir=root / "cases",
        tier=tier,
        tags=tag_filter,
        evaluator="mock",
    )
