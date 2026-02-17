#!/usr/bin/env python3
"""
Embedding wrapper for all-MiniLM-L6-v2
Lightweight, local, no API calls
ONNX Runtime with PyTorch fallback for non-AVX2 machines
"""

import os
import sys
import hashlib
import sqlite3
import time
import threading
from functools import lru_cache
from typing import List, Union, Tuple
from pathlib import Path

import numpy as np

# Module-level cache
_model_loading_thread = None
_model_ready_event = threading.Event()
_model_loading_started = False
_model_loading_lock = threading.Lock()
_onnx_session = None
_onnx_tokenizer = None
_pytorch_model = None
_embedder_type = None  # 'onnx' or 'pytorch'

# Cache stats
_cache_hits = 0
_cache_misses = 0
_disk_hits = 0

# Idle timeout support
_idle_timer = None
_idle_timeout_seconds = None
_last_activity_time = None
_idle_lock = threading.Lock()


def _has_avx2() -> bool:
    """Detect AVX2 support at runtime."""
    try:
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                return 'avx2' in f.read().lower()
    except Exception:
        pass
    return False


def _load_model_background():
    """Load model in background thread."""
    global _onnx_session, _embedder_type
    try:
        _load_onnx_model()
        _embedder_type = 'onnx'
        _model_ready_event.set()
    except Exception as e:
        print(f"[Embed] ONNX failed ({e}), will try PyTorch fallback", file=sys.stderr)
        try:
            _load_pytorch_model()
            _embedder_type = 'pytorch'
            _model_ready_event.set()
        except Exception as e2:
            print(f"[Embed] PyTorch fallback also failed: {e2}", file=sys.stderr)
            _model_ready_event.set()


def _start_background_loading():
    """Start background model loading."""
    global _model_loading_thread, _model_loading_started
    with _model_loading_lock:
        if _model_loading_started:
            return
        _model_loading_started = True
        _model_loading_thread = threading.Thread(target=_load_model_background, daemon=True)
        _model_loading_thread.start()


def is_model_ready() -> bool:
    """Check if model has finished loading."""
    return _model_ready_event.is_set()


def wait_for_model(timeout: float = 30.0) -> bool:
    """Wait for model to be ready."""
    return _model_ready_event.wait(timeout)


def _reset_idle_timer():
    """Reset idle timer on model activity."""
    global _idle_timer, _last_activity_time
    with _idle_lock:
        _last_activity_time = time.time()
        if _idle_timer is not None:
            _idle_timer.cancel()
        if _idle_timeout_seconds is not None and _idle_timeout_seconds > 0:
            _idle_timer = threading.Timer(_idle_timeout_seconds, unload_model)
            _idle_timer.daemon = True
            _idle_timer.start()


def set_idle_timeout(minutes: float) -> None:
    """Set idle timeout for automatic model unloading."""
    global _idle_timeout_seconds
    if minutes is None or minutes <= 0:
        _idle_timeout_seconds = None
        with _idle_lock:
            if _idle_timer is not None:
                _idle_timer.cancel()
                _idle_timer = None
    else:
        _idle_timeout_seconds = minutes * 60
        _reset_idle_timer()


def unload_model(force: bool = False) -> bool:
    """Free model from RAM."""
    global _onnx_session, _pytorch_model, _embedder_type
    global _model_loading_started, _model_ready_event, _model_loading_thread
    global _idle_timer  # Add this line
    
    unloaded = False
    if _onnx_session is not None:
        _onnx_session = None
        unloaded = True
    if _pytorch_model is not None:
        _pytorch_model = None
        unloaded = True
    
    if not unloaded:
        return False
        
    with _idle_lock:
        if _idle_timer is not None:
            _idle_timer.cancel()
            _idle_timer = None
    
    _embedder_type = None
    _model_loading_started = False
    _model_ready_event.clear()
    _model_loading_thread = None
    import gc
    gc.collect()
    return True


def get_memory_usage() -> dict:
    """Get current memory usage statistics."""
    result = {
        'model_loaded': False, 
        'embedder_type': _embedder_type,
        'estimated_mb': 0, 
        'idle_timeout_min': None, 
        'seconds_idle': None
    }
    if _onnx_session is not None or _pytorch_model is not None:
        result['model_loaded'] = True
        result['estimated_mb'] = 85 if _embedder_type == 'onnx' else 80
    if _idle_timeout_seconds is not None:
        result['idle_timeout_min'] = _idle_timeout_seconds / 60
        if _last_activity_time is not None:
            result['seconds_idle'] = time.time() - _last_activity_time
    return result


