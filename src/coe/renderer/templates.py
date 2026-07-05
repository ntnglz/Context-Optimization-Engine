"""Plantillas de prosa hacia el LLM por locale."""

from __future__ import annotations

DEFAULT_LOCALE = "en"

_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "shared_intro": "The following information appears in multiple sources:",
        "shared_item": "- {line} (sources {refs}).",
        "unique_intro": "Additional content by source:",
        "unique_block": "From source {id}:",
        "compact_refs": "References: {refs}",
        "section_session_state": "--- session state ---",
        "section_context": "--- context ---",
        "view_intro": "Accumulated session state:",
        "change_intro": "Changes since the last turn:",
        "edge_knows": "{source} knows {target}.",
        "edge_company": "{source} works at {target}.",
        "edge_generic": "{source} → {target} ({edge_type}).",
    },
    "es": {
        "shared_intro": "La siguiente información aparece en varias fuentes:",
        "shared_item": "- {line} (fuentes {refs}).",
        "unique_intro": "Contenido adicional por fuente:",
        "unique_block": "De la fuente {id}:",
        "compact_refs": "Referencias: {refs}",
        "section_session_state": "--- estado de sesión ---",
        "section_context": "--- contexto ---",
        "view_intro": "Estado acumulado de la sesión:",
        "change_intro": "Cambios desde el último turno:",
        "edge_knows": "{source} conoce a {target}.",
        "edge_company": "{source} trabaja en {target}.",
        "edge_generic": "{source} → {target} ({edge_type}).",
    },
}


def get_templates(locale: str | None) -> dict[str, str]:
    key = (locale or DEFAULT_LOCALE).split("-")[0].lower()
    return _TEMPLATES.get(key, _TEMPLATES[DEFAULT_LOCALE])
