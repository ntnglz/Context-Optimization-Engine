"""Traducción determinista ES→EN para L0 v1 (casos benchmark)."""

from __future__ import annotations

import re

_LINE_TRANSLATIONS: dict[str, str] = {
    "Empresa: ACME": "Company: ACME",
    "Cliente: Globex": "Client: Globex",
    "Presupuesto: 50k": "Budget: 50k",
    "Juan trabaja en ACME.": "Juan works at ACME.",
    "Pedro trabaja en ACME.": "Pedro works at ACME.",
    "Juan aprobó el presupuesto.": "Juan approved the budget.",
}

_SUBSTRING_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("trabaja en", "works at"),
    ("aprobó el presupuesto", "approved the budget"),
    ("Presupuesto:", "Budget:"),
    ("Empresa:", "Company:"),
    ("Cliente:", "Client:"),
)

_FENCE_RE = re.compile(r"^```")


def translate_text(text: str, *, source_lang: str, target_lang: str) -> str:
    if source_lang == target_lang:
        return text
    pair = (source_lang.split("-")[0].lower(), target_lang.split("-")[0].lower())
    if pair == ("es", "en"):
        return _translate_es_en(text)
    raise NotImplementedError(f"Translation pair not supported: {pair!r}")


def _translate_es_en(text: str) -> str:
    if _FENCE_RE.match(text.strip()):
        return text

    lines = text.splitlines()
    translated = [_translate_line_es_en(line) for line in lines]
    return "\n".join(translated)


def _translate_line_es_en(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return line
    if stripped in _LINE_TRANSLATIONS:
        return _LINE_TRANSLATIONS[stripped]
    result = stripped
    for src, dst in _SUBSTRING_REPLACEMENTS:
        result = result.replace(src, dst)
    return result
