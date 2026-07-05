"""L0 — normalización de idioma pre-N1."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import ContextBlock
from .detect import detect_language
from .translate import translate_text

_MIN_DETECT_CONFIDENCE = 0.55


@dataclass
class IngestTrace:
    target_lang: str
    blocks_translated: int = 0
    blocks_skipped: int = 0
    detected_langs: dict[str, str] = field(default_factory=dict)
    mixed_bundle: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass
class NormalizeLanguageResult:
    blocks: list[ContextBlock]
    ingest_trace: IngestTrace


def normalize_language(
    blocks: list[ContextBlock],
    *,
    target_lang: str,
    source_lang: str | None = None,
    translate_code_blocks: bool = False,
) -> NormalizeLanguageResult:
    """Detecta idioma por bloque y traduce a ``target_lang`` cuando aplica."""
    target = target_lang.split("-")[0].lower()
    trace = IngestTrace(target_lang=target)
    normalized: list[ContextBlock] = []
    langs_seen: set[str] = set()

    for block in blocks:
        if block.metadata.get("preserve_lang"):
            trace.blocks_skipped += 1
            trace.detected_langs[block.id] = "preserved"
            normalized.append(block)
            continue

        if not translate_code_blocks and block.content.strip().startswith("```"):
            trace.blocks_skipped += 1
            trace.detected_langs[block.id] = "code"
            normalized.append(block)
            continue

        detected, confidence = (
            (source_lang.split("-")[0].lower(), 1.0)
            if source_lang
            else detect_language(block.content)
        )

        trace.detected_langs[block.id] = detected
        if detected not in {"unknown", "preserved", "code"}:
            langs_seen.add(detected)

        if detected == target or detected == "unknown":
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

        translated_content = translate_text(
            block.content,
            source_lang=detected,
            target_lang=target,
        )
        trace.blocks_translated += 1
        normalized.append(
            ContextBlock(
                id=block.id,
                content=translated_content,
                metadata=dict(block.metadata),
            )
        )

    trace.mixed_bundle = len(langs_seen) > 1 or (
        bool(langs_seen - {target}) and trace.blocks_translated > 0
    )
    return NormalizeLanguageResult(blocks=normalized, ingest_trace=trace)
