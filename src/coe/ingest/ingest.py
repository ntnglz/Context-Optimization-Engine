"""API principal de Context Ingest."""

from __future__ import annotations

from typing import Any

from ..models import ContextBlock
from .normalizer import normalize_blocks
from .types import (
    ContextBundle,
    IngestOptions,
    IngestResult,
    raw_block_to_context_block,
)


def ingest_context(
    raw_blocks: list[dict[str, Any]],
    *,
    target_lang: str | None = None,
    locale: str | None = None,
    query_context: str | None = None,
    response_lang: str | None = None,
    session_id: str | None = None,
    options: IngestOptions | None = None,
) -> IngestResult:
    """
    Convierte bloques crudos en un ``ContextBundle`` normalizado.

    Asigna ``id``/``source_type``, aplica normalizer v1 (CRLF, fences metadata)
    y conserva el orden de entrada.
    """
    if not raw_blocks:
        raise ValueError("raw_blocks must not be empty")

    warnings: list[str] = []
    blocks: list[ContextBlock] = []
    for index, raw in enumerate(raw_blocks):
        try:
            blocks.append(raw_block_to_context_block(raw, index=index))
        except ValueError as exc:
            raise ValueError(f"invalid raw block at index {index}: {exc}") from exc

    resolved_locale = locale or target_lang or "en"
    blocks = normalize_blocks(blocks, locale=resolved_locale)

    bundle = ContextBundle(
        blocks=blocks,
        target_lang=target_lang,
        locale=resolved_locale,
        query_context=query_context,
        response_lang=response_lang,
        session_id=session_id,
        options=options or IngestOptions(),
    )
    return IngestResult(bundle=bundle, warnings=warnings)
