# Memento

> **Persistent semantic memory for AI agents.** Local, fast, and privacy-focused.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Quick Start

```bash
# Install
pip install -e .

# Store a memory
memento remember "The server IP is 192.168.1.155" --tags "infra"

# Recall it
memento recall "where is the server?"
```

## Python API

```python
from memento import get_store

store = get_store()

# Store
store.remember("Deploy new model to production", importance=0.9, tags=["todo"])

# Recall
results = store.recall("deployment tasks")
```

## Documentation

📚 **[Full Documentation](docs/INDEX.md)** — Installation, API, architecture, and more.

Quick links:
- [Installation](docs/DEPLOYMENT.md)
- [API Reference](docs/API.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Architecture](docs/ARCHITECTURE.md)

## Why Memento?

- **🧠 Token Efficient:** Semantic recall loads only relevant context
- **⚡ Fast:** 274,000x speedup with LRU cache (9ms warm search)
- **🪶 Lightweight:** SQLite + NumPy, no cloud dependencies
- **🛡️ Resilient:** Survives crashes, auto-backup, auto-rollback
- **🦀 Rust Hybrid:** Optional Rust engine for sub-millisecond cold start

## Project Status

- ✅ **v0.2.2:** Type hints, background loading, query timeout, CI/CD
- 🔄 **v0.3.0:** Rust embedding engine (in progress)
- ⏳ **v1.0.0:** Full production release

See [ROADMAP.md](docs/ROADMAP.md) for details.

## License

MIT — See [LICENSE](LICENSE)

---

*Memento: Because AI shouldn't forget.*
