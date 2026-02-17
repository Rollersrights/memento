#!/usr/bin/env python3
"""
Vector search backends with automatic hardware optimization
- hnswlib (fastest, requires AVX2)
- FAISS (fast, optional)
- NumPy (fallback, always works)
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import os

# Backend selection
_search_backend = None
_hnsw_index = None
_faiss_index = None
_vectors_np = None  # For numpy fallback

def _get_search_backend() -> str:
    """Determine best search backend for this hardware."""
    global _search_backend
    
    if _search_backend is not None:
        return _search_backend
    
    # Default to numpy (always works)
    _search_backend = 'numpy'
    
    # Try hnswlib first (fastest, pure C++)
    try:
        import hnswlib
        _search_backend = 'hnswlib'
        print("[Search] Using hnswlib (fast)")
        return _search_backend
    except ImportError:
        pass
    
    # Try FAISS
    try:
        import faiss
        _search_backend = 'faiss'
        print("[Search] Using FAISS (fast)")
        return _search_backend
    except ImportError:
        pass
    
    print("[Search] Using NumPy (compatible)")
    return _search_backend

def build_index(vectors: Dict[str, np.ndarray], dim: int = 384) -> Any:
    """
    Build search index from vectors.
    
    Args:
        vectors: Dict of id -> numpy array
        dim: Vector dimension
    
    Returns:
        Index object (type depends on backend)
    """
    backend = _get_search_backend()
    ids = list(vectors.keys())
    
    if len(ids) == 0:
        return None, ids
    
    # Convert to numpy array
    data = np.array([vectors[i] for i in ids], dtype=np.float32)
    
    if backend == 'hnswlib':
        import hnswlib
        
        # HNSW index
        index = hnswlib.Index(space='cosine', dim=dim)
        index.init_index(
            max_elements=len(ids) * 2,  # Allow growth
            ef_construction=200,
            M=16
        )
        index.add_items(data)
        index.set_ef(50)  # Search accuracy vs speed tradeoff
        
        return ('hnswlib', index, ids), ids
    
    elif backend == 'faiss':
        import faiss
        
        # FAISS index with IVF for large datasets
        if len(ids) < 1000:
            # Brute force for small datasets
            index = faiss.IndexFlatIP(dim)  # Inner product = cosine for normalized vectors
        else:
            # IVF for large datasets
            nlist = int(np.sqrt(len(ids)))  # Number of clusters
            quantizer = faiss.IndexFlatIP(dim)
            index = faiss.IndexIVFFlat(quantizer, dim, nlist)
            index.train(data)
        
        index.add(data)
        return ('faiss', index, ids), ids
    
    else:
        # NumPy fallback - just return the data
        return ('numpy', data, ids), ids

def search_index(
    index_obj: Any,
    query: np.ndarray,
    topk: int = 10
) -> List[Tuple[int, float]]:
    """
    Search index for nearest neighbors.
    
    Args:
        index_obj: Index from build_index()
        query: Query vector (normalized)
        topk: Number of results
    
    Returns:
        List of (index_id, score) tuples
    """
    if index_obj is None:
        return []
    
    backend, index, ids = index_obj
    
    if backend == 'hnswlib':
        # HNSW search
        labels, distances = index.knn_query(query.reshape(1, -1), k=min(topk, len(ids)))
        # Convert to similarity scores (hnswlib returns distances)
        results = []
        for idx, dist in zip(labels[0], distances[0]):
            # Cosine distance to similarity
            score = 1.0 - dist
            results.append((idx, score))
        return results
    
    elif backend == 'faiss':
        # FAISS search
        scores, indices = index.search(query.reshape(1, -1), min(topk, len(ids)))
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx >= 0:  # FAISS returns -1 for not found
                results.append((idx, float(score)))
        return results
    
    else:
        # NumPy brute force
        # query: (384,), index: (n, 384)
        scores = np.dot(index, query)  # Cosine similarity for normalized vectors
        top_indices = np.argsort(scores)[::-1][:topk]
        return [(int(i), float(scores[i])) for i in top_indices]

def batch_search(
    index_obj: Any,
    queries: List[np.ndarray],
    topk: int = 10
) -> List[List[Tuple[int, float]]]:
    """
    Batch search for multiple queries.
    
    Args:
        index_obj: Index from build_index()
        queries: List of query vectors
        topk: Number of results per query
    
    Returns:
        List of result lists
    """
    if index_obj is None:
        return [[] for _ in queries]
    
    backend, index, ids = index_obj
    
    if backend == 'hnswlib':
        # HNSW batch search
        queries_np = np.array(queries)
        labels, distances = index.knn_query(queries_np, k=min(topk, len(ids)))
        results = []
        for label, dist in zip(labels, distances):
            query_results = [(int(idx), 1.0 - d) for idx, d in zip(label, dist)]
            results.append(query_results)
        return results
    
    elif backend == 'faiss':
        # FAISS batch search
        queries_np = np.array(queries)
        scores, indices = index.search(queries_np, min(topk, len(ids)))
        results = []
        for score_vec, idx_vec in zip(scores, indices):
            query_results = [(int(i), float(s)) for i, s in zip(idx_vec, score_vec) if i >= 0]
            results.append(query_results)
        return results
    
    else:
        # NumPy batch search - vectorized
        queries_np = np.array(queries)  # (batch, 384)
        # scores: (batch, n_vectors)
        scores = np.dot(queries_np, index.T)
        results = []
        for score_vec in scores:
            top_indices = np.argsort(score_vec)[::-1][:topk]
            results.append([(int(i), float(score_vec[i])) for i in top_indices])
        return results

if __name__ == "__main__":
    # Test
    print("Testing vector search backends...")
    
    # Generate test data
    np.random.seed(42)
    n_vectors = 1000
    dim = 384
    
    vectors = {
        f"vec_{i}": np.random.randn(dim).astype(np.float32)
        for i in range(n_vectors)
    }
    
    # Normalize
    for k, v in vectors.items():
        v /= np.linalg.norm(v)
    
    print(f"Built {n_vectors} test vectors")
    
    # Build index
    index_obj, ids = build_index(vectors, dim)
    print(f"Backend: {index_obj[0]}")
    
    # Single query
    query = np.random.randn(dim).astype(np.float32)
    query /= np.linalg.norm(query)
    
    import time
    start = time.perf_counter()
    results = search_index(index_obj, query, topk=10)
    t1 = (time.perf_counter() - start) * 1000
    print(f"Single query: {t1:.3f}ms")
    
    # Batch query
    queries = [np.random.randn(dim).astype(np.float32) for _ in range(10)]
    for q in queries:
        q /= np.linalg.norm(q)
    
    start = time.perf_counter()
    batch_results = batch_search(index_obj, queries, topk=10)
    t2 = (time.perf_counter() - start) * 1000
    print(f"Batch 10 queries: {t2:.3f}ms ({t2/10:.3f}ms each)")
    print(f"Speedup: {t1*10/t2:.1f}x")
