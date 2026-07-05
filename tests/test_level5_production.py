"""Tests de N5 producción — auto-store, retención, conflictos y retracts."""

from __future__ import annotations

from coe.gateway import optimize_context
from coe.level5 import FilesystemStateStore, InMemoryStateStore, update_semantic_state
from coe.level5.materialize import render_state_view
from coe.level5.merge import merge_context_graphs
from coe.level5.retention import prune_history
from coe.level5.state import RetractRecord, SemanticState
from coe.models import ContextBlock, ContextGraph, GraphNode


class TestGatewayAutoStore:
    def test_session_id_without_store_uses_filesystem(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        session_id = "auto-store-session"
        blocks = [ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME.")]

        optimize_context(blocks, levels=[1, 5], locale="en", session_id=session_id)

        root = tmp_path / "data" / "sessions"
        assert list(root.glob("*.json"))
        store = FilesystemStateStore(root)
        restored = store.load(session_id)
        assert restored is not None
        assert restored.commit_count == 1


class TestRetention:
    def test_max_commits_prunes_history_keeps_head(self):
        store = InMemoryStateStore()
        session_id = "retention-session"

        for turn in range(5):
            update_semantic_state(
                [ContextBlock(id=f"T{turn}", content=f"Fact {turn}.")],
                session_id=session_id,
                store=store,
                locale="en",
                levels=[1],
                max_commits=3,
            )

        state = store.load(session_id)
        assert state is not None
        assert state.commit_count == 5
        assert len(state.history) == 3
        assert state.head_commit_id == f"{session_id}-c5"
        assert state.graph is not None

    def test_prune_history_standalone(self):
        from coe.level5.state import Commit

        state = SemanticState(session_id="x", max_commits=2)
        state.history = [Commit(commit_id=f"c{i}", graph=None) for i in range(1, 5)]
        dropped = prune_history(state)
        assert dropped == 2
        assert len(state.history) == 2
        assert state.history[0].commit_id == "c3"
        assert state.history[1].commit_id == "c4"


class TestConflictsAndRetracts:
    def test_conflict_prose_in_state_view(self):
        base = ContextGraph(
            nodes=[
                GraphNode(
                    id="budget",
                    kind="concept",
                    labels=["Budget"],
                    properties={"amount": "50k"},
                    source_refs=["A"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version="0.1",
            original_tokens=10,
        )
        incoming = ContextGraph(
            nodes=[
                GraphNode(
                    id="budget",
                    kind="concept",
                    labels=["Budget"],
                    properties={"amount": "80k"},
                    source_refs=["B"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version="0.1",
            original_tokens=10,
        )
        merged = merge_context_graphs(base, incoming)
        view = render_state_view(merged, previous=None, locale="en")
        prose = view.render()

        assert "Conflicting information in session state:" in prose
        assert "50k" in prose
        assert "80k" in prose

    def test_retract_prose_in_state_view(self):
        graph = ContextGraph(
            nodes=[],
            edges=[],
            orphans=[],
            schema_version="0.1",
            original_tokens=0,
        )
        retract_log = [
            RetractRecord(
                commit_id="sess-c1",
                previous="Budget is 50k",
                corrects="Budget is 80k",
                source_id="C",
            )
        ]
        view = render_state_view(graph, previous=None, locale="en", retract_log=retract_log)
        prose = view.render()

        assert "Corrections since earlier turns:" in prose
        assert "sess-c1" in prose
        assert "Budget is 50k" in prose
        assert "Budget is 80k" in prose

    def test_retract_metadata_collected_on_update(self):
        store = InMemoryStateStore()
        session_id = "retract-session"

        turn1 = [ContextBlock(id="A", content="Budget is 50k.")]
        update_semantic_state(turn1, session_id=session_id, store=store, locale="en", levels=[1])

        turn2 = [
            ContextBlock(
                id="B",
                content="Budget is 80k.",
                metadata={
                    "retracts": "retract-session-c1",
                    "previous": "Budget is 50k",
                    "corrects": "Budget is 80k",
                },
            )
        ]
        result = update_semantic_state(
            turn2,
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1],
        )

        prose = result.view.render()
        assert len(result.state.retract_log) == 1
        assert result.state.retract_log[0].commit_id == "retract-session-c1"
        assert "Corrections since earlier turns:" in prose
