# DECISION-001: Database Location

**Status:** ACCEPTED
**Date:** 2026-02-17
**Decision Maker:** Bob

## Context
Memento databases were scattered across multiple locations:
- `~/.memento/memory.db` (main store)
- `~/.openclaw/memory/memory.db` (auto-memory)
- `~/.memento/cache.db` (embeddings)

This caused confusion, backup issues, and made it unclear where data lived.

## Options Considered

### Option A: Keep scattered
- Pros: Backward compatibility
- Cons: Confusing, hard to backup, inconsistent

### Option B: `~/.memento/`
- Pros: Simple name
- Cons: Generic, might conflict with other tools

### Option C: `~/.openclaw/memento/` (SELECTED)
- Pros: Clear ownership, follows XDG, easy backup
- Cons: Migration needed

## Decision
Unify all Memento data under `~/.openclaw/memento/`:

```
~/.openclaw/memento/
├── memory.db        # Main vector store
├── cache.db         # Embedding cache
├── config.yaml      # User configuration
├── automemory.log   # Auto-store logs
└── backups/         # Automatic backups
```

## Consequences

**Positive:**
- Single source of truth
- Easy to backup/restore
- Clear ownership
- Can add more tools under ~/.openclaw/

**Negative:**
- Existing users need migration (handled in code)
- Path changes in documentation

## Implementation
- Updated: memento/config.py
- Updated: memento/store.py
- Updated: memento/embed.py
- Updated: memento/auto_memory.py
- Migration: Automatic on first run

## Related
- GitHub Issue: #29
- Commit: e921817
