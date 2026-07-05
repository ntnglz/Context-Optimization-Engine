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
        "conflict_intro": "Conflicting information in session state:",
        "conflict_item": "Source {prev_sources} says {property} is {previous}; source {new_sources} says {incoming}.",
        "retract_intro": "Corrections since earlier turns:",
        "retract_item": "Previously ({commit_id}): {previous}; corrected to: {corrected} (source {source_id}).",
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
        "conflict_intro": "Información contradictoria en el estado de sesión:",
        "conflict_item": "La fuente {prev_sources} indica {property} = {previous}; la fuente {new_sources} indica {incoming}.",
        "retract_intro": "Correcciones respecto a turnos anteriores:",
        "retract_item": "Antes ({commit_id}): {previous}; corregido a: {corrected} (fuente {source_id}).",
    },
}


def _ensure_zh_templates() -> None:
    if "zh" in _TEMPLATES:
        return
    from ..locales.zh.templates import ZH_TEMPLATES

    _TEMPLATES["zh"] = ZH_TEMPLATES


def get_templates(locale: str | None) -> dict[str, str]:
    key = (locale or DEFAULT_LOCALE).split("-")[0].lower()
    if key == "zh":
        _ensure_zh_templates()
    return _TEMPLATES.get(key, _TEMPLATES[DEFAULT_LOCALE])
