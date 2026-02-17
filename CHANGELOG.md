# Changelog

All notable changes to Memento will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Full type hint coverage across all modules
- GitHub Actions CI/CD pipeline

### Changed
- Improved documentation for all public APIs

## [0.2.2] - 2026-02-17

### Added
- **Background Model Loading** - Fixes cold start latency (#13)
  - Model loads in background thread on module import
  - `warmup()` function for explicit pre-loading
  - `is_model_ready()` and `wait_for_model()` for status checking
  - Cold start reduced from ~10s to ~1s
- **Query Timeout Support** - Cross-platform timeout for search operations (#14)
  - New `timeout_ms` parameter in `recall()` method
  - `QueryTimeoutError` exception for timeout handling
  - Unix (SIGALRM) and Windows (threading) implementations
  - Default 5s timeout prevents runaway queries
- **Complete Type Hints** - Full mypy-compatible type annotations (#12, #13, #14, #15)
  - `store.py`: MemoryStore class fully typed
  - `embed.py`: All embedding functions typed
  - `cli.py`: CLI functions and argument parsers typed
  - `search.py`: Search functions and filters typed
  - `models.py`: Dataclass definitions with proper types
- **GitHub Actions CI** - Automated testing on push/PR
  - Tests on Python 3.8, 3.9, 3.10, 3.11, 3.12
  - Model caching for faster CI runs
  - Linting with flake8

### Fixed
- **Import paths in analyze_bottlenecks.py** - Fixed 'No module named scripts' error (#15)
  - Analyzer now correctly detects embedder and generates bottleneck reports
- **SearchResult item assignment** - Fixed dict-like assignment for dynamic fields (#17)
- **PersistentCache.get_cache_key** - Added missing method for test compatibility (#18)

### Changed
- pyproject.toml version bumped to 0.2.2
- Enhanced docstrings across all public APIs
- Improved error messages with more context

## [0.2.1] - 2026-02-17

### Added
- **Echo Notifications** 💾 - Visible CLI feedback when memories stored
- **MEMORY_ECHO env var** - Control notification display
- **Lower storage threshold** - 0.15 (was 0.3), captures ~40% more conversations

### Changed  
- Session watcher shows cleaner output with emoji confirmations
- [auto] vs [explicit] tags distinguish auto-store from "remember this"

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
