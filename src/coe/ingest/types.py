"""Tipos de Context Ingest — bundle, opciones y source_type."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import ContextBlock

SOURCE_TYPES = frozenset(
    {"prose", "history", "rag", "tool", "structured", "code", "glossary", "memory"}
)
DEFAULT_SOURCE_TYPE = "prose"


@dataclass
class IngestOptions:
    max_context_tokens: int | None = None
    cite_sources: bool = False
    section_delimiters: bool = True
    include_pending_turn: bool = False
    max_commits: int | None = None
    target_model: str | None = None
    session_ttl_hours: float | None = None
    fuzzy_link_threshold: float | None = None
    state_store_backend: str | None = None
    state_store_path: str | None = None


@dataclass
class ContextBundle:
    blocks: list[ContextBlock]
    target_lang: str | None = None
    locale: str | None = None
    query_context: str | None = None
    response_lang: str | None = None
    session_id: str | None = None
    options: IngestOptions = field(default_factory=IngestOptions)


@dataclass
class IngestResult:
    bundle: ContextBundle
    warnings: list[str] = field(default_factory=list)


def coerce_source_type(value: str | None) -> str:
    if not value:
        return DEFAULT_SOURCE_TYPE
    normalized = value.strip().lower()
    if normalized not in SOURCE_TYPES:
        raise ValueError(f"Unknown source_type: {value!r}")
    return normalized


def raw_block_to_context_block(raw: dict[str, Any], *, index: int) -> ContextBlock:
    """Convierte un dict de entrada cruda en ``ContextBlock``."""
    content = raw.get("content")
    if content is None:
        content = raw.get("text")
    if content is None:
        raise ValueError(f"raw block {index}: missing content/text")

    block_id = raw.get("id") or f"block-{index + 1}"
    source_type = coerce_source_type(raw.get("source_type"))

    metadata = dict(raw.get("metadata") or {})
    if "uri" in raw and raw["uri"] is not None:
        metadata.setdefault("source_uri", raw["uri"])
    if "source_uri" in raw and raw["source_uri"] is not None:
        metadata.setdefault("source_uri", raw["source_uri"])
    if "source_label" in raw and raw["source_label"] is not None:
        metadata.setdefault("source_label", raw["source_label"])
    if "preserve_lang" in raw:
        metadata["preserve_lang"] = bool(raw["preserve_lang"])
    if "entity_aliases" in raw:
        metadata["entity_aliases"] = list(raw["entity_aliases"])
    if "levels_override" in raw and raw["levels_override"] is not None:
        metadata["levels_override"] = [int(level) for level in raw["levels_override"]]

    token_estimate = raw.get("token_estimate")
    if token_estimate is not None:
        token_estimate = int(token_estimate)

    return ContextBlock(
        id=str(block_id),
        content=str(content),
        source_type=source_type,
        detected_lang=raw.get("detected_lang"),
        token_estimate=token_estimate,
        metadata=metadata,
    )
