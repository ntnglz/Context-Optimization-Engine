"""Tests locale pack chino (Fase 17)."""

from __future__ import annotations

from coe.ingest.normalizer import normalize_block_content
from coe.ingest.translate import translate_text
from coe.level2 import factorize_context
from coe.level2.patterns import parse_line
from coe.level3.patterns import parse_knows_line
from coe.models import ContextBlock
from coe.renderer.templates import get_templates


class TestZhSegmentation:
    def test_splits_sentences_on_period(self):
        raw = "公司：ACME\n张三在ACME工作。李四在ACME工作。"
        out = normalize_block_content(raw, locale="zh")
        assert "张三在ACME工作。" in out
        assert "李四在ACME工作。" in out


class TestZhPatterns:
    def test_works_at(self):
        parsed = parse_line("张三在ACME工作。", locale="zh")
        assert parsed is not None
        assert parsed.entity == "张三"
        assert parsed.attribute_value == "ACME"

    def test_action(self):
        parsed = parse_line("张三批准了预算。", locale="zh")
        assert parsed is not None
        assert parsed.entity == "张三"
        assert "批准" in (parsed.action_text or "")

    def test_knows(self):
        parsed = parse_knows_line("张三认识李四。", locale="zh")
        assert parsed is not None
        assert parsed.entity == "张三"
        assert parsed.target == "李四"


class TestZhFactorization:
    def test_acme_budget_case(self):
        blocks = [
            ContextBlock(id="A", content="公司：ACME\n客户：Globex\n张三在ACME工作。"),
            ContextBlock(id="B", content="公司：ACME\n预算：80k\n张三批准了预算。"),
            ContextBlock(id="C", content="公司：ACME\n客户：Globex\n李四在ACME工作。"),
        ]
        result = factorize_context(blocks, locale="zh")
        prose = result.render_prose(locale="zh")
        assert "张三" in prose
        assert "批准" in prose
        assert "entity:" not in prose


class TestZhL0:
    def test_en_to_zh_stub(self):
        text = "Company: ACME\nJuan works at ACME.\nJuan approved the budget."
        out = translate_text(text, source_lang="en", target_lang="zh")
        assert "公司：ACME" in out
        assert "张三" in out
        assert "批准" in out


class TestZhTemplates:
    def test_renderer_templates(self):
        tpl = get_templates("zh")
        assert "会话状态" in tpl["section_session_state"]
