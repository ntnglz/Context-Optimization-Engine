"""Serialización N2 — prosa hacia LLM e interno."""

from __future__ import annotations

from ..models import FactorizationResult, SharedFact


def render_factorization_prose(
    result: FactorizationResult,
    *,
    locale: str | None = "en",
) -> str:
    """Modo ``prose_compact``: sujeto explícito una vez por entidad."""
    _ = locale
    sections: list[str] = []

    if result.shared_facts:
        sections.append(_render_shared_facts(result.shared_facts))
        sections.append("")

    for entity in result.entities:
        sections.append(_render_entity_prose(entity))

    for line in result.unparsed:
        sections.append(line)

    return "\n".join(part for part in sections if part).rstrip() + "\n"


def _render_shared_facts(facts: list[SharedFact]) -> str:
    lines = [fact.canonical_line.strip() for fact in facts if fact.canonical_line.strip()]
    return "\n".join(lines)


def _render_entity_prose(entity) -> str:
    parts: list[str] = []
    company = entity.attributes.get("company")
    if company:
        parts.append(f"works at {company}")
    parts.extend(entity.actions)

    if not parts:
        return f"{entity.name}."

    if len(parts) == 1:
        return f"{entity.name} {parts[0]}."

    head = f"{entity.name} {parts[0]}"
    if len(parts) == 2:
        return f"{head} and {parts[1]}."
    middle = ", ".join(parts[1:-1])
    return f"{head}, {middle}, and {parts[-1]}."


def render_factorization_structured(result: FactorizationResult) -> str:
    """Representación interna ``entity:`` (no hacia LLM)."""
    sections: list[str] = []
    for entity in result.entities:
        sections.append(f"entity:{entity.name}")
        for key, value in sorted(entity.attributes.items()):
            sections.append(f"  {key}={value}")
        for action in entity.actions:
            sections.append(f"  action: {action}")
        refs = ", ".join(entity.source_refs)
        if refs:
            sections.append(f"  refs: {refs}")
        sections.append("")

    for line in result.unparsed:
        sections.append(f"unparsed: {line}")

    return "\n".join(sections).rstrip() + "\n"
