"""Tests presupuesto de tokens COE (Fase 10)."""

from coe import optimize_context
from coe.budget import apply_assembled_budget, truncate_text_to_tokens
from coe.models import ContextBlock, estimate_tokens


class TestTruncateHelpers:
    def test_truncate_keeps_tail(self):
        text = "alpha " * 200 + "KEEP-TAIL-MARKER"
        out = truncate_text_to_tokens(text, max_tokens=20, keep_end=True)
        assert "KEEP-TAIL-MARKER" in out
        assert "[truncated]" in out
        assert estimate_tokens(out) <= 20

    def test_apply_assembled_budget_drops_state_first(self):
        state = "Estado acumulado " * 80
        turn = "Turno reciente con detalle " * 10
        out, truncated = apply_assembled_budget(
            state_prose=state,
            turn_prose=turn,
            max_tokens=40,
            locale="es",
        )
        assert truncated
        assert "Turno reciente" in out
        assert estimate_tokens(out) <= 40


class TestGatewayTokenBudget:
    def test_truncates_when_over_max_context_tokens(self):
        blocks = [
            ContextBlock(
                id=f"b{i}",
                content=f"Empresa: ACME — bloque {i} con texto de relleno adicional.",
            )
            for i in range(30)
        ]
        out = optimize_context(blocks, levels=[1], locale="es", max_context_tokens=40)

        assert out.metrics.truncated is True
        assert out.metrics.pre_truncation_tokens is not None
        assert out.metrics.pre_truncation_tokens > 40
        assert out.metrics.optimized_tokens <= 40
        assert "[truncated]" in out.text

    def test_no_truncation_when_under_budget(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME"),
            ContextBlock(id="B", content="Empresa: ACME"),
        ]
        out = optimize_context(blocks, levels=[1], locale="en", max_context_tokens=500)

        assert out.metrics.truncated is False
        assert out.metrics.pre_truncation_tokens is None
        assert "multiple sources" in out.text

    def test_n5_truncates_expanded_state(self):
        blocks = [
            ContextBlock(
                id="A",
                content="Juan works at ACME and leads the platform team for infrastructure.",
            ),
            ContextBlock(
                id="B",
                content="Juan approved the budget and scheduled the quarterly review meeting.",
            ),
        ]
        out = optimize_context(
            blocks,
            levels=[1, 5],
            locale="en",
            session_id="budget-test-session-trunc",
            max_context_tokens=15,
        )

        assert out.metrics.truncated is True
        assert out.metrics.optimized_tokens <= out.metrics.pre_truncation_tokens
        assert out.metrics.optimized_tokens <= 17  # ~1 token slack vs estimate_tokens heurística
