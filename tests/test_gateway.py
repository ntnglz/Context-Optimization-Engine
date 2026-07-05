"""Tests del Gateway y render_prose N1."""

from coe import optimize_context
from coe.level1 import deduplicate_context
from coe.models import ContextBlock
from coe.renderer import render_raw_context


class TestRenderProse:
    def test_prose_avoids_compact_notation(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nCliente: Globex"),
            ContextBlock(id="B", content="Empresa: ACME\nPresupuesto: 50k"),
            ContextBlock(id="C", content="Empresa: ACME\nCliente: Globex"),
        ]
        result = deduplicate_context(blocks)
        prose = result.render_prose(locale="en")
        compact = result.render_compact()

        assert "Empresa=ACME" not in prose
        assert "Empresa=ACME" in compact
        assert "multiple sources" in prose
        assert "ACME" in prose
        assert "50k" in prose

    def test_render_compact_unchanged_for_tests(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nCliente: Globex"),
            ContextBlock(id="B", content="Empresa: ACME\nPresupuesto: 50k"),
            ContextBlock(id="C", content="Empresa: ACME\nCliente: Globex"),
        ]
        result = deduplicate_context(blocks)
        assert "Referencias:" in result.render()


class TestOptimizeContext:
    def test_n1_only(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME"),
            ContextBlock(id="B", content="Empresa: ACME"),
        ]
        out = optimize_context(blocks, levels=[1], locale="en")

        assert "multiple sources" in out.text
        assert out.metrics.original_tokens > 0
        assert out.metrics.latency_ms >= 0
        assert "n1" in out.metrics.latency_ms_by_level
        assert out.deduplication is not None

    def test_raw_when_no_shared_facts(self):
        blocks = [
            ContextBlock(id="A", content="Alpha"),
            ContextBlock(id="B", content="Beta"),
        ]
        out = optimize_context(blocks, levels=[1])
        assert "Alpha" in out.text
        assert out.metrics.compression_ratio == 0.0

    def test_arm_a_raw_context(self):
        blocks = [
            ContextBlock(id="A", content="Line one"),
            ContextBlock(id="B", content="Line two"),
        ]
        raw = render_raw_context(blocks)
        assert "[A]" in raw
        assert "[B]" in raw
