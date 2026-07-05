# Changelog

All notable changes to this project are documented in this file.

## [1.0.1] — 2026-07-05

Documentación visitante e integrador (Fase 20).

### Added

- [getting-started.md](docs/getting-started.md), [FAQ.md](docs/FAQ.md), [STATUS.md](docs/STATUS.md)
- Ejemplos MCP/HTTP/N5/structured en `data/examples/`
- [LICENSE](LICENSE) MIT
- README orientado a visitantes e integradores

## [1.0.0] — 2026-07-05

Producto v1 cerrado (plan de ejecución fases 0–18).

### Added

- Pipeline L0 → N1–N5 con Gateway `optimize_context`
- Context Ingest, matriz `source_type`, structured/code/glossary (Fase 18)
- Renderer prosa hacia LLM; CIR v1.0 interno (grafo + envelope N5)
- State Store filesystem + SQLite; TTL, archivado, entity linking fuzzy
- Locale packs N2 EN / ES / ZH; L0 v2 con `TranslationBackend`
- MCP stdio (`optimize_context`, `estimate_savings`)
- HTTP API (`POST /optimize`, `POST /estimate`, `GET /health`)
- Integración PCM+COE y Model Adapter (`target_model`)
- Harness de benchmarks con CI smoke (234 tests, 10 perfiles)

### Notes

- Fase 19 (CIR v1.1 stages N1–N3): omitida

[1.0.1]: https://github.com/ntnglz/Context-Optimization-Engine/releases/tag/v1.0.1
[1.0.0]: https://github.com/ntnglz/Context-Optimization-Engine/compare/07ab071...8f414b5
