"""CIR v1.0 envelope — serialización del grafo N4+ para N5 y herramientas."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from ..models import ContextGraph, GraphEdge, GraphNode, GraphOrphan

CIR_VERSION = "1.0"


class CIRNodeKind(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    CONCEPT = "concept"
    DOCUMENT = "document"
    CHUNK = "chunk"


class CIREdgeType(StrEnum):
    COMPANY = "company"
    KNOWS = "knows"
    ACTION = "action"
    CONTAINS = "contains"
    REFERENCE = "reference"


def graph_core_to_dict(graph: ContextGraph) -> dict[str, Any]:
    """Núcleo CIR: solo nodes, edges, orphans (sin métricas ni vista)."""
    return {
        "nodes": [
            {
                "id": node.id,
                "kind": node.kind,
                "labels": list(node.labels),
                "properties": dict(node.properties),
                "source_refs": list(node.source_refs),
            }
            for node in graph.nodes
        ],
        "edges": [
            {
                "from": edge.from_id,
                "to": edge.to_id,
                "type": edge.type,
                "properties": dict(edge.properties),
            }
            for edge in graph.edges
        ],
        "orphans": [
            {"text": orphan.text, "source_refs": list(orphan.source_refs)}
            for orphan in graph.orphans
        ],
    }


def envelope_from_context_graph(graph: ContextGraph) -> dict[str, Any]:
    """Envelope CIR v1.0 para persistencia N5 y logs."""
    active_nodes = graph.active_nodes or graph.nodes
    return {
        "cir_version": CIR_VERSION,
        "graph": graph_core_to_dict(graph),
        "view": {
            "active_node_ids": [node.id for node in active_nodes],
        },
        "slice": {
            "query_context": graph.query_context,
            "max_hops": graph.max_hops,
            "include_orphans": graph.include_orphans,
        },
        "metrics": {
            "original_tokens": graph.original_tokens,
            "optimized_tokens": graph.optimized_tokens,
            "internal_tokens": graph.internal_tokens,
        },
    }


def _is_envelope(data: dict[str, Any]) -> bool:
    return "cir_version" in data and "graph" in data


def context_graph_from_envelope(data: dict[str, Any]) -> ContextGraph:
    """Reconstruye ``ContextGraph`` desde envelope CIR o dict plano legacy."""
    if _is_envelope(data):
        core = dict(data["graph"])
        view = data.get("view") or {}
        slice_data = data.get("slice") or {}
        metrics = data.get("metrics") or {}
        flat: dict[str, Any] = {
            "schema_version": data.get("cir_version", CIR_VERSION),
            **core,
            "active_node_ids": view.get("active_node_ids"),
            "query_context": slice_data.get("query_context"),
            "max_hops": slice_data.get("max_hops", 2),
            "include_orphans": slice_data.get("include_orphans", True),
            "original_tokens": metrics.get("original_tokens", 0),
            "optimized_tokens": metrics.get("optimized_tokens", 0),
            "internal_tokens": metrics.get("internal_tokens", 0),
        }
        graph = _context_graph_from_flat(flat)
        migrate_legacy_actions(graph)
        return graph

    graph = _context_graph_from_flat(data)
    migrate_legacy_actions(graph)
    return graph


def _context_graph_from_flat(data: dict[str, Any]) -> ContextGraph:
    """Parser plano — misma lógica que ``ContextGraph.from_dict`` sin recursión."""
    nodes = [
        GraphNode(
            id=node["id"],
            kind=node["kind"],
            labels=list(node.get("labels") or []),
            properties=dict(node.get("properties") or {}),
            source_refs=list(node.get("source_refs") or []),
        )
        for node in data.get("nodes") or []
    ]
    edges = [
        GraphEdge(
            from_id=edge["from"],
            to_id=edge["to"],
            type=edge["type"],
            properties=dict(edge.get("properties") or {}),
        )
        for edge in data.get("edges") or []
    ]
    orphans = [
        GraphOrphan(
            text=orphan["text"],
            source_refs=list(orphan.get("source_refs") or []),
        )
        for orphan in data.get("orphans") or []
    ]
    node_by_id = {node.id: node for node in nodes}
    active_ids = data.get("active_node_ids")
    if active_ids is None:
        active_nodes = None
        active_edges = None
    else:
        active_id_set = set(active_ids)
        active_nodes = [node_by_id[node_id] for node_id in active_ids if node_id in node_by_id]
        active_edges = [
            edge
            for edge in edges
            if edge.from_id in active_id_set and edge.to_id in active_id_set
        ]
    version = data.get("schema_version") or data.get("cir_version") or CIR_VERSION
    return ContextGraph(
        nodes=nodes,
        edges=edges,
        orphans=orphans,
        schema_version=version,
        original_tokens=int(data.get("original_tokens") or 0),
        optimized_tokens=int(data.get("optimized_tokens") or 0),
        internal_tokens=int(data.get("internal_tokens") or 0),
        active_nodes=active_nodes,
        active_edges=active_edges,
        query_context=data.get("query_context"),
        max_hops=int(data.get("max_hops") or 2),
        include_orphans=bool(data.get("include_orphans", True)),
    )


def migrate_legacy_actions(graph: ContextGraph) -> None:
    """Convierte ``properties.actions[]`` (0.1) a aristas ``action`` (1.0)."""
    from ..level4.builder import _action_concept_id, _dedupe_edges

    nodes_by_id = {node.id: node for node in graph.nodes}
    new_edges: list[GraphEdge] = []

    for node in graph.nodes:
        actions = node.properties.pop("actions", None)
        if not actions:
            continue
        for action in actions:
            concept_id = _action_concept_id(action)
            if concept_id not in nodes_by_id:
                concept = GraphNode(
                    id=concept_id,
                    kind=CIRNodeKind.CONCEPT,
                    labels=[action],
                    properties={"canonical_line": action},
                    source_refs=list(node.source_refs),
                )
                nodes_by_id[concept_id] = concept
                graph.nodes.append(concept)
            new_edges.append(
                GraphEdge(
                    from_id=node.id,
                    to_id=concept_id,
                    type=CIREdgeType.ACTION,
                    properties={"value": action},
                )
            )

    if new_edges:
        graph.edges = _dedupe_edges([*graph.edges, *new_edges])
    if graph.schema_version == "0.1":
        graph.schema_version = CIR_VERSION
