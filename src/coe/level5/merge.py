"""Merge de grafos N4 entre turnos (N5)."""

from __future__ import annotations

from ..models import (
    GRAPH_SCHEMA_VERSION,
    ContextGraph,
    GraphEdge,
    GraphNode,
    GraphOrphan,
    estimate_tokens,
)
from ..level4.builder import _dedupe_edges
from ..level4.render import serialize_graph_internal
from .entity_linking import DEFAULT_FUZZY_THRESHOLD, link_incoming_entities


_SKIP_PROPERTY_KEYS = frozenset({"conflict", "conflict_entries", "retracts", "superseded_by"})


def merge_context_graphs(
    base: ContextGraph | None,
    incoming: ContextGraph,
    *,
    alias_map: dict[str, str] | None = None,
    fuzzy_link_threshold: float | None = DEFAULT_FUZZY_THRESHOLD,
) -> ContextGraph:
    """Fusiona el grafo del turno en el head acumulado (mismo id canónico → un nodo)."""
    if base is None:
        return _clone_graph(incoming)

    linked_incoming = link_incoming_entities(
        base,
        incoming,
        alias_map=alias_map,
        fuzzy_threshold=(
            DEFAULT_FUZZY_THRESHOLD
            if fuzzy_link_threshold is None
            else fuzzy_link_threshold
        ),
    )

    nodes_by_id: dict[str, GraphNode] = {node.id: _clone_node(node) for node in base.nodes}

    for node in linked_incoming.nodes:
        if node.id not in nodes_by_id:
            nodes_by_id[node.id] = _clone_node(node)
            continue
        existing = nodes_by_id[node.id]
        _merge_node_properties(existing, node)
        refs = set(existing.source_refs) | set(node.source_refs)
        existing.source_refs = sorted(refs)
        if not existing.labels and node.labels:
            existing.labels = list(node.labels)

    edges = _dedupe_edges([*base.edges, *linked_incoming.edges])

    orphan_texts = {orphan.text for orphan in base.orphans}
    orphans = [_clone_orphan(orphan) for orphan in base.orphans]
    for orphan in linked_incoming.orphans:
        if orphan.text in orphan_texts:
            continue
        orphans.append(_clone_orphan(orphan))
        orphan_texts.add(orphan.text)

    merged = ContextGraph(
        nodes=list(nodes_by_id.values()),
        edges=edges,
        orphans=orphans,
        schema_version=GRAPH_SCHEMA_VERSION,
        original_tokens=base.original_tokens + linked_incoming.original_tokens,
    )
    internal = serialize_graph_internal(merged)
    merged.internal_tokens = estimate_tokens(internal)
    return merged


def _merge_node_properties(existing: GraphNode, incoming: GraphNode) -> None:
    conflicts = list(existing.properties.get("conflict_entries", []))
    for key, value in incoming.properties.items():
        if key in _SKIP_PROPERTY_KEYS or key == "actions":
            continue
        if key in existing.properties and existing.properties[key] != value:
            existing.properties["conflict"] = True
            conflicts.append(
                {
                    "property": key,
                    "previous": existing.properties[key],
                    "incoming": value,
                    "previous_sources": list(existing.source_refs),
                    "incoming_sources": list(incoming.source_refs),
                }
            )
        existing.properties[key] = value
    if conflicts:
        existing.properties["conflict_entries"] = conflicts
        existing.properties["conflict"] = True


def _clone_node(node: GraphNode) -> GraphNode:
    return GraphNode(
        id=node.id,
        kind=node.kind,
        labels=list(node.labels),
        properties=dict(node.properties),
        source_refs=list(node.source_refs),
    )


def _clone_orphan(orphan: GraphOrphan) -> GraphOrphan:
    return GraphOrphan(text=orphan.text, source_refs=list(orphan.source_refs))


def _clone_graph(graph: ContextGraph) -> ContextGraph:
    cloned = ContextGraph(
        nodes=[_clone_node(node) for node in graph.nodes],
        edges=[
            GraphEdge(
                from_id=edge.from_id,
                to_id=edge.to_id,
                type=edge.type,
                properties=dict(edge.properties),
            )
            for edge in graph.edges
        ],
        orphans=[_clone_orphan(orphan) for orphan in graph.orphans],
        schema_version=graph.schema_version,
        original_tokens=graph.original_tokens,
        optimized_tokens=graph.optimized_tokens,
        internal_tokens=graph.internal_tokens,
        query_context=graph.query_context,
        max_hops=graph.max_hops,
        include_orphans=graph.include_orphans,
        active_nodes=[_clone_node(node) for node in graph.active_nodes]
        if graph.active_nodes
        else None,
        active_edges=[
            GraphEdge(
                from_id=edge.from_id,
                to_id=edge.to_id,
                type=edge.type,
                properties=dict(edge.properties),
            )
            for edge in graph.active_edges
        ]
        if graph.active_edges
        else None,
    )
    return cloned
