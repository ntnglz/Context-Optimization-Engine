"""Tests del optimizador Nivel 3 — estructuración relacional."""

from coe import optimize_context
from coe.level1 import deduplicate_context
from coe.level2 import factorize_context
from coe.level3 import structure_context
from coe.level3.patterns import parse_knows_line
from coe.models import ContextBlock, EntityRecord, FactorizationResult, SharedFact


class TestN3Patterns:
    def test_parse_knows_en(self):
        parsed = parse_knows_line("Juan knows Pedro.")
        assert parsed is not None
        assert parsed.entity == "Juan"
        assert parsed.target == "Pedro"

    def test_parse_knows_es(self):
        parsed = parse_knows_line("Juan conoce a Pedro.", locale="es")
        assert parsed is not None
        assert parsed.entity == "Juan"
        assert parsed.target == "Pedro"


class TestN3Structure:
    def test_spec_example(self):
        factorized = FactorizationResult(
            entities=[
                EntityRecord(
                    name="Juan",
                    attributes={"company": "ACME"},
                    actions=[],
                    source_refs=["C"],
                ),
                EntityRecord(
                    name="Pedro",
                    attributes={"company": "ACME"},
                    actions=[],
                    source_refs=["B"],
                ),
            ],
            unparsed=["Juan knows Pedro."],
            shared_facts=[],
            original_tokens=10,
            optimized_tokens=8,
        )
        result = structure_context(factorized, locale="en")

        assert len(result.entities) == 2
        juan = next(e for e in result.entities if e.name == "Juan")
        assert any(r.type == "knows" and r.target == "pedro" for r in juan.relations)
        assert result.unparsed == []

        prose = result.render_prose()
        assert "Juan works at ACME" in prose
        assert "knows Pedro" in prose
        assert "Pedro works at ACME" in prose
        assert "entity:" not in prose

        debug = result.render_debug()
        assert "entity:juan" in debug
        assert "knows->pedro" in debug
        assert "entity:" not in prose

    def test_unparsed_passthrough(self):
        factorized = FactorizationResult(
            entities=[],
            unparsed=["Some free-form note."],
            shared_facts=[],
            original_tokens=5,
            optimized_tokens=5,
        )
        result = structure_context(factorized)
        assert result.unparsed == ["Some free-form note."]
        assert "Some free-form note." in result.render_prose()

    def test_preserves_shared_facts(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nJuan knows Pedro."),
            ContextBlock(id="B", content="Empresa: ACME\nPedro works at ACME."),
            ContextBlock(id="C", content="Empresa: ACME\nJuan works at ACME."),
        ]
        dedup = deduplicate_context(blocks)
        factorized = factorize_context(dedup, locale="en")
        result = structure_context(factorized, locale="en")

        prose = result.render_prose()
        assert "Empresa: ACME" in prose
        assert len(result.global_facts) == 1


class TestN3Gateway:
    def test_n1_n2_n3_pipeline(self):
        blocks = [
            ContextBlock(id="A", content="Juan knows Pedro."),
            ContextBlock(id="B", content="Pedro works at ACME."),
            ContextBlock(id="C", content="Juan works at ACME."),
        ]
        out = optimize_context(blocks, levels=[1, 2, 3], locale="en")

        assert "knows Pedro" in out.text
        assert "entity:" not in out.text
        assert "n3" in out.metrics.latency_ms_by_level
        assert out.structured is not None
        assert out.factorization is not None

    def test_n3_only_runs_factorization(self):
        blocks = [
            ContextBlock(id="A", content="Juan knows Pedro."),
            ContextBlock(id="B", content="Juan works at ACME."),
        ]
        out = optimize_context(blocks, levels=[3], locale="en")

        assert out.structured is not None
        assert "n3" in out.metrics.latency_ms_by_level
        assert "n1" not in out.metrics.latency_ms_by_level
