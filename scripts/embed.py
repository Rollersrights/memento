#!/usr/bin/env python3
"""
Embedding wrapper for all-MiniLM-L6-v2
Lightweight, local, no API calls
With LRU caching, Persistent Disk Cache (SQLite), AVX2/ONNX optimization,
and BACKGROUND LOADING for fast cold start.
"""

import os
import sys
import hashlib
import sqlite3
import json
import time
import threading
from functools import lru_cache
from typing import List, Union, Tuple, Optional
from pathlib import Path

# Background loading support
_model_loading_thread = None
_model_ready_event = threading.Event()
_model_loading_started = False
_model_loading_lock = threading.Lock()

# Cache model at module level for reuse
_model = None
_tokenizer = None
_onnx_session = None
_embedder_type = None  # 'onnx' or 'pytorch'
_onnx_tokenizer = None  # Cached tokenizer for ONNX path

# Cache stats
_cache_hits = 0
_cache_misses = 0
_disk_hits = 0

# ============================================================================
# BACKGROUND MODEL LOADING - Fixes cold start issue #13
# ============================================================================

def _load_model_background():
    """Load model in background thread to hide cold start latency."""
    global _model, _onnx_session, _embedder_type
    
    try:
        # Detect best embedder type
        embedder = _get_embedder_type()
        
        if embedder == 'onnx':
            # Pre-load ONNX model
            _load_onnx_model()
        else:
            # Pre-load PyTorch model
            from sentence_transformers import SentenceTransformer
            cache_dir = os.path.expanduser("~/.memento/models")
            os.makedirs(cache_dir, exist_ok=True)
            _model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                cache_folder=cache_dir
            )
        
        # Signal that model is ready
        _model_ready_event.set()
        
    except Exception as e:
        print(f"[Embed] Background loading failed: {e}", file=sys.stderr)
        # Still signal ready to prevent blocking forever
        _model_ready_event.set()

def _start_background_loading():
    """Start background model loading thread (call once on import)."""
    global _model_loading_thread, _model_loading_started
    
    with _model_loading_lock:
        if _model_loading_started:
            return
        _model_loading_started = True
        
        _model_loading_thread = threading.Thread(target=_load_model_background, daemon=True)
        _model_loading_thread.start()

def is_model_ready() -> bool:
    """Check if model has finished loading in background."""
    return _model_ready_event.is_set()

def wait_for_model(timeout: float = 30.0) -> bool:
    """Wait for model to be ready. Returns True if ready, False on timeout."""
    return _model_ready_event.wait(timeout)

# Start background loading immediately on module import
_start_background_loading()

