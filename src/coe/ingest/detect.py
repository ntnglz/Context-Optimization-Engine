"""Detección heurística de idioma por bloque (L0 v1)."""

from __future__ import annotations

_ES_MARKERS = (
    "trabaja en",
    "aprobó",
    "creó",
    "presupuesto",
    "¿",
    "á",
    "é",
    "í",
    "ó",
    "ú",
    "ñ",
)
_EN_MARKERS = (
    "works at",
    "approved",
    "created",
    "budget",
    " the ",
    " who ",
)


def detect_language(text: str) -> tuple[str, float]:
    """Devuelve código ISO639-1 aproximado y confianza [0, 1]."""
    lower = text.lower()
    es_score = sum(1 for marker in _ES_MARKERS if marker in lower)
    en_score = sum(1 for marker in _EN_MARKERS if marker in lower)

    if es_score == 0 and en_score == 0:
        return "unknown", 0.0
    total = es_score + en_score
    if es_score > en_score:
        return "es", es_score / total
    if en_score > es_score:
        return "en", en_score / total
    return "unknown", 0.5
