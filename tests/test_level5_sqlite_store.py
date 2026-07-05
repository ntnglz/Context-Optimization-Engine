"""Tests SQLiteStateStore N5 — persistencia y CIR envelope."""

from __future__ import annotations

from coe.cir import CIR_VERSION
from coe.level5 import SQLiteStateStore, update_semantic_state
from coe.level5.serialize import semantic_state_to_dict
from coe.models import ContextBlock


class TestSQLiteStateStore:
    def test_persists_multi_turn_across_instances(self, tmp_path):
        db_path = tmp_path / "sessions.db"
        session_id = "sqlite-session-1"

        turn1 = [
            ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME."),
            ContextBlock(id="B", content="Empresa: ACME\nPedro works at ACME."),
        ]
        turn2 = [
            ContextBlock(
                id="C",
                content="Empresa: ACME\nPresupuesto: 50k\nJuan approved the budget.",
            ),
        ]

        store_a = SQLiteStateStore(db_path)
        update_semantic_state(turn1, session_id=session_id, store=store_a, locale="en", levels=[1])
        update_semantic_state(turn2, session_id=session_id, store=store_a, locale="en", levels=[1])

        store_b = SQLiteStateStore(db_path)
        restored = store_b.load(session_id)

        assert restored is not None
        assert restored.commit_count == 2
        assert len(restored.blocks) == 3
        assert restored.head_commit_id == f"{session_id}-c2"

    def test_cir_envelope_roundtrip_in_payload(self, tmp_path):
        db_path = tmp_path / "cir.db"
        session_id = "sqlite-cir"

        update_semantic_state(
            [ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME.")],
            session_id=session_id,
            store=SQLiteStateStore(db_path),
            locale="en",
            levels=[1, 4],
        )
        state = SQLiteStateStore(db_path).load(session_id)
        assert state is not None
        payload = semantic_state_to_dict(state)
        assert payload.get("graph") is not None
        assert payload["graph"]["cir_version"] == CIR_VERSION

    def test_new_connection_sees_committed_state(self, tmp_path):
        """Simula otro proceso reabriendo la misma base SQLite."""
        db_path = tmp_path / "proc.db"
        session_id = "sqlite-proc"
        writer = SQLiteStateStore(db_path)
        update_semantic_state(
            [ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME.")],
            session_id=session_id,
            store=writer,
            locale="en",
            levels=[1],
        )
        reader = SQLiteStateStore(db_path)
        restored = reader.load(session_id)
        assert restored is not None
        assert restored.commit_count == 1

    def test_collect_metrics(self, tmp_path):
        db_path = tmp_path / "metrics.db"
        store = SQLiteStateStore(db_path)
        update_semantic_state(
            [ContextBlock(id="A", content="hello")],
            session_id="m1",
            store=store,
            locale="en",
            levels=[1],
        )
        metrics = store.collect_metrics()
        assert metrics.active_sessions == 1
        assert metrics.total_bytes > 0

    def test_resolve_sqlite_backend(self, tmp_path):
        from coe.level5.store import resolve_state_store

        db_path = tmp_path / "resolved.db"
        store = resolve_state_store(
            "sess-1",
            None,
            backend="sqlite",
            store_path=db_path,
        )
        assert isinstance(store, SQLiteStateStore)
        assert store.db_path == db_path
