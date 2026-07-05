"""Patrones de relación N3 (locale packs EN/ES v1)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RelationPattern:
    knows_re: re.Pattern[str]


_RELATION_PACKS: dict[str, RelationPattern] = {
    "en": RelationPattern(
        knows_re=re.compile(
            r"^(?P<entity>[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*)"
            r"\s+knows\s+(?P<target>[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*)\.?\s*$",
            re.IGNORECASE,
        ),
    ),
    "es": RelationPattern(
        knows_re=re.compile(
            r"^(?P<entity>[A-ZÁÉÍÓÚÑ][a-záéíóúñA-Z0-9]*(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñA-Z0-9]*)*)"
            r"\s+conoce\s+a\s+(?P<target>[A-ZÁÉÍÓÚÑ][a-záéíóúñA-Z0-9]*(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñA-Z0-9]*)*)\.?\s*$",
            re.IGNORECASE,
        ),
    ),
}


@dataclass(frozen=True)
class ParsedKnows:
    entity: str
    target: str
    source_line: str


def parse_knows_line(line: str, *, locale: str = "en") -> ParsedKnows | None:
    key = locale.split("-")[0].lower()
    pack = _RELATION_PACKS.get(key)
    if pack is None:
        raise NotImplementedError(f"Locale pack not implemented: {locale!r}")

    text = line.strip()
    if not text:
        return None

    match = pack.knows_re.match(text)
    if not match:
        return None

    return ParsedKnows(
        entity=_normalize_name(match.group("entity")),
        target=_normalize_name(match.group("target")),
        source_line=text,
    )


def _normalize_name(name: str) -> str:
    parts = name.strip().split()
    if not parts:
        return ""
    return " ".join(p[:1].upper() + p[1:] if p else p for p in parts)