class PersistentCache:
    """SQLite-backed persistent cache for embeddings."""
    def __init__(self) -> None:
        self.db_path = os.path.expanduser("~/.openclaw/memento/cache.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        
    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT vector FROM embeddings WHERE hash = ?", (text_hash,))
                row = cursor.fetchone()
                if row:
                    conn.execute("UPDATE embeddings SET last_accessed = ? WHERE hash = ?",
                                (time.time(), text_hash))
                    return tuple(np.frombuffer(row[0], dtype=np.float32))
        except Exception as e:
            print(f"Cache read error: {e}")
        return None

    def set(self, text_hash: str, vector: Tuple[float, ...]) -> None:
        try:
            blob = np.array(vector, dtype=np.float32).tobytes()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO embeddings (hash, vector, last_accessed) VALUES (?, ?, ?)",
                            (text_hash, blob, time.time()))
        except Exception as e:
            print(f"Cache write error: {e}")


_disk_cache = PersistentCache()


def _load_onnx_model():
    """Load or convert model to ONNX format."""
    global _onnx_session
    if _onnx_session is not None:
        return _onnx_session
    
    import onnxruntime as ort
    from pathlib import Path
    from transformers import AutoTokenizer, AutoModel
    import torch
    
    cache_dir = Path.home() / ".memento" / "models"
    onnx_path = cache_dir / "all-MiniLM-L6-v2.onnx"
    
    if onnx_path.exists():
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        _onnx_session = ort.InferenceSession(str(onnx_path), sess_options)
        return _onnx_session
    
    print("[Embed] Converting model to ONNX (one-time)...")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2", cache_dir=str(cache_dir))
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2", cache_dir=str(cache_dir))
    
    dummy_input = tokenizer("This is a test sentence.", padding=True, truncation=True, 
                           max_length=256, return_tensors='pt')
    
    torch.onnx.export(
        model,
        (dummy_input['input_ids'], dummy_input['attention_mask']),
        str(onnx_path),
        input_names=['input_ids', 'attention_mask'],
        output_names=['output'],
        dynamic_axes={'input_ids': {0: 'batch_size', 1: 'sequence'},
                     'attention_mask': {0: 'batch_size', 1: 'sequence'},
                     'output': {0: 'batch_size'}},
        opset_version=14
    )
    
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    _onnx_session = ort.InferenceSession(str(onnx_path), sess_options)
    print(f"[Embed] ONNX model saved to {onnx_path}")
    return _onnx_session


def _load_pytorch_model():
    """Load PyTorch model as fallback."""
    global _pytorch_model
    if _pytorch_model is not None:
        return _pytorch_model
    
    from sentence_transformers import SentenceTransformer
    cache_dir = os.path.expanduser("~/.openclaw/memento/models")
    os.makedirs(cache_dir, exist_ok=True)
    
    print("[Embed] Loading PyTorch model (fallback)...", file=sys.stderr)
    _pytorch_model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        cache_folder=cache_dir
    )
    return _pytorch_model


def _get_onnx_tokenizer():
    """Get or load tokenizer."""
    global _onnx_tokenizer
    if _onnx_tokenizer is None:
        from transformers import AutoTokenizer
        cache_dir = os.path.expanduser("~/.openclaw/memento/models")
        _onnx_tokenizer = AutoTokenizer.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2", cache_dir=cache_dir)
    return _onnx_tokenizer


_start_background_loading()


def _embed_onnx(texts: List[str]) -> List[List[float]]:
    """Embed using ONNX Runtime."""
    _reset_idle_timer()
    
    if not _model_ready_event.is_set():
        print("[Embed] Loading ONNX model...", file=sys.stderr, flush=True)
        if not wait_for_model(timeout=60.0):
            print("[Embed] Model loading timed out", file=sys.stderr)
    
    session = _load_onnx_model()
    tokenizer = _get_onnx_tokenizer()
    
    # Process individually to avoid ONNX batch shape issues
    # See Issue #38: ONNX has buffer reuse problems with variable batch sizes
    if len(texts) == 1:
        return _embed_onnx_single(texts[0], session, tokenizer)
    
    results = []
    for text in texts:
        results.append(_embed_onnx_single(text, session, tokenizer))
    return results


def _embed_onnx_single(text: str, session, tokenizer) -> List[float]:
    """Embed a single text using ONNX."""
    inputs = tokenizer(text, padding=True, truncation=True, max_length=256, return_tensors='np')
    
    ort_inputs = {
        'input_ids': inputs['input_ids'].astype(np.int64),
        'attention_mask': inputs['attention_mask'].astype(np.int64),
        'token_type_ids': inputs.get('token_type_ids', np.zeros_like(inputs['input_ids'])).astype(np.int64)
    }
    
    outputs = session.run(None, ort_inputs)[0]
    
    # Mean pooling
    attention_mask = inputs['attention_mask']
    input_mask_expanded = np.expand_dims(attention_mask, -1).astype(np.float32)
    sum_embeddings = np.sum(outputs * input_mask_expanded, axis=1)
    mask_sum = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
    embeddings = sum_embeddings / mask_sum
    
    # Normalize
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    return embeddings[0].tolist()


def _embed_pytorch(texts: List[str]) -> List[List[float]]:
    """Embed using PyTorch/SentenceTransformers (fallback)."""
    global _pytorch_model
    _reset_idle_timer()
    
    if _pytorch_model is None:
        _load_pytorch_model()
    
    results = _pytorch_model.encode(texts, convert_to_numpy=True)
    return [r.tolist() for r in results]


