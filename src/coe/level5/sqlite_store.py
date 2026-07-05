"""SQLite State Store N5 — persistencia embebida con API filesystem."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from .operations import ArchiveResult, StoreMetrics, build_archive_payload, session_is_expired, write_archive_file
from .serialize import semantic_state_from_dict, semantic_state_to_dict
from .state import SemanticState

DEFAULT_SQLITE_PATH = Path("data/sessions/coe_sessions.db")


def _archive_path(archive_root: Path, session_id: str, head_commit_id: str | None) -> Path:
    import hashlib
    import re

    safe_pattern = re.compile(r"^[\w.-]+$")
    safe_id = session_id if safe_pattern.fullmatch(session_id) else hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()[:16]
    return archive_root / safe_id / f"{head_commit_id or 'head'}.json"


class SQLiteStateStore:
    """
    Persistencia durable en SQLite (un registro JSON por sesión).

    v1: single-writer recomendado; WAL + ``timeout=30s`` toleran lectores concurrentes.
    Escritores simultáneos pueden bloquearse — ver ``docs/level5.md``.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        archive_root: str | Path | None = None,
        session_ttl_hours: float | None = None,
    ) -> None:
        self._db_path = Path(db_path or DEFAULT_SQLITE_PATH)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._archive_root = (
            Path(archive_root) if archive_root is not None else self._db_path.parent / "archives"
        )
        self._session_ttl_hours = session_ttl_hours
        self._init_schema()

    @property
    def db_path(self) -> Path:
        return self._db_path

    @property
    def archive_root(self) -> Path:
        return self._archive_root

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )

    def load(self, session_id: str) -> SemanticState | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload, updated_at FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        data = json.loads(row["payload"])
        updated_at = float(row["updated_at"])
        if session_is_expired(
            updated_at=updated_at,
            session_ttl_hours=self._session_ttl_hours,
        ):
            state = semantic_state_from_dict(data)
            if state.session_id != session_id:
                raise ValueError(
                    f"session_id mismatch in {self._db_path}: expected {session_id!r}, got {state.session_id!r}"
                )
            self.archive_session(session_id, remove_active=True, state=state)
            return None
        state = semantic_state_from_dict(data)
        if state.session_id != session_id:
            raise ValueError(
                f"session_id mismatch in {self._db_path}: expected {session_id!r}, got {state.session_id!r}"
            )
        state.updated_at = updated_at
        return state

    def save(self, state: SemanticState) -> None:
        state.updated_at = time.time()
        payload = json.dumps(
            semantic_state_to_dict(state),
            ensure_ascii=False,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (state.session_id, payload, state.updated_at),
            )
            conn.commit()

    def archive_session(
        self,
        session_id: str,
        *,
        remove_active: bool = True,
        state: SemanticState | None = None,
    ) -> ArchiveResult | None:
        if state is None:
            state = self.load(session_id)
            if state is None:
                with self._connect() as conn:
                    row = conn.execute(
                        "SELECT payload FROM sessions WHERE session_id = ?",
                        (session_id,),
                    ).fetchone()
                if row is None:
                    return None
                state = semantic_state_from_dict(json.loads(row["payload"]))
        payload = build_archive_payload(state)
        archive_path = _archive_path(self._archive_root, session_id, state.head_commit_id)
        write_archive_file(archive_path, payload)
        if remove_active:
            with self._connect() as conn:
                conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
        return ArchiveResult(
            session_id=session_id,
            head_commit_id=state.head_commit_id,
            archive_path=archive_path,
            cir_envelope=payload.get("cir"),
        )

    def sweep_expired_sessions(self, *, now: float | None = None) -> list[str]:
        expired: list[str] = []
        with self._connect() as conn:
            rows = conn.execute("SELECT session_id, payload, updated_at FROM sessions").fetchall()
        for row in rows:
            session_id = row["session_id"]
            updated_at = float(row["updated_at"])
            if session_is_expired(
                updated_at=updated_at,
                session_ttl_hours=self._session_ttl_hours,
                now=now,
            ):
                state = semantic_state_from_dict(json.loads(row["payload"]))
                self.archive_session(session_id, remove_active=True, state=state)
                expired.append(session_id)
        return expired

    def collect_metrics(self) -> StoreMetrics:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS active_sessions,
                    COALESCE(SUM(LENGTH(payload)), 0) AS total_bytes,
                    COALESCE(SUM(CAST(json_extract(payload, '$.history_pruned_total') AS INTEGER)), 0)
                        AS history_pruned_total
                FROM sessions
                """
            ).fetchone()
        archive_bytes = 0
        if self._archive_root.exists():
            archive_bytes = sum(
                path.stat().st_size for path in self._archive_root.rglob("*.json")
            )
        return StoreMetrics(
            active_sessions=int(row["active_sessions"]),
            total_bytes=int(row["total_bytes"]),
            archive_bytes=archive_bytes,
            history_pruned_total=int(row["history_pruned_total"] or 0),
        )
