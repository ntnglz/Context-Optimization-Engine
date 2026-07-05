"""Context Optimization Engine — optimización de contexto para LLM."""

from .gateway import optimize_context, OptimizeResult, OptimizationMetrics
from .models import ContextBlock, DeduplicationResult, SharedFact

__all__ = [
    "ContextBlock",
    "DeduplicationResult",
    "SharedFact",
    "optimize_context",
    "OptimizeResult",
    "OptimizationMetrics",
]
