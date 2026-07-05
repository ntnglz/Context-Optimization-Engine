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
class RetractRecord:
    """Corrección explícita referenciando un commit previo."""

    commit_id: str
    previous: str
    corrects: str
    source_id: str


@dataclass
class SemanticState:
    """Estado acumulado de sesión en el State Store."""

    session_id: str
    blocks: list[ContextBlock] = field(default_factory=list)
    graph: ContextGraph | None = None
    head_commit_id: str | None = None
    history: list[Commit] = field(default_factory=list)
    commit_count: int = 0
    max_commits: int = 100
    retract_log: list[RetractRecord] = field(default_factory=list)
    updated_at: float | None = None
    history_pruned_total: int = 0


@dataclass
class UpdateResult:
    view: StateView
    state: SemanticState
    commit_id: str
