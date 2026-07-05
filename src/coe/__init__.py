"""Context Optimization Engine — optimización de contexto para LLM."""

from .gateway import optimize_context, OptimizeResult, OptimizationMetrics
from .ingest import ContextBundle, IngestOptions, IngestResult, IngestTrace, ingest_context, normalize_language
from .level5 import StateView, update_semantic_state
from .models import ContextBlock, DeduplicationResult, FactorizationResult, SharedFact, StructuredContext, ContextGraph

__all__ = [
    "ContextBlock",
    "ContextBundle",
    "DeduplicationResult",
    "FactorizationResult",
    "IngestOptions",
    "IngestResult",
    "IngestTrace",
    "SharedFact",
    "StateView",
    "StructuredContext",
    "ContextGraph",
    "ingest_context",
    "normalize_language",
    "optimize_context",
    "OptimizeResult",
    "OptimizationMetrics",
    "update_semantic_state",
]
