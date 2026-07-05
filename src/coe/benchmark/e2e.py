"""Orquestación E2E compartida (mock y LLM real)."""

from __future__ import annotations

from dataclasses import dataclass

from .evaluators.base import LLMEvaluator
from .evaluators.mock import mock_responses
from .scorers.artifacts import detect_artifact_leak
from .scorers.embedding import EmbeddingBackend, comprehension_similarity
from .scorers.factual import comprehension_delta, factual_f1, factual_recall
from .scorers.language import user_language_match
from .scorers.readability import judge_readability
from .arms import build_answer_messages, render_arm_a_context
from .schema import BenchmarkCase, PipelineProfile


@dataclass
class E2EScores:
    arm_a: str
    arm_b: str
    factual_recall: float | None
    factual_f1: float | None
    comprehension_similarity: float | None
    comprehension_delta: float | None
    readability_score_a: float | None = None
    readability_score_b: float | None = None
    user_language_ok: bool | None = None
    response_artifact_leak: bool = False
    failures: list[str] | None = None


def run_e2e_arms(
    case: BenchmarkCase,
    *,
    optimized_context: str,
    evaluator: LLMEvaluator | None,
    evaluator_id: str,
    profile: PipelineProfile,
    embedding_backend: EmbeddingBackend | None,
    judge_readability_enabled: bool,
) -> E2EScores:
    failures: list[str] = []

    if evaluator_id == "mock" or evaluator is None:
        mock = mock_responses(case)
        arm_a = mock.arm_a_response
        arm_b = mock.arm_b_response
    else:
        arm_a_context = render_arm_a_context(case)
        messages_a = build_answer_messages(case, arm_a_context)
        messages_b = build_answer_messages(case, optimized_context)
        arm_a = evaluator.complete(messages_a, temperature=0.0).text
        arm_b = evaluator.complete(messages_b, temperature=0.0).text

    recall = factual_recall(arm_b, case.expected_facts)
    f1 = factual_f1(arm_b, case.expected_facts)
    if profile.gate.factual_recall is not None and recall < profile.gate.factual_recall:
        failures.append(f"factual_recall {recall:.2f} < {profile.gate.factual_recall}")

    similarity = comprehension_similarity(arm_a, arm_b, backend=embedding_backend)
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
        failures.append(f"comprehension_delta {delta:.4f} < {delta_min}")

    response_artifact = detect_artifact_leak(arm_b)
    if response_artifact:
        failures.append("artifact_leak in response B")

    lang_ok = user_language_match(arm_b, case.response_lang)
    if profile.gate.user_language_match is not None and not lang_ok:
        failures.append(f"user_language_match failed for lang {case.response_lang!r}")

    readability_a: float | None = None
    readability_b: float | None = None
    if judge_readability_enabled and evaluator is not None:
        readability_b = judge_readability(evaluator, case, arm_b)
        readability_a = judge_readability(evaluator, case, arm_a)
        min_score = profile.gate.readability_score_min
        if min_score is not None:
            if readability_b is None:
                failures.append("readability_score B could not be parsed")
            elif readability_b < min_score:
                failures.append(
                    f"readability_score {readability_b:.2f} < {min_score}"
                )
        delta_max = profile.gate.readability_delta_max
        if (
            delta_max is not None
            and readability_a is not None
            and readability_b is not None
            and readability_b < readability_a - delta_max
        ):
            failures.append(
                f"readability delta {readability_b - readability_a:.2f} "
                f"< -{delta_max}"
            )

    return E2EScores(
        arm_a=arm_a,
        arm_b=arm_b,
        factual_recall=recall,
        factual_f1=f1,
        comprehension_similarity=similarity,
        comprehension_delta=delta,
        readability_score_a=readability_a,
        readability_score_b=readability_b,
        user_language_ok=lang_ok,
        response_artifact_leak=response_artifact,
        failures=failures,
    )
