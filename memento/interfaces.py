"""
Memento Abstract Interfaces

Defines the contracts for all pluggable components:
- Engine: Top-level orchestrator (remember/recall)
- EmbeddingProvider: Text → vector conversion
- VectorIndex: Vector storage and search
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from memento.models import Memory, SearchResult


class EmbeddingProvider(ABC):
    """Abstract base for embedding models (PyTorch, ONNX, Rust)."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Embed a single string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of strings."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return vector dimension."""
        pass

    @property
    def name(self) -> str:
        """Human-readable provider name."""
        return self.__class__.__name__


class VectorIndex(ABC):
    """Abstract base for vector storage/search (NumPy, HNSW, Rust)."""

    @abstractmethod
    def add(self, doc_id: str, vector: List[float]) -> None:
        """Add a vector to the index."""
        pass

    @abstractmethod
    def remove(self, doc_id: str) -> None:
        """Remove a vector from the index."""
        pass

    @abstractmethod
    def search(self, query_vector: List[float], topk: int) -> List[Tuple[str, float]]:
        """Search for nearest neighbors. Returns list of (id, score)."""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Persist index to disk."""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Load index from disk."""
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        """Number of vectors in the index."""
        pass


class Engine(ABC):
    """
    Top-level orchestrator for Memento operations.
    
    Composes an EmbeddingProvider and VectorIndex to provide
    the full remember/recall interface. This is the interface
    that PythonEngine and RustEngine both implement.
    """

    @abstractmethod
    def remember(
        self,
        text: str,
        collection: str = "knowledge",
        importance: float = 0.5,
        source: str = "conversation",
        session_id: str = "default",
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Store a memory. Returns document ID.
        
        Implementations should:
        - Validate input
        - Check for near-duplicates
        - Embed the text
        - Store in database + vector index
        """
        pass

    @abstractmethod
    def recall(
        self,
        query: str,
        collection: Optional[str] = None,
        topk: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search memories by semantic similarity.
        
        Returns list of SearchResult ordered by relevance.
        """
        pass

    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """Delete a memory by ID."""
        pass

    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Get engine statistics (vector count, backend info, etc.)."""
        pass

    @property
    @abstractmethod
    def embedding_provider(self) -> EmbeddingProvider:
        """The embedding provider used by this engine."""
        pass

    @property
    @abstractmethod
    def vector_index(self) -> VectorIndex:
        """The vector index used by this engine."""
        pass

    @property
    def name(self) -> str:
        """Human-readable engine name."""
        return self.__class__.__name__

    def close(self) -> None:
        """Clean up resources. Override if needed."""
        pass
