# Memento

**Persistent semantic memory for AI agents.** Local, fast, and privacy-focused.

> *Memento gives AI agents persistent, semantic memory that survives sessions, scales efficiently, and recalls what matters—without drowning in context.*

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](./run_tests.sh)

## Why Memento?

- **🧠 Token Efficient:** Semantic recall loads only relevant context, not full history
- **⚡ Fast:** 274,000x speedup with LRU cache (9ms warm search)
- **🪶 Lightweight:** SQLite + NumPy, no cloud dependencies
- **🛡️ Resilient:** Survives crashes, auto-backup, auto-rollback
- **🤝 Team Ready:** Proper GitHub workflow, documented, contributor-friendly
- **🦀 Rust Hybrid:** Rust embedding engine for sub-millisecond cold start (optional)

## Quick Start

```bash
# Install from source
git clone https://github.com/rollersrights/memento.git
cd memento
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt

# Store a memory
memento remember "The server IP is 192.168.1.155" --tags "infra"

# Recall it
memento recall "where is the server?"
```

## The CLI

Memento detects if you're a human or a script.

**Human Mode (Rich Tables):**
```text
ID        Score   Text
──────────────────────────────────────────
a1b2c3d4  0.89    The server IP is...
```

**Script Mode (JSON):**
```bash
memento recall "server" | jq .[0].text
# "The server IP is 192.168.1.155"
```

## Python API

```python
from memento import get_store, Memory, SearchResult

# Get singleton store instance
store = get_store()

# Store a memory
doc_id = store.remember(
    text="Deploy new model to production",
    importance=0.9,
    tags=["todo", "deploy"],
    collection="tasks"
)

# Search memories
results = store.recall(
    query="deployment tasks",
    topk=5,
    filters={"tags": ["todo"]},
    timeout_ms=5000
)

for result in results:
    print(f"{result['score']:.3f}: {result['text']}")

# Batch search for multiple queries
batch_results = store.batch_recall(
    queries=["deployment", "meeting notes", "bug fixes"],
    topk=3
)
```

## Architecture

```
┌──────────┐    ┌─────────────┐    ┌──────────────┐
│  Query   │───▶│  RAM Cache  │───▶│  Disk Cache  │
└──────────┘    │  (0.03ms)   │    │   (SQLite)   │
                └──────┬──────┘    └──────┬───────┘
                       │ (miss)           │ (miss)
                ┌──────▼──────┐           │
                │ ONNX/PyTorch│◀──────────┘
                │  Inference  │
                └─────────────┘
```

### Storage Backends

- **NumPy (default):** Pure Python, works everywhere
- **FAISS:** Optimized for 10,000+ vectors
- **HNSW:** Fastest approximate search

### Embedding Backends

- **ONNX Runtime:** Fast inference on AVX2 CPUs
- **PyTorch:** Compatible fallback
- **Rust (optional):** Sub-millisecond cold start

## Configuration

Environment variables:
```bash
export MEMORY_DB_PATH=/path/to/custom/memory.db
export MEMENTO_RUST=1  # Enable Rust engine (if available)
export MEMORY_ECHO=1   # Show storage confirmations
```

Config file (`~/.memento/config.yaml`):
```yaml
storage:
  db_path: ~/.memento/memory.db
  backup_enabled: true
  
embedding:
  model: all-MiniLM-L6-v2
  use_onnx: true
  
cache:
  lru_size: 1000
```

## Development

Run the test suite:
```bash
./run_tests.sh
```

Or with pytest:
```bash
pytest tests/ -v
```

Lint and format:
```bash
flake8 .
black .
```

## Project Structure

```
memento/
├── memento/           # Main package
│   ├── __init__.py    # Public API
│   ├── store.py       # MemoryStore class
│   ├── embed.py       # Embedding engine
│   ├── search.py      # Vector search
│   ├── cli.py         # Command line interface
│   ├── models.py      # Data models (Memory, SearchResult)
│   ├── exceptions.py  # Custom exceptions
│   ├── config.py      # Configuration management
│   └── migrations.py  # Database migrations
├── scripts/           # Legacy scripts (deprecated)
├── tests/             # Test suite
├── memento_rs/        # Rust implementation (optional)
└── docs/              # Documentation
```

## Roadmap

- ✅ **v0.2.0:** LRU caching, persistent disk cache, CLI
- ✅ **v0.2.1:** Echo notifications, storage threshold tuning
- ✅ **v0.2.2:** Background model loading, query timeout, type hints
- 🔄 **v0.3.0:** Rust embedding engine (Phase 2a of RFC-001)
- ⏳ **v0.4.0:** Rust vector search (Phase 2b)
- ⏳ **v1.0.0:** Full production release

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup and guidelines.

We use GitHub Issues → Branches → PRs → Reviews → Merge workflow.

## License

MIT

---

*Memento: Because AI shouldn't forget.*
