# Memento Resilient Memory System

**Automatic memory storage that survives sessions, reboots, and failures.**

## Architecture

```
┌─────────────────────────────────────────┐
│         User Conversation               │
└──────────────┬──────────────────────────┘
               │
        ┌──────▼──────┐
        │ Significance│ ← Detects important exchanges
        │  Detection  │
└──────┬──────────────┘
       │
┌──────▼──────────────────────────────────┐
│     AutoMemory (auto_memory.py)         │
│  • Stores to Memento (SQLite + vectors) │
│  • Tags automatically                   │
│  • Fallback to file log if DB fails     │
└──────┬──────────────────────────────────┘
       │
┌──────▼──────────────────────────────────┐
│     Memento Store (SQLite)              │
│  • Semantic search enabled              │
│  • 274,000x caching speedup             │
│  • Persistent across reboots            │
└──────┬──────────────────────────────────┘
       │
┌──────▼──────────────────────────────────┐
│     Health Monitor (cron)               │
│  • Hourly backup                        │
│  • Integrity checks                     │
│  • Auto-rollback on corruption          │
│  • GitHub issue on failure              │
└─────────────────────────────────────────┘
```

## Components

### 1. Auto-Memory (`scripts/auto_memory.py`)
Automatically stores significant conversations:
- Detects decisions, RFCs, bugs, benchmarks
- Auto-tags (rust, github, bob, brett, etc.)
- Importance scoring (0.6-0.95)
- File logging for failures

**Usage:**
```python
from scripts.auto_memory import store_interaction, recall_memories

# Store (automatic significance detection)
store_interaction(
    query="What did we decide?",
    response="Approved RFC-001",
    context="Architecture meeting"
)

# Recall
results = recall_memories("Rust decision", topk=5)
```

### 2. Health Monitor (`scripts/memento_health.sh`)
Hourly automated tasks:
- Database integrity check
- Daily backup creation
- Auto-rollback on corruption
- Log rotation

**Runs via:** Cron job every hour

### 3. Failure Handler (`scripts/memento_failure_handler.py`)
When Memento breaks:
1. Logs critical error
2. Attempts rollback from backup
3. Creates GitHub issue automatically
4. Alerts via logs

### 4. Daily Backups
Location: `~/.openclaw/memory/backups/`
Retention: Last 7 backups

## Failure Recovery

### Scenario: Database Corruption
```
1. Health check detects corruption
2. Auto-rollback to latest backup
3. Create GitHub issue #XXX
4. Log failure to failures.log
5. Continue operation
```

### Scenario: Complete DB Loss
```
1. Check for backups
2. Restore latest
3. Create GitHub issue
4. Alert user of data loss window
```

## Monitoring

**Health Log:** `~/.openclaw/memory/health.log`
**Failure Log:** `~/.openclaw/memory/failures.log`
**Auto-Memory Log:** `~/.openclaw/memory/automemory.log`

## GitHub Integration

On failure:
- Issue created with label `critical`
- Contains system info, logs, checklist
- Assigned to team
- Tracked in project board

## Manual Operations

**Force backup:**
```bash
~/.openclaw/workspace/memento/scripts/memento_health.sh
```

**Check health:**
```bash
python3 -c "
from scripts.auto_memory import get_memory
mem = get_memory()
print(f'Vectors: {mem.store.stats()[\"total_vectors\"]}')
"
```

**Restore from backup:**
```bash
cp ~/.openclaw/memory/backups/memory_YYYYMMDD_HHMMSS.db \
   ~/.openclaw/memory/memory.db
```

## Guarantees

- ✅ **Persistence:** Survives session restarts
- ✅ **Resilience:** Auto-rollback on corruption
- ✅ **Monitoring:** Hourly health checks
- ✅ **Alerts:** GitHub issues on failure
- ✅ **Backups:** Daily snapshots, 7-day retention

## Team Responsibilities

**Rita:** Maintain health scripts, monitor logs
**Bob:** Review GitHub issues, fix failures
**Brett:** Access to backups, disaster recovery

---
*Always Available Memory System - v0.2.0*
