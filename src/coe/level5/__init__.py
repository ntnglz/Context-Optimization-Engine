"""Nivel 5 — estado semántico multi-turno."""

from .state import SemanticState, StateView, UpdateResult
from .store import InMemoryStateStore, StateStore
from .updater import update_semantic_state

__all__ = [
    "InMemoryStateStore",
    "SemanticState",
    "StateStore",
    "StateView",
    "UpdateResult",
    "update_semantic_state",
]
