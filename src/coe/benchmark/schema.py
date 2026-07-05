"""Modelos de datos del harness de benchmarks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CaseBlock:
    id: str
    content: str
    source_type: str = "prose"


@dataclass
class SessionTurn:
    blocks: list[CaseBlock]
    question: str
    expected_facts: list[str]


@dataclass
class BenchmarkSession:
    session_id: str
    turns: list[SessionTurn]


@dataclass
class MockFixture:
    arm_a_response: str
    arm_b_response: str


@dataclass
class BenchmarkCase:
    id: str
    version: int
    tags: list[str]
    description: str
    blocks: list[CaseBlock]
    question: str
    expected_facts: list[str]
    response_lang: str = "en"
    user_message_lang: str = "en"
    system_addendum: str = ""
    mock: MockFixture | None = None
    session: BenchmarkSession | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BenchmarkCase:
        mock_data = data.get("mock")
        mock = (
            MockFixture(
                arm_a_response=str(mock_data["arm_a_response"]),
                arm_b_response=str(mock_data["arm_b_response"]),
            )
            if mock_data
            else None
        )
        session = _parse_session(data.get("session"))
        blocks = _parse_blocks(data.get("blocks") or [])
        question = str(data.get("question", ""))
        expected_facts = [str(x) for x in data.get("expected_facts", [])]
        if session:
            if not question:
                question = session.turns[-1].question
            if not expected_facts:
                expected_facts = list(session.turns[-1].expected_facts)
            if not blocks:
                blocks = []
                for turn_idx, turn in enumerate(session.turns, start=1):
                    for block in turn.blocks:
                        blocks.append(
                            CaseBlock(
                                id=f"T{turn_idx}-{block.id}",
                                content=block.content,
                                source_type=block.source_type,
                            )
                        )
        if not question:
            raise ValueError(f"Case {data.get('id')} missing question")
        return cls(
            id=str(data["id"]),
            version=int(data.get("version", 1)),
            tags=list(data.get("tags", [])),
            description=str(data.get("description", "")),
            blocks=blocks,
            question=question,
            expected_facts=expected_facts,
            response_lang=str(data.get("response_lang", "en")),
            user_message_lang=str(data.get("user_message_lang", "en")),
            system_addendum=str(data.get("system_addendum", "")),
            mock=mock,
            session=session,
        )


def _parse_blocks(raw: list[Any]) -> list[CaseBlock]:
    return [
        CaseBlock(
            id=str(b["id"]),
            content=str(b["content"]),
            source_type=str(b.get("source_type", "prose")),
        )
        for b in raw
    ]


def _parse_session(raw: Any) -> BenchmarkSession | None:
    if not raw:
        return None
    if not isinstance(raw, dict):
        raise ValueError("session must be an object")
    turns_raw = raw.get("turns") or []
    if not turns_raw:
        raise ValueError("session.turns must not be empty")
    turns: list[SessionTurn] = []
    for item in turns_raw:
        turns.append(
            SessionTurn(
                blocks=_parse_blocks(item.get("blocks") or []),
                question=str(item["question"]),
                expected_facts=[str(x) for x in item.get("expected_facts", [])],
            )
        )
    return BenchmarkSession(session_id=str(raw.get("session_id", "")), turns=turns)


@dataclass
class GateConfig:
    t_coe_p95_ms: float | None = None
    comprehension_similarity: float | None = None
    comprehension_delta_min: float | None = None
    factual_recall: float | None = None
    readability_score_min: float | None = None
    readability_delta_max: float | None = None
    artifact_leak_rate_max: float | None = None
    user_language_match: float | None = None


@dataclass
class PipelineProfile:
    id: str
    description: str
    levels: list[int]
    target_lang: str | None
    locale: str | None
    l0: bool
    options: dict[str, Any]
    gate: GateConfig
    tier_ci: bool = True
    tier_release: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineProfile:
        gate_raw = data.get("gate") or {}
        tier = data.get("tier") or {}
        return cls(
            id=str(data["id"]),
            description=str(data.get("description", "")),
            levels=[int(x) for x in data.get("levels", [1])],
            target_lang=data.get("target_lang"),
            locale=data.get("locale"),
            l0=bool(data.get("l0", False)),
            options=dict(data.get("options") or {}),
            gate=GateConfig(
                t_coe_p95_ms=gate_raw.get("t_coe_p95_ms"),
                comprehension_similarity=gate_raw.get("comprehension_similarity"),
                comprehension_delta_min=gate_raw.get("comprehension_delta_min"),
                factual_recall=gate_raw.get("factual_recall"),
                readability_score_min=gate_raw.get("readability_score_min"),
                readability_delta_max=gate_raw.get("readability_delta_max"),
                artifact_leak_rate_max=gate_raw.get("artifact_leak_rate_max"),
                user_language_match=gate_raw.get("user_language_match"),
            ),
            tier_ci=bool(tier.get("ci", True)),
            tier_release=bool(tier.get("release", True)),
        )


@dataclass
class CaseMetrics:
    t_coe_ms: float
    optimized_tokens: int
    original_tokens: int
    prose_ratio: float
    artifact_leak: bool
    factual_recall: float | None = None
    factual_f1: float | None = None
    comprehension_similarity: float | None = None
    comprehension_delta: float | None = None
    readability_score: float | None = None
    readability_score_a: float | None = None
    user_language_ok: bool | None = None
    response_artifact_leak: bool = False


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    failures: list[str]
    metrics: CaseMetrics
    optimized_context_preview: str = ""
    mock_arm_a: str = ""
    mock_arm_b: str = ""


@dataclass
class BenchmarkReport:
    harness_version: str
    profile_id: str
    tier: str
    evaluator: str
    cases_run: int
    cases_passed: int
    gate_passed: bool
    gate_failures: list[str]
    results: list[CaseResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "harness_version": self.harness_version,
            "profile_id": self.profile_id,
            "tier": self.tier,
            "evaluator": self.evaluator,
            "cases_run": self.cases_run,
            "cases_passed": self.cases_passed,
            "gate_passed": self.gate_passed,
            "gate_failures": self.gate_failures,
            "summary": self.summary,
            "results": [
                {
                    "case_id": r.case_id,
                    "passed": r.passed,
                    "failures": r.failures,
                    "metrics": {
                        "t_coe_ms": round(r.metrics.t_coe_ms, 2),
                        "optimized_tokens": r.metrics.optimized_tokens,
                        "original_tokens": r.metrics.original_tokens,
                        "prose_ratio": round(r.metrics.prose_ratio, 4),
                        "artifact_leak": r.metrics.artifact_leak,
                        "factual_recall": r.metrics.factual_recall,
                        "factual_f1": r.metrics.factual_f1,
                        "comprehension_similarity": r.metrics.comprehension_similarity,
                        "comprehension_delta": r.metrics.comprehension_delta,
                        "readability_score": r.metrics.readability_score,
                        "readability_score_a": r.metrics.readability_score_a,
                        "user_language_ok": r.metrics.user_language_ok,
                        "response_artifact_leak": r.metrics.response_artifact_leak,
                    },
                    "optimized_context_preview": r.optimized_context_preview[:500],
                }
                for r in self.results
            ],
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data
