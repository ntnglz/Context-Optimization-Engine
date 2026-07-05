"""Nivel 5 — estado semántico multi-turno."""

from .entity_linking import DEFAULT_FUZZY_THRESHOLD, build_alias_map
from .operations import (
    ArchiveResult,
    StoreMetrics,
    archive_session,
    collect_store_metrics,
    session_is_expired,
    sweep_expired_sessions,
)
from .state import Commit, RetractRecord, SemanticState, StateView, UpdateResult
from .store import (
    FilesystemStateStore,
    InMemoryStateStore,
    StateStore,
    resolve_state_store,
)
from .updater import update_semantic_state

__all__ = [
    "ArchiveResult",
    "Commit",
    "DEFAULT_FUZZY_THRESHOLD",
    "FilesystemStateStore",
    "InMemoryStateStore",
    "RetractRecord",
    "SemanticState",
    "StateStore",
    "StateView",
    "StoreMetrics",
    "UpdateResult",
    "archive_session",
    "build_alias_map",
    "collect_store_metrics",
    "resolve_state_store",
    "session_is_expired",
    "sweep_expired_sessions",
    "update_semantic_state",
]
