"""Patrones N2/N3 para locale ``zh``."""

from __future__ import annotations

import re

from ...level2.patterns import LocalePack, ParsedStatement
from ...level3.patterns import ParsedKnows, RelationPattern

_ENTITY = r"[\u4e00-\u9fffA-Z][\u4e00-\u9fffA-Za-z0-9]*"

ZH_LOCALE_PACK = LocalePack(
    works_at_re=re.compile(
        rf"^(?P<entity>{_ENTITY}(?:\s+{_ENTITY})*)\s*在\s*(?P<company>[^\s，。；]+(?:\s+[^\s，。；]+)*)\s*工作",
        re.IGNORECASE,
    ),
    action_verbs=frozenset(
        {
            "批准了",
            "创建了",
            "领导",
            "管理",
            "拥有",
            "拒绝了",
            "更新了",
            "工作",
        }
    ),
    pronoun_subjects=frozenset({"他", "她", "他们", "她们", "它", "这", "那"}),
    works_at_action_prefix="在",
)

ZH_RELATION_PATTERN = RelationPattern(
    knows_re=re.compile(
        rf"^(?P<entity>{_ENTITY}(?:\s+{_ENTITY})*)\s*认识\s*(?P<target>{_ENTITY}(?:\s+{_ENTITY})*)[\.。]?\s*$",
        re.IGNORECASE,
    ),
)


def parse_line_zh(line: str, pack: LocalePack) -> ParsedStatement | None:
    text = line.strip().rstrip("，。")
    if not text:
        return None

    match = pack.works_at_re.match(text)
    if match:
        return ParsedStatement(
            entity=_normalize_zh_entity(match.group("entity")),
            kind="attribute",
            attribute_key="company",
            attribute_value=match.group("company").strip().rstrip("，。"),
            source_line=line.strip(),
        )

    action_match = re.match(
        rf"^(?P<entity>{_ENTITY})(?P<action>批准了|创建了|领导|管理|拥有|拒绝了|更新了)(?P<rest>.*)$",
        text,
    )
    if action_match:
        entity = _normalize_zh_entity(action_match.group("entity"))
        if entity in pack.pronoun_subjects:
            return None
        action_text = action_match.group("action") + action_match.group("rest").strip()
        if action_text.startswith("在") and "工作" in action_text:
            return None
        return ParsedStatement(
            entity=entity,
            kind="action",
            action_text=action_text.rstrip("，。"),
            source_line=line.strip(),
        )

    return None


def parse_knows_line_zh(line: str, pack: RelationPattern) -> ParsedKnows | None:
    text = line.strip()
    if not text:
        return None
    match = pack.knows_re.match(text)
    if not match:
        return None
    return ParsedKnows(
        entity=_normalize_zh_entity(match.group("entity")),
        target=_normalize_zh_entity(match.group("target")),
        source_line=text,
    )


def _normalize_zh_entity(name: str) -> str:
    return name.strip()
