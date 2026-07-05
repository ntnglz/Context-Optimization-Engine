"""Similitud semántica entre respuestas A y B (comprehension_similarity)."""

from __future__ import annotations

import os
import re
from collections import Counter
from typing import Literal

DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_BACKEND = "simple"

EmbeddingBackend = Literal["auto", "simple", "sentence_transformers"]

_model_cache: dict[str, object] = {}


def resolve_backend(backend: EmbeddingBackend | None = None) -> str:
    if backend and backend != "auto":
        return backend
    env = os.environ.get("COE_EMBEDDING_BACKEND", DEFAULT_BACKEND)
    if env == "auto":
        return DEFAULT_BACKEND
    return env


def comprehension_similarity(
    text_a: str,
    text_b: str,
    *,
    backend: EmbeddingBackend | None = None,
    model_name: str = DEFAULT_MODEL,
) -> float:
    """Similitud coseno en [0, 1] entre respuesta A y respuesta B."""
    resolved = resolve_backend(backend)
    if resolved == "sentence_transformers":
        try:
            return _sentence_transformer_similarity(text_a, text_b, model_name)
        except ImportError:
            return _simple_similarity(text_a, text_b)
    return _simple_similarity(text_a, text_b)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold())


def _simple_similarity(text_a: str, text_b: str) -> float:
    a = text_a.strip()
    b = text_b.strip()
    if not a and not b:
        return 1.0
    if a == b:
        return 1.0

    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0

    counter_a = Counter(tokens_a)
    counter_b = Counter(tokens_b)
    keys = set(counter_a) | set(counter_b)
    dot = sum(counter_a[k] * counter_b[k] for k in keys)
    norm_a = sum(v * v for v in counter_a.values()) ** 0.5
    norm_b = sum(v * v for v in counter_b.values()) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def _sentence_transformer_similarity(
    text_a: str,
    text_b: str,
    model_name: str,
) -> float:
    if model_name not in _model_cache:
        from sentence_transformers import SentenceTransformer

        _model_cache[model_name] = SentenceTransformer(model_name)
    model = _model_cache[model_name]
    embeddings = model.encode([text_a, text_b], normalize_embeddings=True)
    return max(0.0, min(1.0, float(embeddings[0] @ embeddings[1])))
