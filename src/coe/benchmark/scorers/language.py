"""Coincidencia de idioma de respuesta con ``response_lang``."""

from __future__ import annotations

import re

from coe.ingest.detect import detect_language, has_chinese_surface, has_spanish_surface


def user_language_match(response: str, expected_lang: str) -> bool:
    """
    True si la respuesta parece estar en ``expected_lang``.

    Reutiliza detección L0; tolera respuestas ES con jerga técnica en inglés.
    """
    text = response.strip()
    if not text:
        return False

    expected = expected_lang.split("-")[0].lower()
    detected, confidence = detect_language(text)
    if detected == expected:
        return True

    if expected == "es" and has_spanish_surface(text):
        return True

    if expected == "zh" and has_chinese_surface(text):
        return True

    if expected == "en" and detected == "unknown":
        return _fallback_match(text, expected)

    return False


def _fallback_match(text: str, expected_lang: str) -> bool:
    if expected_lang == "en":
        letters = re.findall(r"[A-Za-z]", text)
        if not letters:
            return False
        latin = sum(1 for ch in letters if ord(ch) < 128)
        return latin / len(letters) >= 0.9
    return len(text) > 0
