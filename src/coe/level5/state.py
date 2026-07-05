"""Modelos de estado N5 — StateView y SemanticState."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import ContextBlock


@dataclass
class StateView:
    """Vista materializada hacia el LLM (única salida autorizada de N5)."""

    prose: str

    def render(self) -> str:
        return self.prose


@dataclass
class SemanticState:
    """Estado acumulado de sesión en el State Store."""

    session_id: str
    blocks: list[ContextBlock] = field(default_factory=list)
    commit_count: int = 0


@dataclass
class UpdateResult:
    view: StateView
    state: SemanticState
    commit_id: str
