"""Patrones de extracción N2 (locale packs EN/ES v1)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LocalePack:
    works_at_re: re.Pattern[str]
    action_verbs: frozenset[str]
    pronoun_subjects: frozenset[str]
    works_at_action_prefix: str


_LOCALE_PACKS: dict[str, LocalePack] = {
    "en": LocalePack(
        works_at_re=re.compile(
            r"^(?P<entity>[A-Z][a-zA-Z0-9]*)\s+works\s+at\s+(?P<company>.+?)\.?\s*$",
            re.IGNORECASE,
        ),
        action_verbs=frozenset(
            {
                "approved",
                "created",
                "leads",
                "manages",
                "owns",
                "rejected",
                "updated",
                "works",
            }
        ),
        pronoun_subjects=frozenset({"he", "she", "they", "it"}),
        works_at_action_prefix="works at ",
    ),
    "es": LocalePack(
        works_at_re=re.compile(
            r"^(?P<entity>[A-ZÁÉÍÓÚÑ][a-záéíóúñA-Z0-9]*(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñA-Z0-9]*)*)"
            r"\s+trabaja\s+en\s+(?P<company>.+?)\.?\s*$",
            re.IGNORECASE,
        ),
        action_verbs=frozenset(
            {
                "aprobó",
                "creó",
                "lidera",
                "gestiona",
                "posee",
                "rechazó",
                "actualizó",
                "trabaja",
            }
        ),
        pronoun_subjects=frozenset(
            {"él", "ella", "ellos", "ellas", "usted", "ustedes", "lo", "la", "los", "las"}
        ),
        works_at_action_prefix="trabaja en ",
    ),
}


@dataclass(frozen=True)
class ParsedStatement:
    entity: str
    kind: str  # "attribute" | "action"
    attribute_key: str | None = None
    attribute_value: str | None = None
    action_text: str | None = None
    source_line: str = ""


def parse_line(line: str, *, locale: str = "en") -> ParsedStatement | None:
    """Parsea una línea con sujeto explícito repetido."""
    key = locale.split("-")[0].lower()
    pack = _LOCALE_PACKS.get(key)
    if pack is None:
        raise NotImplementedError(f"Locale pack not implemented: {locale!r}")

    text = line.strip()
    if not text:
        return None

    match = pack.works_at_re.match(text)
    if match:
        return ParsedStatement(
            entity=_normalize_entity(match.group("entity")),
            kind="attribute",
            attribute_key="company",
            attribute_value=match.group("company").strip().rstrip("."),
            source_line=text,
        )

    tokens = text.rstrip(".").split()
    if len(tokens) < 2:
        return None

    verb_idx = None
    for idx, token in enumerate(tokens[1:], start=1):
        if token.lower() in pack.action_verbs:
            verb_idx = idx
            break
    if verb_idx is None:
        return None

    entity = _normalize_entity(" ".join(tokens[:verb_idx]))
    if not entity or entity.lower() in pack.pronoun_subjects:
        return None

    action_text = " ".join(tokens[verb_idx:])
    if action_text.lower().startswith(pack.works_at_action_prefix):
        return None

    return ParsedStatement(
        entity=entity,
        kind="action",
        action_text=action_text,
        source_line=text,
    )


def _normalize_entity(name: str) -> str:
    parts = name.strip().split()
    if not parts:
        return ""
    return " ".join(p[:1].upper() + p[1:] if p else p for p in parts)
