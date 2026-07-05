"""Tests del State Store N5 — serialización y persistencia en disco."""

from __future__ import annotations

import json

import pytest

from coe.level5 import FilesystemStateStore, InMemoryStateStore, update_semantic_state
from coe.level5.serialize import semantic_state_from_dict, semantic_state_to_dict
from coe.models import ContextBlock, ContextGraph, GraphEdge, GraphNode


class TestSemanticStateSerialization:
    def test_roundtrip_through_json(self):
        store = InMemoryStateStore()
        session_id = "serialize-session"

        turn1 = [ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME.")]
        turn2 = [ContextBlock(id="B", content="Empresa: ACME\nPresupuesto: 50k")]

        update_semantic_state(turn1, session_id=session_id, store=store, locale="en", levels=[1, 4])
        result = update_semantic_state(
            turn2,
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1, 4],
        )

        payload = semantic_state_to_dict(result.state)
        restored = semantic_state_from_dict(payload)

        assert restored.session_id == session_id
        assert restored.commit_count == 2
        assert restored.head_commit_id == result.state.head_commit_id
        assert len(restored.blocks) == 2
        assert restored.graph is not None
        assert len(restored.history) == 2
        assert restored.max_commits == 100
        assert len(restored.graph.nodes) == len(result.state.graph.nodes)
        assert restored.graph.render_prose(locale="en") == result.state.graph.render_prose(locale="en")

    def test_context_graph_from_dict_active_slice(self):
        graph = ContextGraph(
            nodes=[
                GraphNode(id="a", kind="entity", labels=["A"]),
                GraphNode(id="b", kind="entity", labels=["B"]),
            ],
            edges=[GraphEdge(from_id="a", to_id="b", type="knows")],
            orphans=[],
            schema_version="0.1",
            original_tokens=10,
            active_nodes=[GraphNode(id="a", kind="entity", labels=["A"])],
            active_edges=[],
        )
        restored = ContextGraph.from_dict(graph.to_dict())
        assert [node.id for node in restored.active_nodes or []] == ["a"]
        assert restored.active_edges == []


class TestFilesystemStateStore:
    def test_persists_multi_turn_across_instances(self, tmp_path):
        session_id = "disk-session-1"
        root = tmp_path / "sessions"

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

        store_a = FilesystemStateStore(root)
        update_semantic_state(turn1, session_id=session_id, store=store_a, locale="en", levels=[1])
        update_semantic_state(turn2, session_id=session_id, store=store_a, locale="en", levels=[1])

        store_b = FilesystemStateStore(root)
        restored = store_b.load(session_id)

        assert restored is not None
        assert restored.commit_count == 2
        assert len(restored.blocks) == 3
        assert restored.head_commit_id == f"{session_id}-c2"

        session_files = list(root.glob("*.json"))
        assert len(session_files) == 1
        on_disk = json.loads(session_files[0].read_text(encoding="utf-8"))
        assert on_disk["schema_version"] == "0.1"
        assert on_disk["session_id"] == session_id

    def test_load_missing_session_returns_none(self, tmp_path):
        store = FilesystemStateStore(tmp_path / "sessions")
        assert store.load("missing") is None

    def test_unsafe_session_id_uses_hashed_filename(self, tmp_path):
        session_id = "agent/session:42"
        store = FilesystemStateStore(tmp_path / "sessions")
        update_semantic_state(
            [ContextBlock(id="A", content="hello")],
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1],
        )

        assert store.load(session_id) is not None
        assert list(store.root.glob("session_*.json"))

    def test_session_id_mismatch_raises(self, tmp_path):
        path = tmp_path / "sessions" / "sess-x.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": "0.1",
                    "session_id": "other",
                    "blocks": [],
                    "graph": None,
                    "head_commit_id": None,
                    "history": [],
                    "commit_count": 0,
                }
            ),
            encoding="utf-8",
        )
        store = FilesystemStateStore(tmp_path / "sessions")
        with pytest.raises(ValueError, match="session_id mismatch"):
            store.load("sess-x")
