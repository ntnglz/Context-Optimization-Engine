"""Context Ingest — bundle, normalizer y L0."""

from .ingest import ingest_context
from .l0 import IngestTrace, NormalizeLanguageResult, compute_dominant_language, normalize_language
from .matrix import l0_allowed_for_blocks, resolve_effective_levels
from .translation_backend import (
    BenchmarkStubBackend,
    DeepTranslatorBackend,
    TranslationBackend,
    get_default_translation_backend,
)
from .types import ContextBundle, IngestOptions, IngestResult, SOURCE_TYPES

__all__ = [
    "BenchmarkStubBackend",
    "ContextBundle",
    "DeepTranslatorBackend",
    "IngestOptions",
    "IngestResult",
    "IngestTrace",
    "NormalizeLanguageResult",
    "SOURCE_TYPES",
    "TranslationBackend",
    "compute_dominant_language",
    "get_default_translation_backend",
    "ingest_context",
    "l0_allowed_for_blocks",
    "normalize_language",
    "resolve_effective_levels",
]
