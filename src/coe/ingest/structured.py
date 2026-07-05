"""Parser structured → líneas N1-friendly (JSON, logs, CSV)."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any, Literal

StructuredFormat = Literal["json", "log", "csv", "plain"]

_LOG_LEVEL = re.compile(
    r"^\s*(?:\d{4}[-/]\d{2}[-/]\d{2}[T\s]\S+\s+)?(?:\[(?:INFO|WARN|ERROR|DEBUG|TRACE)\]\s*)?",
    re.IGNORECASE,
)


def detect_structured_format(content: str, *, hint: str | None = None) -> StructuredFormat:
    if hint in {"json", "log", "csv", "plain"}:
        return hint  # type: ignore[return-value]

    stripped = content.strip()
    if not stripped:
        return "plain"

    if stripped.startswith("{") or stripped.startswith("["):
        try:
            json.loads(stripped)
            return "json"
        except json.JSONDecodeError:
            pass

    lines = [line for line in stripped.splitlines() if line.strip()]
    if len(lines) >= 2 and _looks_like_csv(lines):
        return "csv"

    if any(_LOG_LEVEL.match(line) for line in lines[:5]):
        return "log"

    return "plain"


def flatten_structured_content(
    content: str,
    *,
    fmt: StructuredFormat | None = None,
) -> str:
    """Convierte JSON/logs/CSV en líneas deduplicables por N1."""
    resolved = fmt or detect_structured_format(content)
    if resolved == "json":
        return _flatten_json(content)
    if resolved == "csv":
        return _flatten_csv(content)
    if resolved == "log":
        return _flatten_log(content)
    return content


def _looks_like_csv(lines: list[str]) -> bool:
    header = lines[0]
    if header.count(",") < 1:
        return False
    width = header.count(",") + 1
    sample = lines[1 : min(len(lines), 4)]
    return all(line.count(",") + 1 == width for line in sample if line.strip())


def _flatten_json(content: str) -> str:
    try:
        payload = json.loads(content.strip())
    except json.JSONDecodeError:
        return content

    lines = [line for line in _json_to_lines(payload) if line.strip()]
    return "\n".join(lines) if lines else content


def _json_to_lines(value: Any, *, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        lines: list[str] = []
        for key in sorted(value):
            child_prefix = f"{prefix}{key}." if prefix else f"{key}."
            lines.extend(_json_to_lines(value[key], prefix=child_prefix))
        return lines

    if isinstance(value, list):
        lines = []
        for index, item in enumerate(value):
            lines.extend(_json_to_lines(item, prefix=f"{prefix}{index}."))
        return lines

    key = prefix.rstrip(".") or "value"
    return [f"{key}: {value}"]


def _flatten_csv(content: str) -> str:
    reader = csv.reader(io.StringIO(content.strip()))
    rows = list(reader)
    if not rows:
        return content

    header = [cell.strip() for cell in rows[0]]
    if not any(header):
        return content

    lines: list[str] = []
    for row in rows[1:]:
        if not any(cell.strip() for cell in row):
            continue
        pairs: list[str] = []
        for index, cell in enumerate(row):
            name = header[index] if index < len(header) else f"col{index + 1}"
            if cell.strip():
                pairs.append(f"{name}: {cell.strip()}")
        if pairs:
            lines.append(" | ".join(pairs))
    return "\n".join(lines) if lines else content


def _flatten_log(content: str) -> str:
    lines: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        normalized = _LOG_LEVEL.sub("", stripped).strip()
        lines.append(normalized or stripped)
    return "\n".join(lines)
