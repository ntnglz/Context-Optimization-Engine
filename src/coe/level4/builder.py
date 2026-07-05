"""Nivel 4 — materialización StructuredContext → ContextGraph."""

from __future__ import annotations

from ..cir import CIRNodeKind, CIREdgeType
from ..models import (
    GRAPH_SCHEMA_VERSION,
    ContextBlock,
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
    source_blocks: list[ContextBlock] | None = None,
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
            kind=CIRNodeKind.CONCEPT,
            labels=[fact.canonical_line.strip()],
            properties={"canonical_line": fact.canonical_line.strip()},
            source_refs=list(fact.source_ids),
        )

    for entity in structured.entities:
        _materialize_entity(entity, nodes=nodes, edges=edges)

    for line in structured.unparsed:
        orphans.append(GraphOrphan(text=line, source_refs=[]))

    if source_blocks:
        _materialize_rag_blocks(source_blocks, nodes=nodes, edges=edges)

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
            kind=CIRNodeKind.PERSON,
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
                    kind=CIRNodeKind.ORGANIZATION,
                    labels=[rel.value],
                    properties={"name": rel.value},
                    source_refs=[entity.id],
                )
            edges.append(
                GraphEdge(from_id=entity.id, to_id=org_id, type=CIREdgeType.COMPANY)
            )
        elif rel.type == "knows" and rel.target:
            target = nodes.get(rel.target)
            if target is None:
                target_name = rel.target.replace("_", " ").title()
                target = GraphNode(
                    id=rel.target,
                    kind=CIRNodeKind.PERSON,
                    labels=[target_name],
                    properties={},
                    source_refs=[entity.id],
                )
                nodes[rel.target] = target
            edges.append(
                GraphEdge(from_id=entity.id, to_id=rel.target, type=CIREdgeType.KNOWS)
            )
        elif rel.type == "action" and rel.value:
            concept_id = _action_concept_id(rel.value)
            if concept_id not in nodes:
                nodes[concept_id] = GraphNode(
                    id=concept_id,
                    kind=CIRNodeKind.CONCEPT,
                    labels=[rel.value],
                    properties={"canonical_line": rel.value},
                    source_refs=[entity.id],
                )
            edges.append(
                GraphEdge(
                    from_id=entity.id,
                    to_id=concept_id,
                    type=CIREdgeType.ACTION,
                    properties={"value": rel.value},
                )
            )


def _materialize_rag_blocks(
    blocks: list[ContextBlock],
    *,
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
) -> None:
    """Bloques ``source_type=rag`` → nodos ``document`` + ``chunk``."""
    for block in blocks:
        if block.source_type != "rag":
            continue
        doc_id = f"doc_{block.id}"
        label = block.metadata.get("source_label") or block.id
        uri = block.metadata.get("source_uri")
        props: dict = {}
        if uri:
            props["uri"] = uri
        nodes[doc_id] = GraphNode(
            id=doc_id,
            kind=CIRNodeKind.DOCUMENT,
            labels=[str(label)],
            properties=props,
            source_refs=[block.id],
        )
        for idx, line in enumerate(block.content.splitlines()):
            stripped = line.strip()
            if not stripped:
                continue
            chunk_id = f"chunk_{block.id}_{idx}"
            nodes[chunk_id] = GraphNode(
                id=chunk_id,
                kind=CIRNodeKind.CHUNK,
                labels=[stripped],
                properties={"parent_doc": doc_id},
                source_refs=[block.id],
            )
            edges.append(
                GraphEdge(from_id=doc_id, to_id=chunk_id, type=CIREdgeType.CONTAINS)
            )


def _concept_id(fact: SharedFact) -> str:
    slug = fact.canonical_line.strip().lower().replace(" ", "_").replace(":", "")
    return f"concept_{slug[:48]}"


def _action_concept_id(action_text: str) -> str:
    slug = action_text.strip().lower().replace(" ", "_")[:48]
    return f"concept_action_{slug}"


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
