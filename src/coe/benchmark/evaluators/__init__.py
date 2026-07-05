"""Evaluadores LLM (mock + Ollama)."""

from .base import LLMEvaluator, LLMResult, Message, default_evaluator_for_tier, parse_evaluator_spec
from .factory import create_evaluator
from .mock import mock_responses
from .ollama import OllamaEvaluator

__all__ = [
    "LLMEvaluator",
    "LLMResult",
    "Message",
    "OllamaEvaluator",
    "create_evaluator",
    "default_evaluator_for_tier",
    "mock_responses",
    "parse_evaluator_spec",
]
