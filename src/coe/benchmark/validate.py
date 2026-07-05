"""Validación JSON Schema de casos de benchmark."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:  # pragma: no cover - guarded in tests
    jsonschema = None  # type: ignore[assignment]

DEFAULT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "benchmarks" / "schema" / "case.schema.json"
)


@lru_cache(maxsize=1)
def load_case_schema(path: Path | None = None) -> dict[str, Any]:
    schema_path = path or DEFAULT_SCHEMA_PATH
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_case_dict(data: dict[str, Any], *, schema_path: Path | None = None) -> None:
    """Valida un dict de caso contra ``case.schema.json``."""
    if jsonschema is None:
        raise RuntimeError(
            "jsonschema is required for case validation; install requirements.txt"
        )
    schema = load_case_schema(schema_path)
    jsonschema.validate(instance=data, schema=schema)
