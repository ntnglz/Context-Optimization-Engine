"""Tests del optimizador Nivel 1 — deduplicación."""

import pytest

from coe.level1 import deduplicate_context
from coe.models import ContextBlock


class TestLevel1Deduplication:
    def test_acme_example_from_vision(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nCliente: Globex"),
            ContextBlock(id="B", content="Empresa: ACME\nPresupuesto: 50k"),
            ContextBlock(id="C", content="Empresa: ACME\nCliente: Globex"),
        ]

        result = deduplicate_context(blocks)
        rendered = result.render()

        assert "Empresa=ACME" in rendered
        assert "Referencias: A, B, C" in rendered
        assert "Cliente=Globex" in rendered
        assert "Referencias: A, C" in rendered
        assert "[B]" in rendered
        assert "Presupuesto: 50k" in rendered
        assert result.compression_ratio > 0
        assert result.tokens_saved > 0

    def test_no_duplicates_returns_unchanged_blocks(self):
        blocks = [
            ContextBlock(id="A", content="Alpha"),
            ContextBlock(id="B", content="Beta"),
        ]

        result = deduplicate_context(blocks)

        assert result.shared_facts == []
        assert len(result.unique_blocks) == 2
        assert result.compression_ratio == 0.0

    def test_duplicate_within_single_block_not_extracted(self):
        """Una línea repetida solo dentro de un bloque no es redundancia inter-bloque."""
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nEmpresa: ACME"),
        ]

        result = deduplicate_context(blocks)

        assert result.shared_facts == []
        assert "Empresa: ACME" in result.unique_blocks[0].content

    def test_case_insensitive_matching(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME"),
            ContextBlock(id="B", content="empresa: acme"),
        ]

        result = deduplicate_context(blocks)

        assert len(result.shared_facts) == 1
        assert result.shared_facts[0].source_ids == ["A", "B"]

    def test_min_occurrences_validation(self):
        with pytest.raises(ValueError, match="min_occurrences"):
            deduplicate_context([ContextBlock(id="A", content="x")], min_occurrences=1)

    def test_reconstruction_preserves_all_information(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nCliente: Globex"),
            ContextBlock(id="B", content="Empresa: ACME\nPresupuesto: 50k"),
            ContextBlock(id="C", content="Empresa: ACME\nCliente: Globex"),
        ]

        result = deduplicate_context(blocks)
        all_content = result.render()

        for phrase in ("ACME", "Globex", "50k"):
            assert phrase in all_content

    def test_shared_facts_sorted_by_canonical_line(self):
        blocks = [
            ContextBlock(id="A", content="Zebra: 1\nAlpha: 1"),
            ContextBlock(id="B", content="Zebra: 1\nAlpha: 1"),
        ]

        result = deduplicate_context(blocks)
        compacts = [fact.to_compact() for fact in result.shared_facts]

        assert compacts == sorted(compacts, key=str.lower)
