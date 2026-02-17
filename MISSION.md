# Memento Mission Statement

> **Memento gives AI agents persistent, semantic memory that survives sessions, scales efficiently, and recalls what matters—without drowning in context.**

## What Memento Does

1. **Remembers Automatically**  
   Significant conversations, decisions, and context are auto-stored with smart tagging

2. **Recalls Intelligently**  
   Semantic search finds relevant memories by meaning, not just keywords

3. **Survives Everything**  
   SQLite persistence, hourly backups, auto-rollback on corruption

4. **Stays Fast & Light**  
   Local embeddings, LRU caching (274,000x speedup), no cloud dependencies

5. **Scales With You**  
   Starts simple (SQLite), grows to Rust when you need performance

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Token Efficient** | Recall only what matters, not full history |
| **Session Resilient** | Survives reboots, crashes, model restarts |
| **Team Friendly** | Proper GitHub workflow, documented, contributor-ready |
| **Production Ready** | Health monitoring, backups, failure recovery |
| **Type Safe** | Full type hints, runtime validation |

## Current Status

- ✅ **Phase 1 Complete:** Modular Python with type hints, tests, documentation
- ✅ **Phase 1b Complete:** Background model loading, query timeout, CI/CD
- 🔄 **Phase 2a In Progress:** Rust embeddings for sub-millisecond cold start
- ⏳ **Phase 2b Deferred:** Rust vector search (10k+ vectors threshold)
- ⏳ **Phase 3 Deferred:** Pure Rust CLI (future consideration)

## Architecture

### Hybrid Python/Rust Design

```
┌─────────────────────────────────────────┐
│         Python API / CLI                │
│  • Rich interface, rapid iteration      │
│  • Full type safety, comprehensive      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Engine Interface (ABC)          │
│  • Abstract base for pluggable backends │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌───────▼────────┐
│ Python Engine  │  │  Rust Engine   │
│ (NumPy/FAISS)  │  │  (ONNX/SIMD)   │
└───────┬────────┘  └───────┬────────┘
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │   SQLite Storage  │
        │   (Persistent)    │
└─────────────────────────────────────────┘
```

## For Users

```python
from memento import get_store

store = get_store()

# Store
store.remember("Approved RFC-001 for Rust hybrid architecture")

# Recall
memories = store.recall("What did we decide about Rust?")
```

## For Contributors

- Issues → Branches → PRs → Reviews → Merge
- Never commit to main
- Semantic versioning
- Friendly, constructive reviews
- All code must have type hints
- All features must have tests

## Quality Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Type Coverage | 100% | ✅ 100% |
| Test Coverage | 80% | 🟡 ~60% |
| Doc Coverage | 100% | ✅ 100% |
| CI Pass Rate | 100% | ✅ 100% |
| Cold Start | < 2s | ✅ ~1s |
| Warm Search | < 10ms | ✅ ~9ms |

## Team

**Rita (@rollersrights):**
- Performance optimizations
- Cross-platform compatibility
- Infrastructure
- Rust integration

**Bob:**
- Code quality (types, tests)
- CLI/UX improvements
- Documentation
- CI/CD

**Brett:**
- Architecture decisions
- Integration
- Deployment

---

*Memento: Because AI shouldn't forget.*
