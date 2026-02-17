# API Reference

> Complete reference for the Memento Python API.

*Last updated: 2026-02-17*

---

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from memento import get_store

# Get singleton store instance
store = get_store()

# Store a memory
store.remember("Meeting with team at 3pm")

# Recall memories
results = store.recall("team meeting")
```

---

## Core Classes

### `MemoryStore`

The main interface for storing and retrieving memories.

```python
from memento.store import MemoryStore

# Create/get singleton instance
store = MemoryStore(db_path="~/.memento/memory.db")

# Or use the convenience function
from memento import get_store
store = get_store()
```

#### `remember()`

Store a new memory.

```python
doc_id = store.remember(
    text: str,                           # Required: text to store
    collection: str = "knowledge",       # Optional: collection name
    importance: float = 0.5,             # Optional: 0.0-1.0 relevance
    source: str = "conversation",        # Optional: source identifier
    session_id: str = "default",         # Optional: session ID
    tags: Optional[List[str]] = None,    # Optional: list of tags
)
```

**Returns:** `str` - Document ID

**Raises:**
- `ValidationError` - If input is invalid (empty text, too long, etc.)

**Example:**
```python
doc_id = store.remember(
    text="Deploy new model to production",
    importance=0.9,
    tags=["todo", "deploy"],
    collection="tasks"
)
print(f"Stored: {doc_id}")
```

#### `recall()`

Search memories by semantic similarity.

```python
results = store.recall(
    query: str,                          # Required: search query
    collection: Optional[str] = None,    # Optional: filter by collection
    topk: int = 5,                       # Optional: number of results
    filters: Optional[Dict] = None,      # Optional: metadata filters
    min_importance: Optional[float] = None,  # Optional: importance threshold
    since: Optional[str] = None,         # Optional: time filter (e.g., "7d")
    before: Optional[str] = None,        # Optional: time filter (e.g., "1d")
    timeout_ms: int = 5000,              # Optional: query timeout
)
```

**Filters:**
- `tags`: List of tags to match (any)
- `source`: Exact source match
- `session_id`: Exact session ID match
- `text_like`: Substring search (LIKE pattern)
- `min_importance`: Importance threshold
- `since`/`before`: Time strings like "7d", "24h", "30m"

**Returns:** `List[Dict[str, Any]]` - List of results with keys:
- `id`: Document ID
- `text`: Memory text
- `score`: Similarity score (0.0-1.0)
- `timestamp`: Unix timestamp
- `source`: Source identifier
- `session_id`: Session ID
- `importance`: Importance score
- `tags`: List of tags
- `collection`: Collection name

**Example:**
```python
# Simple search
results = store.recall("deployment", topk=3)

# With filters
results = store.recall(
    query="meeting",
    filters={"tags": ["work"], "since": "7d"},
    min_importance=0.7,
    topk=10
)
```

#### `batch_recall()`

Search multiple queries efficiently.

```python
results = store.batch_recall(
    queries: List[str],                  # Required: list of queries
    collection: Optional[str] = None,    # Optional: collection filter
    topk: int = 5,                       # Optional: results per query
    filters: Optional[Dict] = None,      # Optional: metadata filters
)
```

**Returns:** `List[List[Dict]]` - List of result lists (one per query)

**Example:**
```python
queries = ["deployment", "meeting", "bug fix"]
all_results = store.batch_recall(queries, topk=3)

for query, results in zip(queries, all_results):
    print(f"\n{query}:")
    for r in results:
        print(f"  - {r['text'][:50]}")
