"""Serialización N4 — prosa, interno y proyección a StructuredContext."""

from __future__ import annotations

from ..models import (
    ContextGraph,
    GraphEdge,
    GraphNode,
    SCHEMA_VERSION,
    SharedFact,
    StructuredContext,
    StructuredEntity,
    StructuredRelation,
)


def render_graph_prose(
    graph: ContextGraph,
    *,
    locale: str | None = "en",
    include_orphans: bool = True,
) -> str:
    """Proyecta el subgrafo activo a lenguaje natural (reutiliza plantillas N3)."""
    structured = graph_to_structured_view(graph, include_orphans=include_orphans)
    return structured.render_prose(locale=locale)


def graph_to_structured_view(
    graph: ContextGraph,
    *,
    include_orphans: bool = True,
) -> StructuredContext:
    nodes = graph.active_nodes or graph.nodes
    edges = graph.active_edges or graph.edges
    node_by_id = {node.id: node for node in nodes}

    global_facts: list[SharedFact] = []
    entities: list[StructuredEntity] = []

    for node in nodes:
        if node.kind == "concept":
            line = node.properties.get("canonical_line") or (node.labels[0] if node.labels else "")
            if line:
                global_facts.append(
                    SharedFact(
                        canonical_line=line,
                        normalized_key=line.lower(),
                        source_ids=list(node.source_refs),
                    )
                )
        elif node.kind == "person":
            entities.append(_person_to_entity(node, node_by_id=node_by_id, edges=edges))

    unparsed = [orphan.text for orphan in graph.orphans] if include_orphans else []
    for node in nodes:
        if node.kind == "chunk" and node.labels:
            unparsed.append(node.labels[0])
        if node.kind == "term" and node.labels:
            translation = str(node.properties.get("translation") or "").strip()
            if translation:
                unparsed.append(f"{node.labels[0]}: {translation}")
            else:
                unparsed.append(node.labels[0])

    return StructuredContext(
        entities=sorted(entities, key=lambda e: e.name),
        global_facts=global_facts,
        unparsed=unparsed,
        schema_version=SCHEMA_VERSION,
        original_tokens=graph.original_tokens,
        optimized_tokens=graph.optimized_tokens,
    )


def _person_to_entity(
    node: GraphNode,
    *,
    node_by_id: dict[str, GraphNode],
    edges: list[GraphEdge],
) -> StructuredEntity:
    relations: list[StructuredRelation] = []

    for edge in edges:
        if edge.from_id != node.id:
            continue
        if edge.type == "action":
            value = edge.properties.get("value")
            if not value:
                target = node_by_id.get(edge.to_id)
                value = target.labels[0] if target and target.labels else None
            if value:
                relations.append(StructuredRelation(type="action", value=value))
        elif edge.type == "company":
            org = node_by_id.get(edge.to_id)
            company = org.labels[0] if org and org.labels else edge.to_id
            relations.append(StructuredRelation(type="company", value=company))
        elif edge.type == "knows":
            relations.append(StructuredRelation(type="knows", target=edge.to_id))

    name = node.labels[0] if node.labels else node.id
    return StructuredEntity(id=node.id, name=name, relations=relations)


def serialize_graph_internal(graph: ContextGraph) -> str:
    """Representación compacta para logs/métricas (no enviar al LLM)."""
    nodes = graph.active_nodes or graph.nodes
    edges = graph.active_edges or graph.edges
    lines: list[str] = []

    for node in nodes:
        lines.append(f"node:{node.id}:{node.kind}")

    for edge in edges:
        lines.append(f"edge:{edge.from_id}->{edge.to_id}:{edge.type}")

    for orphan in graph.orphans:
        lines.append(f"orphan:{orphan.text}")

    complexity = graph.complexity
    lines.append(
        f"complexity: {{ nodes: {complexity.node_count}, "
        f"edges: {complexity.edge_count}, orphans: {complexity.orphan_count} }}"
    )
    return "\n".join(lines) + "\n"
