"""Traducción L0 con preservación de identificadores."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .translation_backend import TranslationBackend

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

_FENCE_RE = re.compile(r"^(```[^\n]*\n)(.*?)(\n```\s*$)", re.DOTALL)
_PRESERVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"https?://\S+"), "URL"),
    (
        re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            re.I,
        ),
        "UUID",
    ),
    (re.compile(r"`[^`\n]+`"), "CODE"),
    (re.compile(r"\b/[A-Za-z0-9_./-]+\b"), "PATH"),
)


def translate_text(text: str, *, source_lang: str, target_lang: str) -> str:
    if source_lang.split("-")[0].lower() == target_lang.split("-")[0].lower():
        return text
    pair = (source_lang.split("-")[0].lower(), target_lang.split("-")[0].lower())
    if pair == ("es", "en"):
        return _translate_es_en(text)
    raise NotImplementedError(f"Translation pair not supported: {pair!r}")


def translate_block_content(
    text: str,
    *,
    source_lang: str,
    target_lang: str,
    backend: TranslationBackend,
    translate_code_blocks: bool = False,
) -> str:
    """Traduce un bloque respetando fences y tokens protegidos."""
    stripped = text.strip()
    if stripped.startswith("```"):
        if not translate_code_blocks:
            return text
        match = _FENCE_RE.match(text)
        if match:
            open_fence, inner, close_fence = match.groups()
            translated = _translate_with_masks(
                inner,
                source_lang=source_lang,
                target_lang=target_lang,
                backend=backend,
            )
            return f"{open_fence}{translated}{close_fence}"
    return _translate_with_masks(
        text,
        source_lang=source_lang,
        target_lang=target_lang,
        backend=backend,
    )


def _translate_with_masks(
    text: str,
    *,
    source_lang: str,
    target_lang: str,
    backend: TranslationBackend,
) -> str:
    placeholders: dict[str, str] = {}

    def _mask(match: re.Match[str], label: str) -> str:
        key = f"__COE_{label}_{len(placeholders)}__"
        placeholders[key] = match.group(0)
        return key

    masked = text
    for pattern, label in _PRESERVE_PATTERNS:
        masked = pattern.sub(lambda m, lbl=label: _mask(m, lbl), masked)

    translated = backend.translate(
        masked,
        source_lang=source_lang,
        target_lang=target_lang,
    )
    for key, original in placeholders.items():
        translated = translated.replace(key, original)
    return translated


def _translate_es_en(text: str) -> str:
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
