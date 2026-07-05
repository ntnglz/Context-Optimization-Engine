"""F1 sobre hechos esperados (determinista, sin LLM)."""

from __future__ import annotations


def factual_recall(response: str, expected_facts: list[str]) -> float:
    if not expected_facts:
        return 1.0
    lower = response.casefold()
    hits = sum(1 for fact in expected_facts if fact.casefold() in lower)
    return hits / len(expected_facts)
