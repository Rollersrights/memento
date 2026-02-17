# Memento TODO

*Last updated: 2026-02-17*

## Active Work

### Infrastructure (Type Hints) ✅ COMPLETE

| Ticket | Description | Status | Assignee | Notes |
|--------|-------------|--------|----------|-------|
| #12 | Add type hints to `store.py` | ✅ | @Bob | MemoryStore class - DONE |
| #13 | Add type hints to `embed.py` | ✅ | @Bob | All functions typed - DONE |
| #14 | Add type hints to `cli.py` | ✅ | @Bob | All CLI functions - DONE |
| #15 | Add type hints to `search.py` | ✅ | @Bob | Search functions - DONE |
| #16 | Create `memento/models.py` | ✅ | @Bob | Shared type definitions - DONE |
| #17 | Fix bare `except:` clauses | ✅ | @Bob | Fixed in core & dashboard - DONE |
| #18 | Create `MementoError` class | ✅ | @Rita | memento/exceptions.py - DONE |

### Performance Improvements ✅ COMPLETE

| Ticket | Description | Status | Assignee | Notes |
|--------|-------------|--------|----------|-------|
| #13 | Background model loading | ✅ | @Rita | Cold start ~1s - DONE |
| #14 | Query timeout support | ✅ | @Rita | Cross-platform - DONE |
| #18 | PersistentCache.get_cache_key | ✅ | @Bob | Test compatibility - DONE |

### CI/CD ✅ COMPLETE

| Ticket | Description | Status | Assignee | Notes |
|--------|-------------|--------|----------|-------|
| - | GitHub Actions workflow | ✅ | @Bob | Python 3.8-3.12 - DONE |
| - | Model caching in CI | ✅ | @Bob | Faster builds - DONE |
| - | Linting with flake8 | ✅ | @Bob | Enforced in CI - DONE |

## Backlog

### Testing

| Ticket | Description | Status | Assignee | Target |
|--------|-------------|--------|----------|--------|
| #19 | Test `embed.py` cache scenarios | ✅ | @Rita | 80% coverage |
| #20 | Test `store.py` edge cases | ✅ | @Rita | 70% coverage |
| #21 | Test `search.py` hybrid search | 🔄 | @Bob | 60% coverage |
| #22 | Test `ingest.py` document loading | [ ] | | 50% coverage |
| #23 | Test `cli.py` argument parsing | [ ] | | 40% coverage |
| #24 | Test concurrent access | [ ] | | Threading safety |
| - | Test Rust engine integration | [ ] | | When ready |

### Reliability

| Ticket | Description | Status | Assignee | Notes |
|--------|-------------|--------|----------|-------|
| #25 | Config system (YAML) | ✅ | @Bob | ~/.memento/config.yaml |
| #26 | DB migrations | ✅ | @Bob | schema_version table |
| #27 | Input validation | ✅ | @Bob | Length limits, sanitization |
| #28 | Migrate prints to logging | 🔄 | @Bob | Use logging_config.py |
| #29 | Query timeout option | ✅ | @Rita | Done! |
| #30 | Pagination for results | [ ] | | Limit result sets |

### Rust Integration (RFC-001 Phase 2a)

| Ticket | Description | Status | Assignee | Notes |
|--------|-------------|--------|----------|-------|
| - | Engine ABC interface | [ ] | @Rita | Abstract base class |
| - | Create memento-core crate | [ ] | @Rita | Rust library |
| - | ONNX inference in Rust | [ ] | @Rita | Using `ort` crate |
| - | PyO3 bindings | [ ] | @Rita | Python bindings |
| - | Feature flag MEMENTO_RUST | [ ] | @Rita | Enable/disable |
| - | CI builds for wheels | [ ] | | maturin |

## Future Ideas

- [ ] Web API (FastAPI)
- [ ] Vector visualization
- [ ] Memory consolidation (auto-summarize old memories)
- [ ] Multi-agent memory sharing
- [ ] Import/export formats (JSON, Markdown)
- [ ] Memory browser web UI
- [ ] Plugin system for custom embedders
- [ ] Cloud sync (encrypted)
- [ ] Mobile app

## Completed Milestones

### v0.2.2 (2026-02-17) ✅
- Type hints complete
- Background model loading
- Query timeout support
- GitHub Actions CI

### v0.2.1 (2026-02-17) ✅
- Echo notifications
- Storage threshold tuning

### v0.2.0 (2026-02-17) ✅
- Persistent disk cache
- Full CLI with Rich
- Test suite
- LRU caching
- AVX2/ONNX auto-detection

### v0.1.0 (2026-02-16) ✅
- Initial release
- Core memory storage
- Semantic search
- Document ingestion
