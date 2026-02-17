# Changelog

All notable changes to Memento will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Logging infrastructure (`scripts/logging_config.py`)
- CI/CD with GitHub Actions
- Linting configuration (flake8)
- pyproject.toml for modern packaging
- CONTRIBUTING.md and CHANGELOG.md

### Changed
- Improved project structure documentation

## [0.2.0] - 2026-02-17

### Added
- **Persistent Disk Cache** - SQLite-based cache survives restarts (Bob)
- **Full CLI** - Rich terminal interface with smart piping (Bob)
- **Test Suite** - pytest coverage for core and cache (Bob)
- **LRU Caching** - 500,000x speedup for repeated queries (Rita)
- **AVX2/ONNX Auto-detection** - Hardware acceleration when available (Rita)
- **Vector Search Backends** - hnswlib/FAISS/NumPy auto-select (Rita)
- **Batch Queries** - Optimized multi-query search (Rita)
- **Release Notes** - v0.2.0 release documentation

### Changed
- Merged divergent optimizations from Rita and Bob
- Performance: 0.03ms search (was ~9ms)
- Boot time: Instant via disk cache (was ~4s cold)

## [0.1.0] - 2026-02-16

### Added
- Initial release
- Core memory storage (SQLite + NumPy)
- Semantic search with MiniLM embeddings
- Document ingestion
- Dashboard
- Auto-store for conversation memory