```

#### `get_recent()`

Get the most recent memories from a collection.

```python
results = store.get_recent(
    n: int = 10,                        # Number of memories
    collection: str = "knowledge",       # Collection name
)
```

#### `delete()`

Delete a memory by ID.

```python
success = store.delete(doc_id: str)  # Returns bool
```

#### `stats()`

Get statistics about the memory store.

```python
stats = store.stats()
# Returns: {
#     'collections': {'knowledge': 100, 'conversations': 50},
#     'total_vectors': 150,
#     'db_path': '/home/user/.memento/memory.db',
#     'backend': 'numpy'
# }
```

#### `backup()`

Create a backup of the database.

```python
backup_path = store.backup(
    backup_path: Optional[str] = None,  # Optional: custom path
)
# Returns path to backup file
```

#### `export_json()`

Export all memories to JSON.

```python
export_path = store.export_json(
    export_path: Optional[str] = None,  # Optional: custom path
)
# Returns path to export file
```

---

### `Memory` (Dataclass)

Represents a single memory item.

```python
from memento.models import Memory

memory = Memory(
    id="abc123",
    text="Meeting notes",
    timestamp=1708195200,
    source="conversation",
    session_id="default",
    importance=0.8,
    tags=["work", "meeting"],
    collection="knowledge",
)

# Convert to dict
data = memory.to_dict()

# Get datetime
dt = memory.datetime  # Python datetime object
```

**Fields:**
- `id`: str - Document ID
- `text`: str - Memory content
- `timestamp`: int - Unix timestamp
- `source`: str - Source identifier (default: "unknown")
- `session_id`: str - Session ID (default: "default")
- `importance`: float - Importance score (default: 0.5)
- `tags`: List[str] - Tags (default: [])
- `collection`: str - Collection name (default: "knowledge")
- `embedding`: Optional[bytes] - Raw embedding bytes

### `SearchResult` (Dataclass)

A memory returned from search, with relevance score.

```python
from memento.models import SearchResult

# Same as Memory but with score field
result = SearchResult(
    id="abc123",
    text="Meeting notes",
    timestamp=1708195200,
    score=0.95,  # Similarity score
)
```

---

## Exceptions

All exceptions inherit from `MementoError`.

```python
from memento.exceptions import (
    MementoError,
    StorageError,
    EmbeddingError,
    SearchError,
    ValidationError,
    ConfigurationError,
)

try:
    store.remember("")
except ValidationError as e:
    print(f"Invalid input: {e}")
except StorageError as e:
    print(f"Storage failed: {e}")
```

---

## Embedding

### `embed()`

Embed text into a vector.

```python
from memento.embed import embed

# Single text
vector = embed("This is a test")  # Returns List[float] (384 dimensions)

# Batch
vectors = embed(["Text 1", "Text 2", "Text 3"])  # Returns List[List[float]]

# Skip cache
vector = embed("Text", use_cache=False)
```

### Cache Functions

```python
from memento.embed import get_cache_stats, clear_cache

# Get cache statistics
stats = get_cache_stats()
# Returns: {
#     'hits': 100,
#     'misses': 10,
#     'disk_hits': 50,
#     'lru_hits': 50,
#     'hit_rate': 90.9,
#     'embedder': 'onnx'  # or 'pytorch'
# }

# Clear cache
clear_cache()
```

---

## Configuration

```python
from memento.config import get_config

config = get_config()

# Access config values
db_path = config.storage.db_path
backup_enabled = config.storage.backup_enabled
```

---

## CLI

The CLI is available as `memento` after installation.

```bash
# Store a memory
memento remember "Important note" --tags work --importance 0.9

# Search
memento recall "meeting notes" --limit 10

# JSON output (for scripting)
memento recall "server" --format json | jq '.[0].text'

# Statistics
memento stats

# Delete
memento delete abc123

# Dashboard
memento dashboard
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MEMORY_DB_PATH` | Database file path | `~/.memento/memory.db` |
| `MEMENTO_RUST` | Enable Rust engine | `0` (disabled) |
| `MEMORY_ECHO` | Show storage confirmations | `0` |

---

## Constants

```python
from memento.embed import get_embedding_dimension, get_max_tokens

DIMENSION = get_embedding_dimension()  # 384 for MiniLM-L6-v2
MAX_TOKENS = get_max_tokens()          # 256 for MiniLM-L6-v2
```
