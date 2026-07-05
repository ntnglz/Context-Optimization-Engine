#!/usr/bin/env python3
"""Context Optimization Engine entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
EXAMPLE = ROOT / "data" / "examples" / "acme_rag_en.json"


def _ensure_src_path() -> None:
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _load_canonical_example() -> tuple[dict, list]:
    from coe.models import ContextBlock

    if EXAMPLE.exists():
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        blocks = [ContextBlock(**item) for item in data["blocks"]]
        return data, blocks

    blocks = [
        ContextBlock(id="A", content="Company: ACME\nJuan works at ACME.", source_type="rag"),
        ContextBlock(
            id="B",
            content="Company: ACME\nBudget: 50k\nJuan approved the budget.",
            source_type="rag",
        ),
        ContextBlock(id="C", content="Company: ACME\nPedro works at ACME.", source_type="rag"),
    ]
    return {"description": "Canonical ACME RAG example", "levels": [1, 2], "locale": "en"}, blocks


def run_demo(*, show_snippet: bool = False) -> int:
    _ensure_src_path()

    from coe import optimize_context

    data, blocks = _load_canonical_example()
    levels = data.get("levels", [1, 2])
    locale = data.get("locale", "en")

    print(f"# {data.get('description', 'COE demo')}\n")
    print("## Input\n")
    for block in blocks:
        print(f"[{block.id}]")
        print(block.content)
        print()

    result = optimize_context(blocks, levels=levels, locale=locale)
    print("## Optimized output\n")
    print(result.text)
    print(
        f"\nEstimated tokens: {result.metrics.original_tokens} → "
        f"{result.metrics.optimized_tokens}"
    )
    print(
        f"Savings: {result.metrics.compression_ratio:.1%} "
        f"({result.metrics.original_tokens - result.metrics.optimized_tokens} tokens)"
    )

    if show_snippet:
        print("\n## Copy-paste (Python)\n")
        print(
            "from coe import optimize_context\n"
            "from coe.models import ContextBlock\n\n"
            "blocks = [\n"
            '    ContextBlock(id="A", content="Company: ACME\\nJuan works at ACME.", source_type="rag"),\n'
            '    ContextBlock(id="B", content="Company: ACME\\nBudget: 50k\\nJuan approved the budget.", source_type="rag"),\n'
            '    ContextBlock(id="C", content="Company: ACME\\nPedro works at ACME.", source_type="rag"),\n'
            "]\n"
            'out = optimize_context(blocks, levels=[1, 2], locale="en")\n'
            "print(out.text)"
        )

    return 0


def run_tests() -> int:
    import subprocess

    return subprocess.call(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        cwd=ROOT,
    )


def run_ci() -> int:
    import subprocess

    script = ROOT / "scripts" / "ci" / "smoke.sh"
    return subprocess.call(["bash", str(script)], cwd=ROOT)


def _add_visitor_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--demo", action="store_true", help="Canonical EN RAG demo (optimize_context)")
    parser.add_argument(
        "--quickstart",
        action="store_true",
        help="Same as --demo plus copy-paste Python snippet",
    )
    parser.add_argument("--test", action="store_true", help="Run pytest suite")
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Local CI smoke: pytest + benchmark profiles",
    )


def _add_maintainer_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="(maintainer) Run benchmark harness smoke tier",
    )
    parser.add_argument(
        "--release-dev-agent",
        action="store_true",
        help="(maintainer) Release tier dev_agent with Ollama qwen3:4b",
    )
    parser.add_argument(
        "--benchmark-dev-agent-fast",
        action="store_true",
        help="(maintainer) Fast dev_agent iteration (see docs/benchmark-ollama.md)",
    )
    parser.add_argument(
        "--profile",
        default="n1",
        help="(maintainer) Benchmark profile with --benchmark",
    )


def _print_visitor_help() -> None:
    print(
        "Context Optimization Engine (COE)\n\n"
        "Visitor commands:\n"
        "  python run.py --demo         Canonical EN RAG example\n"
        "  python run.py --quickstart   Demo + copy-paste Python snippet\n"
        "  python run.py --test         Run tests\n"
        "  python run.py --ci           Local CI smoke\n\n"
        "Maintainer commands: python run.py --help-all\n"
    )


def main(argv: list[str] | None = None) -> int:
    if argv is not None:
        sys.argv = [sys.argv[0], *argv]

    if "--help-all" in sys.argv:
        parser = argparse.ArgumentParser(description="Context Optimization Engine (COE)")
        _add_visitor_args(parser)
        _add_maintainer_args(parser)
        parser.print_help()
        return 0

    parser = argparse.ArgumentParser(description="Context Optimization Engine (COE)", add_help=True)
    _add_visitor_args(parser)
    args, unknown = parser.parse_known_args()

    if unknown:
        maintainer = argparse.ArgumentParser(description="COE maintainer flags")
        _add_maintainer_args(maintainer)
        margs = maintainer.parse_args(unknown, namespace=args)
        args = margs

    if args.demo:
        return run_demo()
    if args.quickstart:
        return run_demo(show_snippet=True)
    if args.test:
        return run_tests()
    if args.ci:
        return run_ci()
    if getattr(args, "release_dev_agent", False):
        import subprocess

        script = ROOT / "scripts" / "ci" / "release-dev-agent.sh"
        return subprocess.call(["bash", str(script)], cwd=ROOT)
    if getattr(args, "benchmark_dev_agent_fast", False):
        import subprocess

        script = ROOT / "scripts" / "ci" / "benchmark-dev-agent-fast.sh"
        return subprocess.call(["bash", str(script)], cwd=ROOT)
    if getattr(args, "benchmark", False):
        import subprocess

        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "benchmark" / "run.py"),
            "--tier",
            "smoke",
            "--profile",
            args.profile,
        ]
        return subprocess.call(cmd, cwd=ROOT)

    if len(sys.argv) == 1:
        _print_visitor_help()
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
