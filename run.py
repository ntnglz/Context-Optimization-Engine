#!/usr/bin/env python3
"""Punto de entrada del Context Optimization Engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
EXAMPLE = ROOT / "data" / "examples" / "level1_acme.json"


def run_demo() -> int:
    sys.path.insert(0, str(ROOT / "src"))

    from coe.level1 import deduplicate_context
    from coe.models import ContextBlock

    if EXAMPLE.exists():
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        blocks = [ContextBlock(**item) for item in data["blocks"]]
        print(f"# {data.get('description', 'Demo Nivel 1')}\n")
    else:
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nCliente: Globex"),
            ContextBlock(id="B", content="Empresa: ACME\nPresupuesto: 50k"),
            ContextBlock(id="C", content="Empresa: ACME\nCliente: Globex"),
        ]

    print("## Entrada\n")
    for block in blocks:
        print(f"[{block.id}]")
        print(block.content)
        print()

    result = deduplicate_context(blocks)
    print("## Salida optimizada (Nivel 1)\n")
    print(result.render())
    print(f"Tokens estimados: {result.original_tokens} → {result.optimized_tokens}")
    print(f"Ahorro: {result.compression_ratio:.1%} ({result.tokens_saved} tokens)")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Context Optimization Engine (COE)")
    parser.add_argument("--demo", action="store_true", help="Demo Nivel 1 deduplicación")
    parser.add_argument("--test", action="store_true", help="Ejecutar tests")
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI smoke local: pytest + 8 perfiles benchmark con compare baseline",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Ejecutar harness smoke (equiv. scripts/benchmark/run.py --tier smoke --profile n1)",
    )
    parser.add_argument(
        "--release-dev-agent",
        action="store_true",
        help="Release tier dev_agent con Ollama qwen3:4b (scripts/ci/release-dev-agent.sh)",
    )
    parser.add_argument(
        "--benchmark-dev-agent-fast",
        action="store_true",
        help="Iteración rápida dev_agent con Granite/Gemma (informativo; ver docs/benchmark-ollama.md)",
    )
    parser.add_argument("--profile", default="n1", help="Perfil benchmark con --benchmark")
    args = parser.parse_args()

    if args.demo:
        return run_demo()
    if args.test:
        return run_tests()
    if args.ci:
        return run_ci()
    if args.release_dev_agent:
        import subprocess

        script = ROOT / "scripts" / "ci" / "release-dev-agent.sh"
        return subprocess.call(["bash", str(script)], cwd=ROOT)
    if args.benchmark_dev_agent_fast:
        import subprocess

        script = ROOT / "scripts" / "ci" / "benchmark-dev-agent-fast.sh"
        return subprocess.call(["bash", str(script)], cwd=ROOT)
    if args.benchmark:
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

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
