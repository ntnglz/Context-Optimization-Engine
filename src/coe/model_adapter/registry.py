"""Registro y resolución de adaptadores por ``target_model``."""

from __future__ import annotations

from .adapters import DefaultAdapter, MistralAdapter, OpenAIAdapter
from .base import ModelAdapter

_ADAPTERS: dict[str, ModelAdapter] = {
    "default": DefaultAdapter(),
    "mistral": MistralAdapter(),
    "openai": OpenAIAdapter(),
}

_MODEL_PREFIXES: tuple[tuple[str, str], ...] = (
    ("mistral", "mistral"),
    ("mixtral", "mistral"),
    ("codestral", "mistral"),
    ("openai", "openai"),
    ("gpt-", "openai"),
    ("gpt4", "openai"),
    ("gpt3", "openai"),
    ("o1-", "openai"),
    ("o1", "openai"),
    ("o3-", "openai"),
    ("o3", "openai"),
    ("chatgpt", "openai"),
)


def get_adapter(adapter_id: str) -> ModelAdapter:
    try:
        return _ADAPTERS[adapter_id]
    except KeyError as exc:
        raise ValueError(f"Unknown model adapter: {adapter_id!r}") from exc


def resolve_adapter_id(target_model: str | None) -> str | None:
    """Resuelve nombre de modelo (p. ej. ``mistral-large``) a id de adaptador."""
    if not target_model or not str(target_model).strip():
        return None
    key = str(target_model).strip().lower()
    if key in _ADAPTERS:
        return key
    for prefix, adapter_id in _MODEL_PREFIXES:
        if key.startswith(prefix) or prefix in key:
            return adapter_id
    return "default"


def adapt_for_model(text: str, target_model: str | None) -> tuple[str, str | None]:
    """Aplica adaptador; devuelve ``(texto, adapter_id)``."""
    adapter_id = resolve_adapter_id(target_model)
    if adapter_id is None:
        return text, None
    adapted = get_adapter(adapter_id).adapt(text, target_model or "")
    return adapted, adapter_id
