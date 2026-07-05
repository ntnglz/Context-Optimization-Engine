"""Materialización de turno → grafo y StateView (N5)."""

from __future__ import annotations

from ..level1 import deduplicate_context
from ..level2 import factorize_context
from ..level3 import structure_context
from ..level4 import build_context_graph
from ..models import SCHEMA_VERSION, ContextBlock, ContextGraph, GraphEdge, StructuredContext
from ..renderer.templates import get_templates
from .state import StateView


def blocks_to_context_graph(
    blocks: list[ContextBlock],
    *,
    locale: str,
    levels: list[int],
) -> ContextGraph:
    """Construye el grafo del turno aplicando sub-niveles N1–N4."""
    dedup = deduplicate_context(blocks)
    sub_levels = sorted(n for n in levels if n != 5)

    if 2 in sub_levels or 3 in sub_levels or 4 in sub_levels:
        factorized = factorize_context(dedup, locale=locale)
        structured = structure_context(factorized, locale=locale)
    else:
        structured = _dedup_to_structured(dedup)

    return build_context_graph(structured, locale=locale)


def render_state_view(
    graph: ContextGraph,
    *,
    previous: ContextGraph | None,
    locale: str,
) -> StateView:
    """Proyecta el head acumulado a prosa; añade diff reciente si hay cambios."""
    tpl = get_templates(locale)
    intro = tpl["view_intro"]
    body = graph.render_prose(locale=locale).strip()
    sections = [intro, "", body]

    if previous is not None:
        diff = _diff_to_prose(previous, graph, locale=locale)
        if diff:
            sections.extend(["", tpl["change_intro"], diff])

    prose = "\n".join(sections).rstrip() + "\n"
    return StateView(prose=prose)


def _dedup_to_structured(dedup) -> StructuredContext:
    unparsed: list[str] = []
    for block in dedup.unique_blocks:
        for line in block.content.splitlines():
            stripped = line.strip()
            if stripped:
                unparsed.append(stripped)
    return StructuredContext(
        entities=[],
        global_facts=list(dedup.shared_facts),
        unparsed=unparsed,
        schema_version=SCHEMA_VERSION,
        original_tokens=dedup.original_tokens,
        optimized_tokens=dedup.optimized_tokens,
    )


def _diff_to_prose(
    previous: ContextGraph,
    current: ContextGraph,
    *,
    locale: str,
) -> str:
    prev_orphans = {orphan.text for orphan in previous.orphans}
    new_orphans = [orphan.text for orphan in current.orphans if orphan.text not in prev_orphans]

    prev_edges = {
        (edge.from_id, edge.to_id, edge.type) for edge in previous.edges
    }
    new_edges = [
        edge for edge in current.edges if (edge.from_id, edge.to_id, edge.type) not in prev_edges
    ]

    prev_node_ids = {node.id for node in previous.nodes}
    new_nodes = [node for node in current.nodes if node.id not in prev_node_ids]

    lines: list[str] = []
    for orphan in new_orphans:
        lines.append(orphan)

    for edge in new_edges:
        lines.append(_edge_to_phrase(edge, current, locale=locale))

    for node in new_nodes:
        if node.kind == "concept" and node.labels:
            lines.append(node.labels[0])

    return "\n".join(lines)


def _edge_to_phrase(edge: GraphEdge, graph: ContextGraph, *, locale: str) -> str:
    tpl = get_templates(locale)
    nodes = {node.id: node for node in graph.nodes}
    source = nodes.get(edge.from_id)
    target = nodes.get(edge.to_id)
    source_name = source.labels[0] if source and source.labels else edge.from_id
    target_name = target.labels[0] if target and target.labels else edge.to_id

    if edge.type == "knows":
        return tpl["edge_knows"].format(source=source_name, target=target_name)
    if edge.type == "company":
        return tpl["edge_company"].format(source=source_name, target=target_name)
    return tpl["edge_generic"].format(
        source=source_name,
        target=target_name,
        edge_type=edge.type,
    )
