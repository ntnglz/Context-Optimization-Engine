"""CIR v1.0 — contrato interno del grafo semántico."""

from .envelope import (
    CIR_VERSION,
    CIREdgeType,
    CIRNodeKind,
    context_graph_from_envelope,
    envelope_from_context_graph,
    graph_core_to_dict,
)

__all__ = [
    "CIR_VERSION",
    "CIRNodeKind",
    "CIREdgeType",
    "context_graph_from_envelope",
    "envelope_from_context_graph",
    "graph_core_to_dict",
]
