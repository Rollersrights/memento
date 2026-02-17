#!/usr/bin/env python3
"""
Embedding wrapper for all-MiniLM-L6-v2
Lightweight, local, no API calls
With LRU caching and automatic hardware optimization (ONNX for AVX2, PyTorch fallback)
"""

import os
import sys
import hashlib
from functools import lru_cache
from typing import List, Union, Tuple, Optional

# Cache model at module level for reuse
_model = None
_tokenizer = None
_onnx_session = None
_embedder_type = None  # 'onnx' or 'pytorch'

# Cache stats
_cache_hits = 0
_cache_misses = 0

def _has_avx2() -> bool:
    """Detect AVX2 support at runtime."""
    try:
        # Method 1: Check CPU flags via /proc/cpuinfo (Linux)
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'avx2' in cpuinfo.lower():
                    return True
        
        # Method 2: Try cpuinfo library if available
        try:
            import cpuinfo
            info = cpuinfo.get_cpu_info()
            flags = info.get('flags', []) if info else []
            if isinstance(flags, list):
                return 'avx2' in [f.lower() for f in flags]
            elif isinstance(flags, str):
                return 'avx2' in flags.lower()
        except:
            pass
        
        # Method 3: Try to execute AVX2 instruction (dangerous, skip for safety)
        return False
    except:
        return False

def _try_onnx() -> bool:
    """Try to load ONNX Runtime with the optimized model."""
    global _onnx_session
    
    try:
        import onnxruntime as ort
        
        # Check ONNX Runtime has AVX2 support
        sess_options = ort.SessionOptions()
        
        # Try to create a test session to verify it works
        # We'll create the actual session later when we have the model path
        _onnx_session = 'available'  # Mark as available, load model on first use
        return True
        
    except ImportError:
        return False
    except Exception as e:
        print(f"[Embed] ONNX Runtime available but failed: {e}", file=sys.stderr)
        return False

def _get_embedder_type() -> str:
    """Determine best embedder for this hardware."""
    global _embedder_type
    
    if _embedder_type is not None:
        return _embedder_type
    
    # Default to PyTorch (always works)
    _embedder_type = 'pytorch'
    
    # Check for AVX2
    has_avx2 = _has_avx2()
    
    if has_avx2:
        print("[Embed] AVX2 detected, trying ONNX Runtime...")
        if _try_onnx():
            _embedder_type = 'onnx'
            print("[Embed] Using ONNX Runtime (fast)")
        else:
            print("[Embed] ONNX not available, using PyTorch (compatible)")
    else:
        print("[Embed] No AVX2 detected, using PyTorch (compatible)")
    
    return _embedder_type

def _load_onnx_model():
    """Load or convert model to ONNX format."""
    global _onnx_session
    
    if _onnx_session is not None and _onnx_session != 'available':
        return _onnx_session
    
    import onnxruntime as ort
    from pathlib import Path
    
    cache_dir = Path.home() / ".memento" / "models"
    onnx_path = cache_dir / "all-MiniLM-L6-v2.onnx"
    
    # Check if ONNX model already exists
    if onnx_path.exists():
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        _onnx_session = ort.InferenceSession(str(onnx_path), sess_options)
        return _onnx_session
    
    # Need to convert from PyTorch to ONNX
    print("[Embed] Converting model to ONNX (one-time)...")
    
    try:
        from sentence_transformers import SentenceTransformer
        import torch
        import numpy as np
        
        # Load PyTorch model
        model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            cache_folder=str(cache_dir)
        )
        
        # Export to ONNX
        dummy_input = "This is a test sentence."
        dummy_tokens = model.tokenize([dummy_input])
        
        # Get actual input names and shapes
        input_ids = dummy_tokens['input_ids']
        attention_mask = dummy_tokens['attention_mask']
        
        # Export
        torch.onnx.export(
            model._first_module().auto_model,
            (input_ids, attention_mask),
            str(onnx_path),
            input_names=['input_ids', 'attention_mask'],
            output_names=['output'],
            dynamic_axes={
                'input_ids': {0: 'batch_size', 1: 'sequence'},
                'attention_mask': {0: 'batch_size', 1: 'sequence'},
                'output': {0: 'batch_size'}
            },
            opset_version=14
        )
        
        # Load the ONNX model
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        _onnx_session = ort.InferenceSession(str(onnx_path), sess_options)
        print(f"[Embed] ONNX model saved to {onnx_path}")
        return _onnx_session
        
    except Exception as e:
        print(f"[Embed] ONNX conversion failed: {e}", file=sys.stderr)
        print("[Embed] Falling back to PyTorch", file=sys.stderr)
        global _embedder_type
        _embedder_type = 'pytorch'
        return None

