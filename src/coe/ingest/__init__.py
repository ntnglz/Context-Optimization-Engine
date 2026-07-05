"""Context Ingest — bundle, normalizer y L0."""

from .ingest import ingest_context
from .l0 import IngestTrace, NormalizeLanguageResult, normalize_language
from .matrix import l0_allowed_for_blocks, resolve_effective_levels
from .types import ContextBundle, IngestOptions, IngestResult, SOURCE_TYPES

__all__ = [
    "ContextBundle",
    "IngestOptions",
    "IngestResult",
    "IngestTrace",
    "NormalizeLanguageResult",
    "SOURCE_TYPES",
    "ingest_context",
    "l0_allowed_for_blocks",
    "normalize_language",
    "resolve_effective_levels",
]
