from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from scripts.types import Memory, SearchResult

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

class VectorIndex(ABC):
    """Abstract base for vector storage/search (NumPy, HNSW, Rust)."""
    
    @abstractmethod
    def add(self, doc_id: str, vector: List[float]):
        """Add a vector to the index."""
        pass
        
    @abstractmethod
    def remove(self, doc_id: str):
        """Remove a vector from the index."""
        pass
        
    @abstractmethod
    def search(self, query_vector: List[float], topk: int) -> List[tuple[str, float]]:
        """Search for nearest neighbors. Returns list of (id, score)."""
        pass
        
    @abstractmethod
    def save(self, path: str):
        """Persist index to disk."""
        pass
        
    @abstractmethod
    def load(self, path: str):
        """Load index from disk."""
        pass
