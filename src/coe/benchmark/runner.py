"""Orquestación de suites de benchmark."""

from __future__ import annotations

from pathlib import Path

from . import HARNESS_VERSION
from .dataset import load_cases
from .evaluators.mock import mock_responses
from .pipeline_runner import run_pipeline_on_case
from .profile import load_profile_by_id
from .report import build_report_metadata, evaluate_gate
from .schema import BenchmarkCase, BenchmarkReport, CaseMetrics, CaseResult, PipelineProfile
from .scorers.artifacts import detect_artifact_leak
from .scorers.embedding import DEFAULT_BACKEND, EmbeddingBackend, resolve_backend
from .scorers.factual import (
    comprehension_delta,
    factual_f1,
    factual_recall,
)
from .scorers.latency import latency_ok


def run_suite(
    *,
    profile: PipelineProfile,
    cases_dir: Path,
    tier: str = "smoke",
    tags: set[str] | None = None,
    evaluator: str = "mock",
    embedding_backend: EmbeddingBackend | None = None,
) -> BenchmarkReport:
    cases = load_cases(cases_dir, tags=tags)
    if not cases:
        raise ValueError(f"No cases found in {cases_dir} with tags={tags}")

    resolved_backend = resolve_backend(embedding_backend)
    results: list[CaseResult] = []
    for case in cases:
        results.append(
            _run_case(
                case,
                profile,
                tier=tier,
                evaluator=evaluator,
                embedding_backend=embedding_backend,
            )
        )

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
        metadata=build_report_metadata(embedding_backend=resolved_backend),
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
    embedding_backend: EmbeddingBackend | None,
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
    f1: float | None = None
    similarity: float | None = None
    delta: float | None = None
    arm_a = ""
    arm_b = ""
    if tier in ("smoke", "ci", "nightly", "release"):
        if evaluator == "mock":
            mock = mock_responses(case)
            arm_a = mock.arm_a_response
            arm_b = mock.arm_b_response
            recall = factual_recall(arm_b, case.expected_facts)
            f1 = factual_f1(arm_b, case.expected_facts)
            if profile.gate.factual_recall is not None and recall < profile.gate.factual_recall:
                failures.append(
                    f"factual_recall {recall:.2f} < {profile.gate.factual_recall}"
                )

            from .scorers.embedding import comprehension_similarity

            similarity = comprehension_similarity(
                arm_a,
                arm_b,
                backend=embedding_backend,
            )
            delta = comprehension_delta(similarity)
            if (
                profile.gate.comprehension_similarity is not None
                and similarity < profile.gate.comprehension_similarity
            ):
                failures.append(
                    f"comprehension_similarity {similarity:.4f} < "
                    f"{profile.gate.comprehension_similarity}"
                )
            delta_min = profile.gate.comprehension_delta_min
            if delta_min is not None and delta < delta_min:
                failures.append(
                    f"comprehension_delta {delta:.4f} < {delta_min}"
                )
        elif evaluator != "mock":
            failures.append(f"evaluator {evaluator!r} not implemented before H4")

    metrics = CaseMetrics(
        t_coe_ms=pipeline.t_coe_ms,
        optimized_tokens=pipeline.optimized_tokens,
        original_tokens=pipeline.original_tokens,
        prose_ratio=prose_ratio,
        artifact_leak=artifact,
        factual_recall=recall,
        factual_f1=f1,
        comprehension_similarity=similarity,
        comprehension_delta=delta,
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

    def _mean(values: list[float | None]) -> float | None:
        present = [v for v in values if v is not None]
        if not present:
            return None
        return round(sum(present) / len(present), 4)

    summary = {
        "factual_recall_mean": _mean([r.metrics.factual_recall for r in results]) or 0.0,
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
    sim_mean = _mean([r.metrics.comprehension_similarity for r in results])
    delta_mean = _mean([r.metrics.comprehension_delta for r in results])
    f1_mean = _mean([r.metrics.factual_f1 for r in results])
    if sim_mean is not None:
        summary["comprehension_similarity_mean"] = sim_mean
    if delta_mean is not None:
        summary["comprehension_delta_mean"] = delta_mean
    if f1_mean is not None:
        summary["factual_f1_mean"] = f1_mean
    return summary


def default_benchmark_root() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "benchmarks"


def run_suite_from_ids(
    *,
    profile_id: str,
    tier: str = "smoke",
    tags: set[str] | None = None,
    benchmark_root: Path | None = None,
    embedding_backend: EmbeddingBackend | None = None,
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
        embedding_backend=embedding_backend or DEFAULT_BACKEND,
    )
