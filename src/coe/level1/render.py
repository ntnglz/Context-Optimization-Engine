"""Serialización de resultados Nivel 1."""

from __future__ import annotations

from ..models import DeduplicationResult
from ..renderer.templates import get_templates


def render_deduplication(result: DeduplicationResult) -> str:
    """Representación compacta con hechos compartidos y bloques únicos (interno)."""
    sections: list[str] = []

    for fact in result.shared_facts:
        sections.append(fact.to_compact())
        refs = ", ".join(fact.source_ids)
        sections.append(f"Referencias: {refs}")
        sections.append("")

    for block in result.unique_blocks:
        content = block.content.strip()
        if not content:
            continue
        sections.append(f"[{block.id}]")
        sections.append(content)
        sections.append("")

    return "\n".join(sections).rstrip() + "\n"


def render_deduplication_prose(
    result: DeduplicationResult,
    *,
    locale: str | None = "en",
) -> str:
    """Proyección en lenguaje natural para el LLM."""
    tpl = get_templates(locale)
    sections: list[str] = []

    if result.shared_facts:
        sections.append(tpl["shared_intro"])
        for fact in result.shared_facts:
            refs = ", ".join(fact.source_ids)
            line = fact.canonical_line.strip()
            sections.append(tpl["shared_item"].format(line=line, refs=refs))
        sections.append("")

    unique_parts: list[str] = []
    for block in result.unique_blocks:
        content = block.content.strip()
        if not content:
            continue
        unique_parts.append(tpl["unique_block"].format(id=block.id))
        unique_parts.append(content)
        unique_parts.append("")

    if unique_parts:
        sections.append(tpl["unique_intro"])
        sections.extend(unique_parts)

    return "\n".join(sections).rstrip() + "\n"

