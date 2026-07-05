"""Serialización N3 — prosa, debug y borrador CIR."""

from __future__ import annotations

from ..models import SharedFact, StructuredContext, StructuredEntity, StructuredRelation

_COMPANY_PHRASE = {
    "en": "works at {company}",
    "es": "trabaja en {company}",
    "zh": "在{company}工作",
}

_KNOWS_PHRASE = {
    "en": "knows {target}",
    "es": "conoce a {target}",
    "zh": "认识{target}",
}

_CONJUNCTION = {
    "en": {"pair": " and ", "list": ", "},
    "es": {"pair": " y ", "list": ", "},
    "zh": {"pair": "，", "list": "，"},
}


def render_structured_prose(
    result: StructuredContext,
    *,
    locale: str | None = "en",
) -> str:
    loc = (locale or "en").split("-")[0].lower()
    sections: list[str] = []

    if result.global_facts:
        sections.append(_render_global_facts(result.global_facts))
        sections.append("")

    for entity in result.entities:
        sections.append(_render_entity_prose(entity, result=result, locale=loc))

    for line in result.unparsed:
        sections.append(line)

    return "\n".join(part for part in sections if part).rstrip() + "\n"


def _render_global_facts(facts: list[SharedFact]) -> str:
    lines = [fact.canonical_line.strip() for fact in facts if fact.canonical_line.strip()]
    return "\n".join(lines)


def _render_entity_prose(
    entity: StructuredEntity,
    *,
    result: StructuredContext,
    locale: str,
) -> str:
    loc = locale if locale in _COMPANY_PHRASE else "en"
    conj = _CONJUNCTION[loc]
    parts: list[str] = []

    for rel in entity.relations:
        if rel.type == "company" and rel.value:
            parts.append(_COMPANY_PHRASE[loc].format(company=rel.value))
        elif rel.type == "knows" and rel.target:
            target_name = _target_display_name(result, rel.target)
            parts.append(_KNOWS_PHRASE[loc].format(target=target_name))
        elif rel.type == "action" and rel.value:
            parts.append(rel.value)

    if not parts:
        return f"{entity.name}."

    if len(parts) == 1:
        return f"{entity.name} {parts[0]}."

    head = f"{entity.name} {parts[0]}"
    if len(parts) == 2:
        return f"{head}{conj['pair']}{parts[1]}."

    middle = conj["list"].join(parts[1:-1])
    return f"{head}{conj['list']}{middle}{conj['pair']}{parts[-1]}."


def _target_display_name(result: StructuredContext, target_id: str) -> str:
    for entity in result.entities:
        if entity.id == target_id:
            return entity.name
    return " ".join(p[:1].upper() + p[1:] for p in target_id.replace("_", " ").split())


def render_structured_debug(result: StructuredContext) -> str:
    sections: list[str] = []
    for entity in result.entities:
        sections.append(f"entity:{entity.id} ({entity.name})")
        for rel in entity.relations:
            if rel.type == "knows" and rel.target:
                sections.append(f"  knows->{rel.target}")
            elif rel.value is not None:
                sections.append(f"  {rel.type}={rel.value}")
            else:
                sections.append(f"  {rel.type}")
        sections.append("")

    for line in result.unparsed:
        sections.append(f"unparsed: {line}")

    return "\n".join(sections).rstrip() + "\n"


def structured_to_cir_draft(result: StructuredContext) -> dict:
    return {
        "schema_version": result.schema_version,
        "entities": [
            {
                "id": entity.id,
                "name": entity.name,
                "relations": [
                    {
                        "type": rel.type,
                        "value": rel.value,
                        "target": rel.target,
                    }
                    for rel in entity.relations
                ],
            }
            for entity in result.entities
        ],
        "global_facts": [fact.to_compact() for fact in result.global_facts],
        "unparsed": list(result.unparsed),
    }
