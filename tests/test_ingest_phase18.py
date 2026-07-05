"""Tests Fase 18 — ingest structured, code y glossary."""

from __future__ import annotations

from coe.gateway import optimize_context
from coe.ingest import ingest_context
from coe.ingest.structured import flatten_structured_content
from coe.level1 import deduplicate_context
from coe.level1.code_signature import code_line_signature
from coe.level5.glossary import merge_glossary_terms, parse_glossary_lines
from coe.level5 import update_semantic_state
from coe.level5.store import InMemoryStateStore
from coe.models import ContextBlock, ContextGraph, GraphNode, GRAPH_SCHEMA_VERSION


class TestStructuredParser:
    def test_flattens_json(self):
        raw = '{"company": "ACME", "budget": "50k"}'
        out = flatten_structured_content(raw, fmt="json")
        assert "company: ACME" in out
        assert "budget: 50k" in out

    def test_flattens_csv(self):
        raw = "name,role\nJuan,engineer\nPedro,analyst"
        out = flatten_structured_content(raw, fmt="csv")
        assert "name: Juan" in out
        assert "role: engineer" in out

    def test_ingest_prepares_structured_block(self):
        result = ingest_context(
            [
                {
                    "id": "json-1",
                    "source_type": "structured",
                    "content": '{"status": "ok", "code": 200}',
                }
            ]
        )
        block = result.bundle.blocks[0]
        assert block.metadata.get("structured_format") == "json"
        assert "status: ok" in block.content
        assert "code: 200" in block.content


class TestCodeDedup:
    def test_signature_ignores_trailing_comment(self):
        assert code_line_signature("x = 1  # init") == code_line_signature("x=1")

    def test_deduplicates_identical_code_lines(self):
        blocks = [
            ContextBlock(id="A", content="x = 1\ny = 2", source_type="code"),
            ContextBlock(id="B", content="x=1  # dup\nz = 3", source_type="code"),
        ]
        result = deduplicate_context(blocks)
        assert len(result.shared_facts) == 1
        assert result.shared_facts[0].canonical_line.startswith("x")

    def test_code_block_skips_l0(self):
        bundle = ingest_context(
            [{"id": "c1", "content": "print('hola')", "source_type": "code"}],
            target_lang="en",
            locale="en",
        ).bundle
        out = optimize_context(bundle, levels=[1], l0=True, target_lang="en")
        assert out.ingest_trace is None
        assert any("L0 disabled" in t.detail for t in out.trace)


class TestGlossary:
    def test_parse_glossary_lines(self):
        entries = parse_glossary_lines("ACME: 顶顶公司\nBudget: 预算")
        assert ("ACME", "顶顶公司") in entries
        assert ("Budget", "预算") in entries

    def test_glossary_sets_preserve_lang(self):
        block = ingest_context(
            [{"id": "g1", "source_type": "glossary", "content": "ACME: ACME Corp"}]
        ).bundle.blocks[0]
        assert block.metadata.get("preserve_lang") is True

    def test_n5_merges_glossary_terms(self):
        store = InMemoryStateStore()
        session_id = "glossary-session"
        update_semantic_state(
            [ContextBlock(id="t1", content="Empresa: ACME\nJuan works at ACME.", source_type="rag")],
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1, 4],
        )
        update_semantic_state(
            [
                ContextBlock(
                    id="g1",
                    content="ACME: ACME Corporation",
                    source_type="glossary",
                )
            ],
            session_id=session_id,
            store=store,
            locale="en",
            levels=[1, 5],
        )
        state = store.load(session_id)
        assert state is not None
        term_nodes = [node for node in state.graph.nodes if node.kind == "term"]
        assert len(term_nodes) == 1
        assert term_nodes[0].properties.get("translation") == "ACME Corporation"
        assert "ACME: ACME Corporation" in state.graph.render_prose(locale="en")

    def test_merge_glossary_updates_existing_term(self):
        graph = ContextGraph(
            nodes=[
                GraphNode(
                    id="glossary:acme",
                    kind="term",
                    labels=["ACME"],
                    properties={"term": "ACME", "translation": "old"},
                    source_refs=["g0"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version=GRAPH_SCHEMA_VERSION,
            original_tokens=0,
        )
        merged = merge_glossary_terms(
            graph,
            [ContextBlock(id="g1", content="ACME: ACME Corporation", source_type="glossary")],
        )
        node = next(node for node in merged.nodes if node.kind == "term")
        assert node.properties["translation"] == "ACME Corporation"
        assert "g1" in node.source_refs
