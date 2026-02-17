#!/usr/bin/env python3
"""
Embedding wrapper for all-MiniLM-L6-v2
Lightweight, local, no API calls
"""

import os
from typing import List, Union

# Cache model at module level for reuse
_model = None
_tokenizer = None

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

def embed(text: Union[str, List[str]], batch_size: int = 32) -> Union[List[float], List[List[float]]]:
    """
    Embed text(s) into 384-dimensional vectors.
    
    Args:
        text: Single string or list of strings
        batch_size: Batch size for processing (default 32)
    
    Returns:
        Single vector (list of 384 floats) or list of vectors
    """
    model = get_model()
    
    if isinstance(text, str):
        result = model.encode(text, convert_to_numpy=True)
        return result.tolist()
    else:
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

if __name__ == "__main__":
    # Test
    print("Loading model...")
    test_text = "This is a test sentence for embedding."
    vector = embed(test_text)
    print(f"Embedded '{test_text[:30]}...'")
    print(f"Dimension: {len(vector)}")
    print(f"First 5 values: {vector[:5]}")
