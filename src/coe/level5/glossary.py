"""Glosario bilingüe — parseo y merge N5."""

from __future__ import annotations

import re

from ..models import ContextBlock, ContextGraph, GraphNode

_TERM_LINE = re.compile(
    r"^(?P<term>[^:|=]+?)\s*(?:[:|=|｜]\s*|\s+→\s+)(?P<translation>.+?)\s*$"
)


def parse_glossary_lines(content: str) -> list[tuple[str, str]]:
    """Parsea entradas ``term: translation`` (una por línea)."""
    entries: list[tuple[str, str]] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _TERM_LINE.match(stripped)
        if not match:
            continue
        term = match.group("term").strip()
        translation = match.group("translation").strip()
        if term and translation:
            entries.append((term, translation))
    return entries


def merge_glossary_terms(
    graph: ContextGraph,
    glossary_blocks: list[ContextBlock],
) -> ContextGraph:
    """Fusiona términos de glosario como nodos ``kind=term`` en el grafo N5."""
    if not glossary_blocks:
        return graph

    nodes_by_id = {node.id: node for node in graph.nodes}
    for block in glossary_blocks:
        for term, translation in parse_glossary_lines(block.content):
            node_id = _term_node_id(term)
            existing = nodes_by_id.get(node_id)
            if existing is None:
                node = GraphNode(
                    id=node_id,
                    kind="term",
                    labels=[term],
                    properties={"term": term, "translation": translation},
                    source_refs=[block.id],
                )
                nodes_by_id[node_id] = node
                continue

            existing.properties["translation"] = translation
            refs = set(existing.source_refs) | {block.id}
            existing.source_refs = sorted(refs)

    graph.nodes = list(nodes_by_id.values())
    return graph


def _term_node_id(term: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", term.strip().casefold()).strip("-") or "term"
    return f"glossary:{slug}"
