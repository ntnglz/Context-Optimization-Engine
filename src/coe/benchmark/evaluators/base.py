"""Protocolo y tipos para evaluadores LLM."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass
class LLMResult:
    text: str
    model: str = ""
    latency_ms: float = 0.0


class LLMEvaluator(Protocol):
    """Backend que completa un turno de chat."""

    def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
    ) -> LLMResult: ...


def parse_evaluator_spec(spec: str) -> tuple[str, str | None]:
    """Parsea ``mock``, ``ollama`` o ``ollama:model``."""
    if spec == "mock":
        return "mock", None
    if spec == "ollama":
        return "ollama", os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    if spec.startswith("ollama:"):
        model = spec.split(":", 1)[1].strip()
        if not model:
            raise ValueError(f"Invalid evaluator spec: {spec!r}")
        return "ollama", model
    raise ValueError(f"Unknown evaluator: {spec!r}")


def default_evaluator_for_tier(tier: str) -> str:
    if tier in ("nightly", "release"):
        return "ollama"
    return "mock"
