"""Detección de notación COE prohibida en texto hacia LLM."""

from __future__ import annotations

import re

ARTIFACT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bentity:", re.I),
    re.compile(r"\bnode:", re.I),
    re.compile(r"\bedge:", re.I),
    re.compile(r"\borphan:", re.I),
    re.compile(r"commit_id", re.I),
    re.compile(r"#\s*delta", re.I),
    re.compile(r"\+edge\s*\(", re.I),
    re.compile(r"entity\{", re.I),
)


def detect_artifact_leak(text: str) -> bool:
    """True si el texto contiene patrones prohibidos."""
    return any(p.search(text) for p in ARTIFACT_PATTERNS)
