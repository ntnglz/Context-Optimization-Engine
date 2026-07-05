"""Tests N5 operaciones — TTL, archivado CIR y métricas store."""

from __future__ import annotations

import json

import pytest

from coe.cir import context_graph_from_envelope
from coe.level5 import (
    FilesystemStateStore,
    archive_session,
    collect_store_metrics,
    sweep_expired_sessions,
    update_semantic_state,
)
from coe.level5.operations import session_is_expired
from coe.models import ContextBlock


class TestSessionTtl:
    def test_session_is_expired_respects_hours(self):
        assert session_is_expired(updated_at=1000.0, session_ttl_hours=1.0, now=4600.0) is True
        assert session_is_expired(updated_at=1000.0, session_ttl_hours=1.0, now=2000.0) is False
        assert session_is_expired(updated_at=1000.0, session_ttl_hours=None, now=99999.0) is False

    def test_expired_session_archived_on_load(self, tmp_path, monkeypatch):
        session_id = "ttl-session"
        root = tmp_path / "sessions"
        store = FilesystemStateStore(root, session_ttl_hours=1.0)

        monkeypatch.setattr("coe.level5.store.time.time", lambda: 1_000.0)
        update_semantic_state(
            [ContextBlock(id="A", content="Juan works at ACME.")],
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1, 4],
        )

        monkeypatch.setattr("coe.level5.store.time.time", lambda: 1_000.0 + 7200.0)
        assert store.load(session_id) is None
        archive_files = list((root / "archives").rglob("*.json"))
        assert len(archive_files) == 1
        payload = json.loads(archive_files[0].read_text(encoding="utf-8"))
        assert payload["session_id"] == session_id
        assert payload["cir"] is not None
        assert not list(root.glob("*.json"))

    def test_sweep_expired_sessions(self, tmp_path, monkeypatch):
        root = tmp_path / "sessions"
        store = FilesystemStateStore(root, session_ttl_hours=2.0)

        monkeypatch.setattr("coe.level5.store.time.time", lambda: 500.0)
        update_semantic_state(
            [ContextBlock(id="A", content="hello")],
            session_id="sweep-me",
            store=store,
            locale="en",
            levels=[1],
        )

        swept = sweep_expired_sessions(store, now=500.0 + 10_000.0)
        assert swept == ["sweep-me"]
        assert store.load("sweep-me") is None


class TestArchiveSession:
    def test_archive_roundtrip_cir_envelope(self, tmp_path):
        session_id = "archive-session"
        root = tmp_path / "sessions"
        store = FilesystemStateStore(root)

        update_semantic_state(
            [ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME.")],
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1, 4],
        )
        result = update_semantic_state(
            [ContextBlock(id="B", content="Empresa: ACME\nBudget: 50k")],
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1, 4],
        )

        archived = archive_session(session_id, store, remove_active=True)
        assert archived is not None
        assert archived.head_commit_id == result.state.head_commit_id
        assert archived.archive_path.exists()
        assert store.load(session_id) is None

        payload = json.loads(archived.archive_path.read_text(encoding="utf-8"))
        assert payload["archive_version"] == "1.0"
        graph = context_graph_from_envelope(payload["cir"])
        assert graph is not None
        assert graph.render_prose(locale="en") == result.state.graph.render_prose(locale="en")


class TestStoreMetrics:
    def test_collect_metrics_reports_sessions_and_pruned(self, tmp_path):
        root = tmp_path / "sessions"
        store = FilesystemStateStore(root)
        session_id = "metrics-session"

        update_semantic_state(
            [ContextBlock(id="A", content="line one")],
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1],
            max_commits=1,
        )
        update_semantic_state(
            [ContextBlock(id="B", content="line two")],
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1],
            max_commits=1,
        )

        metrics = collect_store_metrics(store)
        assert metrics.active_sessions == 1
        assert metrics.total_bytes > 0
        assert metrics.history_pruned_total >= 1
