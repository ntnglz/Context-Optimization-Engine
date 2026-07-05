"""Tests del optimizador Nivel 5 — StateView y sesión multi-turno."""

from coe.gateway import optimize_context
from coe.level5 import InMemoryStateStore, update_semantic_state
from coe.models import ContextBlock


class TestN5StateView:
    def test_single_turn_update(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME."),
            ContextBlock(id="B", content="Empresa: ACME\nPedro works at ACME."),
        ]
        result = update_semantic_state(
            blocks,
            session_id="sess-1",
            locale="en",
            levels=[1],
        )

        prose = result.view.render()
        assert prose.startswith("Accumulated session state:")
        assert "Juan works at ACME" in prose
        assert "Pedro works at ACME" in prose
        assert "entity:" not in prose
        assert result.commit_id == "sess-1-c1"

    def test_multi_turn_accumulation(self):
        store = InMemoryStateStore()
        session_id = "bench-acme-session-1"

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

        update_semantic_state(
            turn1,
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1],
        )
        result = update_semantic_state(
            turn2,
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1],
        )

        prose = result.view.render()
        assert "Juan works at ACME" in prose
        assert "Pedro works at ACME" in prose
        assert "Presupuesto: 50k" in prose
        assert "approved the budget" in prose
        assert result.commit_id == "bench-acme-session-1-c2"
        assert len(result.state.blocks) == 3
        assert result.state.graph is not None
        assert result.state.head_commit_id == "bench-acme-session-1-c2"
        assert len(result.state.history) == 2

    def test_graph_merge_across_turns(self):
        store = InMemoryStateStore()
        session_id = "graph-session-1"

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

        update_semantic_state(
            turn1,
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1, 2, 3, 4],
        )
        result = update_semantic_state(
            turn2,
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1, 2, 3, 4],
        )

        prose = result.view.render()
        assert result.state.graph is not None
        assert len(result.state.history) == 2
        assert "Juan works at ACME" in prose
        assert "Pedro works at ACME" in prose
        assert "approved the budget" in prose
        assert "node:" not in prose

    def test_gateway_n5_single_shot(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME."),
            ContextBlock(id="B", content="Empresa: ACME\nPedro works at ACME."),
        ]
        out = optimize_context(blocks, levels=[1, 5], locale="en", session_id="sess-x")

        assert out.state_view is not None
        assert out.commit_id == "sess-x-c1"
        assert "n5" in out.metrics.latency_ms_by_level
        assert "Accumulated session state:" in out.text
        assert "entity:" not in out.text
