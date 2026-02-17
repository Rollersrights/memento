"""
Vector Math Operations (The Hot Path).
This module encapsulates all NumPy/math logic.
Future: Replace implementation with Rust bindings (memento-core-rs).
"""

import numpy as np
from typing import List, Tuple, Dict

def normalize(vector: List[float]) -> np.ndarray:
    """Normalize a vector to unit length."""
    v = np.array(vector, dtype=np.float32)
    norm = np.linalg.norm(v)
    if norm > 0:
        return v / norm
    return v

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two normalized vectors."""
    # Since vectors are normalized, cosine sim is just dot product
    return float(np.dot(a, b))

def batch_cosine_similarity(query: np.ndarray, index_vectors: Dict[str, np.ndarray], topk: int) -> List[Tuple[str, float]]:
    """
    Search an index of vectors.
    Args:
        query: Normalized query vector
        index_vectors: Dict mapping ID -> Normalized vector
        topk: Number of results
    Returns:
        List of (id, score) tuples sorted by score desc.
    """
    # Convert dict to matrix for vectorized operation (faster)
    if not index_vectors:
        return []
        
    ids = list(index_vectors.keys())
    matrix = np.stack(list(index_vectors.values()))
    
    # Dot product of query against all vectors
    scores = np.dot(matrix, query)
    
    # Get top-k indices
    # Optimization: use argpartition for large N instead of full sort
    if len(scores) > topk:
        top_indices = np.argpartition(scores, -topk)[-topk:]
        # Sort the top k
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
    else:
        top_indices = np.argsort(scores)[::-1]
        
    results = []
    for idx in top_indices:
        results.append((ids[idx], float(scores[idx])))
        
    return results
