#!/usr/bin/env python3
"""
Stress tests for Memento.
Tests high-volume insertion, concurrent load, and stability.
"""

import os
import sys
import time
import threading
import tempfile
import gc

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memento.store import MemoryStore


class TestHighVolumeInsertion:
    """Test inserting large numbers of memories."""

    @pytest.mark.slow
    def test_100_memories(self, tmp_db):
        """Insert 100 memories and verify integrity."""
        store = MemoryStore(db_path=tmp_db)
        ids = set()

        start = time.perf_counter()
        for i in range(100):
            doc_id = store.remember(
                f"Stress test memory {i}: This is about topic {i % 10} with detail {i}",
                importance=(i % 10) / 10.0,
                tags=[f"topic{i % 10}", "stress"],
                source=f"stress100_{i}"
            )
            ids.add(doc_id)
        elapsed = time.perf_counter() - start

        stats = store.stats()
        print(f"\n  100 memories: {elapsed:.2f}s ({elapsed/100*1000:.1f}ms/item)")
        print(f"  Unique IDs: {len(ids)}")
        print(f"  DB vectors: {stats['total_vectors']}")

        # Should have close to 100 (minus dedup)
        assert stats['total_vectors'] >= 90, f"Too few: {stats['total_vectors']}"
        store.close()

    @pytest.mark.slow
    def test_500_memories(self, tmp_db):
        """Insert 500 memories - target for typical agent usage."""
        store = MemoryStore(db_path=tmp_db)

        start = time.perf_counter()
        for i in range(500):
            store.remember(
                f"Memory {i}: {time.time()} topic-{i%20} detail-{i}",
                importance=0.5,
                tags=[f"group{i % 20}"],
                source=f"stress500_{i}"
            )
        elapsed = time.perf_counter() - start

        stats = store.stats()
        print(f"\n  500 memories: {elapsed:.1f}s ({elapsed/500*1000:.1f}ms/item)")
        assert stats['total_vectors'] >= 450

        # Search should still work
        results = store.recall("topic-5", topk=10)
        assert len(results) > 0
        store.close()

    @pytest.mark.slow
    def test_1000_memories(self, tmp_db):
        """Insert 1000 memories - stress test."""
        store = MemoryStore(db_path=tmp_db)

        start = time.perf_counter()
        for i in range(1000):
            store.remember(
                f"Large scale test {i}: {time.time()} area-{i%50}",
                importance=0.5,
                source=f"stress1k_{i}"
            )
            if i % 200 == 0 and i > 0:
                elapsed_so_far = time.perf_counter() - start
                rate = i / elapsed_so_far
                print(f"  {i} memories, {rate:.0f}/sec")

        elapsed = time.perf_counter() - start
        stats = store.stats()
        db_size = os.path.getsize(tmp_db) / 1024

        print(f"\n  1000 memories: {elapsed:.1f}s ({elapsed/1000*1000:.1f}ms/item)")
        print(f"  DB size: {db_size:.0f}KB")

        # Recall should still be fast
        start = time.perf_counter()
        results = store.recall("area-25", topk=10)
        recall_ms = (time.perf_counter() - start) * 1000
        print(f"  Recall from 1000: {recall_ms:.1f}ms, found {len(results)} results")

        assert recall_ms < 500, f"Recall too slow at 1000 memories: {recall_ms:.1f}ms"
        store.close()


