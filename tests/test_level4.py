"""Tests del optimizador Nivel 4 — grafo de conocimiento."""

from coe import optimize_context
from coe.level1 import deduplicate_context
from coe.level2 import factorize_context
from coe.level3 import structure_context
from coe.level4 import build_context_graph
from coe.models import ContextBlock, EntityRecord, FactorizationResult, SharedFact


class TestN4Build:
    def test_spec_example_graph(self):
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
        structured = structure_context(factorized, locale="en")
        graph = build_context_graph(structured, locale="en")

        assert graph.complexity.node_count >= 3
        assert graph.complexity.edge_count >= 2
        assert any(node.kind == "organization" for node in graph.nodes)

        prose = graph.render_prose()
        assert "Juan works at ACME" in prose
        assert "knows Pedro" in prose
        assert "Pedro works at ACME" in prose
        assert "node:" not in prose

        internal = graph.serialize_internal()
        assert "node:juan:person" in internal
        assert "edge:juan->pedro:knows" in internal

    def test_zero_loss_unparsed(self):
        factorized = FactorizationResult(
            entities=[],
            unparsed=["Some free-form note."],
            shared_facts=[],
            original_tokens=5,
            optimized_tokens=5,
        )
        structured = structure_context(factorized)
        graph = build_context_graph(structured)

        assert len(graph.orphans) == 1
        assert graph.orphans[0].text == "Some free-form note."
        assert "Some free-form note." in graph.render_prose()

    def test_global_facts_as_concept_nodes(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nJuan knows Pedro."),
            ContextBlock(id="B", content="Empresa: ACME\nPedro works at ACME."),
            ContextBlock(id="C", content="Empresa: ACME\nJuan works at ACME."),
        ]
        dedup = deduplicate_context(blocks)
        factorized = factorize_context(dedup, locale="en")
        structured = structure_context(factorized, locale="en")
        graph = build_context_graph(structured, locale="en")

        assert any(node.kind == "concept" for node in graph.nodes)
        assert "Empresa: ACME" in graph.render_prose()


class TestN4Slice:
    def test_query_slice_limits_nodes(self):
        factorized = FactorizationResult(
            entities=[
                EntityRecord(
                    name="Juan",
                    attributes={"company": "ACME"},
                    actions=[],
                    source_refs=["A"],
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
        structured = structure_context(factorized, locale="en")
        graph = build_context_graph(
            structured,
            query_context="What does Juan know?",
            max_hops=1,
            locale="en",
        )

        active_ids = {node.id for node in (graph.active_nodes or graph.nodes)}
        assert "juan" in active_ids
        assert graph.query_context == "What does Juan know?"


class TestN4Gateway:
    def test_n1_n2_n3_n4_pipeline(self):
        blocks = [
            ContextBlock(id="A", content="Juan knows Pedro."),
            ContextBlock(id="B", content="Pedro works at ACME."),
            ContextBlock(id="C", content="Juan works at ACME."),
        ]
        out = optimize_context(blocks, levels=[1, 2, 3, 4], locale="en")

        assert out.context_graph is not None
        assert out.structured is not None
        assert "knows Pedro" in out.text
        assert "node:" not in out.text
        assert "n4" in out.metrics.latency_ms_by_level

    def test_n4_only_runs_upstream(self):
        blocks = [
            ContextBlock(id="A", content="Juan knows Pedro."),
            ContextBlock(id="B", content="Juan works at ACME."),
        ]
        out = optimize_context(blocks, levels=[4], locale="en")

        assert out.context_graph is not None
        assert "n4" in out.metrics.latency_ms_by_level
        assert "n1" not in out.metrics.latency_ms_by_level
