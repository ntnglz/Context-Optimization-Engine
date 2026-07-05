"""Locale pack chino (zh) — N2, N3, Renderer y segmentación."""

from __future__ import annotations

from .patterns import ZH_LOCALE_PACK, ZH_RELATION_PATTERN
from .segmentation import segment_chinese_sentences
from .templates import ZH_TEMPLATES

__all__ = [
    "ZH_LOCALE_PACK",
    "ZH_RELATION_PATTERN",
    "ZH_TEMPLATES",
    "segment_chinese_sentences",
]
