"""State Store N5 — persistencia de sesión."""

from __future__ import annotations

import json
import re
import hashlib
import time
from pathlib import Path
from typing import Protocol

from .operations import (
    ArchiveResult,
    StoreMetrics,
    build_archive_payload,
    session_is_expired,
    write_archive_file,
)
from .serialize import semantic_state_from_dict, semantic_state_to_dict
from .state import SemanticState

_SAFE_SESSION_ID = re.compile(r"^[\w.-]+$")
DEFAULT_SESSIONS_ROOT = Path("data/sessions")
_EPHEMERAL_SESSION = "_ephemeral"


def resolve_state_store(
    session_id: str | None,
    store: StateStore | None,
    *,
    root: str | Path | None = None,
    session_ttl_hours: float | None = None,
) -> StateStore:
    """Elige store durable si hay ``session_id`` real y no se pasó uno explícito."""
    if store is not None:
        return store
    if session_id and session_id != _EPHEMERAL_SESSION:
        return FilesystemStateStore(
            root or DEFAULT_SESSIONS_ROOT,
            session_ttl_hours=session_ttl_hours,
        )
    return InMemoryStateStore(session_ttl_hours=session_ttl_hours)


class StateStore(Protocol):
    def load(self, session_id: str) -> SemanticState | None: ...

    def save(self, state: SemanticState) -> None: ...


class InMemoryStateStore:
    """Store local en memoria para tests y sesiones efímeras."""

    def __init__(self, *, session_ttl_hours: float | None = None) -> None:
        self._sessions: dict[str, SemanticState] = {}
        self._archives: dict[str, dict] = {}
        self._session_ttl_hours = session_ttl_hours

    def load(self, session_id: str) -> SemanticState | None:
        state = self._sessions.get(session_id)
        if state is None:
            return None
        if session_is_expired(
            updated_at=state.updated_at,
            session_ttl_hours=self._session_ttl_hours,
        ):
            self.archive_session(session_id, remove_active=True)
            return None
        return state

    def save(self, state: SemanticState) -> None:
        state.updated_at = time.time()
        self._sessions[state.session_id] = state

    def archive_session(self, session_id: str, *, remove_active: bool = True) -> ArchiveResult | None:
        state = self._sessions.get(session_id)
        if state is None:
            return None
        payload = build_archive_payload(state)
        self._archives[session_id] = payload
        if remove_active:
            self._sessions.pop(session_id, None)
        return ArchiveResult(
            session_id=session_id,
            head_commit_id=state.head_commit_id,
            archive_path=Path("memory") / session_id / f"{state.head_commit_id or 'head'}.json",
            cir_envelope=payload.get("cir"),
        )

    def sweep_expired_sessions(self, *, now: float | None = None) -> list[str]:
        expired: list[str] = []
        for session_id, state in list(self._sessions.items()):
            if session_is_expired(
                updated_at=state.updated_at,
                session_ttl_hours=self._session_ttl_hours,
                now=now,
            ):
                self.archive_session(session_id, remove_active=True)
                expired.append(session_id)
        return expired

    def collect_metrics(self) -> StoreMetrics:
        pruned = sum(state.history_pruned_total for state in self._sessions.values())
        return StoreMetrics(
            active_sessions=len(self._sessions),
            total_bytes=0,
            archive_bytes=0,
            history_pruned_total=pruned,
        )

    def get_archive_payload(self, session_id: str) -> dict | None:
        return self._archives.get(session_id)


def _session_path(root: Path, session_id: str) -> Path:
    if _SAFE_SESSION_ID.fullmatch(session_id):
        filename = f"{session_id}.json"
    else:
        digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]
        filename = f"session_{digest}.json"
    return root / filename


def _archive_path(archive_root: Path, session_id: str, head_commit_id: str | None) -> Path:
    safe_id = session_id if _SAFE_SESSION_ID.fullmatch(session_id) else hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()[:16]
    return archive_root / safe_id / f"{head_commit_id or 'head'}.json"


