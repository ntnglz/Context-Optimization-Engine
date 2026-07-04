"""Serialización de resultados Nivel 1 para consumo por LLM."""

from __future__ import annotations

from ..models import DeduplicationResult


def render_deduplication(result: DeduplicationResult) -> str:
    """Genera representación compacta con hechos compartidos y bloques únicos."""
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
