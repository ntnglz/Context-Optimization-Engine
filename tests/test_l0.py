"""Tests L0 — normalización de idioma."""

from coe import optimize_context
from coe.ingest import normalize_language
from coe.models import ContextBlock


class TestL0Detect:
    def test_detects_spanish(self):
        from coe.ingest.detect import detect_language

        lang, confidence = detect_language("Juan trabaja en ACME y aprobó el presupuesto.")
        assert lang == "es"
        assert confidence > 0.5

    def test_detects_english(self):
        from coe.ingest.detect import detect_language

        lang, confidence = detect_language("Juan works at ACME and approved the budget.")
        assert lang == "en"
        assert confidence > 0.5


class TestL0Normalize:
    def test_translates_es_blocks_to_en(self):
        blocks = [
            ContextBlock(
                id="A",
                content="Empresa: ACME\nCliente: Globex\nJuan trabaja en ACME.",
            ),
            ContextBlock(
                id="B",
                content="Empresa: ACME\nPresupuesto: 50k\nJuan aprobó el presupuesto.",
            ),
        ]
        result = normalize_language(blocks, target_lang="en")

        assert result.ingest_trace.blocks_translated == 2
        assert "works at ACME" in result.blocks[0].content
        assert "approved the budget" in result.blocks[1].content
        assert "trabaja" not in result.blocks[0].content

    def test_skips_preserve_lang(self):
        blocks = [
            ContextBlock(
                id="A",
                content="Juan trabaja en ACME.",
                metadata={"preserve_lang": True},
            ),
        ]
        result = normalize_language(blocks, target_lang="en")

        assert result.blocks[0].content == "Juan trabaja en ACME."
        assert result.ingest_trace.blocks_skipped == 1

    def test_skips_already_english(self):
        blocks = [ContextBlock(id="A", content="Juan works at ACME.")]
        result = normalize_language(blocks, target_lang="en")

        assert result.ingest_trace.blocks_translated == 0
        assert result.blocks[0].content == "Juan works at ACME."


class TestL0Gateway:
    def test_l0_then_n1(self):
        blocks = [
            ContextBlock(
                id="A",
                content="Empresa: ACME\nJuan trabaja en ACME.",
            ),
            ContextBlock(
                id="B",
                content="Empresa: ACME\nJuan aprobó el presupuesto.",
            ),
        ]
        out = optimize_context(
            blocks,
            levels=[1],
            locale="en",
            target_lang="en",
            l0=True,
        )

        assert out.ingest_trace is not None
        assert out.ingest_trace.blocks_translated == 2
        assert "l0" in out.metrics.latency_ms_by_level
        assert "works at ACME" in out.text
        assert "approved the budget" in out.text

    def test_l0_requires_target_lang(self):
        blocks = [ContextBlock(id="A", content="Juan trabaja en ACME.")]

        try:
            optimize_context(blocks, levels=[1], l0=True)
            raised = False
        except ValueError:
            raised = True

        assert raised
