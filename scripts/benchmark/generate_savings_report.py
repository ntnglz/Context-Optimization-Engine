#!/usr/bin/env python3
"""Generate visitor-facing token savings docs from versioned benchmark baselines."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINES_DIR = ROOT / "data" / "benchmarks" / "baselines"
RESULTS_DOC = ROOT / "docs" / "benchmark-results.md"
README = ROOT / "README.md"

MARKER_START = "<!-- coe-savings:start -->"
MARKER_END = "<!-- coe-savings:end -->"

# Profiles shown to visitors (recommended defaults and multilingual variants).
VISITOR_PROFILES: tuple[tuple[str, str], ...] = (
    ("n1_n2_en_smoke.json", "Dedup + entity grouping (EN) — **default for narrative RAG**"),
    ("n1_n2_es_smoke.json", "Dedup + entity grouping (ES)"),
    ("n1_n2_zh_smoke.json", "Dedup + entity grouping (ZH)"),
)

# Illustrative cost example (acme_budget_v1, n1_n2_en).
COST_EXAMPLE = {
    "case_id": "acme_budget_v1",
    "profile_file": "n1_n2_en_smoke.json",
    "requests_per_day": 10_000,
    "price_per_million_usd": 2.50,
}


@dataclass(frozen=True)
class CaseSavings:
    case_id: str
    original_tokens: int
    optimized_tokens: int

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.optimized_tokens

    @property
    def savings_pct(self) -> float:
        if self.original_tokens <= 0:
            return 0.0
        return 100.0 * self.tokens_saved / self.original_tokens


@dataclass(frozen=True)
class ProfileSavings:
    profile_id: str
    label: str
    cases: tuple[CaseSavings, ...]
    factual_recall_mean: float | None
    comprehension_similarity_mean: float | None

    @property
    def cases_with_savings(self) -> tuple[CaseSavings, ...]:
        return tuple(c for c in self.cases if c.tokens_saved > 0)

    @property
    def min_savings_pct(self) -> float | None:
        saved = self.cases_with_savings
        if not saved:
            return None
        return min(c.savings_pct for c in saved)

    @property
    def max_savings_pct(self) -> float | None:
        saved = self.cases_with_savings
        if not saved:
            return None
        return max(c.savings_pct for c in saved)


def _load_profile(path: Path, label: str) -> ProfileSavings:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases: list[CaseSavings] = []
    for row in data.get("results", []):
        metrics = row.get("metrics") or {}
        if "original_tokens" not in metrics or "optimized_tokens" not in metrics:
            continue
        cases.append(
            CaseSavings(
                case_id=row.get("case_id", "?"),
                original_tokens=int(metrics["original_tokens"]),
                optimized_tokens=int(metrics["optimized_tokens"]),
            )
        )
    summary = data.get("summary") or {}
    return ProfileSavings(
        profile_id=data.get("profile_id", path.stem),
        label=label,
        cases=tuple(cases),
        factual_recall_mean=summary.get("factual_recall_mean"),
        comprehension_similarity_mean=summary.get("comprehension_similarity_mean"),
    )


def load_visitor_profiles() -> list[ProfileSavings]:
    profiles: list[ProfileSavings] = []
    for filename, label in VISITOR_PROFILES:
        path = BASELINES_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing baseline: {path}")
        profiles.append(_load_profile(path, label))
    return profiles


def _overall_savings_range(profiles: list[ProfileSavings]) -> tuple[float, float] | None:
    pcts: list[float] = []
    for profile in profiles:
        for case in profile.cases_with_savings:
            pcts.append(case.savings_pct)
    if not pcts:
        return None
    return min(pcts), max(pcts)


def _find_case(profiles: list[ProfileSavings], profile_file: str, case_id: str) -> CaseSavings | None:
    path = BASELINES_DIR / profile_file
    profile_id = json.loads(path.read_text(encoding="utf-8")).get("profile_id")
    for profile in profiles:
        if profile.profile_id != profile_id:
            continue
        for case in profile.cases:
            if case.case_id == case_id:
                return case
    return None


def _monthly_cost_saved(case: CaseSavings, *, requests_per_day: int, price_per_million_usd: float) -> float:
    daily_tokens_saved = case.tokens_saved * requests_per_day
    monthly_tokens_saved = daily_tokens_saved * 30
    return monthly_tokens_saved / 1_000_000 * price_per_million_usd


def render_readme_section(profiles: list[ProfileSavings]) -> str:
    savings_range = _overall_savings_range(profiles)
    range_line = (
        f"**Typical savings:** ~{savings_range[0]:.0f}–{savings_range[1]:.0f}% fewer context tokens"
        if savings_range
        else "**Typical savings:** varies by payload"
    )

    example = _find_case(profiles, COST_EXAMPLE["profile_file"], COST_EXAMPLE["case_id"])
    cost_block = ""
    if example and example.tokens_saved > 0:
        monthly = _monthly_cost_saved(
            example,
            requests_per_day=COST_EXAMPLE["requests_per_day"],
            price_per_million_usd=COST_EXAMPLE["price_per_million_usd"],
        )
        cost_block = (
            f"\n**Illustrative cost** ({COST_EXAMPLE['requests_per_day']:,} requests/day, "
            f"${COST_EXAMPLE['price_per_million_usd']:.2f}/M input tokens): "
            f"~**${monthly:,.0f}/month** saved on context input for the "
            f"`{example.case_id}` case ({example.original_tokens} → {example.optimized_tokens} tokens). "
            f"Run [`estimate_savings`](docs/benchmark-results.md#try-on-your-data) on your data — not a guarantee.\n"
        )

    lines = [
        "## Savings at a glance",
        "",
        f"{range_line} on repetitive narrative RAG — **no extra LLM calls**, no summarization.",
        "Quality gate on smoke benchmarks: `factual_recall` ≥ 0.95, `comprehension_similarity` ≥ 0.90.",
        cost_block.rstrip(),
        "",
        "| Profile | Case | Before | After | Saved |",
        "|---------|------|--------|-------|-------|",
    ]
    for profile in profiles:
        for case in profile.cases_with_savings:
            lines.append(
                f"| {profile.profile_id} | `{case.case_id}` | {case.original_tokens} | "
                f"{case.optimized_tokens} | **{case.savings_pct:.0f}%** |"
            )
    lines.extend(
        [
            "",
            "Full tables, methodology, and reproduce commands: **[docs/benchmark-results.md](docs/benchmark-results.md)**",
            "",
            "_Regenerate after baseline refresh: `python scripts/benchmark/generate_savings_report.py`_",
        ]
    )
    return "\n".join(line for line in lines if line is not None)


def render_results_doc(profiles: list[ProfileSavings]) -> str:
    savings_range = _overall_savings_range(profiles)
    range_text = (
        f"~{savings_range[0]:.0f}–{savings_range[1]:.0f}%"
        if savings_range
        else "varies"
    )

    lines = [
        "# Benchmark results — token savings",
        "",
        "> Auto-generated from `data/benchmarks/baselines/`. "
        "Do not edit by hand — run `python scripts/benchmark/generate_savings_report.py`.",
        "",
        "COE optimizes **context** you already retrieved. Savings depend on repetition and structure; "
        "these smoke cases use narrative RAG with duplicated facts across chunks.",
        "",
        "## Summary",
        "",
        f"- **Typical token reduction** (recommended `levels=[1, 2]`): **{range_text}**",
        "- **No extra LLM** — deterministic pipeline; savings are measured, not generated",
        "- **Quality preserved** — smoke gate requires high factual recall and comprehension similarity",
        "",
        "## Results by profile",
        "",
    ]

    for profile in profiles:
        lines.append(f"### `{profile.profile_id}`")
        lines.append("")
        lines.append(profile.label)
        lines.append("")
        if profile.factual_recall_mean is not None:
            lines.append(
                f"- `factual_recall_mean`: {profile.factual_recall_mean:.2f}"
            )
        if profile.comprehension_similarity_mean is not None:
            lines.append(
                f"- `comprehension_similarity_mean`: {profile.comprehension_similarity_mean:.2f}"
            )
        lines.append("")
        lines.append("| Case | Before | After | Tokens saved | Reduction |")
        lines.append("|------|--------|-------|--------------|-----------|")
        for case in profile.cases:
            saved = case.tokens_saved
            pct = f"{case.savings_pct:.0f}%" if saved > 0 else "—"
            saved_cell = str(saved) if saved > 0 else "—"
            lines.append(
                f"| `{case.case_id}` | {case.original_tokens} | {case.optimized_tokens} | "
                f"{saved_cell} | {pct} |"
            )
        lines.append("")

    example = _find_case(profiles, COST_EXAMPLE["profile_file"], COST_EXAMPLE["case_id"])
    lines.extend(["## Illustrative monthly cost", ""])
    if example and example.tokens_saved > 0:
        monthly = _monthly_cost_saved(
            example,
            requests_per_day=COST_EXAMPLE["requests_per_day"],
            price_per_million_usd=COST_EXAMPLE["price_per_million_usd"],
        )
        lines.extend(
            [
                f"Using `{example.case_id}` (`{example.original_tokens}` → `{example.optimized_tokens}` tokens):",
                "",
                "| Assumption | Value |",
                "|------------|-------|",
                f"| Requests per day | {COST_EXAMPLE['requests_per_day']:,} |",
                f"| Input price | ${COST_EXAMPLE['price_per_million_usd']:.2f} / 1M tokens |",
                f"| Tokens saved per request | {example.tokens_saved} |",
                f"| **Estimated monthly savings** | **~${monthly:,.0f}** |",
                "",
                "Adjust inputs for your model pricing and traffic. COE adds negligible latency "
                f"(smoke p95 &lt; 1 ms on these cases).",
                "",
            ]
        )

    lines.extend(
        [
            "## Try on your data",
            "",
            "**Python** — check `out.metrics` after `optimize_context(...)`:",
            "",
            "```python",
            "from coe import optimize_context",
            "out = optimize_context(blocks, levels=[1, 2], locale=\"en\")",
            "print(out.metrics.original_tokens, out.metrics.optimized_tokens)",
            "```",
            "",
            "**MCP / HTTP** — `estimate_savings` returns metrics without optimized prose:",
            "",
            "```bash",
            "curl -s -X POST http://127.0.0.1:8080/estimate \\",
            "  -H 'Content-Type: application/json' \\",
            "  -d @data/examples/acme_rag_en.json",
            "```",
            "",
            "## Reproduce",
            "",
            "Smoke benchmarks (mock evaluator, no Ollama):",
            "",
            "```bash",
            "python run.py --ci",
            "# or a single profile:",
            "python scripts/benchmark/run.py --tier smoke --profile n1_n2_en \\",
            "  --compare-baseline data/benchmarks/baselines/n1_n2_en_smoke.json",
            "```",
            "",
            "Refresh baselines after intentional pipeline changes — see "
            "`data/benchmarks/baselines/README.md`.",
            "",
            "Regenerate this page:",
            "",
            "```bash",
            "python scripts/benchmark/generate_savings_report.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _extract_readme_section(readme_text: str) -> str | None:
    pattern = re.compile(
        re.escape(MARKER_START) + r"\n(.*?)\n" + re.escape(MARKER_END),
        flags=re.DOTALL,
    )
    match = pattern.search(readme_text)
    return match.group(1) if match else None


def _patch_readme(readme_text: str, section: str) -> str:
    block = f"{MARKER_START}\n{section}\n{MARKER_END}"
    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        flags=re.DOTALL,
    )
    if pattern.search(readme_text):
        return pattern.sub(block, readme_text, count=1)
    raise ValueError(
        f"README.md must contain {MARKER_START} and {MARKER_END} markers"
    )


def generate(*, write: bool = True) -> tuple[str, str]:
    profiles = load_visitor_profiles()
    readme_section = render_readme_section(profiles)
    results_doc = render_results_doc(profiles)
    if write:
        RESULTS_DOC.write_text(results_doc + "\n", encoding="utf-8")
        readme_text = README.read_text(encoding="utf-8")
        README.write_text(_patch_readme(readme_text, readme_section) + "\n", encoding="utf-8")
    return readme_section, results_doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate COE savings docs from baselines")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if generated files differ from disk (for CI)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print README section to stdout instead of writing files",
    )
    args = parser.parse_args(argv)

    try:
        readme_section, results_doc = generate(write=not args.stdout and not args.check)
    except (OSError, json.JSONDecodeError, ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.stdout:
        print(readme_section)
        return 0

    if args.check:
        drift: list[str] = []
        on_disk_results = RESULTS_DOC.read_text(encoding="utf-8") if RESULTS_DOC.exists() else ""
        if on_disk_results != results_doc + "\n":
            drift.append(str(RESULTS_DOC.relative_to(ROOT)))
        readme_text = README.read_text(encoding="utf-8")
        current_section = _extract_readme_section(readme_text)
        if current_section != readme_section:
            drift.append(str(README.relative_to(ROOT)))
        if drift:
            print(
                "Savings docs out of date — run: python scripts/benchmark/generate_savings_report.py",
                file=sys.stderr,
            )
            for path in drift:
                print(f"  - {path}", file=sys.stderr)
            return 1
        print("Savings docs: up to date")
        return 0

    print(f"Wrote {RESULTS_DOC.relative_to(ROOT)}")
    print(f"Updated {README.relative_to(ROOT)} ({MARKER_START} block)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
