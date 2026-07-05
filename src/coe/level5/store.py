"""State Store N5 — persistencia de sesión."""

from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path
from typing import Protocol

from .serialize import semantic_state_from_dict, semantic_state_to_dict
from .state import SemanticState

_SAFE_SESSION_ID = re.compile(r"^[\w.-]+$")


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


def _session_path(root: Path, session_id: str) -> Path:
    if _SAFE_SESSION_ID.fullmatch(session_id):
        filename = f"{session_id}.json"
    else:
        digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]
        filename = f"session_{digest}.json"
    return root / filename


class FilesystemStateStore:
    """Persistencia durable en JSON — un archivo por sesión."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def load(self, session_id: str) -> SemanticState | None:
        path = _session_path(self._root, session_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        state = semantic_state_from_dict(data)
        if state.session_id != session_id:
            raise ValueError(
                f"session_id mismatch in {path}: expected {session_id!r}, got {state.session_id!r}"
            )
        return state

    def save(self, state: SemanticState) -> None:
        path = _session_path(self._root, state.session_id)
        payload = json.dumps(
            semantic_state_to_dict(state),
            indent=2,
            ensure_ascii=False,
        )
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(f"{payload}\n", encoding="utf-8")
        tmp.replace(path)
