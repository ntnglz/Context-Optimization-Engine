"""Nivel 4 — materialización StructuredContext → ContextGraph."""

from __future__ import annotations

from ..models import (
    GRAPH_SCHEMA_VERSION,
    ContextGraph,
    GraphComplexity,
    GraphEdge,
    GraphNode,
    GraphOrphan,
    SharedFact,
    StructuredContext,
    StructuredEntity,
    estimate_tokens,
)
from .render import graph_to_structured_view, render_graph_prose, serialize_graph_internal
from .slice import apply_query_slice


def build_context_graph(
    structured: StructuredContext,
    *,
    query_context: str | None = None,
    max_hops: int = 2,
    include_orphans: bool = True,
    locale: str | None = "en",
) -> ContextGraph:
    """Materializa ``StructuredContext`` en grafo con invariante cero pérdida."""
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    orphans: list[GraphOrphan] = []

    for fact in structured.global_facts:
        node_id = _concept_id(fact)
        nodes[node_id] = GraphNode(
            id=node_id,
            kind="concept",
            labels=[fact.canonical_line.strip()],
            properties={"canonical_line": fact.canonical_line.strip()},
            source_refs=list(fact.source_ids),
        )

    for entity in structured.entities:
        _materialize_entity(entity, nodes=nodes, edges=edges)

    for line in structured.unparsed:
        orphans.append(GraphOrphan(text=line, source_refs=[]))

    graph = ContextGraph(
        nodes=list(nodes.values()),
        edges=_dedupe_edges(edges),
        orphans=orphans,
        schema_version=GRAPH_SCHEMA_VERSION,
        original_tokens=structured.original_tokens,
        query_context=query_context,
        max_hops=max_hops,
        include_orphans=include_orphans,
    )

    if query_context:
        graph = apply_query_slice(graph, query_context=query_context, max_hops=max_hops)

    loc = locale or "en"
    prose = render_graph_prose(graph, locale=loc, include_orphans=include_orphans)
    internal = serialize_graph_internal(graph)

    graph.optimized_tokens = estimate_tokens(prose)
    graph.internal_tokens = estimate_tokens(internal)
    return graph


def _materialize_entity(
    entity: StructuredEntity,
    *,
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
) -> None:
    person = nodes.get(entity.id)
    if person is None:
        person = GraphNode(
            id=entity.id,
            kind="person",
            labels=[entity.name],
            properties={},
            source_refs=[entity.id],
        )
        nodes[entity.id] = person

    for rel in entity.relations:
        if rel.type == "company" and rel.value:
            org_id = _org_id(rel.value)
            if org_id not in nodes:
                nodes[org_id] = GraphNode(
                    id=org_id,
                    kind="organization",
                    labels=[rel.value],
                    properties={"name": rel.value},
                    source_refs=[entity.id],
                )
            edges.append(GraphEdge(from_id=entity.id, to_id=org_id, type="company"))
        elif rel.type == "knows" and rel.target:
            target = nodes.get(rel.target)
            if target is None:
                target_name = rel.target.replace("_", " ").title()
                target = GraphNode(
                    id=rel.target,
                    kind="person",
                    labels=[target_name],
                    properties={},
                    source_refs=[entity.id],
                )
                nodes[rel.target] = target
            edges.append(GraphEdge(from_id=entity.id, to_id=rel.target, type="knows"))
        elif rel.type == "action" and rel.value:
            actions = list(person.properties.get("actions", []))
            if rel.value not in actions:
                actions.append(rel.value)
            person.properties["actions"] = actions


def _concept_id(fact: SharedFact) -> str:
    slug = fact.canonical_line.strip().lower().replace(" ", "_").replace(":", "")
    return f"concept_{slug[:48]}"


def _org_id(name: str) -> str:
    return f"org_{name.strip().lower().replace(' ', '_')}"


def _dedupe_edges(edges: list[GraphEdge]) -> list[GraphEdge]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[GraphEdge] = []
    for edge in edges:
        key = (edge.from_id, edge.to_id, edge.type)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(edge)
    return deduped


def graph_complexity(graph: ContextGraph) -> GraphComplexity:
    active_nodes = graph.active_nodes or graph.nodes
    active_edges = graph.active_edges or graph.edges
    orphan_count = len(graph.orphans) if graph.include_orphans else 0
    return GraphComplexity(
        node_count=len(active_nodes),
        edge_count=len(active_edges),
        orphan_count=orphan_count,
    )
