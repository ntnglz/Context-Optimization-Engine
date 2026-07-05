"""Normalizer — preparación de contenido pre-L0/N1."""

from __future__ import annotations

from ..models import ContextBlock


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _content_has_code_fence(text: str) -> bool:
    return "```" in text


def normalize_block_content(content: str) -> str:
    """Colapsa finales de línea; no traduce ni segmenta."""
    return normalize_line_endings(content)


def normalize_blocks(blocks: list[ContextBlock]) -> list[ContextBlock]:
    normalized: list[ContextBlock] = []
    for block in blocks:
        content = normalize_block_content(block.content)
        metadata = dict(block.metadata)
        if _content_has_code_fence(content):
            metadata.setdefault("has_code_fence", True)
        normalized.append(
            ContextBlock(
                id=block.id,
                content=content,
                source_type=block.source_type,
                detected_lang=block.detected_lang,
                token_estimate=block.token_estimate,
                metadata=metadata,
            )
        )
    return normalized
