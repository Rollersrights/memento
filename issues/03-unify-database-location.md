---
title: "[P0] Unify database location - single path for all memory storage"
labels: ["bug", "configuration", "P0"]
assignees: ["Rita"]
---

## Problem
Database locations are fragmented across multiple directories:
- `~/.memento/memory.db` - Main store default
- `~/.openclaw/memory/memory.db` - Auto-memory tries to use this
- `~/.openclaw/memory/automemory.log` - Logs
- `~/.memento/cache.db` - Embedding cache

This causes:
- Confusion about where data lives
- Split memories (some in one DB, some in another)
- Backup confusion
- Harder to migrate/backup

## Current State
```python
# memento/config.py
DEFAULT_DB_PATH = os.environ.get(
    'MEMORY_DB_PATH', 
    os.path.expanduser("~/.memento/memory.db")  # ❌ Wrong location
)

# scripts/auto_memory.py  
self.db_path = self.store.db_path  # ❌ Uses wrong path
```

## Proposed Solution

### Step 1: Define New Unified Location
```python
# memento/config.py
DEFAULT_DB_PATH = os.environ.get(
    'MEMORY_DB_PATH',
    os.path.expanduser("~/.openclaw/memento/memory.db")
)

CACHE_DB_PATH = os.path.expanduser("~/.openclaw/memento/cache.db")
LOG_PATH = os.path.expanduser("~/.openclaw/memento/logs/")
BACKUP_PATH = os.path.expanduser("~/.openclaw/memento/backups/")
```

### Step 2: Create Directory Structure
```
~/.openclaw/memento/
├── memory.db          # Main database
├── cache.db           # Embedding cache
├── config.yaml        # User configuration
├── logs/
│   ├── automemory.log
│   ├── health.log
│   └── errors.log
└── backups/           # Daily backups
```

### Step 3: Migration Path
```python
# memento/migrations.py
def migrate_to_unified_location():
    old_paths = [
        "~/.memento/memory.db",
        "~/.openclaw/memory/memory.db"
    ]
    new_path = "~/.openclaw/memento/memory.db"
    
    # Check if old data exists
    # Copy to new location if new doesn't exist
    # Leave old for safety (don't delete)
```

### Step 4: Update All References
- `memento/config.py`
- `memento/store.py`
- `scripts/auto_memory.py`
- Documentation
- Health scripts

## Acceptance Criteria
- [ ] Single database location: `~/.openclaw/memento/`
- [ ] All components use same path
- [ ] Migration handles existing data
- [ ] Backwards compatible (env var override)
- [ ] Documentation updated
- [ ] Health scripts updated

## Related
- #4 (Fix auto-memory)
- #6 (Create OpenClaw integration)
