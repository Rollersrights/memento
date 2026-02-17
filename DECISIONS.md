# Memento Architectural Decisions

*This document records significant architectural decisions and their rationale.*

## ADR-001: Hybrid Python/Rust Architecture

**Status:** Accepted  
**Date:** 2026-02-17  
**Context:** Performance vs development velocity trade-off

### Decision

Use a "Thin Python, Fat Rust" architecture:
- Python for orchestration, CLI, and rapid iteration
- Rust (via PyO3) for compute-heavy embedding operations
- Abstract Engine interface allows swapping implementations

### Rationale

- Pure Python has ~10s cold start due to model loading
- Rust with ONNX can reduce this to ~1-2s
- Full Rust rewrite would sacrifice development velocity
- Hybrid gives us 80% of the benefit with 20% of the effort

### Consequences

- **Positive:** Better performance, gradual migration path
- **Negative:** Complex build (maturin/cargo), dual language maintenance

---

## ADR-002: SQLite for Primary Storage

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** Storage backend selection

### Decision

Use SQLite as the primary storage backend.

### Rationale

- Zero configuration required
- Single file, easy backup/restore
- ACID transactions
- Good performance for 10k-100k memories
- VSS extension available for vector search

### Consequences

- **Positive:** Simplicity, reliability, portability
- **Negative:** Not ideal for >1M memories (may need migration later)

---

## ADR-003: Singleton Pattern for MemoryStore

**Status:** Accepted  
**Date:** 2026-02-16  
**Context:** Connection management

### Decision

Use singleton pattern for MemoryStore to avoid multiple SQLite connections.

### Rationale

- SQLite doesn't handle concurrent writes well
- Singleton ensures single connection per database
- Prevents "database locked" errors
- Simpler resource management

### Consequences

- **Positive:** No connection conflicts
- **Negative:** Must use `get_store()` for access, harder to test

---

## ADR-004: LRU + Persistent Disk Cache

**Status:** Accepted  
**Date:** 2026-02-17  
**Context:** Embedding performance

### Decision

Two-tier caching:
1. In-memory LRU cache (1000 entries, ~0.03ms)
2. Persistent SQLite cache (survives restarts)

### Rationale

- Embeddings are deterministic (same text = same vector)
- Model loading is expensive (~10s cold start)
- Disk cache survives process restarts
- RAM cache for repeated queries in same session

### Consequences

- **Positive:** 274,000x speedup on cache hits
- **Negative:** ~1536 bytes per cached embedding, disk usage grows

---

## ADR-005: Type Hints Required

**Status:** Accepted  
**Date:** 2026-02-17  
**Context:** Code quality

### Decision

All public APIs must have complete type hints.

### Rationale

- Better IDE support (autocomplete, refactoring)
- Catch errors at development time
- Self-documenting code
- Enables mypy for CI validation

### Consequences

- **Positive:** Fewer bugs, better DX
- **Negative:** Slightly more verbose code

---

## ADR-006: Background Model Loading

**Status:** Accepted  
**Date:** 2026-02-17  
**Context:** Cold start latency (Issue #13)

### Decision

Load embedding model in background thread on module import.

### Rationale

- First query taking 10s feels broken
- Background loading hides latency
- Most imports are not immediately followed by embed
- Can wait for ready with `wait_for_model()`

### Consequences

- **Positive:** Cold start reduced to ~1s
- **Negative:** Uses RAM before first query, slightly complex

---

## ADR-007: Query Timeout by Default

**Status:** Accepted  
**Date:** 2026-02-17  
**Context:** Reliability (Issue #14)

### Decision

All search methods have 5 second default timeout.

### Rationale

- Prevents runaway queries on large databases
- Cross-platform implementation (SIGALRM + threading)
- Can be disabled with `timeout_ms=0`
- Better user experience

### Consequences

- **Positive:** No hung queries, graceful degradation
- **Negative:** Very large databases may need timeout increase

---

## ADR-008: Semantic Versioning

**Status:** Accepted  
**Date:** 2026-02-17  
**Context:** Release management

### Decision

Use Semantic Versioning (SemVer) for releases.

### Rationale

- Clear communication of breaking changes
- Users can pin to compatible versions
- Standard practice in Python ecosystem
- Enables automated dependency management

### Version Format

- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

---

## Rejected Decisions

### ADR-R001: Pure Rust Implementation

**Status:** Rejected  
**Date:** 2026-02-17

**Proposal:** Full Rust rewrite for maximum performance.

**Rationale for rejection:**
- Sacrifices development velocity
- "Raspberry Pi Zero" use case is speculative
- Hybrid approach gives 80% benefit with 20% effort
- Python ecosystem (sentence-transformers) is valuable

---

## Pending Decisions

### ADR-P001: Vector Search Backend Selection

**Status:** Pending  
**Date:** TBD

**Question:** When to use NumPy vs FAISS vs HNSW vs Rust?

**Options:**
1. Size-based auto-selection (<10k NumPy, <100k FAISS, >100k HNSW)
2. User configuration
3. Benchmark-based at runtime

---

*This document is a living record. Update when making significant architectural decisions.*
