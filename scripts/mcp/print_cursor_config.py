#!/usr/bin/env python3
"""Print Cursor MCP config JSON with absolute paths for this repo."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for candidate in (ROOT / ".venv" / "bin" / "python", ROOT / ".venv" / "bin" / "python3"):
    if candidate.exists():
        py = candidate
        break
else:
    py = Path(sys.executable)

print(
    json.dumps(
        {
            "mcpServers": {
                "coe": {
                    "command": str(py),
                    "args": [str((ROOT / "scripts/mcp/run_server.py").resolve())],
                    "env": {},
                }
            }
        },
        indent=2,
    )
)