class PersistentCache:
    """SQLite-backed persistent cache for embeddings (binary blob storage)."""
    def __init__(self) -> None:
        self.db_path = os.path.expanduser("~/.memento/cache.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        
    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            # Check if we need to migrate from JSON text to binary blob
            cursor = conn.execute("SELECT sql FROM sqlite_master WHERE name='embeddings'")
            row = cursor.fetchone()
            if row and 'vector TEXT' in row[0]:
                # Migrate: rename old table, create new, copy data
                try:
                    conn.execute("ALTER TABLE embeddings RENAME TO embeddings_old")
                    conn.execute("""
                        CREATE TABLE embeddings (
                            hash TEXT PRIMARY KEY,
                            vector BLOB,
                            last_accessed REAL
                        )
                    """)
                    # Migrate existing data from JSON text to binary blob
                    cursor = conn.execute("SELECT hash, vector, last_accessed FROM embeddings_old")
                    import numpy as np
                    for r in cursor.fetchall():
                        try:
                            vec = json.loads(r[1])
                            blob = np.array(vec, dtype=np.float32).tobytes()
                            conn.execute(
                                "INSERT INTO embeddings (hash, vector, last_accessed) VALUES (?, ?, ?)",
                                (r[0], blob, r[2])
                            )
                        except Exception:
                            pass  # Skip corrupt entries
                    conn.execute("DROP TABLE embeddings_old")
                    conn.commit()
                except Exception:
                    # If migration fails, just recreate
                    conn.execute("DROP TABLE IF EXISTS embeddings_old")
                    conn.execute("DROP TABLE IF EXISTS embeddings")
                    conn.execute("""
                        CREATE TABLE embeddings (
                            hash TEXT PRIMARY KEY,
                            vector BLOB,
                            last_accessed REAL
                        )
                    """)
                    conn.commit()
            elif row is None:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        hash TEXT PRIMARY KEY,
                        vector BLOB,
                        last_accessed REAL
                    )
                """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_access ON embeddings(last_accessed)")
            
    def get(self, text_hash: str) -> Union[Tuple[float, ...], None]:
        try:
            import numpy as np
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT vector FROM embeddings WHERE hash = ?", 
                    (text_hash,)
                )
                row = cursor.fetchone()
                if row:
                    conn.execute(
                        "UPDATE embeddings SET last_accessed = ? WHERE hash = ?",
                        (time.time(), text_hash)
                    )
                    return tuple(np.frombuffer(row[0], dtype=np.float32))
        except Exception as e:
            print(f"Cache read error: {e}")
        return None

    def set(self, text_hash: str, vector: Tuple[float, ...]) -> None:
        try:
            import numpy as np
            blob = np.array(vector, dtype=np.float32).tobytes()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO embeddings (hash, vector, last_accessed) VALUES (?, ?, ?)",
                    (text_hash, blob, time.time())
                )
        except Exception as e:
            print(f"Cache write error: {e}")

# Global disk cache instance
_disk_cache = PersistentCache()

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
        except ImportError:
            pass
        except Exception:
            pass
        
        # Method 3: Try to execute AVX2 instruction (dangerous, skip for safety)
        return False
    except Exception:
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
        # Only print once
        # print("[Embed] AVX2 detected, trying ONNX Runtime...")
        if _try_onnx():
            _embedder_type = 'onnx'
            # print("[Embed] Using ONNX Runtime (fast)")
        else:
            # print("[Embed] ONNX not available, using PyTorch (compatible)")
            pass
    else:
        # print("[Embed] No AVX2 detected, using PyTorch (compatible)")
        pass
    
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

def _get_onnx_tokenizer():
    """Get or load cached ONNX tokenizer."""
    global _onnx_tokenizer
    if _onnx_tokenizer is None:
        from transformers import AutoTokenizer
        cache_dir = os.path.expanduser("~/.memento/models")
        _onnx_tokenizer = AutoTokenizer.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=cache_dir
        )
    return _onnx_tokenizer

def _embed_onnx(texts: List[str]) -> List[List[float]]:
    """Embed using ONNX Runtime."""
    import numpy as np
    
    # Wait for background loading to complete (fixes cold start issue #13)
    if not _model_ready_event.is_set():
        print("[Embed] Loading ONNX model (one-time)...", file=sys.stderr, flush=True)
        if not wait_for_model(timeout=60.0):
            print("[Embed] ONNX model loading timed out, forcing load...", file=sys.stderr)
    
    session = _load_onnx_model()
    if session is None:
        # Fallback to PyTorch
        return _embed_pytorch(texts)
    
    # Load tokenizer (cached after first call)
    tokenizer = _get_onnx_tokenizer()
    
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
    
    # Wait for background loading to complete (fixes cold start issue #13)
    if not _model_ready_event.is_set():
        print("[Embed] Loading model (one-time)...", file=sys.stderr, flush=True)
        if not wait_for_model(timeout=60.0):
            print("[Embed] Model loading timed out, forcing load...", file=sys.stderr)
    
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
    """Generate cache key for text (blake2b — fast, collision-resistant)."""
    return hashlib.blake2b(text.encode('utf-8'), digest_size=16).hexdigest()

# LRU cache for single text embeddings (max 1000 entries) - RAM Layer
@lru_cache(maxsize=1000)
def _embed_single_cached(text_hash: str, text: str) -> Tuple[float, ...]:
    """
    Internal cached embedding function.
    RAM -> Disk -> Compute (ONNX/PyTorch)
    """
    global _cache_misses, _disk_hits
    
    # Check disk cache first (missed RAM if we are here)
    disk_result = _disk_cache.get(text_hash)
    if disk_result:
        _disk_hits += 1
        return disk_result
    
    # Real miss - compute
    _cache_misses += 1
    
    embedder = _get_embedder_type()
    if embedder == 'onnx':
        result = _embed_onnx([text])[0]
    else:
        result = _embed_pytorch([text])[0]
    
    vector_tuple = tuple(result)
    
    # Save to disk for next time
    _disk_cache.set(text_hash, vector_tuple)
    
    return vector_tuple

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
            
            # Check RAM cache
            cached_info = _embed_single_cached.cache_info()
            result_tuple = _embed_single_cached(cache_key, text)
            
            # If hits count increased, it was in RAM
            if _embed_single_cached.cache_info().hits > cached_info.hits:
                _cache_hits += 1
            
            return list(result_tuple)
        else:
            # Bypass cache (compute directly)
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

def warmup() -> bool:
    """
    Pre-load model to eliminate cold start latency.
    Call this at system startup or in cron jobs.
    
    Returns:
        True if model is ready, False on timeout
    """
    if is_model_ready():
        return True
    
    print("[Embed] Warming up model (background loading)...", file=sys.stderr, flush=True)
    
    # Wait for background loading to complete
    if wait_for_model(timeout=60.0):
        print("[Embed] Model ready!", file=sys.stderr)
        return True
    else:
        print("[Embed] Model loading timed out", file=sys.stderr)
        return False

def get_cache_stats() -> dict:
    """Get cache statistics."""
    cache_info = _embed_single_cached.cache_info()
    embedder = _get_embedder_type()
    return {
        'hits': _cache_hits,
        'misses': _cache_misses,
        'disk_hits': _disk_hits,
        'lru_hits': cache_info.hits,
        'lru_misses': cache_info.misses,
        'maxsize': cache_info.maxsize,
        'currsize': cache_info.currsize,
        'hit_rate': cache_info.hits / (cache_info.hits + cache_info.misses) * 100 if (cache_info.hits + cache_info.misses) > 0 else 0,
        'embedder': embedder,
        'model_ready': is_model_ready(),
        'background_loading': _model_loading_started
    }

def clear_cache() -> None:
    """Clear the embedding cache."""
    _embed_single_cached.cache_clear()
    global _cache_hits, _cache_misses, _disk_hits
    _cache_hits = 0
    _cache_misses = 0
    _disk_hits = 0

if __name__ == "__main__":
    # Test with auto-detect
    print("Testing embedding with automatic hardware detection...")
    print(f"Embedder type: {_get_embedder_type()}")
    print(f"Background loading: {_model_loading_started}")
    print(f"Model ready: {is_model_ready()}")
    
    test_text = "This is a test sentence for embedding."
    
    # First call - test cold start with background loading
    import time
    start = time.perf_counter()
    vector1 = embed(test_text)
    t1 = (time.perf_counter() - start) * 1000
    print(f"\nFirst embed: {t1:.2f}ms (cold start with background loading)")
    
    # Second call - cache hit
    start = time.perf_counter()
    vector2 = embed(test_text)
    t2 = (time.perf_counter() - start) * 1000
    print(f"Second embed: {t2:.2f}ms (cached)")
    
    if t2 > 0:
        print(f"Speedup: {t1/t2:.1f}x")
    print(f"Vectors match: {vector1 == vector2}")
    
    print(f"\nCache stats: {get_cache_stats()}")
    print(f"Dimension: {len(vector1)}")
    
    # Cold start target: < 1000ms with background loading
    if t1 < 1000:
        print(f"\n✅ Cold start target met: {t1:.0f}ms < 1000ms")
    else:
        print(f"\n⚠️ Cold start slow: {t1:.0f}ms (target: <1000ms)")
