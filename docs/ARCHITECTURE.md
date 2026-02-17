# Architecture

> Memento system design and component architecture.

*Last updated: 2026-02-17*

---

## System Overview

Memento uses a hybrid Python/Rust architecture optimized for local-first AI memory:

```
┌─────────────────────────────────────────┐
│         Python API / CLI                │
│  • Rich interface, rapid iteration      │
│  • Full type safety, comprehensive      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Engine Interface (ABC)          │
│  • Abstract base for pluggable backends │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌───────▼────────┐
│ Python Engine  │  │  Rust Engine   │
│ (NumPy/FAISS)  │  │  (ONNX/SIMD)   │
└───────┬────────┘  └───────┬────────┘
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │   SQLite Storage  │
        │   (Persistent)    │
└─────────────────────────────────────────┘
```

---

## Core Components

### 1. MemoryStore (`memento/store.py`)

The main interface for storing and retrieving memories.

**Responsibilities:**
- Singleton pattern for SQLite connection management
- CRUD operations for memories
- Search with filtering and ranking
- Backup and export functionality

**Key Methods:**
- `remember()` — Store a memory
- `recall()` — Search memories by semantic similarity
- `batch_recall()` — Search multiple queries efficiently
- `get_recent()` — Get recent memories from a collection
- `delete()` — Delete a memory by ID
- `stats()` — Get store statistics

### 2. Embedding Engine (`memento/embed.py`)

Handles text-to-vector conversion using transformer models.

**Features:**
- Two-tier caching (LRU + persistent disk cache)
- Automatic backend selection (ONNX/PyTorch)
- Background model loading for fast cold start
- Batch processing for efficiency

**Performance:**
- Cold start: ~1s (with background loading)
- Cached embedding: 0.04ms
- Cache hit rate: 90%+

### 3. Search Module (`memento/search.py`)

Vector search implementations with multiple backends.

**Backends:**
- **NumPy (default):** Pure Python, works everywhere
- **FAISS:** Optimized for 10,000+ vectors
- **HNSW:** Fastest approximate search
- **sqlite-vec:** SQLite-native vector search

**Features:**
- Cosine similarity matching
- Metadata filtering
- Hybrid search (dense + lexical)

### 4. CLI (`memento/cli.py`)

Rich terminal interface with smart piping.

**Modes:**
- Human mode: Rich tables and formatting
- Script mode: JSON output for piping

**Commands:**
- `remember` — Store a memory
- `recall` — Search memories
- `stats` — Show statistics
- `delete` — Remove a memory
- `dashboard` — Live memory monitor

### 5. Auto-Memory (`memento/auto_memory.py`)

Automatic memory storage for conversations.

**Features:**
- Significance detection
- Auto-tagging
- Importance scoring
- Fallback logging

---

## Data Flow

### Storing a Memory

```
┌──────────────┐
│   User/API   │──▶ Text + metadata
└──────┬───────┘
       │
┌──────▼───────────────────┐
│   MemoryStore.remember   │
└──────┬───────────────────┘
       │
       ├──────────────┐
       │              │
┌──────▼──────┐  ┌────▼──────────┐
│   Embed     │  │   Metadata    │
│   (cache?)  │  │   processing  │
└──────┬──────┘  └───────────────┘
       │
┌──────▼───────────────────┐
│   SQLite INSERT          │
│   + vector storage       │
└──────────────────────────┘
```

### Searching Memories

```
┌──────────────┐
│   User/API   │──▶ Query string
└──────┬───────┘
       │
┌──────▼───────────────────┐
│   MemoryStore.recall     │
└──────┬───────────────────┘
       │
       ├───────────────────────────────────┐
       │                                   │
┌──────▼──────┐  ┌──────────────────┐  ┌──▼───────────┐
│   Embed     │  │   Metadata       │  │   Timeout    │
│   query     │  │   filters        │  │   (5s)       │
└──────┬──────┘  └──────────────────┘  └──────────────┘
       │
┌──────▼───────────────────┐
│   Vector search          │
│   (cosine similarity)    │
└──────┬───────────────────┘
       │
┌──────▼───────────────────┐
│   Return ranked results  │
└──────────────────────────┘
```

---

## Storage Architecture

### 3-Tier Memory Hierarchy

```
┌─────────────────────────────────────────┐
│  TIER 1: Working Memory (Context)       │
│  - Active conversation                  │
│  - LRU cache (1000 entries)             │
│  - ~0.03ms access                       │
├─────────────────────────────────────────┤
│  TIER 2: Episodic Memory (SQLite)       │
│  - Recent events, fast retrieval        │
│  - Persistent disk cache                │
│  - ~9ms access                          │
├─────────────────────────────────────────┤
│  TIER 3: Semantic Memory (SQLite)       │
│  - Long-term facts, structured          │
│  - Full database with vectors           │
│  - ~50ms access                         │
└─────────────────────────────────────────┘
```

### Database Schema

**memories table:**
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    source TEXT,
    session_id TEXT,
    importance REAL,
    tags TEXT,  -- JSON array
    collection TEXT DEFAULT 'knowledge',
    embedding BLOB  -- 384-dim float32 vector
);
```

**embedding_cache table:**
```sql
CREATE TABLE embedding_cache (
    text_hash TEXT PRIMARY KEY,
    embedding BLOB NOT NULL,
    timestamp INTEGER NOT NULL
);
```

---

## Resilience Features

### Failure Recovery

```
┌─────────────────────────────────────────┐
│         Health Monitor                  │
│  • Hourly backup                        │
│  • Integrity checks                     │
│  • Auto-rollback on corruption          │
└─────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌───────▼────────┐
│   DB OK        │  │   DB Corrupt   │
│   Continue     │  │                │
│                │  │  • Rollback    │
│                │  │  • Alert       │
└────────────────┘  └────────────────┘
```

### Guarantees

- ✅ **Persistence:** Survives session restarts
- ✅ **Resilience:** Auto-rollback on corruption
- ✅ **Monitoring:** Hourly health checks
- ✅ **Backups:** Daily snapshots, 7-day retention
- ✅ **Timeout Protection:** Query timeout prevents hangs

---

## Configuration

**Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `MEMORY_DB_PATH` | Database file path | `~/.memento/memory.db` |
| `MEMENTO_RUST` | Enable Rust engine | `0` (disabled) |
| `MEMORY_ECHO` | Show storage confirmations | `0` |

**Config File** (`~/.memento/config.yaml`):

```yaml
storage:
  db_path: ~/.memento/memory.db
  backup_enabled: true
  backup_retention_days: 7
  
embedding:
  model: sentence-transformers/all-MiniLM-L6-v2
  use_onnx: true
  
cache:
  lru_size: 1000
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Cold Start | ~1s | With background loading |
| Warm Search | ~9ms | NumPy backend |
| Cached Embedding | 0.04ms | After first call |
| Cache Hit Rate | 90%+ | LRU + disk cache |
| Speedup | 274,000x | Cache hit vs cold |

---

## Technology Stack

**Core:**
- Python 3.8+
- SQLite (storage)
- NumPy (vector operations)

**Optional:**
- sentence-transformers (embeddings)
- ONNX Runtime (fast inference)
- FAISS/hnswlib (large-scale search)
- Rust + PyO3 (performance-critical paths)

---

*For implementation details, see [API.md](API.md)*