class TestConcurrentStress:
    """Test concurrent access under load."""

    @pytest.mark.slow
    def test_4_writer_threads(self, tmp_db):
        """4 threads writing simultaneously."""
        store = MemoryStore(db_path=tmp_db)
        errors = []
        counts = [0] * 4

        def writer(tid):
            for i in range(25):
                try:
                    store.remember(
                        f"Thread-{tid} item-{i} ts-{time.time()}",
                        importance=0.5,
                        source=f"thread_{tid}_{i}"
                    )
                    counts[tid] += 1
                except Exception as e:
                    errors.append((tid, i, e))

        start = time.perf_counter()
        threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)
        elapsed = time.perf_counter() - start

        total = sum(counts)
        print(f"\n  4-thread write: {total} memories in {elapsed:.1f}s")
        print(f"  Per-thread: {counts}")
        if errors:
            print(f"  Errors: {len(errors)}")
            for tid, i, e in errors[:5]:
                print(f"    Thread-{tid} item-{i}: {e}")

        assert len(errors) == 0, f"{len(errors)} errors in concurrent write"
        store.close()

    @pytest.mark.slow
    def test_mixed_read_write_load(self, tmp_db):
        """2 writers + 3 readers simultaneously."""
        store = MemoryStore(db_path=tmp_db)
        # Pre-seed
        for i in range(20):
            store.remember(f"Seed data {i} about topic {i%5}", importance=0.5,
                           source=f"mixed_seed_{i}")

        errors = []
        write_count = [0]
        read_count = [0]

        def writer():
            for i in range(20):
                try:
                    store.remember(f"Live write {i} ts-{time.time()}", importance=0.5,
                                   source=f"mixed_w_{i}")
                    write_count[0] += 1
                except Exception as e:
                    errors.append(("write", e))

        def reader():
            queries = ["topic 0", "topic 1", "topic 2", "seed data", "live write"]
            for q in queries * 4:
                try:
                    store.recall(q, topk=3)
                    read_count[0] += 1
                except Exception as e:
                    errors.append(("read", e))

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]

        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)
        elapsed = time.perf_counter() - start

        print(f"\n  Mixed r/w: {write_count[0]} writes, {read_count[0]} reads in {elapsed:.1f}s")
        if errors:
            print(f"  Errors: {len(errors)}")

        assert len(errors) == 0, f"{len(errors)} errors in mixed load"
        store.close()


class TestSearchUnderLoad:
    """Test search quality and speed as DB grows."""

    @pytest.mark.slow
    def test_search_accuracy_at_scale(self, tmp_db):
        """Search should return relevant results even with 200+ memories."""
        store = MemoryStore(db_path=tmp_db)

        # Insert diverse topics
        topics = {
            "python": "Python programming language uses dynamic typing and indentation",
            "rust": "Rust programming ensures memory safety without garbage collection",
            "cooking": "Italian pasta recipes use fresh basil and olive oil",
            "travel": "Japan cherry blossom season is in April with beautiful sakura",
            "music": "Jazz music originated in New Orleans with improvisation",
        }

        for i in range(200):
            topic_key = list(topics.keys())[i % len(topics)]
            text = f"{topics[topic_key]} - variation {i}"
            store.remember(text, importance=0.5, tags=[topic_key], source=f"accuracy_{i}")

        # Search for each topic
        for topic_key, expected_content in topics.items():
            results = store.recall(expected_content[:30], topk=5)
            assert len(results) > 0, f"No results for '{topic_key}'"
            # At least one result should contain the topic keyword
            found_relevant = any(topic_key in r['text'].lower() for r in results)
            assert found_relevant, f"No relevant result for '{topic_key}'"

        print("\n  Search accuracy at 200 memories: all topics found")
        store.close()


class TestStability:
    """Test system stability over sustained usage."""

    @pytest.mark.slow
    def test_rapid_create_delete_cycle(self, tmp_db):
        """Rapid creation and deletion should not corrupt the DB."""
        store = MemoryStore(db_path=tmp_db)

        for cycle in range(10):
            ids = []
            for i in range(10):
                doc_id = store.remember(
                    f"Cycle {cycle} item {i} timestamp {time.time()}",
                    importance=0.5, source=f"cycle_{cycle}_{i}"
                )
                ids.append(doc_id)

            # Delete half
            for doc_id in ids[:5]:
                store.delete(doc_id)

        stats = store.stats()
        print(f"\n  After 10 create/delete cycles: {stats['total_vectors']} memories")
        assert stats['total_vectors'] > 0

        # Should still be searchable
        results = store.recall("cycle", topk=5)
        assert len(results) > 0
        store.close()

    @pytest.mark.slow
    def test_gc_pressure(self, tmp_db):
        """Test under GC pressure."""
        store = MemoryStore(db_path=tmp_db)

        for i in range(50):
            store.remember(f"GC pressure test {i} {time.time()}", importance=0.5,
                           source=f"gc_{i}")
            if i % 10 == 0:
                gc.collect()

        gc.collect()
        results = store.recall("GC pressure", topk=5)
        assert len(results) > 0
        store.close()
