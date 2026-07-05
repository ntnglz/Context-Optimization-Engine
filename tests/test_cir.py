"""Tests CIR v1.0 — envelope, builder, roundtrip y proyección prosa."""

from __future__ import annotations

import json
from pathlib import Path

from coe.cir import (
    CIR_VERSION,
    context_graph_from_envelope,
    envelope_from_context_graph,
)
from coe.level2 import factorize_context
from coe.level3 import structure_context
from coe.level4 import build_context_graph
from coe.level5.merge import merge_context_graphs
from coe.level5.materialize import render_state_view
from coe.level5.serialize import semantic_state_from_dict, semantic_state_to_dict
from coe.level5 import InMemoryStateStore, update_semantic_state
from coe.models import (
    ContextBlock,
    ContextGraph,
    EntityRecord,
    FactorizationResult,
    GraphEdge,
    GraphNode,
    GRAPH_SCHEMA_VERSION,
)

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data/benchmarks/schema/cir-1.0.schema.json"


class TestCIRBuilder:
    def test_action_as_edge_not_property(self):
        factorized = FactorizationResult(
            entities=[
                EntityRecord(
                    name="Juan",
                    attributes={"company": "ACME"},
                    actions=["approved the budget"],
                    source_refs=["A"],
                ),
            ],
            unparsed=[],
            shared_facts=[],
            original_tokens=10,
            optimized_tokens=8,
        )
        structured = structure_context(factorized, locale="en")
        graph = build_context_graph(structured, locale="en")

        action_edges = [e for e in graph.edges if e.type == "action"]
        assert len(action_edges) == 1
        assert action_edges[0].properties.get("value") == "approved the budget"
        assert "actions" not in (graph.nodes[0].properties if graph.nodes else {})

        prose = graph.render_prose(locale="en")
        assert "approved the budget" in prose
        assert "node:" not in prose

    def test_rag_document_and_chunk_nodes(self):
        blocks = [
            ContextBlock(
                id="rag-a",
                source_type="rag",
                content="Budget Report Q1\nPresupuesto: 50k",
                metadata={"source_label": "Budget Report Q1", "source_uri": "rag://budget-q1"},
            ),
        ]
        factorized = factorize_context(blocks, locale="en")
        structured = structure_context(factorized, locale="en")
        graph = build_context_graph(structured, source_blocks=blocks, locale="en")

        kinds = {node.kind for node in graph.nodes}
        assert "document" in kinds
        assert "chunk" in kinds
        contains = [e for e in graph.edges if e.type == "contains"]
        assert len(contains) >= 1
        doc = next(n for n in graph.nodes if n.kind == "document")
        assert doc.properties.get("uri") == "rag://budget-q1"


class TestCIREnvelope:
    def test_roundtrip_envelope_json(self):
        factorized = FactorizationResult(
            entities=[
                EntityRecord(
                    name="Juan",
                    attributes={"company": "ACME"},
                    actions=[],
                    source_refs=["C"],
                ),
            ],
            unparsed=["Juan knows Pedro."],
            shared_facts=[],
            original_tokens=10,
            optimized_tokens=8,
        )
        structured = structure_context(factorized, locale="en")
        graph = build_context_graph(structured, locale="en")
        original_prose = graph.render_prose(locale="en")

        payload = envelope_from_context_graph(graph)
        assert payload["cir_version"] == CIR_VERSION
        assert "graph" in payload
        assert "nodes" in payload["graph"]

        restored = context_graph_from_envelope(payload)
        assert restored.schema_version == GRAPH_SCHEMA_VERSION
        assert restored.render_prose(locale="en") == original_prose

    def test_legacy_actions_migrated_on_load(self):
        legacy = ContextGraph(
            nodes=[
                GraphNode(
                    id="juan",
                    kind="person",
                    labels=["Juan"],
                    properties={"actions": ["approved the budget"]},
                    source_refs=["A"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version="0.1",
            original_tokens=5,
        )
        payload = legacy.to_dict()
        restored = context_graph_from_envelope(payload)

        assert restored.schema_version == CIR_VERSION
        assert "actions" not in restored.nodes[0].properties
        assert any(edge.type == "action" for edge in restored.edges)
        assert "approved the budget" in restored.render_prose(locale="en")

    def test_schema_file_exists_and_valid_json(self):
        assert SCHEMA_PATH.is_file()
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        assert schema["properties"]["cir_version"]["const"] == "1.0"


class TestCIRN5Serialize:
    def test_semantic_state_uses_envelope(self):
        store = InMemoryStateStore()
        session_id = "cir-envelope-session"
        turn = [ContextBlock(id="A", content="Juan works at ACME.")]

        result = update_semantic_state(
            turn, session_id=session_id, store=store, locale="en", levels=[1, 4]
        )
        payload = semantic_state_to_dict(result.state)
        assert payload["graph"]["cir_version"] == CIR_VERSION
        assert "graph" in payload["graph"]

        restored = semantic_state_from_dict(payload)
        assert restored.graph is not None
        assert restored.graph.render_prose(locale="en") == result.state.graph.render_prose(
            locale="en"
        )

    def test_merge_conflict_prose_unchanged(self):
        base = ContextGraph(
            nodes=[
                GraphNode(
                    id="budget",
                    kind="concept",
                    labels=["Budget"],
                    properties={"amount": "50k"},
                    source_refs=["A"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version=GRAPH_SCHEMA_VERSION,
            original_tokens=10,
        )
        incoming = ContextGraph(
            nodes=[
                GraphNode(
                    id="budget",
                    kind="concept",
                    labels=["Budget"],
                    properties={"amount": "80k"},
                    source_refs=["B"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version=GRAPH_SCHEMA_VERSION,
            original_tokens=10,
        )
        merged = merge_context_graphs(base, incoming)
        view = render_state_view(merged, previous=None, locale="en")
        prose = view.render()

        assert "Conflicting information in session state:" in prose
        assert "50k" in prose
        assert "80k" in prose
