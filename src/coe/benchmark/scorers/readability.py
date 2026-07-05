"""Juez LLM de legibilidad (capa 2)."""

from __future__ import annotations

import re

from ..evaluators.base import LLMEvaluator, Message
from ..evaluators.prompts import load_prompt
from ..schema import BenchmarkCase

_SCORE_RE = re.compile(
    r"(?:score|rating|puntuaci[oó]n)\s*[:\s]*([1-5](?:\.\d+)?)",
    re.I,
)
_LONE_SCORE_RE = re.compile(r"\b([1-5](?:\.\d+)?)\b")


def parse_readability_score(text: str) -> float | None:
    """Extrae puntuación 1–5 del output del juez."""
    match = _SCORE_RE.search(text)
    if match:
        return _clamp_score(float(match.group(1)))
    for match in _LONE_SCORE_RE.finditer(text):
        value = float(match.group(1))
        if 1.0 <= value <= 5.0:
            return _clamp_score(value)
    return None


def _clamp_score(value: float) -> float:
    return max(1.0, min(5.0, round(value, 2)))


def judge_readability(
    evaluator: LLMEvaluator,
    case: BenchmarkCase,
    response: str,
) -> float | None:
    """Pide al evaluador una puntuación de legibilidad para ``response``."""
    system = load_prompt("readability_judge.txt")
    user = (
        f"Question: {case.question}\n"
        f"Response language: {case.response_lang}\n\n"
        f"Response:\n{response.strip()}"
    )
    result = evaluator.complete(
        [Message(role="system", content=system), Message(role="user", content=user)],
        temperature=0.0,
    )
    return parse_readability_score(result.text)
