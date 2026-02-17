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

## Current Status

- ✅ **Phase 1 Complete:** Modular Python with type hints, tests, documentation
- 🔄 **Phase 2a In Progress:** Rust embeddings for sub-millisecond cold start
- ⏳ **Phase 2b Deferred:** Rust vector search (10k+ vectors threshold)
- ⏳ **Phase 3 Deferred:** Pure Rust CLI (future consideration)

## For Users

```python
from memento import remember, recall

# Store
remember("Approved RFC-001 for Rust hybrid architecture")

# Recall
memories = recall("What did we decide about Rust?")
```

## For Contributors

- Issues → Branches → PRs → Reviews → Merge
- Never commit to main
- Semantic versioning
- Friendly, constructive reviews

---

*Memento: Because AI shouldn't forget.*
