# Memento Performance Benchmark

**Date:** 2026-02-17  
**Platform:** Linux 6.6.87 (WSL2), Python 3.12.3, x86_64  
**Hardware:** Laptop (Brett's dev machine)  
**Database:** SQLite + sqlite-vec, WAL mode

## Embedding Performance

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Cold start (model load + first embed) | 4,411ms | <30,000ms | ✅ PASS |
| Warm embed (LRU cache hit) | 0.006ms | <10ms | ✅ PASS |
| Uncached single embed (model warm) | 11.2ms | <100ms | ✅ PASS |
| Batch embed (20 items) | 4,456ms (223ms/item) | — | ⚠️ See note |
| Cache speedup | 255x | >10x | ✅ PASS |
| Embedder type | ONNX (single), PyTorch fallback (batch) | — | ⚠️ |

> **Note:** ONNX batch embedding fails with shape mismatch (#38), falling back to PyTorch.
> Single-item ONNX is fast (~5ms), but batch triggers PyTorch reload (~4.4s total for 20 items).

## Store Performance

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Remember (single) | 20.4ms median | <50ms | ✅ PASS |
| Recall (5 results, seeded DB) | 5.3ms median | <50ms | ✅ PASS |
| Recall p95 | 6.5ms | <100ms | ✅ PASS |
| Recall at 10 memories | 0.6ms | — | ✅ |
| Recall at 50 memories | 1.0ms | — | ✅ |
| Recall at 100 memories | 0.5ms | — | ✅ |

## Stress Test Results

| Test | Result | Duration |
|------|--------|----------|
| 100 memories insert | ✅ PASS | ~5s |
| 500 memories insert | ✅ PASS | ~12s |
| 1000 memories insert | ✅ PASS | ~24s |
| 4-thread concurrent write (25 each) | ✅ PASS | ~8s |
| Mixed read/write (2w + 3r) | ❌ FAIL (#36) | Thread timeout crash |
| Search accuracy at 200 | ⚠️ Partial | 4/5 topics found |
| Create/delete cycles | ✅ PASS | — |
| GC pressure | ✅ PASS | — |

## Memory Usage

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| ONNX model estimated | 85MB | <200MB | ✅ PASS |
| Process RSS (both models loaded) | 1,316MB | <500MB | ❌ FAIL (#38) |
| Memory growth (50 ops) | 1,232KB | <10MB | ✅ PASS |

> **Note:** RSS is high because ONNX batch failure loads PyTorch as fallback
> without unloading ONNX. With only ONNX loaded: ~300MB estimated.

## Database Size

| Memories | DB Size | Per Memory |
|----------|---------|------------|
| 10 | 4KB | ~400B |
| 50 | 1.7MB | ~34KB |
| 100 | 1.7MB | ~19KB |

> DB size jumps at ~50 memories due to sqlite-vec page allocation.
> Per-memory cost decreases as DB grows (amortized overhead).

## Cache Performance

| Metric | Value |
|--------|-------|
| LRU cache max size | 1,000 entries |
| LRU hit rate | 20% (test run) |
| Disk cache persistence | ✅ Working |
| Cache bypass (use_cache=False) | ✅ Working |

## Known Issues Affecting Performance

1. **#36 (P0):** `recall()` crashes in non-main threads (SIGALRM)
2. **#38 (P1):** ONNX batch fails → PyTorch fallback → 1.3GB RSS
3. **#37 (P1):** `unload_model()` crashes (can't free memory)

## Test Summary

| Suite | Tests | Passed | Failed |
|-------|-------|--------|--------|
| test_models.py | 10 | 10 | 0 |
| test_edge_cases.py | 60 | 58 | 2 |
| test_performance.py | 13 | 12 | 1 |
| test_stress.py | 8 | 6 | 2 |
| **Total** | **91** | **86** | **5** |

All 5 failures are real bugs (not test issues):
- 3x SIGALRM in threads (#36)
- 1x UnboundLocalError in unload_model (#37)
- 1x Search accuracy at scale (vector quality / k-limit interaction)

## Recommendations

1. **Fix #36 first** — thread-safe timeout is critical for any real-world deployment
2. **Fix #38** — ONNX batch or cleanup prevents 1.3GB memory waste
3. **Fix #37** — unload_model needs `global _idle_timer` declaration
4. **Increase k multiplier** — when filtering, request k*3 from vec table to compensate for filter loss
5. **Target Pi Zero:** Memory must drop to <300MB (fix #38 gets there)
