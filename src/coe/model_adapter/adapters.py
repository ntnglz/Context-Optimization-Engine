"""Adaptadores mínimos: default, mistral, openai."""

from __future__ import annotations

import re

from .base import ModelAdapter

_SECTION_LINE = re.compile(r"^--- (.+?) ---\s*$", re.MULTILINE)


class DefaultAdapter(ModelAdapter):
    id = "default"

    def adapt(self, text: str, target_model: str) -> str:
        return text


class MistralAdapter(ModelAdapter):
    """Marcadores estilo instruct: ``[SECTION]`` en lugar de ``--- section ---``."""

    id = "mistral"

    def adapt(self, text: str, target_model: str) -> str:
        if not text.strip():
            return text
        body = _SECTION_LINE.sub(r"[\1]", text.rstrip())
        return f"[AVAILABLE CONTEXT]\n{body}\n[/AVAILABLE CONTEXT]\n"


class OpenAIAdapter(ModelAdapter):
    """Encabezados markdown + envoltorio XML para modelos chat OpenAI."""

    id = "openai"

    def adapt(self, text: str, target_model: str) -> str:
        if not text.strip():
            return text
        body = _SECTION_LINE.sub(_openai_section_header, text.rstrip())
        return f"<optimized_context>\n{body}\n</optimized_context>\n"


def _openai_section_header(match: re.Match[str]) -> str:
    title = match.group(1).strip()
    normalized = title.title().replace(" ", " ")
    return f"## {normalized}"
