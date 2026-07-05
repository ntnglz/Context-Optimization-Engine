"""Renderer — proyección a prosa para el LLM."""

from __future__ import annotations

from ..models import ContextBlock, DeduplicationResult


def render_raw_context(blocks: list[ContextBlock]) -> str:
    """Contexto crudo pre-COE (brazo A de benchmarks)."""
    parts: list[str] = []
    for block in blocks:
        content = block.content.strip()
        if content:
            parts.append(f"[{block.id}]\n{content}")
    return "\n\n".join(parts) + ("\n" if parts else "")


def render_n1_prose(result: DeduplicationResult, *, locale: str | None = "en") -> str:
    """Prosa N1 hacia el LLM."""
    if not result.shared_facts and not any(b.content.strip() for b in result.unique_blocks):
        return ""
    if not result.shared_facts:
        return render_raw_context(result.unique_blocks)
    from ..level1.render import render_deduplication_prose

    return render_deduplication_prose(result, locale=locale)


def render_n1_compact(result: DeduplicationResult) -> str:
    """Representación compacta interna / legacy."""
    if not result.shared_facts and not any(b.content.strip() for b in result.unique_blocks):
        return ""
    if not result.shared_facts:
        return render_raw_context(result.unique_blocks)
    from ..level1.render import render_deduplication

    return render_deduplication(result)
