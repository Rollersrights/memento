"""
Memento - Persistent semantic memory for AI agents.

Local, fast, and privacy-focused semantic memory using SQLite and embeddings.
"""

__version__ = "0.2.0"
__author__ = "Rollersrights"

from memento.models import Memory, SearchResult
from memento.exceptions import (
    MementoError,
    StorageError,
    EmbeddingError,
    SearchError,
    ValidationError,
)

__all__ = [
    "Memory",
    "SearchResult",
    "MementoError",
    "StorageError",
    "EmbeddingError",
    "SearchError",
    "ValidationError",
    "get_store",
]

# Lazy import to avoid loading heavy dependencies on import
def get_store(*args, **kwargs):
    """Get a MemoryStore instance."""
    from memento.store import MemoryStore
    return MemoryStore(*args, **kwargs)
