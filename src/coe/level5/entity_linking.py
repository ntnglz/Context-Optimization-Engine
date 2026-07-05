"""Entity linking N5 — alias explícitos y fuzzy conservador entre turnos."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from ..models import ContextBlock, ContextGraph, GraphEdge, GraphNode

DEFAULT_FUZZY_THRESHOLD = 0.85
_LINKABLE_KINDS = frozenset({"person", "organization"})


def normalize_label(label: str) -> str:
    text = label.strip().casefold()
    text = re.sub(r"[.\',]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fuzzy_similarity(left: str, right: str) -> float:
    normalized_left = normalize_label(left)
    normalized_right = normalize_label(right)
    if not normalized_left or not normalized_right:
        return 0.0
    if normalized_left == normalized_right:
        return 1.0
    ratio = SequenceMatcher(None, normalized_left, normalized_right).ratio()
    left_tokens = normalized_left.split()
    right_tokens = normalized_right.split()
    if left_tokens and right_tokens and left_tokens[-1] == right_tokens[-1]:
        if left_tokens[0][:1] == right_tokens[0][:1]:
            ratio = max(ratio, DEFAULT_FUZZY_THRESHOLD)
    return ratio


def node_has_conflict(node: GraphNode) -> bool:
    return bool(node.properties.get("conflict"))


def primary_label(node: GraphNode) -> str:
    if node.labels:
        return node.labels[0]
    return node.id.replace("_", " ")


def build_alias_map(blocks: list[ContextBlock]) -> dict[str, str]:
    """Construye mapa alias normalizado → id canónico desde metadata de bloques."""
    mapping: dict[str, str] = {}
    for block in blocks:
        for raw in block.metadata.get("entity_aliases") or []:
            alias: str | None = None
            canonical: str | None = None
            if isinstance(raw, dict):
                alias = raw.get("alias") or raw.get("label")
                canonical = raw.get("canonical_id") or raw.get("id")
            else:
                text = str(raw).strip()
                if "->" in text:
                    alias, canonical = text.split("->", 1)
                elif ":" in text:
                    alias, canonical = text.split(":", 1)
            if not alias or not canonical:
                continue
            mapping[normalize_label(alias)] = _canonical_id(canonical)
    return mapping


def _canonical_id(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def resolve_alias(node: GraphNode, alias_map: dict[str, str]) -> str | None:
    candidates = [primary_label(node), node.id.replace("_", " ")]
    candidates.extend(node.labels)
    for candidate in candidates:
        canonical = alias_map.get(normalize_label(candidate))
        if canonical:
            return canonical
    return None


def compute_entity_id_map(
    base: ContextGraph,
    incoming: ContextGraph,
    *,
    alias_map: dict[str, str] | None = None,
    fuzzy_threshold: float,
) -> dict[str, str]:
    """Devuelve ``incoming_id -> base_id`` para entidades enlazables."""
    aliases = alias_map or {}
    base_by_id = {node.id: node for node in base.nodes}
    id_map: dict[str, str] = {}

    for node in incoming.nodes:
        if node.id in base_by_id:
            continue
        if node.kind not in _LINKABLE_KINDS:
            continue
        if node_has_conflict(node):
            continue

        alias_target = resolve_alias(node, aliases)
        if alias_target and alias_target in base_by_id:
            target = base_by_id[alias_target]
            if not node_has_conflict(target):
                id_map[node.id] = alias_target
            continue

        label = primary_label(node)
        best_id: str | None = None
        best_score = 0.0
        for base_node in base.nodes:
            if base_node.kind != node.kind:
                continue
            if node_has_conflict(base_node):
                continue
            score = fuzzy_similarity(label, primary_label(base_node))
            if score > best_score:
                best_score = score
                best_id = base_node.id
        if best_id and best_score >= fuzzy_threshold:
            id_map[node.id] = best_id

    return id_map


def rewrite_graph_node_ids(graph: ContextGraph, id_map: dict[str, str]) -> ContextGraph:
    """Clona el grafo remapeando ids de nodos y aristas."""
    if not id_map:
        return graph

    remapped_nodes: dict[str, GraphNode] = {}
    for node in graph.nodes:
        new_id = id_map.get(node.id, node.id)
        if new_id in remapped_nodes:
            existing = remapped_nodes[new_id]
            refs = set(existing.source_refs) | set(node.source_refs)
            existing.source_refs = sorted(refs)
            if not existing.labels and node.labels:
                existing.labels = list(node.labels)
            continue
        remapped_nodes[new_id] = GraphNode(
            id=new_id,
            kind=node.kind,
            labels=list(node.labels),
            properties=dict(node.properties),
            source_refs=list(node.source_refs),
        )

    remapped_edges: list[GraphEdge] = []
    for edge in graph.edges:
        remapped_edges.append(
            GraphEdge(
                from_id=id_map.get(edge.from_id, edge.from_id),
                to_id=id_map.get(edge.to_id, edge.to_id),
                type=edge.type,
                properties=dict(edge.properties),
            )
        )

    from ..level4.builder import _dedupe_edges

    return ContextGraph(
        nodes=list(remapped_nodes.values()),
        edges=_dedupe_edges(remapped_edges),
        orphans=list(graph.orphans),
        schema_version=graph.schema_version,
        original_tokens=graph.original_tokens,
        optimized_tokens=graph.optimized_tokens,
        internal_tokens=graph.internal_tokens,
        query_context=graph.query_context,
        max_hops=graph.max_hops,
        include_orphans=graph.include_orphans,
        active_nodes=[
            GraphNode(
                id=id_map.get(node.id, node.id),
                kind=node.kind,
                labels=list(node.labels),
                properties=dict(node.properties),
                source_refs=list(node.source_refs),
            )
            for node in (graph.active_nodes or [])
        ]
        if graph.active_nodes
        else None,
        active_edges=[
            GraphEdge(
                from_id=id_map.get(edge.from_id, edge.from_id),
                to_id=id_map.get(edge.to_id, edge.to_id),
                type=edge.type,
                properties=dict(edge.properties),
            )
            for edge in (graph.active_edges or [])
        ]
        if graph.active_edges
        else None,
    )


def link_incoming_entities(
    base: ContextGraph,
    incoming: ContextGraph,
    *,
    alias_map: dict[str, str] | None = None,
    fuzzy_threshold: float | None = DEFAULT_FUZZY_THRESHOLD,
) -> ContextGraph:
    if fuzzy_threshold is None or fuzzy_threshold <= 0:
        return incoming
    id_map = compute_entity_id_map(
        base,
        incoming,
        alias_map=alias_map,
        fuzzy_threshold=fuzzy_threshold,
    )
    return rewrite_graph_node_ids(incoming, id_map)
