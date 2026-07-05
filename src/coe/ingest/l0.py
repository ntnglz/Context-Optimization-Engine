"""L0 — normalización de idioma pre-N1."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import ContextBlock
from .detect import detect_language
from .translate import _FENCE_RE, translate_block_content
from .translation_backend import TranslationBackend, get_default_translation_backend

_MIN_DETECT_CONFIDENCE = 0.55


@dataclass
class IngestTrace:
    target_lang: str
    blocks_translated: int = 0
    blocks_skipped: int = 0
    detected_langs: dict[str, str] = field(default_factory=dict)
    detect_confidence: dict[str, float] = field(default_factory=dict)
    dominant_lang: str | None = None
    mixed_bundle: bool = False
    translation_backend: str = "benchmark_stub"
    warnings: list[str] = field(default_factory=list)


@dataclass
class NormalizeLanguageResult:
    blocks: list[ContextBlock]
    ingest_trace: IngestTrace


def compute_dominant_language(
    blocks: list[ContextBlock],
    *,
    source_lang: str | None = None,
) -> tuple[str | None, dict[str, tuple[str, float]]]:
    """Idioma dominante por tokens de bloque (i18n § mezcla residual)."""
    per_block: dict[str, tuple[str, float]] = {}
    weights: dict[str, int] = {}

    for block in blocks:
        if block.metadata.get("preserve_lang"):
            per_block[block.id] = ("preserved", 1.0)
            continue
        if block.content.strip().startswith("```"):
            per_block[block.id] = ("code", 1.0)
            continue

        if source_lang:
            detected, confidence = source_lang.split("-")[0].lower(), 1.0
        else:
            detected, confidence = detect_language(block.content)

        per_block[block.id] = (detected, confidence)
        if detected in {"unknown", "preserved", "code"}:
            continue
        weight = block.token_count()
        weights[detected] = weights.get(detected, 0) + weight

    if not weights:
        return None, per_block

    dominant = max(weights, key=weights.get)
    return dominant, per_block


def normalize_language(
    blocks: list[ContextBlock],
    *,
    target_lang: str,
    source_lang: str | None = None,
    translate_code_blocks: bool = False,
    translation_backend: TranslationBackend | None = None,
) -> NormalizeLanguageResult:
    """Detecta idioma por bloque y traduce a ``target_lang`` cuando aplica."""
    backend = translation_backend or get_default_translation_backend()
    requested = target_lang.split("-")[0].lower()

    dominant, pre_detect = compute_dominant_language(blocks, source_lang=source_lang)
    effective_target = dominant if requested == "auto" else requested
    if requested == "auto" and not effective_target:
        effective_target = "en"
        pre_warnings = ["target_lang=auto but no dominant language detected; defaulting to en"]
    else:
        pre_warnings = []

    trace = IngestTrace(
        target_lang=effective_target,
        dominant_lang=dominant,
        translation_backend=backend.name,
        warnings=list(pre_warnings),
    )
    normalized: list[ContextBlock] = []
    langs_seen: set[str] = set()

    for block in blocks:
        if block.metadata.get("preserve_lang") or block.source_type == "glossary":
            trace.blocks_skipped += 1
            trace.detected_langs[block.id] = "preserved"
            trace.detect_confidence[block.id] = 1.0
            normalized.append(block)
            continue

        skip_code_fence = (
            not translate_code_blocks and block.content.strip().startswith("```")
        )
        if skip_code_fence:
            trace.blocks_skipped += 1
            trace.detected_langs[block.id] = "code"
            trace.detect_confidence[block.id] = 1.0
            normalized.append(block)
            continue

        if block.id in pre_detect and not (
            translate_code_blocks and block.content.strip().startswith("```")
        ):
            detected, confidence = pre_detect[block.id]
        elif source_lang:
            detected, confidence = source_lang.split("-")[0].lower(), 1.0
        else:
            sample = block.content
            if translate_code_blocks:
                fence = _FENCE_RE.match(block.content)
                if fence:
                    sample = fence.group(2)
            detected, confidence = detect_language(sample)

        trace.detected_langs[block.id] = detected
        trace.detect_confidence[block.id] = confidence
        if detected not in {"unknown", "preserved", "code"}:
            langs_seen.add(detected)

        if detected == effective_target or detected == "unknown":
            trace.blocks_skipped += 1
            if detected == "unknown" and confidence < _MIN_DETECT_CONFIDENCE:
                trace.warnings.append(
                    f"block {block.id}: low-confidence detect ({confidence:.2f}); passthrough"
                )
            normalized.append(block)
            continue

        if confidence < _MIN_DETECT_CONFIDENCE:
            trace.blocks_skipped += 1
            trace.warnings.append(
                f"block {block.id}: confidence {confidence:.2f} < {_MIN_DETECT_CONFIDENCE}; passthrough"
            )
            normalized.append(block)
            continue

        translated_content = translate_block_content(
            block.content,
            source_lang=detected,
            target_lang=effective_target,
            backend=backend,
            translate_code_blocks=translate_code_blocks,
        )
        trace.blocks_translated += 1
        normalized.append(
            ContextBlock(
                id=block.id,
                content=translated_content,
                source_type=block.source_type,
                detected_lang=effective_target,
                token_estimate=block.token_estimate,
                metadata=dict(block.metadata),
            )
        )

    residual_langs = langs_seen - {effective_target}
    preserved_or_skipped = any(
        trace.detected_langs.get(b.id) in {"preserved", "code", "unknown"}
        for b in blocks
    )
    trace.mixed_bundle = bool(residual_langs) or (
        len(langs_seen) > 1 and trace.blocks_translated > 0
    ) or (preserved_or_skipped and trace.blocks_translated > 0)

    return NormalizeLanguageResult(blocks=normalized, ingest_trace=trace)
