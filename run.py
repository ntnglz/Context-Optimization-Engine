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


def main() -> int:
    parser = argparse.ArgumentParser(description="Context Optimization Engine (COE)")
    parser.add_argument("--demo", action="store_true", help="Demo Nivel 1 deduplicación")
    parser.add_argument("--test", action="store_true", help="Ejecutar tests")
    args = parser.parse_args()

    if args.demo:
        return run_demo()
    if args.test:
        return run_tests()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
