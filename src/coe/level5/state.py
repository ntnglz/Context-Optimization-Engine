"""Modelos de estado N5 — StateView, SemanticState y commits."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import ContextBlock, ContextGraph


@dataclass
class StateView:
    """Vista materializada hacia el LLM (única salida autorizada de N5)."""

    prose: str

    def render(self) -> str:
        return self.prose


@dataclass
class Commit:
    """Snapshot inmutable del grafo tras un turno."""

    commit_id: str
    graph: ContextGraph


@dataclass
class SemanticState:
    """Estado acumulado de sesión en el State Store."""

    session_id: str
    blocks: list[ContextBlock] = field(default_factory=list)
    graph: ContextGraph | None = None
    head_commit_id: str | None = None
    history: list[Commit] = field(default_factory=list)
    commit_count: int = 0


@dataclass
class UpdateResult:
    view: StateView
    state: SemanticState
    commit_id: str
