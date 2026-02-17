# Memento Install Guide

Quick setup guide for getting Memento running on a new machine.

## Prerequisites

- Python 3.8+
- pip
- ~500MB disk space (for model download)
- (Optional) Rust toolchain for Rust acceleration

## Install from Source

```bash
# 1. Clone the repo
git clone https://github.com/rollersrights/memento.git
cd memento

# 2. Install in development mode (recommended)
pip install -e ".[dev]"

# Or install just the core package
pip install -e .
```

## Install Dependencies Only

```bash
# Core dependencies
pip install sentence-transformers numpy rich

# Optional: For faster inference on AVX2 CPUs
pip install onnxruntime

# Optional: For faster search on large datasets (10,000+ vectors)
pip install faiss-cpu  # or hnswlib
```

## Test It Works

```bash
# Run the example
python3 example.py

# Or test the CLI
memento --help
memento stats
```

You should see:
- "Storing memories..."
- Search results for 'shopping' and 'database'
- Memory stats JSON

First run downloads the MiniLM model (~22MB) — takes ~30 seconds.

## Python API Usage

```python
from memento import get_store

# Get singleton store instance
store = get_store()

# Store something
store.remember("Don't forget the milk", importance=0.7, tags=["todo"])

# Search
results = store.recall("groceries")
for r in results:
    print(f"{r['score']:.3f}: {r['text']}")
```

## Storage Location

Default: `~/.memento/memory.db`

Override with env var:
```bash
export MEMORY_DB_PATH=/path/to/custom/memory.db
```

## Configuration

Create `~/.memento/config.yaml`:

```yaml
storage:
  db_path: ~/.memento/memory.db
  backup_enabled: true
  
embedding:
  model: sentence-transformers/all-MiniLM-L6-v2
  use_onnx: true
  
cache:
  lru_size: 1000
```

## Dashboard (Optional)

Live memory monitor:
```bash
memento dashboard
```

Press `Ctrl+C` to exit.

## File Structure

```
~/.memento/
├── memory.db           # Main database
├── memory.db-shm       # WAL file (auto)
├── memory.db-wal       # WAL file (auto)
├── cache.db            # Persistent embedding cache
├── config.yaml         # User configuration
├── models/             # Cached embedding model
│   └── sentence-transformers/
│       └── all-MiniLM-L6-v2/
├── backups/            # Daily backups
└── logs/               # Application logs
```

## Troubleshooting

**"No module named 'sentence_transformers'"**
```bash
pip install sentence-transformers
```

**First query is slow**
- Normal — model is loading in background. Subsequent queries are fast.
- Or run `memento stats` to warm up the model.

**Permission denied on ~/.memento**
```bash
mkdir -p ~/.memento && chmod 755 ~/.memento
```

**Rust extension fails to load**
```bash
# If you see errors about memento_rs, it's optional
# Set this to disable Rust engine:
export MEMENTO_RUST=0
```

## Advanced: Cron Jobs (Optional)

Add to crontab for auto-features:

```bash
# Auto-store from session logs every 3 min
*/3 * * * * cd /path/to/memento && python3 scripts/auto_memory.py

# Process inbox files every 5 min
*/5 * * * * cd /path/to/memento && python3 scripts/processor.py

# Daily backup
0 2 * * * cd /path/to/memento && python3 -c "from memento import get_store; get_store().backup()"

# Health check every hour
0 * * * * cd /path/to/memento && scripts/memento_health.sh
```

## Federation Note

If connecting multiple agents/machines, memories stay local to each. For shared memory, sync the `.db` file or use a shared network path.

## Uninstall

```bash
# If installed with pip -e
pip uninstall memento

# Clean up data (optional)
rm -rf ~/.memento
```

---

**Questions?** Check `README.md` or open an issue.
