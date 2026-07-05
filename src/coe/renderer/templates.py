"""Plantillas de prosa hacia el LLM por locale."""

from __future__ import annotations

from typing import Any

DEFAULT_LOCALE = "en"

_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "shared_intro": "The following information appears in multiple sources:",
        "shared_item": "- {line} (sources {refs}).",
        "unique_intro": "Additional content by source:",
        "unique_block": "From source {id}:",
    },
    "es": {
        "shared_intro": "La siguiente información aparece en varias fuentes:",
        "shared_item": "- {line} (fuentes {refs}).",
        "unique_intro": "Contenido adicional por fuente:",
        "unique_block": "De la fuente {id}:",
    },
}


def get_templates(locale: str | None) -> dict[str, str]:
    key = (locale or DEFAULT_LOCALE).split("-")[0].lower()
    return _TEMPLATES.get(key, _TEMPLATES[DEFAULT_LOCALE])
