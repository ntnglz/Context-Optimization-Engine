"""Modelos de datos compartidos de COE."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


def estimate_tokens(text: str) -> int:
    """Estimación rápida de tokens (~4 chars/token en texto mixto)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


@dataclass
class ContextBlock:
    """Fragmento de contexto con identificador estable."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def token_count(self) -> int:
        return estimate_tokens(self.content)


@dataclass
class SharedFact:
    """Hecho repetido extraído a representación compartida."""

    canonical_line: str
    normalized_key: str
    source_ids: list[str] = field(default_factory=list)

    def to_compact(self) -> str:
        """Formato clave=valor si la línea usa ':', si no la línea literal."""
        if ":" in self.canonical_line:
            key, _, value = self.canonical_line.partition(":")
            return f"{key.strip()}={value.strip()}"
        return self.canonical_line.strip()


@dataclass
class DeduplicationResult:
    """Resultado del optimizador Nivel 1."""

    shared_facts: list[SharedFact]
    unique_blocks: list[ContextBlock]
    original_tokens: int
    optimized_tokens: int

    @property
    def compression_ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.optimized_tokens / self.original_tokens)

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.optimized_tokens

    def render(self) -> str:
        """Alias legacy de ``render_compact()``."""
        return self.render_compact()

    def render_compact(self) -> str:
        from .level1.render import render_deduplication

        if not self.shared_facts and not any(b.content.strip() for b in self.unique_blocks):
            return ""
        if not self.shared_facts:
            from .renderer import render_raw_context

            return render_raw_context(self.unique_blocks)
        return render_deduplication(self)

    def render_prose(self, *, locale: str | None = "en") -> str:
        from .renderer import render_n1_prose

        return render_n1_prose(self, locale=locale)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shared_facts": [
                {
                    "compact": fact.to_compact(),
                    "canonical_line": fact.canonical_line,
                    "source_ids": fact.source_ids,
                }
                for fact in self.shared_facts
            ],
            "unique_blocks": [
                {"id": block.id, "content": block.content} for block in self.unique_blocks
            ],
            "original_tokens": self.original_tokens,
            "optimized_tokens": self.optimized_tokens,
            "compression_ratio": round(self.compression_ratio, 4),
            "tokens_saved": self.tokens_saved,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class EntityRecord:
    """Entidad factorizada con atributos y acciones."""

    name: str
    attributes: dict[str, str] = field(default_factory=dict)
    actions: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)


@dataclass
class FactorizationResult:
    """Resultado del optimizador Nivel 2."""

    entities: list[EntityRecord]
    unparsed: list[str]
    shared_facts: list[SharedFact]
    original_tokens: int
    optimized_tokens: int

    @property
    def compression_ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.optimized_tokens / self.original_tokens)

    def render_prose(self, *, locale: str | None = "en") -> str:
        from .level2.render import render_factorization_prose

        return render_factorization_prose(self, locale=locale)

    def render_structured(self) -> str:
        from .level2.render import render_factorization_structured

        return render_factorization_structured(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": [
                {
                    "name": e.name,
                    "attributes": dict(e.attributes),
                    "actions": list(e.actions),
                    "source_refs": list(e.source_refs),
                }
                for e in self.entities
            ],
            "unparsed": list(self.unparsed),
            "shared_facts": [fact.to_compact() for fact in self.shared_facts],
            "original_tokens": self.original_tokens,
            "optimized_tokens": self.optimized_tokens,
            "compression_ratio": round(self.compression_ratio, 4),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class StructuredRelation:
    """Relación tipada entre entidades (N3)."""

    type: str
    value: str | None = None
    target: str | None = None


@dataclass
class StructuredEntity:
    """Entidad con relaciones en StructuredContext."""

    id: str
    name: str
    relations: list[StructuredRelation] = field(default_factory=list)


SCHEMA_VERSION = "0.1"


@dataclass
class StructuredContext:
    """Resultado del optimizador Nivel 3."""

    entities: list[StructuredEntity]
    global_facts: list[SharedFact]
    unparsed: list[str]
    schema_version: str
    original_tokens: int
    optimized_tokens: int

    @property
    def compression_ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.optimized_tokens / self.original_tokens)

    def render_prose(self, *, locale: str | None = "en") -> str:
        from .level3.render import render_structured_prose

        return render_structured_prose(self, locale=locale)

    def render_debug(self) -> str:
        from .level3.render import render_structured_debug

        return render_structured_debug(self)

    def to_cir_draft(self) -> dict[str, Any]:
        from .level3.render import structured_to_cir_draft

        return structured_to_cir_draft(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "entities": [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "relations": [
                        {
                            "type": rel.type,
                            "value": rel.value,
                            "target": rel.target,
                        }
                        for rel in entity.relations
                    ],
                }
                for entity in self.entities
            ],
            "global_facts": [fact.to_compact() for fact in self.global_facts],
            "unparsed": list(self.unparsed),
            "original_tokens": self.original_tokens,
            "optimized_tokens": self.optimized_tokens,
            "compression_ratio": round(self.compression_ratio, 4),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


GRAPH_SCHEMA_VERSION = "0.1"


@dataclass
class GraphNode:
    """Nodo del grafo N4."""

    id: str
    kind: str
    labels: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    source_refs: list[str] = field(default_factory=list)


@dataclass
class GraphEdge:
    """Arista tipada del grafo N4."""

    from_id: str
    to_id: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphOrphan:
    """Texto no graficable con trazabilidad."""

    text: str
    source_refs: list[str] = field(default_factory=list)


@dataclass
class GraphComplexity:
    node_count: int
    edge_count: int
    orphan_count: int


@dataclass
class ContextGraph:
    """Resultado del optimizador Nivel 4."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    orphans: list[GraphOrphan]
    schema_version: str
    original_tokens: int
    optimized_tokens: int = 0
    internal_tokens: int = 0
    active_nodes: list[GraphNode] | None = None
    active_edges: list[GraphEdge] | None = None
    query_context: str | None = None
    max_hops: int = 2
    include_orphans: bool = True

    @property
    def complexity(self) -> GraphComplexity:
        from .level4.builder import graph_complexity

        return graph_complexity(self)

    @property
    def internal_ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.internal_tokens / self.original_tokens)

    @property
    def prose_ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.optimized_tokens / self.original_tokens)

    def render_prose(self, *, locale: str | None = "en") -> str:
        from .level4.render import render_graph_prose

        return render_graph_prose(
            self,
            locale=locale,
            include_orphans=self.include_orphans,
        )

    def serialize_internal(self) -> str:
        from .level4.render import serialize_graph_internal

        return serialize_graph_internal(self)

    def to_dict(self) -> dict[str, Any]:
        active_nodes = self.active_nodes or self.nodes
        active_edges = self.active_edges or self.edges
        complexity = self.complexity
        return {
            "schema_version": self.schema_version,
            "nodes": [
                {
                    "id": node.id,
                    "kind": node.kind,
                    "labels": list(node.labels),
                    "properties": dict(node.properties),
                    "source_refs": list(node.source_refs),
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "from": edge.from_id,
                    "to": edge.to_id,
                    "type": edge.type,
                    "properties": dict(edge.properties),
                }
                for edge in self.edges
            ],
            "orphans": [
                {"text": orphan.text, "source_refs": list(orphan.source_refs)}
                for orphan in self.orphans
            ],
            "active_node_ids": [node.id for node in active_nodes],
            "active_edge_count": len(active_edges),
            "query_context": self.query_context,
            "max_hops": self.max_hops,
            "include_orphans": self.include_orphans,
            "complexity": {
                "node_count": complexity.node_count,
                "edge_count": complexity.edge_count,
                "orphan_count": complexity.orphan_count,
            },
            "original_tokens": self.original_tokens,
            "optimized_tokens": self.optimized_tokens,
            "internal_tokens": self.internal_tokens,
            "internal_ratio": round(self.internal_ratio, 4),
            "prose_ratio": round(self.prose_ratio, 4),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextGraph:
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
        return cls(
            nodes=nodes,
            edges=edges,
            orphans=orphans,
            schema_version=data.get("schema_version") or GRAPH_SCHEMA_VERSION,
            original_tokens=int(data.get("original_tokens") or 0),
            optimized_tokens=int(data.get("optimized_tokens") or 0),
            internal_tokens=int(data.get("internal_tokens") or 0),
            active_nodes=active_nodes,
            active_edges=active_edges,
            query_context=data.get("query_context"),
            max_hops=int(data.get("max_hops") or 2),
            include_orphans=bool(data.get("include_orphans", True)),
        )
