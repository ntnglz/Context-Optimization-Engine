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
        blocks = [
            CaseBlock(
                id=str(b["id"]),
                content=str(b["content"]),
                source_type=str(b.get("source_type", "prose")),
            )
            for b in data["blocks"]
        ]
        return cls(
            id=str(data["id"]),
            version=int(data.get("version", 1)),
            tags=list(data.get("tags", [])),
            description=str(data.get("description", "")),
            blocks=blocks,
            question=str(data["question"]),
            expected_facts=[str(x) for x in data.get("expected_facts", [])],
            response_lang=str(data.get("response_lang", "en")),
            user_message_lang=str(data.get("user_message_lang", "en")),
            system_addendum=str(data.get("system_addendum", "")),
            mock=mock,
        )


@dataclass
class GateConfig:
    t_coe_p95_ms: float | None = None
    comprehension_similarity: float | None = None
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

    def to_dict(self) -> dict[str, Any]:
        return {
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
                    },
                    "optimized_context_preview": r.optimized_context_preview[:500],
                }
                for r in self.results
            ],
        }
