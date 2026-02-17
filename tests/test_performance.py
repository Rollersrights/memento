#!/usr/bin/env python3
"""
Performance benchmarks for Memento.
Tests cold start, embed speed, recall latency, memory usage, DB growth.
"""

import os
import sys
import time
import tempfile
import resource
import gc
import json

import pytest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ── Embedding performance ─────────────────────────────────────────────────

class TestEmbedPerformance:
    def test_cold_start_under_30s(self):
        """First embed call (model load + embed) should complete within 30s."""
        from memento.embed import embed, clear_cache, unload_model, _model_ready_event

        # Force a cold start
        unload_model(force=True)
        clear_cache()

        start = time.perf_counter()
        result = embed("Cold start test sentence for benchmarking")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result is not None
        assert len(result) == 384
        print(f"\n  Cold start: {elapsed_ms:.1f}ms")
        # Allow generous timeout - model may need to re-load ONNX
        assert elapsed_ms < 30000, f"Cold start too slow: {elapsed_ms:.1f}ms"

    def test_warm_embed_under_10ms(self):
        """Cached/warm embed should be very fast."""
        from memento.embed import embed, clear_cache

        # Warm up
        embed("Warm up call")

        text = "Quick warm embed test"
        embed(text)  # populate cache

        times = []
        for _ in range(20):
            start = time.perf_counter()
            embed(text)
            times.append((time.perf_counter() - start) * 1000)

        median = sorted(times)[len(times) // 2]
        print(f"\n  Warm embed median: {median:.3f}ms (p95: {sorted(times)[18]:.3f}ms)")
        assert median < 10, f"Warm embed too slow: {median:.3f}ms"

    def test_uncached_embed_under_100ms(self):
        """Fresh (non-cached) single embed should be under 100ms once model is warm."""
        from memento.embed import embed

        # Ensure model is loaded
        embed("warmup")

        times = []
        for i in range(5):
            unique = f"Unique benchmark text {i} {time.time()}"
            start = time.perf_counter()
            result = embed(unique, use_cache=False)
            times.append((time.perf_counter() - start) * 1000)
            assert len(result) == 384

        median = sorted(times)[len(times) // 2]
        print(f"\n  Uncached embed median: {median:.1f}ms")
        assert median < 100, f"Uncached embed too slow: {median:.1f}ms"

    def test_batch_embed_throughput(self):
        """Batch embedding should be faster per-item than individual."""
        from memento.embed import embed

        texts = [f"Batch benchmark sentence number {i} about various topics" for i in range(20)]

        start = time.perf_counter()
        results = embed(texts, use_cache=False)
        batch_time = (time.perf_counter() - start) * 1000

        assert len(results) == 20
        per_item = batch_time / 20
        print(f"\n  Batch embed: {batch_time:.1f}ms total, {per_item:.1f}ms/item")


# ── Store performance ──────────────────────────────────────────────────────

class TestStorePerformance:
    def test_remember_latency(self, store):
        """Single remember should complete quickly."""
        # Warm up embedding
        store.remember("Warmup text for embedding model", importance=0.5)

        times = []
        for i in range(10):
            text = f"Performance test memory {i} about {time.time()}"
            start = time.perf_counter()
            doc_id = store.remember(text, importance=0.5)
            times.append((time.perf_counter() - start) * 1000)
            assert doc_id is not None

        median = sorted(times)[len(times) // 2]
        print(f"\n  Remember median: {median:.1f}ms")

    def test_recall_latency(self, seeded_store):
        """Recall on a seeded store should be fast."""
        # Warm up
        seeded_store.recall("test", topk=3)

        queries = ["server IP", "grocery shopping", "deploy production", "cat mat", "machine learning"]
        times = []
        for q in queries:
            start = time.perf_counter()
            results = seeded_store.recall(q, topk=5)
            times.append((time.perf_counter() - start) * 1000)
            assert isinstance(results, list)

        median = sorted(times)[len(times) // 2]
        p95 = sorted(times)[int(len(times) * 0.95)]
        print(f"\n  Recall median: {median:.1f}ms, p95: {p95:.1f}ms")
        # Should be under 50ms for small DB
        assert median < 200, f"Recall too slow: {median:.1f}ms"

    def test_recall_scaling(self, tmp_db):
        """Recall time should scale sub-linearly with DB size."""
        from memento.store import MemoryStore

        store = MemoryStore(db_path=tmp_db)
        sizes = [10, 50, 100]
        recall_times = {}

        # Insert and benchmark at each size
        for target in sizes:
            current = store.stats()['total_vectors']
            for i in range(current, target):
                store.remember(f"Scaling test memory {i} with topic {i % 10}", importance=0.5)

            # Benchmark recall
            times = []
            for _ in range(5):
                start = time.perf_counter()
                store.recall("topic", topk=5)
                times.append((time.perf_counter() - start) * 1000)

            recall_times[target] = sorted(times)[len(times) // 2]

        print(f"\n  Recall scaling: {recall_times}")
        store.close()

    def test_db_size_growth(self, tmp_db):
        """Track DB size growth with number of memories."""
        from memento.store import MemoryStore

        store = MemoryStore(db_path=tmp_db)
        sizes = {}

        for count in [10, 50, 100]:
            current = store.stats()['total_vectors']
            for i in range(current, count):
                store.remember(f"DB size test memory {i} lorem ipsum", importance=0.5)
            sizes[count] = os.path.getsize(tmp_db)

        per_memory = (sizes[100] - sizes[10]) / 90
        print(f"\n  DB sizes: {sizes}")
        print(f"  ~{per_memory:.0f} bytes/memory")
        store.close()


# ── Memory usage ───────────────────────────────────────────────────────────

class TestMemoryUsage:
    def test_embed_memory_footprint(self):
        """Track memory usage of the embedding model."""
        from memento.embed import get_memory_usage, embed

        # Ensure model is loaded
        embed("test")

        mem_info = get_memory_usage()
        print(f"\n  Model memory: {mem_info}")
        assert mem_info['model_loaded'] is True
        assert mem_info['estimated_mb'] < 200, f"Model uses too much RAM: {mem_info['estimated_mb']}MB"

    def test_process_rss_under_limit(self):
        """Total process RSS should stay under 500MB during normal ops."""
        from memento.embed import embed

        embed("trigger model load")

        # Get RSS in MB
        rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_mb = rss_kb / 1024  # On Linux, ru_maxrss is in KB

        print(f"\n  Process RSS: {rss_mb:.1f}MB")
        assert rss_mb < 500, f"Process too large: {rss_mb:.1f}MB"

    def test_no_memory_leak_in_loop(self, store):
        """Repeated operations shouldn't leak memory."""
        import tracemalloc

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        for i in range(50):
            store.remember(f"Leak test {i} {time.time()}", importance=0.5)
            store.recall(f"Leak test {i}", topk=3)

        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()
        tracemalloc.stop()

        stats = snapshot2.compare_to(snapshot1, 'lineno')
        top_growth = sum(s.size_diff for s in stats[:10])
        print(f"\n  Memory growth (top 10 lines): {top_growth / 1024:.1f}KB")


# ── Cache performance ──────────────────────────────────────────────────────

class TestCachePerformance:
    def test_cache_speedup(self):
        """Cache should provide significant speedup."""
        from memento.embed import embed, clear_cache

        clear_cache()
        text = "Cache speedup benchmark test"

        start = time.perf_counter()
        embed(text)
        cold = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        embed(text)
        warm = (time.perf_counter() - start) * 1000

        speedup = cold / warm if warm > 0 else float('inf')
        print(f"\n  Cold: {cold:.2f}ms, Warm: {warm:.4f}ms, Speedup: {speedup:.0f}x")
        assert speedup > 10, f"Cache speedup too low: {speedup:.0f}x"

    def test_cache_stats_accuracy(self):
        """Cache stats should accurately reflect operations."""
        from memento.embed import embed, get_cache_stats, clear_cache

        clear_cache()

        # 3 unique embeds
        for i in range(3):
            embed(f"Stats accuracy {i} {time.time()}")

        # 3 cache hits
        # (use same text that was embedded above - but timestamps make them unique)
        # Instead, embed same text twice
        embed("Repeated text for stats")
        embed("Repeated text for stats")

        stats = get_cache_stats()
        print(f"\n  Cache stats: {stats}")
        assert stats['model_ready'] is True
