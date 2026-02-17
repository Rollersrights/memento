# Memento Resilient Memory System

**Automatic memory storage that survives sessions, reboots, and failures.**

*Version: v0.2.2*

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
from memento import get_store

store = get_store()

# Store with auto-detection (or manual)
store.remember(
    text="Approved RFC-001 for Rust architecture",
    importance=0.9,
    tags=["decision", "rust"]
)

# Recall
results = store.recall("Rust decision", topk=5)
```

### 2. Health Monitor (`scripts/memento_health.sh`)

Hourly automated tasks:
- Database integrity check (`PRAGMA integrity_check`)
- Daily backup creation
- Auto-rollback on corruption
- Log rotation

**Runs via:** Cron job every hour

```bash
# Add to crontab
0 * * * * /path/to/memento/scripts/memento_health.sh
```

### 3. Failure Handler (`scripts/memento_failure_handler.py`)

When Memento breaks:
1. Logs critical error
2. Attempts rollback from backup
3. Creates GitHub issue automatically
4. Alerts via logs

### 4. Daily Backups

Location: `~/.memento/backups/`
Retention: Last 7 backups

```bash
# Manual backup
memento backup

# Or programmatically
from memento import get_store
store = get_store()
backup_path = store.backup()
```

## Failure Recovery

### Scenario: Database Corruption

```
1. Health check detects corruption (PRAGMA integrity_check)
2. Auto-rollback to latest backup
3. Create GitHub issue #XXX
4. Log failure to failures.log
5. Continue operation
```

### Scenario: Complete DB Loss

```
1. Check for backups in ~/.memento/backups/
2. Restore latest backup
3. Create GitHub issue
4. Alert user of data loss window
```

### Manual Recovery

```bash
# Check database integrity
sqlite3 ~/.memento/memory.db "PRAGMA integrity_check;"

# Restore from backup
cp ~/.memento/backups/memory_YYYYMMDD_HHMMSS.db \
   ~/.memento/memory.db

# Export to JSON for inspection
memento export > memories.json
```

## Monitoring

**Health Log:** `~/.memento/logs/health.log`
**Failure Log:** `~/.memento/logs/failures.log`
**Auto-Memory Log:** `~/.memento/logs/automemory.log`

View logs:
```bash
tail -f ~/.memento/logs/health.log
tail -f ~/.memento/logs/failures.log
```

## GitHub Integration

On failure:
- Issue created with label `critical`
- Contains system info, logs, checklist
- Assigned to team
- Tracked in project board

## Guarantees

- ✅ **Persistence:** Survives session restarts
- ✅ **Resilience:** Auto-rollback on corruption
- ✅ **Monitoring:** Hourly health checks
- ✅ **Alerts:** GitHub issues on failure
- ✅ **Backups:** Daily snapshots, 7-day retention
- ✅ **Timeout Protection:** Query timeout prevents hangs

## Configuration

Config file (`~/.memento/config.yaml`):
```yaml
storage:
  db_path: ~/.memento/memory.db
  backup_enabled: true
  backup_retention_days: 7
  
health:
  check_interval_hours: 1
  auto_rollback: true
```

## Team Responsibilities

**Rita:** Maintain health scripts, monitor logs, Rust engine
**Bob:** Review GitHub issues, fix failures, CI/CD
**Brett:** Access to backups, disaster recovery

---

*Always Available Memory System - v0.2.2*
