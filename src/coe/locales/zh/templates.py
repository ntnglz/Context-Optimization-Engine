"""Plantillas Renderer para locale ``zh``."""

from __future__ import annotations

ZH_TEMPLATES: dict[str, str] = {
    "shared_intro": "以下信息在多个来源中出现：",
    "shared_item": "- {line}（来源 {refs}）。",
    "unique_intro": "各来源的附加内容：",
    "unique_block": "来源 {id}：",
    "compact_refs": "参考：{refs}",
    "section_session_state": "--- 会话状态 ---",
    "section_context": "--- 上下文 ---",
    "view_intro": "累积的会话状态：",
    "change_intro": "自上一回合以来的变化：",
    "edge_knows": "{source}认识{target}。",
    "edge_company": "{source}在{target}工作。",
    "edge_generic": "{source} → {target}（{edge_type}）。",
    "conflict_intro": "会话状态中的冲突信息：",
    "conflict_item": "来源 {prev_sources} 称 {property} 为 {previous}；来源 {new_sources} 称 {incoming}。",
    "retract_intro": "相对先前回合的更正：",
    "retract_item": "先前（{commit_id}）：{previous}；更正为：{corrected}（来源 {source_id}）。",
}
