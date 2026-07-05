"""Firma de línea para dedup de bloques ``code``."""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")
_TRAILING_COMMENT = re.compile(r"\s#.*$")


def code_line_signature(line: str) -> str:
    """Colapsa espacios y omite comentarios ``#`` finales en la firma."""
    stripped = line.strip()
    if not stripped:
        return ""
    without_comment = _TRAILING_COMMENT.sub("", stripped)
    compact = _WHITESPACE.sub("", without_comment)
    return compact.casefold()
