"""State Store N5 — persistencia de sesión (v1 in-memory)."""

from __future__ import annotations

from typing import Protocol

from .state import SemanticState


class StateStore(Protocol):
    def load(self, session_id: str) -> SemanticState | None: ...

    def save(self, state: SemanticState) -> None: ...


class InMemoryStateStore:
    """Store local en memoria para tests y sesiones efímeras."""

    def __init__(self) -> None:
        self._sessions: dict[str, SemanticState] = {}

    def load(self, session_id: str) -> SemanticState | None:
        return self._sessions.get(session_id)

    def save(self, state: SemanticState) -> None:
        self._sessions[state.session_id] = state
