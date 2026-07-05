"""Detección de idioma por bloque (L0 v2)."""

from __future__ import annotations

import re

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
_ES_SURFACE_MARKERS = (
    "tras ",
    "queda",
    "quedan",
    "compilar",
    "warning de",
    "español",
    "¿",
    "á",
    "é",
    "í",
    "ó",
    "ú",
    "ñ",
    "prioridad",
    "según",
)
_ZH_MARKERS = (
    "公司",
    "预算",
    "批准",
    "工作",
    "客户",
    "中文",
    "。",
    "？",
)
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _spanish_surface_score(text: str) -> int:
    lower = text.lower()
    return sum(1 for marker in _ES_SURFACE_MARKERS if marker in lower)


def has_spanish_surface(text: str) -> bool:
    """Heurística para prosa ES con términos técnicos en inglés."""
    return _spanish_surface_score(text) >= 2 or (
        _spanish_surface_score(text) >= 1 and any(ch in text for ch in "áéíóúñ¿")
    )


def has_chinese_surface(text: str) -> bool:
    """Heurística para prosa zh con tokens latinos (nombres propios, IDs)."""
    cjk = len(_CJK_RE.findall(text))
    if cjk == 0:
        return False
    letters = re.findall(r"\S", text)
    if not letters:
        return False
    if cjk / len(letters) >= 0.25:
        return True
    return sum(1 for marker in _ZH_MARKERS if marker in text) >= 1


def _heuristic_detect(text: str) -> tuple[str, float]:
    """Fallback para textos cortos o cuando langdetect falla."""
    if has_chinese_surface(text):
        return "zh", 0.85

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


def detect_language(text: str) -> tuple[str, float]:
    """Devuelve código ISO639-1 y confianza [0, 1]."""
    stripped = text.strip()
    if not stripped:
        return "unknown", 0.0
    if len(stripped) < 24:
        return _heuristic_detect(stripped)

    try:
        from langdetect import LangDetectException, detect_langs

        candidates = detect_langs(stripped)
    except Exception:
        return _heuristic_detect(stripped)

    if not candidates:
        return _heuristic_detect(stripped)

    best = candidates[0]
    try:
        lang = best.lang.split("-")[0].lower()
        confidence = float(best.prob)
    except (AttributeError, TypeError, ValueError):
        return _heuristic_detect(stripped)

    if confidence < 0.35:
        heuristic_lang, heuristic_conf = _heuristic_detect(stripped)
        if heuristic_conf > confidence:
            return heuristic_lang, heuristic_conf

    if lang in {"ca", "gl", "eu"} and has_spanish_surface(stripped):
        es_score = _spanish_surface_score(stripped)
        return "es", max(confidence, min(0.95, 0.5 + es_score * 0.1))

    return lang, confidence
