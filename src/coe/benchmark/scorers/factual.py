"""F1 sobre hechos esperados (determinista, sin LLM)."""

from __future__ import annotations


def factual_recall(response: str, expected_facts: list[str]) -> float:
    """Fracción de hechos esperados presentes en la respuesta."""
    _, _, recall = factual_scores(response, expected_facts)
    return recall


def factual_f1(response: str, expected_facts: list[str]) -> float:
    """F1 micro sobre presencia de hechos esperados (FP=0 en v1)."""
    f1, _, _ = factual_scores(response, expected_facts)
    return f1


def factual_scores(
    response: str,
    expected_facts: list[str],
) -> tuple[float, float, float]:
    """
    Devuelve (f1, precision, recall).

    v1: no hay lista de hechos prohibidos; FP=0 → precision=1 cuando hay TP.
    """
    if not expected_facts:
        return 1.0, 1.0, 1.0

    lower = response.casefold()
    tp = sum(1 for fact in expected_facts if fact.casefold() in lower)
    fn = len(expected_facts) - tp
    fp = 0

    recall = tp / len(expected_facts)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    if precision + recall == 0:
        return 0.0, precision, recall
    f1 = 2 * precision * recall / (precision + recall)
    return f1, precision, recall


def comprehension_delta(similarity: float) -> float:
    """Delta de comprensión: similitud(A,B) − 1.0 (umbral v1: ≥ −0.10)."""
    return similarity - 1.0
