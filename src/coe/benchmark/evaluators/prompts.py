"""Carga de plantillas versionadas en ``data/benchmarks/prompts/``."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


def default_prompts_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "benchmarks" / "prompts"


@lru_cache(maxsize=16)
def load_prompt(name: str, prompts_dir: str | None = None) -> str:
    root = Path(prompts_dir) if prompts_dir else default_prompts_dir()
    path = root / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8").strip()
