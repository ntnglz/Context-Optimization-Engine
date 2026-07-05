"""Tests L0 — normalización de idioma (v2)."""

from coe import optimize_context
from coe.ingest import (
    BenchmarkStubBackend,
    compute_dominant_language,
    normalize_language,
)
from coe.ingest.translate import translate_block_content
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

    def test_short_text_uses_heuristic(self):
        from coe.ingest.detect import detect_language

        lang, confidence = detect_language("Juan trabaja en ACME.")
        assert lang == "es"
        assert confidence > 0.0


class TestL0DominantLanguage:
    def test_mixed_bundle_sets_dominant_lang(self):
        blocks = [
            ContextBlock(
                id="A",
                content="Juan trabaja en ACME y aprobó el presupuesto en la reunión.",
            ),
            ContextBlock(
                id="B",
                content="Pedro works at ACME and approved the budget for the project.",
            ),
        ]
        dominant, _ = compute_dominant_language(blocks)
        assert dominant in {"es", "en"}

    def test_mixed_bundle_trace(self):
        blocks = [
            ContextBlock(
                id="A",
                content="Juan trabaja en ACME y aprobó el presupuesto en la reunión.",
            ),
            ContextBlock(
                id="B",
                content="Pedro works at ACME and approved the budget for the project.",
            ),
        ]
        result = normalize_language(blocks, target_lang="en")
        assert result.ingest_trace.mixed_bundle is True
        assert result.ingest_trace.dominant_lang in {"es", "en"}
        assert result.ingest_trace.detect_confidence["A"] > 0.0


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
        assert result.ingest_trace.translation_backend == "benchmark_stub"
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
        assert result.ingest_trace.detected_langs["A"] == "preserved"

    def test_skips_already_english(self):
        blocks = [ContextBlock(id="A", content="Juan works at ACME.")]
        result = normalize_language(blocks, target_lang="en")

        assert result.ingest_trace.blocks_translated == 0
        assert result.blocks[0].content == "Juan works at ACME."

    def test_target_lang_auto_uses_dominant(self):
        blocks = [
            ContextBlock(
                id="A",
                content="Juan trabaja en ACME y aprobó el presupuesto en la reunión larga.",
            ),
            ContextBlock(
                id="B",
                content="Pedro también trabaja en ACME y aprobó el presupuesto del cliente.",
            ),
        ]
        result = normalize_language(blocks, target_lang="auto")
        assert result.ingest_trace.target_lang == "es"
        assert result.ingest_trace.blocks_translated == 0

    def test_preserves_urls_and_uuids(self):
        backend = BenchmarkStubBackend()
        text = (
            "Visita https://acme.example/docs y el id "
            "550e8400-e29b-41d4-a716-446655440000. Juan trabaja en ACME."
        )
        translated = translate_block_content(
            text,
            source_lang="es",
            target_lang="en",
            backend=backend,
        )
        assert "https://acme.example/docs" in translated
        assert "550e8400-e29b-41d4-a716-446655440000" in translated
        assert "works at ACME" in translated

    def test_skips_code_fence_by_default(self):
        blocks = [
            ContextBlock(
                id="A",
                content="```python\nJuan trabaja en ACME.\n```",
            ),
        ]
        result = normalize_language(blocks, target_lang="en")
        assert result.ingest_trace.blocks_skipped == 1
        assert "trabaja" in result.blocks[0].content

    def test_translate_code_blocks_opt_in(self):
        blocks = [
            ContextBlock(
                id="A",
                content="```\nJuan trabaja en ACME.\n```",
            ),
        ]
        result = normalize_language(
            blocks,
            target_lang="en",
            translate_code_blocks=True,
        )
        assert result.ingest_trace.blocks_translated == 1
        assert "works at ACME" in result.blocks[0].content


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
