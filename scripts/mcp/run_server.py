#!/usr/bin/env python3
"""Start the COE MCP server over stdio (Cursor, Claude Desktop, etc.)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from coe.mcp.server import main  # noqa: E402

if __name__ == "__main__":
    main()
