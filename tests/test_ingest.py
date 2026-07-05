"""Tests de Context Ingest — bundle, normalizer y matriz de niveles."""

from __future__ import annotations

import pytest

from coe.gateway import optimize_context
from coe.ingest import (
    ContextBundle,
    ingest_context,
    resolve_effective_levels,
)
from coe.models import ContextBlock


class TestIngestContext:
    def test_builds_bundle_from_raw_blocks(self):
        result = ingest_context(
            [
                {
                    "id": "doc-a",
                    "text": "Empresa: ACME\r\nJuan works at ACME.",
                    "source_type": "rag",
                    "uri": "https://example.com/a",
                    "source_label": "Document A",
                }
            ],
            target_lang="en",
            locale="en",
            query_context="ACME budget?",
            response_lang="es",
            session_id="sess-1",
        )

        bundle = result.bundle
        assert len(bundle.blocks) == 1
        block = bundle.blocks[0]
        assert block.id == "doc-a"
        assert block.content == "Empresa: ACME\nJuan works at ACME."
        assert block.source_type == "rag"
        assert block.metadata["source_uri"] == "https://example.com/a"
        assert block.metadata["source_label"] == "Document A"
        assert bundle.target_lang == "en"
        assert bundle.locale == "en"
        assert bundle.query_context == "ACME budget?"
        assert bundle.response_lang == "es"
        assert bundle.session_id == "sess-1"

    def test_assigns_default_id_and_source_type(self):
        result = ingest_context([{"content": "hello"}])
        block = result.bundle.blocks[0]
        assert block.id == "block-1"
        assert block.source_type == "prose"

    def test_marks_code_fence_metadata(self):
        result = ingest_context(
            [{"id": "c1", "content": "```python\nprint(1)\n```", "source_type": "code"}]
        )
        assert result.bundle.blocks[0].metadata.get("has_code_fence") is True

    def test_rejects_unknown_source_type(self):
        with pytest.raises(ValueError, match="Unknown source_type"):
            ingest_context([{"content": "x", "source_type": "unknown"}])

    def test_rejects_empty_raw_blocks(self):
        with pytest.raises(ValueError, match="raw_blocks must not be empty"):
            ingest_context([])


class TestLevelMatrix:
    def test_code_block_restricts_levels(self):
        blocks = [ContextBlock(id="c", content="x=1", source_type="code")]
        effective, notes = resolve_effective_levels([1, 2, 3, 4], blocks)
        assert effective == [1]
        assert notes

    def test_mixed_bundle_intersects_levels(self):
        blocks = [
            ContextBlock(id="p", content="prose", source_type="prose"),
            ContextBlock(id="c", content="code", source_type="code"),
        ]
        effective, _ = resolve_effective_levels([1, 2, 3], blocks)
        assert effective == [1]

    def test_levels_override_on_block(self):
        blocks = [
            ContextBlock(
                id="s",
                content="{}",
                source_type="structured",
                metadata={"levels_override": [1, 2]},
            )
        ]
        effective, _ = resolve_effective_levels([1, 2, 3, 4], blocks)
        assert effective == [1, 2]


class TestGatewayContextBundle:
    def test_optimize_context_accepts_bundle(self):
        ingested = ingest_context(
            [
                {"id": "A", "content": "Empresa: ACME\nJuan works at ACME."},
                {"id": "B", "content": "Empresa: ACME\nPedro works at ACME."},
            ],
            locale="en",
        )
        out = optimize_context(ingested.bundle, levels=[1])
        assert "Juan works at ACME" in out.text
        assert "Pedro works at ACME" in out.text

    def test_structured_block_skips_n2_in_gateway(self):
        bundle = ContextBundle(
            blocks=[ContextBlock(id="s", content='{"k": 1}', source_type="structured")],
            locale="en",
        )
        out = optimize_context(bundle, levels=[1, 2])
        assert any("skipped" in t.detail for t in out.trace if t.level == 0)
        assert out.factorization is None

    def test_code_block_disables_l0(self):
        bundle = ContextBundle(
            blocks=[ContextBlock(id="c", content="Juan trabaja en ACME.", source_type="code")],
            target_lang="en",
            locale="en",
        )
        out = optimize_context(bundle, levels=[1], l0=True, target_lang="en")
        assert out.ingest_trace is None
        assert any("L0 disabled" in t.detail for t in out.trace)
