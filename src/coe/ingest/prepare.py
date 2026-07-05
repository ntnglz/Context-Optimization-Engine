"""Preparación de bloques por ``source_type`` (structured, code, glossary)."""

from __future__ import annotations

from ..models import ContextBlock
from .structured import detect_structured_format, flatten_structured_content


def prepare_block(block: ContextBlock) -> ContextBlock:
    """Normaliza contenido según matriz ingest (Fase 18)."""
    metadata = dict(block.metadata)
    content = block.content

    if block.source_type == "glossary":
        metadata.setdefault("preserve_lang", True)

    if block.source_type == "structured":
        fmt = metadata.get("structured_format")
        detected = detect_structured_format(content, hint=fmt)
        metadata.setdefault("structured_format", detected)
        if detected != "plain":
            content = flatten_structured_content(content, fmt=detected)

    if block.source_type == "code":
        metadata.setdefault("code_dedup", True)

    if content == block.content and metadata == block.metadata:
        return block

    return ContextBlock(
        id=block.id,
        content=content,
        source_type=block.source_type,
        detected_lang=block.detected_lang,
        token_estimate=block.token_estimate,
        metadata=metadata,
    )


def prepare_blocks(blocks: list[ContextBlock]) -> list[ContextBlock]:
    return [prepare_block(block) for block in blocks]
