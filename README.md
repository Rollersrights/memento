# Memento

Persistent semantic memory for AI agents using local SQLite + NumPy. No cloud required, no AVX2 needed, runs on anything.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Pure Python + NumPy** — No GPU required, runs on older hardware
- **SQLite Backend** — Single file database, easy to backup/transfer
- **Semantic Search** — MiniLM embeddings for concept matching
- **Hybrid Search** — BM25 + Vector combination for best of both worlds
- **Auto-Store** — Intelligent significance detection stores what matters
- **Document Ingestion** — Drop PDFs, markdown, code files for automatic indexing
- **Real-time Dashboard** — Live CLI monitoring
- **Monthly Compaction** — Auto-summarizes old memories to save space

## Quick Start

```bash
pip install sentence-transformers numpy

python3 -c "
from scripts.store import MemoryStore
memory = MemoryStore()

# Store a memory
memory.remember('Remember to buy milk', importance=0.7, tags=['todo'])

# Search memories
results = memory.recall('shopping')
for r in results:
    print(f'{r[\"score\"]:.3f}: {r[\"text\"]}')
"
```

## Storage

Default location: `~/.memento/memory.db`

Override with environment variable:
```bash
export MEMORY_DB_PATH=/custom/path/memory.db
```

## Collections

- `conversations` — Chat history (auto-stored)
- `documents` — Ingested files
- `knowledge` — Explicit facts and todos
- `compacted` — Summarized old memories

## Document Ingestion

Drop files in `~/.memento/inbox/`:
- PDFs, Markdown, Text files
- Code files (.py, .js, .go, etc.)
- Auto-processed every 5 minutes

## Dashboard

```bash
# Live monitoring
python3 scripts/dashboard.py

# One-time snapshot
python3 scripts/dashboard.py --once
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agent     │────▶│   Memento   │────▶│   SQLite    │
│   Chat      │     │   Store     │     │   Database  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │   NumPy     │
                    │   Vectors   │
                    └─────────────┘
```

## Performance

- Typical query: <50ms for thousands of memories
- Embedding: ~100-500 docs/sec (batch)
- Memory: ~1.5KB per vector (384-dim float32)

## Cron Jobs (Optional)

| Job | Frequency | Purpose |
|-----|-----------|---------|
| session-watcher | Every 3 min | Auto-store significant exchanges |
| document-processor | Every 5 min | Process inbox files |
| daily-backup | Daily | Backup database |
| monthly-compaction | Monthly | Summarize old memories |

## License

MIT