def _get_cache_key(text: str) -> str:
    """Generate cache key for text."""
    return hashlib.blake2b(text.encode('utf-8'), digest_size=16).hexdigest()


@lru_cache(maxsize=1000)
def _embed_single_cached(text_hash: str, text: str) -> Tuple[float, ...]:
    """Internal cached embedding function."""
    global _cache_misses, _disk_hits
    
    disk_result = _disk_cache.get(text_hash)
    if disk_result:
        _disk_hits += 1
        return disk_result
    
    _cache_misses += 1
    
    # Try ONNX first, fall back to PyTorch
    try:
        if _embedder_type == 'pytorch' or _onnx_session is None:
            result = _embed_pytorch([text])[0]
        else:
            result = _embed_onnx([text])[0]
    except Exception:
        # Last resort: try PyTorch
        result = _embed_pytorch([text])[0]
    
    vector_tuple = tuple(result)
    _disk_cache.set(text_hash, vector_tuple)
    return vector_tuple


def embed(text: Union[str, List[str]], batch_size: int = 32, use_cache: bool = True) -> Union[List[float], List[List[float]]]:
    """Embed text(s) into 384-dimensional vectors."""
    global _cache_hits, _embedder_type
    
    # Ensure model is loaded and determine embedder type
    if not _model_ready_event.is_set():
        wait_for_model(timeout=60.0)
    
    if isinstance(text, str):
        if use_cache:
            cache_key = _get_cache_key(text)
            cached_info = _embed_single_cached.cache_info()
            result_tuple = _embed_single_cached(cache_key, text)
            if _embed_single_cached.cache_info().hits > cached_info.hits:
                _cache_hits += 1
            return list(result_tuple)
        else:
            # Bypass cache
            try:
                if _embedder_type == 'pytorch':
                    return _embed_pytorch([text])[0]
                return _embed_onnx([text])[0]
            except Exception:
                return _embed_pytorch([text])[0]
    else:
        if use_cache and len(text) <= 10:
            results = []
            for t in text:
                cache_key = _get_cache_key(t)
                result_tuple = _embed_single_cached(cache_key, t)
                results.append(list(result_tuple))
            return results
        else:
            # Large batch - process all at once
            try:
                if _embedder_type == 'pytorch':
                    return _embed_pytorch(text)
                return _embed_onnx(text)
            except Exception:
                return _embed_pytorch(text)


def embed_chunks(chunks: List[str], batch_size: int = 32) -> List[List[float]]:
    """Embed a list of text chunks."""
    return embed(chunks, batch_size=batch_size)


def get_embedding_dimension() -> int:
    """Return the embedding dimension."""
    return 384


def get_max_tokens() -> int:
    """Return max token length."""
    return 256


def warmup() -> bool:
    """Pre-load model to eliminate cold start latency."""
    if is_model_ready():
        return True
    print("[Embed] Warming up model...", file=sys.stderr, flush=True)
    return wait_for_model(timeout=60.0)


def get_embedder_type() -> str:
    """Return the current embedder type ('onnx' or 'pytorch')."""
    return _embedder_type or 'unknown'


def get_cache_stats() -> dict:
    """Get cache statistics."""
    cache_info = _embed_single_cached.cache_info()
    return {
        'hits': _cache_hits,
        'misses': _cache_misses,
        'disk_hits': _disk_hits,
        'lru_hits': cache_info.hits,
        'lru_misses': cache_info.misses,
        'maxsize': cache_info.maxsize,
        'currsize': cache_info.currsize,
        'hit_rate': cache_info.hits / (cache_info.hits + cache_info.misses) * 100 
                    if (cache_info.hits + cache_info.misses) > 0 else 0,
        'embedder': _embedder_type,
        'model_ready': is_model_ready(),
        'memory': get_memory_usage()
    }


def clear_cache() -> None:
    """Clear the embedding cache."""
    _embed_single_cached.cache_clear()
    global _cache_hits, _cache_misses, _disk_hits
    _cache_hits = 0
    _cache_misses = 0
    _disk_hits = 0


if __name__ == "__main__":
    print("Testing embedding with auto-detect...")
    print(f"AVX2 detected: {_has_avx2()}")
    
    test_text = "This is a test sentence for embedding."
    
    import time as time_mod
    start = time_mod.perf_counter()
    vector1 = embed(test_text)
    t1 = (time_mod.perf_counter() - start) * 1000
    print(f"\nFirst embed: {t1:.2f}ms")
    print(f"Embedder type: {_embedder_type}")
    
    start = time_mod.perf_counter()
    vector2 = embed(test_text)
    t2 = (time_mod.perf_counter() - start) * 1000
    print(f"Second embed: {t2:.2f}ms (cached)")
    print(f"Speedup: {t1/t2:.1f}x" if t2 > 0 else "N/A")
    print(f"Vectors match: {vector1 == vector2}")
    print(f"\nDimension: {len(vector1)}")
    print(f"Cache stats: {get_cache_stats()}")
