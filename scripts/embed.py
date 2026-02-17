#!/usr/bin/env python3
"""
Embedding wrapper for all-MiniLM-L6-v2
Lightweight, local, no API calls
With LRU caching for repeated queries
"""

import os
import hashlib
from functools import lru_cache
from typing import List, Union, Tuple

# Cache model at module level for reuse
_model = None
_tokenizer = None

# Cache stats
_cache_hits = 0
_cache_misses = 0

def get_model():
    """Lazy-load the embedding model (cached)."""
    global _model, _tokenizer
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # Use cache dir in ~/.memento
        cache_dir = os.path.expanduser("~/.memento/models")
        os.makedirs(cache_dir, exist_ok=True)
        _model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            cache_folder=cache_dir
        )
    return _model

def _get_cache_key(text: str) -> str:
    """Generate cache key for text (hash-based)."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

# LRU cache for single text embeddings (max 1000 entries)
@lru_cache(maxsize=1000)
def _embed_single_cached(text_hash: str, text: str) -> Tuple[float, ...]:
    """
    Internal cached embedding function.
    Uses hash+text as key to handle collisions safely.
    Returns tuple (hashable for cache).
    """
    global _cache_misses
    _cache_misses += 1
    
    model = get_model()
    result = model.encode(text, convert_to_numpy=True)
    return tuple(result.tolist())

def embed(text: Union[str, List[str]], batch_size: int = 32, use_cache: bool = True) -> Union[List[float], List[List[float]]]:
    """
    Embed text(s) into 384-dimensional vectors.
    
    Args:
        text: Single string or list of strings
        batch_size: Batch size for processing (default 32)
        use_cache: Whether to use LRU cache for single texts (default True)
    
    Returns:
        Single vector (list of 384 floats) or list of vectors
    """
    global _cache_hits
    
    # Single text - use cache
    if isinstance(text, str):
        if use_cache:
            cache_key = _get_cache_key(text)
            # Check if in cache (lru_cache handles this, but we track hits)
            cached = _embed_single_cached.cache_info()
            
            result_tuple = _embed_single_cached(cache_key, text)
            new_cached = _embed_single_cached.cache_info()
            
            # Track hits (approximate)
            if new_cached.hits > cached.hits:
                _cache_hits += 1
            
            return list(result_tuple)
        else:
            # Bypass cache
            model = get_model()
            result = model.encode(text, convert_to_numpy=True)
            return result.tolist()
    
    # Batch - check cache for each, embed missing
    else:
        if use_cache and len(text) <= 10:  # Only cache small batches
            results = []
            for t in text:
                cache_key = _get_cache_key(t)
                result_tuple = _embed_single_cached(cache_key, t)
                results.append(list(result_tuple))
            return results
        else:
            # Large batch - process all at once (faster)
            model = get_model()
            results = model.encode(text, batch_size=batch_size, convert_to_numpy=True)
            return [r.tolist() for r in results]

def embed_chunks(chunks: List[str], batch_size: int = 32) -> List[List[float]]:
    """Embed a list of text chunks efficiently."""
    return embed(chunks, batch_size=batch_size)

def get_embedding_dimension() -> int:
    """Return the embedding dimension (384 for MiniLM-L6-v2)."""
    return 384

def get_max_tokens() -> int:
    """Return max token length (256 for MiniLM-L6-v2)."""
    return 256

def get_cache_stats() -> dict:
    """Get cache statistics."""
    cache_info = _embed_single_cached.cache_info()
    return {
        'hits': _cache_hits,
        'misses': _cache_misses,
        'lru_hits': cache_info.hits,
        'lru_misses': cache_info.misses,
        'maxsize': cache_info.maxsize,
        'currsize': cache_info.currsize,
        'hit_rate': cache_info.hits / (cache_info.hits + cache_info.misses) * 100 if (cache_info.hits + cache_info.misses) > 0 else 0
    }

def clear_cache():
    """Clear the embedding cache."""
    _embed_single_cached.cache_clear()
    global _cache_hits, _cache_misses
    _cache_hits = 0
    _cache_misses = 0

if __name__ == "__main__":
    # Test with caching
    print("Testing embedding with cache...")
    
    test_text = "This is a test sentence for embedding."
    
    # First call - cache miss
    import time
    start = time.perf_counter()
    vector1 = embed(test_text)
    t1 = (time.perf_counter() - start) * 1000
    print(f"First embed: {t1:.2f}ms (cold)")
    
    # Second call - cache hit
    start = time.perf_counter()
    vector2 = embed(test_text)
    t2 = (time.perf_counter() - start) * 1000
    print(f"Second embed: {t2:.2f}ms (cached)")
    
    print(f"Speedup: {t1/t2:.1f}x")
    print(f"Vectors match: {vector1 == vector2}")
    
    print(f"\nCache stats: {get_cache_stats()}")
    print(f"Dimension: {len(vector1)}")
