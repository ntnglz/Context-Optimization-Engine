"""Resolución del paquete PCM (repo hermano o instalación pip)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_PCM_IMPORT_ATTEMPTED = False
_PCM_AVAILABLE = False


def default_pcm_src_path() -> Path:
    """Ruta por defecto: ``../Prompt Compression Middleware/src`` respecto al repo COE."""
    env = os.environ.get("PCM_ROOT") or os.environ.get("COE_PCM_ROOT")
    if env:
        root = Path(env).expanduser().resolve()
        if (root / "src" / "pcm").is_dir():
            return root / "src"
        if (root / "pcm").is_dir():
            return root
        return root
    coe_root = Path(__file__).resolve().parents[3]
    sibling = coe_root.parent / "Prompt Compression Middleware" / "src"
    if sibling.is_dir():
        return sibling
    return coe_root.parent / "Prompt-Compression-Middleware (ref)" / "src"


def ensure_pcm_importable() -> bool:
    """Añade PCM al ``sys.path`` si existe localmente."""
    global _PCM_IMPORT_ATTEMPTED, _PCM_AVAILABLE
    if _PCM_IMPORT_ATTEMPTED:
        return _PCM_AVAILABLE
    _PCM_IMPORT_ATTEMPTED = True

    try:
        import pcm  # noqa: F401

        _PCM_AVAILABLE = True
        return True
    except ImportError:
        pass

    src = default_pcm_src_path()
    if src.is_dir() and str(src) not in sys.path:
        sys.path.insert(0, str(src))

    try:
        import pcm  # noqa: F401

        _PCM_AVAILABLE = True
    except ImportError:
        _PCM_AVAILABLE = False
    return _PCM_AVAILABLE


def get_prompt_compressor_class() -> type[Any] | None:
    if not ensure_pcm_importable():
        return None
    from pcm.compressor import PromptCompressor

    return PromptCompressor
