# COE examples

| File | Use |
|------|-----|
| [acme_rag_en.json](acme_rag_en.json) | **Canonical** — `python run.py --demo`, curl, MCP |
| [level1_acme.json](level1_acme.json) | Legacy N1-only demo (ES) — use `acme_rag_en.json` instead |
| [mcp_optimize_rag.json](mcp_optimize_rag.json) | MCP `optimize_context` payload |
| [http_optimize_rag.json](http_optimize_rag.json) | `curl -d @... POST /optimize` |
| [n5_session_turn2.json](n5_session_turn2.json) | Second turn with `session_id` |
| [structured_block.json](structured_block.json) | JSON → N1-friendly lines |
| [code_blocks.json](code_blocks.json) | Code dedup by signature |
| [glossary_block.json](glossary_block.json) | Glossary + session memory |

Guide: [../docs/getting-started.md](../docs/getting-started.md)
