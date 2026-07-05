"""Nivel 2 — factorización por entidad (sujeto repetido)."""

from __future__ import annotations

from collections import defaultdict

from ..models import (
    ContextBlock,
    DeduplicationResult,
    EntityRecord,
    FactorizationResult,
    SharedFact,
    estimate_tokens,
)
from .patterns import ParsedStatement, parse_line
from .render import render_factorization_prose


def factorize_context(
    source: DeduplicationResult | list[ContextBlock],
    *,
    locale: str | None = "en",
    min_occurrences: int = 2,
) -> FactorizationResult:
    """
    Agrupa oraciones con la misma entidad como sujeto explícito.

    ``shared_facts`` de N1 no se re-factorizan (passthrough en la salida).
    """
    if min_occurrences < 2:
        raise ValueError("min_occurrences debe ser >= 2")

    if isinstance(source, list):
        dedup = DeduplicationResult(
            shared_facts=[],
            unique_blocks=source,
            original_tokens=0,
            optimized_tokens=0,
        )
    else:
        dedup = source

    loc = locale or "en"
    statements: list[tuple[str, str, ParsedStatement]] = []
    unparsed_lines: list[str] = []

    for block in dedup.unique_blocks:
        for raw_line in block.content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parsed = parse_line(line, locale=loc)
            if parsed is None:
                unparsed_lines.append(line)
            else:
                statements.append((block.id, line, parsed))

    by_entity: dict[str, list[tuple[str, str, ParsedStatement]]] = defaultdict(list)
    for block_id, original, parsed in statements:
        by_entity[parsed.entity].append((block_id, original, parsed))

    entities: list[EntityRecord] = []
    for entity_name in sorted(by_entity):
        items = by_entity[entity_name]
        if len(items) < min_occurrences:
            for _, original, _ in items:
                unparsed_lines.append(original)
            continue

        record = EntityRecord(name=entity_name, source_refs=sorted({bid for bid, _, _ in items}))
        for _, _, parsed in items:
            if parsed.kind == "attribute" and parsed.attribute_key:
                record.attributes[parsed.attribute_key] = parsed.attribute_value or ""
            elif parsed.kind == "action" and parsed.action_text:
                record.actions.append(parsed.action_text)
        entities.append(record)

    original_text = _input_text(dedup)
    original_tokens = estimate_tokens(original_text) if original_text else dedup.original_tokens

    result = FactorizationResult(
        entities=entities,
        unparsed=unparsed_lines,
        shared_facts=list(dedup.shared_facts),
        original_tokens=original_tokens,
        optimized_tokens=0,
    )
    prose = render_factorization_prose(result, locale=loc)
    result.optimized_tokens = estimate_tokens(prose)
    return result


def _input_text(dedup: DeduplicationResult) -> str:
    parts: list[str] = []
    for fact in dedup.shared_facts:
        parts.append(fact.canonical_line)
    for block in dedup.unique_blocks:
        parts.append(block.content)
    return "\n".join(parts)
