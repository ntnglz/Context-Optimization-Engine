"""Context Optimization Engine — optimización de contexto para LLM."""

from .gateway import optimize_context, OptimizeResult, OptimizationMetrics
from .level5 import StateView, update_semantic_state
from .models import ContextBlock, DeduplicationResult, FactorizationResult, SharedFact

__all__ = [
    "ContextBlock",
    "DeduplicationResult",
    "FactorizationResult",
    "SharedFact",
    "StateView",
    "optimize_context",
    "OptimizeResult",
    "OptimizationMetrics",
    "update_semantic_state",
]
