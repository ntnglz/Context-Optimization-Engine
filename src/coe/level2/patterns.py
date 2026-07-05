"""Patrones de extracción N2 (locale pack EN v1)."""

from __future__ import annotations

import re
from dataclasses import dataclass

WORKS_AT_RE = re.compile(
    r"^(?P<entity>[A-Z][a-zA-Z0-9]*)\s+works\s+at\s+(?P<company>.+?)\.?\s*$",
    re.IGNORECASE,
)

ACTION_VERBS = frozenset(
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
)


@dataclass(frozen=True)
class ParsedStatement:
    entity: str
    kind: str  # "attribute" | "action"
    attribute_key: str | None = None
    attribute_value: str | None = None
    action_text: str | None = None
    source_line: str = ""


def parse_line(line: str, *, locale: str = "en") -> ParsedStatement | None:
    """Parsea una línea con sujeto explícito repetido (EN v1)."""
    if locale.split("-")[0].lower() != "en":
        raise NotImplementedError(f"Locale pack not implemented: {locale!r}")

    text = line.strip()
    if not text:
        return None

    match = WORKS_AT_RE.match(text)
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
        if token.lower() in ACTION_VERBS:
            verb_idx = idx
            break
    if verb_idx is None:
        return None

    entity = _normalize_entity(" ".join(tokens[:verb_idx]))
    if not entity or entity.lower() in {"he", "she", "they", "it"}:
        return None

    action_text = " ".join(tokens[verb_idx:])
    if action_text.lower().startswith("works at "):
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
