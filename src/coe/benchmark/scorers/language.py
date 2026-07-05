"""Coincidencia de idioma de respuesta con ``response_lang``."""

from __future__ import annotations

import re


def user_language_match(response: str, expected_lang: str) -> bool:
    """
    True si la respuesta parece estar en ``expected_lang``.

    Usa ``langdetect`` si está instalado; si no, heurística ASCII/latin para ``en``.
    """
    text = response.strip()
    if not text:
        return False

    expected = expected_lang.split("-")[0].lower()
    try:
        from langdetect import detect

        detected = detect(text).split("-")[0].lower()
        return detected == expected
    except ImportError:
        return _fallback_match(text, expected)
    except Exception:
        return _fallback_match(text, expected)


def _fallback_match(text: str, expected_lang: str) -> bool:
    if expected_lang == "en":
        letters = re.findall(r"[A-Za-z]", text)
        if not letters:
            return False
        latin = sum(1 for ch in letters if ord(ch) < 128)
        return latin / len(letters) >= 0.9
    return len(text) > 0
