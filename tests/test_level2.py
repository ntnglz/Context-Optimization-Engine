"""Tests del optimizador Nivel 2 — factorización."""

from coe.level1 import deduplicate_context
from coe.level2 import factorize_context
from coe.level2.patterns import parse_line
from coe.models import ContextBlock


class TestN2Patterns:
    def test_parse_works_at(self):
        parsed = parse_line("Juan works at ACME.")
        assert parsed is not None
        assert parsed.entity == "Juan"
        assert parsed.attribute_key == "company"
        assert parsed.attribute_value == "ACME"

    def test_parse_action(self):
        parsed = parse_line("Juan approved the budget")
        assert parsed is not None
        assert parsed.entity == "Juan"
        assert parsed.action_text == "approved the budget"

    def test_rejects_pronoun_subject(self):
        assert parse_line("He created Project X.") is None


class TestN2PatternsEs:
    def test_parse_trabaja_en(self):
        parsed = parse_line("Juan trabaja en ACME.", locale="es")
        assert parsed is not None
        assert parsed.entity == "Juan"
        assert parsed.attribute_key == "company"
        assert parsed.attribute_value == "ACME"

    def test_parse_action_es(self):
        parsed = parse_line("Juan aprobó el presupuesto", locale="es")
        assert parsed is not None
        assert parsed.entity == "Juan"
        assert parsed.action_text == "aprobó el presupuesto"

    def test_rejects_pronoun_subject_es(self):
        assert parse_line("Él creó el Proyecto X.", locale="es") is None


class TestN2Factorization:
    def test_juan_example_from_spec(self):
        blocks = [
            ContextBlock(id="A", content="Juan works at ACME."),
            ContextBlock(id="B", content="Juan created Project X."),
            ContextBlock(id="C", content="Juan approved the budget."),
        ]
        result = factorize_context(blocks)

        assert len(result.entities) == 1
        assert result.entities[0].name == "Juan"
        assert result.entities[0].attributes["company"] == "ACME"
        assert "created Project X" in result.entities[0].actions
        assert result.unparsed == []

        prose = result.render_prose()
        assert "Juan works at ACME" in prose
        assert "approved the budget" in prose
        assert "entity:" not in prose

    def test_single_mention_passthrough(self):
        blocks = [ContextBlock(id="A", content="Juan works at ACME.")]
        result = factorize_context(blocks)

        assert result.entities == []
        assert result.unparsed == ["Juan works at ACME."]

    def test_preserves_n1_shared_facts(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME."),
            ContextBlock(id="B", content="Empresa: ACME\nJuan approved the budget."),
        ]
        dedup = deduplicate_context(blocks)
        result = factorize_context(dedup)

        prose = result.render_prose()
        assert "Empresa: ACME" in prose or "Empresa=ACME" in dedup.render_compact()
        assert len(result.shared_facts) == 1

    def test_structured_internal_not_in_prose(self):
        blocks = [
            ContextBlock(id="A", content="Juan works at ACME."),
            ContextBlock(id="B", content="Juan created Project X."),
        ]
        result = factorize_context(blocks)
        structured = result.render_structured()

        assert "entity:Juan" in structured
        assert "entity:" not in result.render_prose()

    def test_juan_example_es(self):
        blocks = [
            ContextBlock(id="A", content="Juan trabaja en ACME."),
            ContextBlock(id="B", content="Juan creó el Proyecto X."),
            ContextBlock(id="C", content="Juan aprobó el presupuesto."),
        ]
        result = factorize_context(blocks, locale="es")

        assert len(result.entities) == 1
        assert result.entities[0].attributes["company"] == "ACME"
        prose = result.render_prose(locale="es")
        assert "Juan trabaja en ACME" in prose
        assert "aprobó el presupuesto" in prose
        assert " y " in prose
        assert "entity:" not in prose

    def test_acme_budget_es_case(self):
        blocks = [
            ContextBlock(
                id="A",
                content="Empresa: ACME\nCliente: Globex\nJuan trabaja en ACME.",
            ),
            ContextBlock(
                id="B",
                content="Empresa: ACME\nPresupuesto: 50k\nJuan aprobó el presupuesto.",
            ),
            ContextBlock(
                id="C",
                content="Empresa: ACME\nCliente: Globex\nPedro trabaja en ACME.",
            ),
        ]
        dedup = deduplicate_context(blocks)
        result = factorize_context(dedup, locale="es")
        prose = result.render_prose(locale="es")

        assert "Empresa: ACME" in prose
        assert "Juan trabaja en ACME" in prose
        assert "aprobó el presupuesto" in prose
        assert "Pedro trabaja en ACME." in prose
        assert "entity:" not in prose
