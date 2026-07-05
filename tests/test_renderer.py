"""Tests del Renderer — prosa, plantillas locale y ensamblaje Gateway."""

from __future__ import annotations

from coe.gateway import optimize_context
from coe.ingest import ContextBundle, IngestOptions, ingest_context
from coe.level1 import deduplicate_context
from coe.models import ContextBlock
from coe.renderer import render_n1_compact
from coe.renderer.assembly import assemble_gateway_output, render_turn_prose


class TestN1ProseLocale:
    def test_english_prose(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nCliente: Globex"),
            ContextBlock(id="B", content="Empresa: ACME\nPresupuesto: 50k"),
            ContextBlock(id="C", content="Empresa: ACME\nCliente: Globex"),
        ]
        result = deduplicate_context(blocks)
        prose = result.render_prose(locale="en")

        assert "multiple sources" in prose
        assert "Empresa=ACME" not in prose
        assert "entity:" not in prose

    def test_spanish_prose(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nCliente: Globex"),
            ContextBlock(id="B", content="Empresa: ACME\nPresupuesto: 50k"),
            ContextBlock(id="C", content="Empresa: ACME\nCliente: Globex"),
        ]
        result = deduplicate_context(blocks)
        prose = result.render_prose(locale="es")

        assert "varias fuentes" in prose
        assert "De la fuente" in prose
        assert "Referencias:" not in prose
        assert "Empresa=ACME" not in prose

    def test_compact_uses_locale_refs_label(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME"),
            ContextBlock(id="B", content="Empresa: ACME"),
        ]
        result = deduplicate_context(blocks)
        assert "References:" in render_n1_compact(result)


class TestGatewayAssembly:
    def test_assemble_with_section_delimiters(self):
        text = assemble_gateway_output(
            state_prose="Accumulated session state:\n\nJuan works at ACME.",
            turn_prose="New fact from this turn.",
            locale="en",
            section_delimiters=True,
        )
        assert "--- session state ---" in text
        assert "--- context ---" in text
        assert "Juan works at ACME" in text
        assert "New fact from this turn" in text

    def test_assemble_spanish_delimiters(self):
        text = assemble_gateway_output(
            state_prose="Estado acumulado",
            turn_prose="Turno actual",
            locale="es",
            section_delimiters=True,
        )
        assert "--- estado de sesión ---" in text
        assert "--- contexto ---" in text

    def test_n5_omits_turn_by_default(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME."),
            ContextBlock(id="B", content="Empresa: ACME\nPedro works at ACME."),
        ]
        out = optimize_context(blocks, levels=[1, 5], locale="en", session_id="asm-1")
        assert "--- context ---" not in out.text
        assert "Accumulated session state:" in out.text

    def test_n5_include_pending_turn_adds_context_section(self):
        bundle = ContextBundle(
            blocks=[
                ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME."),
            ],
            locale="en",
            session_id="asm-2",
            options=IngestOptions(include_pending_turn=True, section_delimiters=True),
        )
        out = optimize_context(bundle, levels=[1, 5])
        assert "--- session state ---" in out.text
        assert "--- context ---" in out.text
        assert "entity:" not in out.text
        assert "node:" not in out.text

    def test_render_turn_prose_n2_no_artifacts(self):
        blocks = [
            ContextBlock(id="A", content="Juan works at ACME."),
            ContextBlock(id="B", content="Juan created Project X."),
        ]
        prose = render_turn_prose(blocks, levels=[1, 2], locale="en")
        assert "Juan" in prose
        assert "entity:" not in prose

    def test_gateway_n4_via_ingest_bundle(self):
        ingested = ingest_context(
            [
                {"id": "A", "content": "Juan knows Pedro.", "source_type": "prose"},
                {"id": "B", "content": "Pedro works at ACME.", "source_type": "prose"},
            ],
            locale="en",
        )
        out = optimize_context(ingested.bundle, levels=[1, 2, 3, 4])
        assert "entity:" not in out.text
        assert "node:" not in out.text
