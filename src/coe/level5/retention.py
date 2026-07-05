"""Política de retención del historial de commits N5."""

from __future__ import annotations

from .state import SemanticState

DEFAULT_MAX_COMMITS = 100


def prune_history(state: SemanticState) -> int:
    """
    Poda ``history`` conservando los commits más recientes.

    No modifica ``head``, ``graph`` ni ``commit_count``.
    """
    limit = state.max_commits
    if limit <= 0 or len(state.history) <= limit:
        return 0
    drop_count = len(state.history) - limit
    state.history = state.history[drop_count:]
    return drop_count
