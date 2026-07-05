"""Orquestación de suites de benchmark."""

from __future__ import annotations

from pathlib import Path

from . import HARNESS_VERSION
from .dataset import load_cases
from .e2e import run_e2e_arms
from .evaluators.base import default_evaluator_for_tier
from .evaluators.factory import create_evaluator
from .pipeline_runner import run_pipeline_on_case
from .profile import load_profile_by_id
from .report import build_report_metadata, evaluate_gate
from .schema import BenchmarkCase, BenchmarkReport, CaseMetrics, CaseResult, PipelineProfile
from .scorers.artifacts import detect_artifact_leak
from .scorers.embedding import DEFAULT_BACKEND, EmbeddingBackend, resolve_backend
from .scorers.latency import latency_ok


def run_suite(
    *,
    profile: PipelineProfile,
    cases_dir: Path,
    tier: str = "smoke",
    tags: set[str] | None = None,
    evaluator: str | None = None,
    embedding_backend: EmbeddingBackend | None = None,
    fail_fast: bool = False,
) -> BenchmarkReport:
    cases = load_cases(cases_dir, tags=tags)
    if not cases:
        raise ValueError(f"No cases found in {cases_dir} with tags={tags}")

    evaluator_spec = evaluator or default_evaluator_for_tier(tier)
    llm_evaluator, evaluator_id = create_evaluator(evaluator_spec)
    resolved_backend = resolve_backend(embedding_backend)

    results: list[CaseResult] = []
    for case in cases:
        results.append(
            _run_case(
                case,
                profile,
                tier=tier,
                evaluator=llm_evaluator,
                evaluator_id=evaluator_id,
                embedding_backend=embedding_backend,
                fail_fast=fail_fast,
            )
        )

    metadata = build_report_metadata(embedding_backend=resolved_backend)
    metadata["evaluator"] = evaluator_id
    if evaluator_id.startswith("ollama:"):
        metadata["ollama_model"] = evaluator_id.split(":", 1)[1]

    report = BenchmarkReport(
        harness_version=HARNESS_VERSION,
        profile_id=profile.id,
        tier=tier,
        evaluator=evaluator_id,
        cases_run=len(results),
        cases_passed=sum(1 for r in results if r.passed),
        gate_passed=False,
        gate_failures=[],
        results=results,
        metadata=metadata,
    )
    report.summary = _build_summary(results)
    report.gate_passed, report.gate_failures = evaluate_gate(report, profile)
    return report


def _run_case(
    case: BenchmarkCase,
    profile: PipelineProfile,
    *,
    tier: str,
    evaluator,
    evaluator_id: str,
    embedding_backend: EmbeddingBackend | None,
    fail_fast: bool,
) -> CaseResult:
    pipeline = run_pipeline_on_case(case, profile)
    prose_ratio = (
        pipeline.optimized_tokens / pipeline.original_tokens
        if pipeline.original_tokens
        else 1.0
    )
    context_artifact = detect_artifact_leak(pipeline.optimized_text)

    failures: list[str] = []
    if not latency_ok(pipeline.t_coe_ms, profile.gate.t_coe_p95_ms):
        failures.append(
            f"t_coe {pipeline.t_coe_ms:.1f}ms > budget {profile.gate.t_coe_p95_ms}ms"
        )
    if context_artifact:
        failures.append("artifact_leak in optimized context")

    layer1_failed = len(failures) > 0
    skip_e2e = fail_fast and layer1_failed

    recall = None
    f1 = None
    similarity = None
    delta = None
    readability_a = None
    readability_b = None
    lang_ok = None
    response_artifact = False
    arm_a = ""
    arm_b = ""

    if tier in ("smoke", "ci", "nightly", "release") and not skip_e2e:
        judge_readability = evaluator_id != "mock" and (
            tier in ("nightly", "release")
            or profile.gate.readability_score_min is not None
        )
        e2e = run_e2e_arms(
            case,
            optimized_context=pipeline.optimized_text,
            evaluator=evaluator,
            evaluator_id=evaluator_id,
            profile=profile,
            embedding_backend=embedding_backend,
            judge_readability_enabled=judge_readability,
        )
        arm_a = e2e.arm_a
        arm_b = e2e.arm_b
        recall = e2e.factual_recall
        f1 = e2e.factual_f1
        similarity = e2e.comprehension_similarity
        delta = e2e.comprehension_delta
        readability_a = e2e.readability_score_a
        readability_b = e2e.readability_score_b
        lang_ok = e2e.user_language_ok
        response_artifact = e2e.response_artifact_leak
        if e2e.failures:
            failures.extend(e2e.failures)
    elif skip_e2e:
        failures.append("E2E skipped (--fail-fast after layer 1 failure)")

    metrics = CaseMetrics(
        t_coe_ms=pipeline.t_coe_ms,
        optimized_tokens=pipeline.optimized_tokens,
        original_tokens=pipeline.original_tokens,
        prose_ratio=prose_ratio,
        artifact_leak=context_artifact or response_artifact,
        factual_recall=recall,
        factual_f1=f1,
        comprehension_similarity=similarity,
        comprehension_delta=delta,
        readability_score=readability_b,
        readability_score_a=readability_a,
        user_language_ok=lang_ok,
        response_artifact_leak=response_artifact,
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
    readability_mean = _mean([r.metrics.readability_score for r in results])
    lang_rate = _mean(
        [1.0 if r.metrics.user_language_ok else 0.0 for r in results if r.metrics.user_language_ok is not None]
    )
    if sim_mean is not None:
        summary["comprehension_similarity_mean"] = sim_mean
    if delta_mean is not None:
        summary["comprehension_delta_mean"] = delta_mean
    if f1_mean is not None:
        summary["factual_f1_mean"] = f1_mean
    if readability_mean is not None:
        summary["readability_score_mean"] = readability_mean
    if lang_rate is not None:
        summary["user_language_match_rate"] = lang_rate
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
    evaluator: str | None = None,
    fail_fast: bool = False,
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
        evaluator=evaluator,
        embedding_backend=embedding_backend or DEFAULT_BACKEND,
        fail_fast=fail_fast,
    )
