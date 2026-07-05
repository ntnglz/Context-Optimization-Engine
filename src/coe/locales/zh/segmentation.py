"""Segmentación de oraciones chinas para Normalizer (pre-N1)."""

from __future__ import annotations

import re

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_SENTENCE_BREAK = re.compile(r"([。！？；])")


def content_has_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def segment_chinese_sentences(text: str) -> str:
    """
    Inserta saltos de línea tras finales de oración chinos.

    Preserva líneas vacías y encabezados ``clave：valor`` sin segmentar.
    """
    if not content_has_cjk(text):
        return text

    out_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or _is_header_line(stripped) or "```" in line:
            out_lines.append(line)
            continue
        if not content_has_cjk(stripped):
            out_lines.append(line)
            continue
        out_lines.extend(_split_line(stripped))
    return "\n".join(out_lines)


def _is_header_line(line: str) -> bool:
    if "：" in line and not _SENTENCE_BREAK.search(line):
        return True
    if ":" in line and not _SENTENCE_BREAK.search(line) and content_has_cjk(line.split(":", 1)[0]):
        return False
    return ":" in line and not _SENTENCE_BREAK.search(line)


def _split_line(line: str) -> list[str]:
    parts = _SENTENCE_BREAK.split(line)
    if len(parts) == 1:
        return [line]
    merged: list[str] = []
    buf = ""
    for part in parts:
        if part in "。！？；":
            buf += part
            if buf.strip():
                merged.append(buf.strip())
            buf = ""
        else:
            buf += part
    if buf.strip():
        merged.append(buf.strip())
    return merged or [line]
