# Memento Development Tickets
*Single Source of Truth (SSOT)*
*Last Updated: 2026-02-17 08:23 GMT*

Use this file to track all work. Check off items when done, add your name when starting.

---

## Legend

- `[ ]` - Not started
- `[@Bob]` - Bob is working on it
- `[@Rita]` - Rita is working on it
- `[x]` - Completed

---

## Phase 1: Foundation ✅ COMPLETE

| Ticket | Description | Status | Notes |
|--------|-------------|--------|-------|
| #1 | Core memory storage (SQLite + NumPy) | [x] | v0.1.0 |
| #2 | Semantic search with MiniLM | [x] | v0.1.0 |
| #3 | Document ingestion | [x] | v0.1.0 |
| #4 | Dashboard | [x] | v0.1.0 |
| #5 | Auto-store for conversations | [x] | v0.1.0 |

## Phase 2: Performance ✅ COMPLETE

| Ticket | Description | Status | Assignee | Notes |
|--------|-------------|--------|----------|-------|
| #6 | LRU caching for embeddings | [x] | @Rita | 500,000x speedup |
| #7 | Persistent disk cache (SQLite) | [x] | @Bob | 4ms cold boot |
| #8 | AVX2/ONNX auto-detection | [x] | @Rita | Hardware accel |
| #9 | Vector search backends | [x] | @Rita | hnswlib/FAISS/NumPy |
| #10 | Batch query optimization | [x] | @Rita | Multi-query support |
| #11 | CLI with rich output | [x] | @Bob | Smart piping |

## Phase 3: Hardening 🔄 IN PROGRESS

### Infrastructure

| Ticket | Description | Status | Assignee | Notes |
|--------|-------------|--------|----------|-------|
| #12 | Add type hints to `store.py` | [@Bob] | @Bob | MemoryStore class |
| #13 | Add type hints to `embed.py` | [x] | @Bob | Done! |
| #14 | Add type hints to `cli.py` | [ ] | | All CLI functions |
| #15 | Add type hints to `search.py` | [ ] | | Search functions |
| #16 | Create `scripts/types.py` | [ ] | | Shared type definitions |
| #17 | Fix bare `except:` clauses | [x] | @Rita | Fixed 4 in dashboard.py |
| #18 | Create `MementoError` class | [x] | @Rita | scripts/exceptions.py |

### Testing

| Ticket | Description | Status | Assignee | Target |
|--------|-------------|--------|----------|--------|
| #19 | Test `embed.py` cache scenarios | [ ] | | 80% coverage |
| #20 | Test `store.py` edge cases | [ ] | | 70% coverage |
| #21 | Test `search.py` hybrid search | [ ] | | 60% coverage |
| #22 | Test `ingest.py` document loading | [ ] | | 50% coverage |
| #23 | Test `cli.py` argument parsing | [ ] | | 40% coverage |
| #24 | Test concurrent access | [ ] | | Threading safety |

### Reliability

| Ticket | Description | Status | Assignee | Notes |
|--------|-------------|--------|----------|-------|
| #25 | Config system (YAML) | [ ] | @Bob | ~/.memento/config.yaml |
| #26 | DB migrations | [ ] | @Bob | schema_version table |
| #27 | Input validation | [ ] | @Bob | Length limits, sanitization |
| #28 | Migrate prints to logging | [@Bob] | @Bob | Use logging_config.py |
| #29 | Query timeout option | [ ] | | Prevent hangs |
| #30 | Pagination for results | [ ] | | Limit result sets |

## Phase 4: Polish 📋 BACKLOG

| Ticket | Description | Status | Notes |
|--------|-------------|--------|-------|
| #31 | Dockerfile | [ ] | For easy deployment |
| #32 | PyPI package | [ ] | pip install memento-ai |
| #33 | API documentation | [ ] | Sphinx |
| #34 | REST API | [ ] | FastAPI option |
| #35 | Web UI | [ ] | Browser dashboard |
| #36 | Federation sync | [ ] | Node-to-node sync |

## Phase 5: Experimentation 💡 IDEAS

| Ticket | Description | Status | Notes |
|--------|-------------|--------|-------|
| #37 | Rust port | [ ] | memento_rs started |
| #38 | ONNX conversion | [ ] | Stub exists, broken |

---

## Current Sprint

**Active:**
- @Bob: #12 (Type hints), #28 (Logging migration)

**Next Up:**
- #17 (Fix bare excepts) - Quick win
- #19-23 (More tests) - Coverage

**Blocked:**
- #37 (Rust) - OpenSSL issues
- #38 (ONNX) - Conversion broken

---

## How to Use This File

1. **Before starting work:** Find an unassigned ticket, add your name
2. **While working:** Keep this file updated with progress
3. **When done:** Mark as `[x]`, commit with ticket number

**Commit format:**
```
Ticket #17: Fix bare except clauses in store.py

- Replaced 3 bare excepts with specific exceptions
- Added MementoError wrapper
```

---

## Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Type hint coverage | 100% | ~5% |
| Test coverage | 80% | ~20% |
| Docs coverage | 100% public APIs | ~30% |
| Open tickets | 0 | 27 |
| Completed | 11 | 11 |

---

*This is the SSOT. All work tracked here.*
