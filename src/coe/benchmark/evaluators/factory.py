"""Factory de evaluadores LLM."""

from __future__ import annotations

from .base import LLMEvaluator, parse_evaluator_spec
from .ollama import OllamaEvaluator


def create_evaluator(spec: str) -> tuple[LLMEvaluator | None, str]:
    """
    Devuelve (evaluator, evaluator_id).

    ``mock`` devuelve evaluator=None — el runner usa fixtures del caso.
    """
    kind, model = parse_evaluator_spec(spec)
    if kind == "mock":
        return None, "mock"
    if kind == "ollama":
        return OllamaEvaluator(model=model), f"ollama:{model}"
    raise ValueError(f"Unsupported evaluator kind: {kind}")
