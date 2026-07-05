"""Operaciones N5 — TTL, archivado CIR y métricas del store."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..cir import envelope_from_context_graph
from .serialize import semantic_state_to_dict

if TYPE_CHECKING:
    from .state import SemanticState
    from .store import FilesystemStateStore, InMemoryStateStore, StateStore

ARCHIVE_SCHEMA_VERSION = "1.0"


@dataclass
class ArchiveResult:
    session_id: str
    head_commit_id: str | None
    archive_path: Path
    cir_envelope: dict[str, Any] | None


@dataclass
class StoreMetrics:
    active_sessions: int
    total_bytes: int
    archive_bytes: int
    history_pruned_total: int


def session_is_expired(
    *,
    updated_at: float | None,
    session_ttl_hours: float | None,
    now: float | None = None,
) -> bool:
    if session_ttl_hours is None or session_ttl_hours <= 0:
        return False
    if updated_at is None:
        return False
    clock = now if now is not None else time.time()
    return (clock - updated_at) >= session_ttl_hours * 3600.0


def build_archive_payload(state: SemanticState) -> dict[str, Any]:
    """Exporta el commit head como envelope CIR v1.0."""
    cir = envelope_from_context_graph(state.graph) if state.graph is not None else None
    return {
        "archive_version": ARCHIVE_SCHEMA_VERSION,
        "session_id": state.session_id,
        "archived_at": datetime.now(UTC).isoformat(),
        "head_commit_id": state.head_commit_id,
        "commit_count": state.commit_count,
        "history_pruned_total": state.history_pruned_total,
        "cir": cir,
        "state_snapshot": semantic_state_to_dict(state),
    }


def write_archive_file(archive_path: Path, payload: dict[str, Any]) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    tmp = archive_path.with_suffix(".json.tmp")
    tmp.write_text(f"{body}\n", encoding="utf-8")
    tmp.replace(archive_path)


def archive_session(
    session_id: str,
    store: StateStore,
    *,
    remove_active: bool = True,
) -> ArchiveResult | None:
    """
    Exporta la sesión activa a JSON CIR bajo ``archives/`` del store.

    Si ``remove_active`` es True, elimina la sesión del store activo tras archivar.
    """
    from .store import FilesystemStateStore, InMemoryStateStore

    from .store import FilesystemStateStore, InMemoryStateStore
    from .sqlite_store import SQLiteStateStore

    if isinstance(store, FilesystemStateStore):
        return store.archive_session(session_id, remove_active=remove_active)
    if isinstance(store, SQLiteStateStore):
        return store.archive_session(session_id, remove_active=remove_active)
    if isinstance(store, InMemoryStateStore):
        return store.archive_session(session_id, remove_active=remove_active)
    state = store.load(session_id)
    if state is None:
        return None
    payload = build_archive_payload(state)
    archive_path = Path("archives") / session_id / f"{state.head_commit_id or 'head'}.json"
    write_archive_file(archive_path, payload)
    return ArchiveResult(
        session_id=session_id,
        head_commit_id=state.head_commit_id,
        archive_path=archive_path,
        cir_envelope=payload.get("cir"),
    )


def collect_store_metrics(store: StateStore) -> StoreMetrics:
    from .store import FilesystemStateStore, InMemoryStateStore
    from .sqlite_store import SQLiteStateStore

    if isinstance(store, FilesystemStateStore):
        return store.collect_metrics()
    if isinstance(store, SQLiteStateStore):
        return store.collect_metrics()
    if isinstance(store, InMemoryStateStore):
        return store.collect_metrics()
    return StoreMetrics(
        active_sessions=0,
        total_bytes=0,
        archive_bytes=0,
        history_pruned_total=0,
    )


def sweep_expired_sessions(store: StateStore, *, now: float | None = None) -> list[str]:
    """Elimina (tras archivar) sesiones cuyo TTL expiró. Devuelve ids barridos."""
    from .store import FilesystemStateStore, InMemoryStateStore
    from .sqlite_store import SQLiteStateStore

    if isinstance(store, FilesystemStateStore):
        return store.sweep_expired_sessions(now=now)
    if isinstance(store, SQLiteStateStore):
        return store.sweep_expired_sessions(now=now)
    if isinstance(store, InMemoryStateStore):
        return store.sweep_expired_sessions(now=now)
    return []
