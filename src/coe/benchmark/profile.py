"""Carga de perfiles de pipeline (YAML)."""

from __future__ import annotations

from pathlib import Path

import yaml

from .schema import PipelineProfile


def load_profile(path: Path) -> PipelineProfile:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid profile YAML: {path}")
    return PipelineProfile.from_dict(data)


def load_profile_by_id(profiles_dir: Path, profile_id: str) -> PipelineProfile:
    path = profiles_dir / f"{profile_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")
    return load_profile(path)
