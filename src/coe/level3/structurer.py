"""Nivel 3 — estructuración relacional sobre factorización N2."""

from __future__ import annotations

from ..models import (
    SCHEMA_VERSION,
    EntityRecord,
    FactorizationResult,
    StructuredContext,
    StructuredEntity,
    StructuredRelation,
    estimate_tokens,
)
from .patterns import parse_knows_line
from .render import render_structured_prose


def structure_context(
    source: FactorizationResult,
    *,
    locale: str | None = "en",
) -> StructuredContext:
    """Convierte ``FactorizationResult`` en ``StructuredContext`` con relaciones tipadas."""
    loc = locale or "en"
    entities: dict[str, StructuredEntity] = {}

    for record in source.entities:
        entity = _entity_from_record(record)
        entities[entity.id] = entity

    remaining_unparsed: list[str] = []
    for line in source.unparsed:
        parsed = parse_knows_line(line, locale=loc)
        if parsed is None:
            remaining_unparsed.append(line)
            continue

        subject = _ensure_entity(entities, parsed.entity)
        target = _ensure_entity(entities, parsed.target)
        _add_relation(subject, StructuredRelation(type="knows", target=target.id))

    for entity in entities.values():
        entity.relations = _dedupe_relations(entity.relations)

    structured = StructuredContext(
        entities=sorted(entities.values(), key=lambda e: e.name),
        global_facts=list(source.shared_facts),
        unparsed=remaining_unparsed,
        schema_version=SCHEMA_VERSION,
        original_tokens=source.original_tokens,
        optimized_tokens=0,
    )
    prose = render_structured_prose(structured, locale=loc)
    structured.optimized_tokens = estimate_tokens(prose)
    return structured


def _entity_id(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _ensure_entity(entities: dict[str, StructuredEntity], name: str) -> StructuredEntity:
    entity_id = _entity_id(name)
    if entity_id not in entities:
        entities[entity_id] = StructuredEntity(id=entity_id, name=name)
    return entities[entity_id]


def _entity_from_record(record: EntityRecord) -> StructuredEntity:
    entity_id = _entity_id(record.name)
    relations: list[StructuredRelation] = []

    company = record.attributes.get("company")
    if company:
        relations.append(StructuredRelation(type="company", value=company))

    for action in record.actions:
        relations.append(StructuredRelation(type="action", value=action))

    return StructuredEntity(id=entity_id, name=record.name, relations=relations)


def _add_relation(entity: StructuredEntity, relation: StructuredRelation) -> None:
    if relation.type == "knows" and relation.target:
        if any(r.type == "knows" and r.target == relation.target for r in entity.relations):
            return
    elif relation.value is not None:
        if any(r.type == relation.type and r.value == relation.value for r in entity.relations):
            return
    entity.relations.append(relation)


def _dedupe_relations(relations: list[StructuredRelation]) -> list[StructuredRelation]:
    deduped: list[StructuredRelation] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    for rel in relations:
        key = (rel.type, rel.value, rel.target)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(rel)
    return deduped
