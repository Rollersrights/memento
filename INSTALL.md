# Memento Install Guide

Quick setup guide for getting Memento running on a new machine.

## Prerequisites

- Python 3.8+
- pip
- ~500MB disk space (for model download)

## Install

```bash
# 1. Clone the repo
git clone https://github.com/rollersrights/memento.git
cd memento

# 2. Install dependencies
pip install sentence-transformers numpy

# Optional: For the dashboard
pip install rich
```

## Test It Works

```bash
python3 example.py
```

You should see:
- "Storing memories..."
- Search results for 'shopping' and 'database'
- Memory stats JSON

First run downloads the MiniLM model (~22MB) — takes ~30 seconds.

## Usage

```python
from scripts.store import MemoryStore

memory = MemoryStore()

# Store something
memory.remember("Don't forget the milk", importance=0.7, tags=["todo"])

# Search
results = memory.recall("groceries")
for r in results:
    print(f"{r['score']:.3f}: {r['text']}")
```

## Storage Location

Default: `~/.memento/memory.db`

Override with env var:
```bash
export MEMORY_DB_PATH=/path/to/custom/memory.db
```

## Dashboard (Optional)

Live memory monitor:
```bash
python3 scripts/dashboard.py
```

Press `Ctrl+C` to exit.

## File Structure

```
~/.memento/
├── memory.db           # Main database
├── memory.db-shm       # WAL file (auto)
├── memory.db-wal       # WAL file (auto)
├── models/             # Cached embedding model
│   └── sentence-transformers/
│       └── all-MiniLM-L6-v2/
├── inbox/              # Drop files here for ingestion
└── processed/          # Processed files moved here
```

## Troubleshooting

**"No module named 'sentence_transformers'"**
```bash
pip install sentence-transformers
```

**First query is slow**
- Normal — model is loading. Subsequent queries are fast.

**Permission denied on ~/.memento**
```bash
mkdir -p ~/.memento && chmod 755 ~/.memento
```

## Advanced: Cron Jobs (Optional)

Add to crontab for auto-features:

```bash
# Auto-store from session logs every 3 min
*/3 * * * * cd /path/to/memento && python3 scripts/session_watcher.py

# Process inbox files every 5 min
*/5 * * * * cd /path/to/memento && python3 scripts/processor.py

# Daily backup
0 2 * * * cd /path/to/memento && python3 -c "from scripts.store import MemoryStore; MemoryStore().backup()"
```

## Federation Note

If connecting multiple agents/machines, memories stay local to each. For shared memory, sync the `.db` file or use a shared network path.

---

**Questions?** Check `README.md` or open an issue.
