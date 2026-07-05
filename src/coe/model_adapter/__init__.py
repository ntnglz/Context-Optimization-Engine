"""Model Adapter — formato post-renderer según modelo destino."""

from .base import ModelAdapter
from .registry import adapt_for_model, get_adapter, resolve_adapter_id

__all__ = [
    "ModelAdapter",
    "adapt_for_model",
    "get_adapter",
    "resolve_adapter_id",
]
