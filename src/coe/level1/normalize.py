"""Normalización de líneas para comparación de redundancias."""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")


def normalize_line(line: str) -> str:
    """Normaliza una línea para detectar duplicados exactos."""
    return _WHITESPACE.sub(" ", line.strip()).casefold()


def split_lines(content: str) -> list[str]:
    """Divide contenido en líneas no vacías."""
    return [line for line in content.splitlines() if line.strip()]