def _embed_onnx(texts: List[str]) -> List[List[float]]:
    """Embed using ONNX Runtime."""
    import numpy as np
    from transformers import AutoTokenizer
    
    session = _load_onnx_model()
    if session is None:
        # Fallback to PyTorch
        return _embed_pytorch(texts)
    
    # Load tokenizer (same as model)
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    
    # Tokenize
    inputs = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors='np'
    )
    
    # Run inference
    ort_inputs = {
        'input_ids': inputs['input_ids'],
        'attention_mask': inputs['attention_mask']
    }
    
    outputs = session.run(None, ort_inputs)[0]
    
    # Mean pooling (same as sentence-transformers)
    attention_mask = inputs['attention_mask']
    input_mask_expanded = np.expand_dims(attention_mask, -1).astype(np.float32)
    sum_embeddings = np.sum(outputs * input_mask_expanded, axis=1)
    mask_sum = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
    embeddings = sum_embeddings / mask_sum
    
    # Normalize
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    return embeddings.tolist()

def _embed_pytorch(texts: List[str]) -> List[List[float]]:
    """Embed using PyTorch/SentenceTransformers."""
    global _model
    
    if _model is None:
        from sentence_transformers import SentenceTransformer
        cache_dir = os.path.expanduser("~/.memento/models")
        os.makedirs(cache_dir, exist_ok=True)
        _model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            cache_folder=cache_dir
        )
    
    results = _model.encode(texts, convert_to_numpy=True)
    return [r.tolist() for r in results]

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
    
    embedder = _get_embedder_type()
    
    if embedder == 'onnx':
        result = _embed_onnx([text])[0]
    else:
        result = _embed_pytorch([text])[0]
    
    return tuple(result)

def embed(text: Union[str, List[str]], batch_size: int = 32, use_cache: bool = True) -> Union[List[float], List[List[float]]]:
    """
    Embed text(s) into 384-dimensional vectors.
    Automatically uses ONNX Runtime (AVX2) or PyTorch fallback.
    
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
            cached = _embed_single_cached.cache_info()
            
            result_tuple = _embed_single_cached(cache_key, text)
            new_cached = _embed_single_cached.cache_info()
            
            if new_cached.hits > cached.hits:
                _cache_hits += 1
            
            return list(result_tuple)
        else:
            # Bypass cache
            embedder = _get_embedder_type()
            if embedder == 'onnx':
                return _embed_onnx([text])[0]
            else:
                return _embed_pytorch([text])[0]
    
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
            embedder = _get_embedder_type()
            if embedder == 'onnx':
                return _embed_onnx(text)
            else:
                return _embed_pytorch(text)

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
    embedder = _get_embedder_type()
    return {
        'hits': _cache_hits,
        'misses': _cache_misses,
        'lru_hits': cache_info.hits,
        'lru_misses': cache_info.misses,
        'maxsize': cache_info.maxsize,
        'currsize': cache_info.currsize,
        'hit_rate': cache_info.hits / (cache_info.hits + cache_info.misses) * 100 if (cache_info.hits + cache_info.misses) > 0 else 0,
        'embedder': embedder
    }

def clear_cache():
    """Clear the embedding cache."""
    _embed_single_cached.cache_clear()
    global _cache_hits, _cache_misses
    _cache_hits = 0
    _cache_misses = 0

if __name__ == "__main__":
    # Test with auto-detect
    print("Testing embedding with automatic hardware detection...")
    print(f"Embedder type: {_get_embedder_type()}")
    
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