class FilesystemStateStore:
    """Persistencia durable en JSON — un archivo por sesión."""

    def __init__(
        self,
        root: str | Path,
        *,
        archive_root: str | Path | None = None,
        session_ttl_hours: float | None = None,
    ) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._archive_root = Path(archive_root) if archive_root is not None else self._root / "archives"
        self._session_ttl_hours = session_ttl_hours

    @property
    def root(self) -> Path:
        return self._root

    @property
    def archive_root(self) -> Path:
        return self._archive_root

    def _read_updated_at(self, path: Path, data: dict) -> float | None:
        raw = data.get("updated_at")
        if raw is not None:
            return float(raw)
        try:
            return path.stat().st_mtime
        except OSError:
            return None

    def load(self, session_id: str) -> SemanticState | None:
        path = _session_path(self._root, session_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        updated_at = self._read_updated_at(path, data)
        if session_is_expired(
            updated_at=updated_at,
            session_ttl_hours=self._session_ttl_hours,
        ):
            state = semantic_state_from_dict(data)
            if state.session_id != session_id:
                raise ValueError(
                    f"session_id mismatch in {path}: expected {session_id!r}, got {state.session_id!r}"
                )
            self.archive_session(session_id, remove_active=True, state=state)
            return None
        state = semantic_state_from_dict(data)
        if state.session_id != session_id:
            raise ValueError(
                f"session_id mismatch in {path}: expected {session_id!r}, got {state.session_id!r}"
            )
        if state.updated_at is None:
            state.updated_at = updated_at
        return state

    def save(self, state: SemanticState) -> None:
        state.updated_at = time.time()
        path = _session_path(self._root, state.session_id)
        payload = json.dumps(
            semantic_state_to_dict(state),
            indent=2,
            ensure_ascii=False,
        )
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(f"{payload}\n", encoding="utf-8")
        tmp.replace(path)

    def archive_session(
        self,
        session_id: str,
        *,
        remove_active: bool = True,
        state: SemanticState | None = None,
    ) -> ArchiveResult | None:
        if state is None:
            path = _session_path(self._root, session_id)
            if not path.exists():
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
            state = semantic_state_from_dict(data)
        payload = build_archive_payload(state)
        archive_path = _archive_path(self._archive_root, session_id, state.head_commit_id)
        write_archive_file(archive_path, payload)
        if remove_active:
            active_path = _session_path(self._root, session_id)
            if active_path.exists():
                active_path.unlink()
        return ArchiveResult(
            session_id=session_id,
            head_commit_id=state.head_commit_id,
            archive_path=archive_path,
            cir_envelope=payload.get("cir"),
        )

    def sweep_expired_sessions(self, *, now: float | None = None) -> list[str]:
        expired: list[str] = []
        for path in sorted(self._root.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            session_id = data.get("session_id")
            if not session_id:
                continue
            updated_at = self._read_updated_at(path, data)
            if session_is_expired(
                updated_at=updated_at,
                session_ttl_hours=self._session_ttl_hours,
                now=now,
            ):
                state = semantic_state_from_dict(data)
                self.archive_session(session_id, remove_active=True, state=state)
                expired.append(session_id)
        return expired

    def collect_metrics(self) -> StoreMetrics:
        session_files = list(self._root.glob("*.json"))
        total_bytes = sum(path.stat().st_size for path in session_files)
        archive_bytes = 0
        if self._archive_root.exists():
            archive_bytes = sum(
                path.stat().st_size for path in self._archive_root.rglob("*.json")
            )
        pruned = 0
        for path in session_files:
            data = json.loads(path.read_text(encoding="utf-8"))
            pruned += int(data.get("history_pruned_total") or 0)
        return StoreMetrics(
            active_sessions=len(session_files),
            total_bytes=total_bytes,
            archive_bytes=archive_bytes,
            history_pruned_total=pruned,
        )
