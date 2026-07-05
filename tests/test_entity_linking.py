"""Tests entity linking fuzzy N5."""

from __future__ import annotations

from coe.level5.entity_linking import (
    DEFAULT_FUZZY_THRESHOLD,
    build_alias_map,
    compute_entity_id_map,
    fuzzy_similarity,
    link_incoming_entities,
)
from coe.level5.merge import merge_context_graphs
from coe.models import ContextBlock, ContextGraph, GraphNode


class TestFuzzySimilarity:
    def test_similar_names_above_threshold(self):
        score = fuzzy_similarity("J. Perez", "Juan Perez")
        assert score >= DEFAULT_FUZZY_THRESHOLD

    def test_different_names_below_threshold(self):
        score = fuzzy_similarity("Maria Lopez", "ACME Corp")
        assert score < DEFAULT_FUZZY_THRESHOLD


class TestEntityLinkingMerge:
    def test_fuzzy_links_person_nodes_across_turns(self):
        base = ContextGraph(
            nodes=[
                GraphNode(
                    id="juan",
                    kind="person",
                    labels=["Juan Perez"],
                    properties={},
                    source_refs=["A"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version="0.1",
            original_tokens=10,
        )
        incoming = ContextGraph(
            nodes=[
                GraphNode(
                    id="j_perez",
                    kind="person",
                    labels=["J. Perez"],
                    properties={},
                    source_refs=["B"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version="0.1",
            original_tokens=10,
        )

        id_map = compute_entity_id_map(
            base,
            incoming,
            alias_map={},
            fuzzy_threshold=DEFAULT_FUZZY_THRESHOLD,
        )
        assert id_map.get("j_perez") == "juan"

        merged = merge_context_graphs(base, incoming)
        assert len(merged.nodes) == 1
        assert merged.nodes[0].id == "juan"
        assert set(merged.nodes[0].source_refs) == {"A", "B"}

    def test_explicit_alias_links_without_fuzzy(self):
        base = ContextGraph(
            nodes=[
                GraphNode(
                    id="juan",
                    kind="person",
                    labels=["Juan"],
                    properties={},
                    source_refs=["A"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version="0.1",
            original_tokens=5,
        )
        incoming = ContextGraph(
            nodes=[
                GraphNode(
                    id="jp",
                    kind="person",
                    labels=["J. P."],
                    properties={},
                    source_refs=["B"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version="0.1",
            original_tokens=5,
        )
        alias_map = build_alias_map(
            [
                ContextBlock(
                    id="B",
                    content="ignored",
                    metadata={"entity_aliases": ["J. P.:juan"]},
                )
            ]
        )
        linked = link_incoming_entities(
            base,
            incoming,
            alias_map=alias_map,
            fuzzy_threshold=0.99,
        )
        assert linked.nodes[0].id == "juan"

    def test_conflict_blocks_fuzzy_merge(self):
        base = ContextGraph(
            nodes=[
                GraphNode(
                    id="juan",
                    kind="person",
                    labels=["Juan Perez"],
                    properties={"conflict": True},
                    source_refs=["A"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version="0.1",
            original_tokens=5,
        )
        incoming = ContextGraph(
            nodes=[
                GraphNode(
                    id="j_perez",
                    kind="person",
                    labels=["J. Perez"],
                    properties={},
                    source_refs=["B"],
                )
            ],
            edges=[],
            orphans=[],
            schema_version="0.1",
            original_tokens=5,
        )
        merged = merge_context_graphs(base, incoming)
        assert len(merged.nodes) == 2
