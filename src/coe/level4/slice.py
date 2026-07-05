"""Slice de subgrafo por consulta (heurística v1)."""

from __future__ import annotations

import re

from ..models import ContextGraph, GraphEdge, GraphNode


def apply_query_slice(
    graph: ContextGraph,
    *,
    query_context: str,
    max_hops: int,
) -> ContextGraph:
    """Selecciona subgrafo por proximidad desde entidades mencionadas en la consulta."""
    seeds = _match_seed_nodes(graph.nodes, query_context)
    if not seeds:
        return graph

    adjacency = _build_adjacency(graph.edges)
    included = set(seeds)
    frontier = set(seeds)

    for _ in range(max(0, max_hops)):
        next_frontier: set[str] = set()
        for node_id in frontier:
            for neighbor in adjacency.get(node_id, ()):
                if neighbor not in included:
                    included.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
        if not frontier:
            break

    active_nodes = [node for node in graph.nodes if node.id in included]
    active_node_ids = {node.id for node in active_nodes}
    active_edges = [
        edge
        for edge in graph.edges
        if edge.from_id in active_node_ids and edge.to_id in active_node_ids
    ]

    return ContextGraph(
        nodes=graph.nodes,
        edges=graph.edges,
        orphans=graph.orphans,
        active_nodes=active_nodes,
        active_edges=active_edges,
        schema_version=graph.schema_version,
        original_tokens=graph.original_tokens,
        optimized_tokens=graph.optimized_tokens,
        internal_tokens=graph.internal_tokens,
        query_context=query_context,
        max_hops=max_hops,
        include_orphans=graph.include_orphans,
    )


def _match_seed_nodes(nodes: list[GraphNode], query_context: str) -> set[str]:
    query = query_context.lower()
    seeds: set[str] = set()
    for node in nodes:
        for label in node.labels:
            token = label.lower()
            if len(token) < 2:
                continue
            if token in query or re.search(rf"\b{re.escape(token)}\b", query):
                seeds.add(node.id)
                break
        if node.id.replace("_", " ") in query:
            seeds.add(node.id)
    return seeds


def _build_adjacency(edges: list[GraphEdge]) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge.from_id, set()).add(edge.to_id)
        adjacency.setdefault(edge.to_id, set()).add(edge.from_id)
    return adjacency
