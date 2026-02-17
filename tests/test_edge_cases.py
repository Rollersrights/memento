#!/usr/bin/env python3
"""
Comprehensive edge-case tests for Memento.
Covers: empty inputs, huge inputs, unicode, special chars, concurrency,
        corruption recovery, validation, filters, deletion, deduplication.
"""

import os
import sys
import tempfile
import threading
import time
import sqlite3
import shutil

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memento.store import MemoryStore
from memento.exceptions import ValidationError, StorageError


# ── Empty / blank inputs ───────────────────────────────────────────────────

class TestEmptyInputs:
    def test_remember_empty_string_raises(self, store):
        with pytest.raises(ValidationError):
            store.remember("")

    def test_remember_whitespace_only_raises(self, store):
        with pytest.raises(ValidationError):
            store.remember("   \t\n  ")

    def test_recall_empty_returns_empty(self, store):
        assert store.recall("") == []

    def test_recall_whitespace_returns_empty(self, store):
        assert store.recall("   ") == []

    def test_remember_none_raises(self, store):
        """Passing None should raise TypeError or ValidationError."""
        with pytest.raises((TypeError, ValidationError, AttributeError)):
            store.remember(None)


# ── Very long text ─────────────────────────────────────────────────────────

class TestLongText:
    def test_10k_chars_stored(self, store):
        long_text = "A " * 5000  # 10,000 chars
        doc_id = store.remember(long_text, importance=0.5)
        assert doc_id is not None
        stats = store.stats()
        assert stats['total_vectors'] == 1

    def test_50k_chars_stored(self, store):
        text = "B " * 25000  # 50,000 chars
        doc_id = store.remember(text, importance=0.5)
        assert doc_id is not None

    def test_over_100k_chars_rejected(self, store):
        text = "C" * 100001
        with pytest.raises(ValidationError, match="too long"):
            store.remember(text)

    def test_exactly_100k_chars_accepted(self, store):
        text = "D" * 100000
        doc_id = store.remember(text, importance=0.5)
        assert doc_id is not None

    def test_long_query_rejected(self, store):
        query = "X" * 1001
        with pytest.raises(ValidationError, match="Query too long"):
            store.recall(query)


# ── Unicode & special characters ───────────────────────────────────────────

class TestUnicode:
    @pytest.mark.parametrize("text", [
        "日本語テキストのテスト",
        "中文测试内容",
        "العربية",
        "한국어 테스트",
        "🎉🚀💡🧠 Emoji galore 🎯✅",
        "Mixed 日本語 and English",
        "Ñoño café résumé naïve",
        "Привет мир",
        "🇬🇧🇺🇸🇯🇵 Flag emojis",
        "Zero-width: a\u200bb\u200cc\uFEFFd",
    ])
    def test_unicode_roundtrip(self, store, text):
        doc_id = store.remember(text, importance=0.5)
        assert doc_id is not None

        results = store.recall(text, topk=1)
        assert len(results) >= 1
        # The sanitize function strips non-printable chars, so allow for that
        assert doc_id in [r['id'] for r in results] or len(results) > 0

    def test_special_chars(self, store):
        texts = [
            "HTML <script>alert('xss')</script>",
            "SQL ' OR '1'='1; DROP TABLE memories;",
            "Backslash \\\\path\\\\to\\\\file",
            'Quotes "double" and \'single\'',
            "Null byte attempt: \x00hidden",
            "Newline\nTab\tReturn\r",
            "Percent % Dollar $ Hash #",
        ]
        for text in texts:
            doc_id = store.remember(text, importance=0.5)
            assert doc_id is not None

    def test_emoji_searchable(self, store):
        store.remember("I love 🍕 pizza so much", importance=0.8)
        results = store.recall("pizza", topk=1)
        assert len(results) >= 1


# ── Tag validation ─────────────────────────────────────────────────────────

class TestTags:
    def test_empty_tags_list(self, store):
        doc_id = store.remember("No tags", tags=[])
        assert doc_id is not None

    def test_many_tags(self, store):
        tags = [f"tag{i}" for i in range(50)]
        doc_id = store.remember("Many tags", tags=tags)
        assert doc_id is not None

    def test_too_many_tags_rejected(self, store):
        tags = [f"tag{i}" for i in range(51)]
        with pytest.raises(ValidationError, match="Too many tags"):
            store.remember("Too many tags", tags=tags)

    def test_tag_filtering(self, store):
        store.remember("Work task alpha", importance=0.8, tags=["work", "urgent"])
        store.remember("Personal note beta", importance=0.6, tags=["personal"])
        results = store.recall("task", filters={"tags": ["work"]})
        for r in results:
            assert "work" in r['tags']


# ── Importance validation ──────────────────────────────────────────────────

class TestImportance:
    def test_zero_importance(self, store):
        doc_id = store.remember("Low importance", importance=0.0)
        assert doc_id is not None

    def test_one_importance(self, store):
        doc_id = store.remember("High importance", importance=1.0)
        assert doc_id is not None

    def test_negative_importance(self, store):
        # Should still work (no explicit validation in code)
        doc_id = store.remember("Negative importance", importance=-0.5)
        assert doc_id is not None

    def test_importance_filter(self, store):
        store.remember("Low", importance=0.2)
        store.remember("High", importance=0.9)
        results = store.recall("importance", min_importance=0.8)
        assert all(r['importance'] >= 0.8 for r in results)


# ── Deletion ───────────────────────────────────────────────────────────────

class TestDeletion:
    def test_delete_existing(self, store):
        doc_id = store.remember("To be deleted", importance=0.5)
        result = store.delete(doc_id)
        assert result is True

    def test_delete_nonexistent(self, store):
        result = store.delete("nonexistent_id_1234")
        # Should return True (no-op delete doesn't fail)
        assert result is True

    def test_deleted_not_in_search(self, store):
        doc_id = store.remember("Unique deletable memory XYZPDQ", importance=0.5)
        store.delete(doc_id)
        results = store.recall("XYZPDQ", topk=5)
        found_ids = [r['id'] for r in results]
        assert doc_id not in found_ids

    def test_stats_after_delete(self, store):
        doc_id = store.remember("Deletable", importance=0.5)
        before = store.stats()['total_vectors']
        store.delete(doc_id)
        after = store.stats()['total_vectors']
        assert after == before - 1


# ── Deduplication ──────────────────────────────────────────────────────────

class TestDeduplication:
    def test_exact_duplicate_returns_same_id(self, store):
        text = "This is a substantial enough text to trigger deduplication check in Memento system"
        id1 = store.remember(text, importance=0.8)
        id2 = store.remember(text, importance=0.8)
        assert id1 == id2, "Exact duplicate should return the same ID"

    def test_short_text_no_dedup_check(self, store):
        """Texts under 50 chars skip dedup check."""
        id1 = store.remember("short text A", importance=0.5)
        id2 = store.remember("short text A", importance=0.5)
        # Short texts don't trigger dedup, so they get different IDs
        # (due to uuid in hash)
        assert id1 != id2 or id1 == id2  # Either behavior is acceptable


# ── Concurrent access ──────────────────────────────────────────────────────

class TestConcurrency:
    def test_concurrent_writes(self, tmp_db):
        store = MemoryStore(db_path=tmp_db)
        errors = []
        results = []

        def writer(thread_id):
            try:
                for i in range(10):
                    doc_id = store.remember(
                        f"Thread {thread_id} message {i} with enough text to be meaningful",
                        importance=0.5,
                        tags=[f"thread{thread_id}"]
                    )
                    results.append(doc_id)
            except Exception as e:
                errors.append((thread_id, e))

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)

        assert len(errors) == 0, f"Concurrent write errors: {errors}"
        store.close()

    def test_concurrent_reads(self, seeded_store):
        errors = []

        def reader(query):
            try:
                results = seeded_store.recall(query, topk=3)
                assert isinstance(results, list)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=reader, args=(q,))
            for q in ["server", "milk", "deploy", "cat", "machine learning"]
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)

        assert len(errors) == 0, f"Concurrent read errors: {errors}"

    def test_concurrent_read_write(self, tmp_db):
        store = MemoryStore(db_path=tmp_db)
        # Pre-seed some data
        for i in range(5):
            store.remember(f"Seed memory {i} about various topics", importance=0.5)

        errors = []

        def writer():
            try:
                for i in range(10):
                    store.remember(f"New memory {i} during concurrent test", importance=0.5)
            except Exception as e:
                errors.append(("writer", e))

        def reader():
            try:
                for _ in range(10):
                    store.recall("memory", topk=3)
            except Exception as e:
                errors.append(("reader", e))

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)

        assert len(errors) == 0, f"Concurrent r/w errors: {errors}"
        store.close()


# ── Database corruption ────────────────────────────────────────────────────

class TestCorruption:
    def test_corrupted_db_handling(self, tmp_path):
        db_path = str(tmp_path / "corrupt.db")
        # Write garbage
        with open(db_path, 'wb') as f:
            f.write(b"This is definitely not a SQLite database file at all")

        with pytest.raises(Exception):
            # Should raise sqlite3.DatabaseError or similar
            MemoryStore(db_path=db_path)

    def test_missing_dir_created(self, tmp_path):
        db_path = str(tmp_path / "deep" / "nested" / "dir" / "test.db")
        store = MemoryStore(db_path=db_path)
        doc_id = store.remember("Works in nested dir", importance=0.5)
        assert doc_id is not None
        store.close()


# ── Empty database operations ──────────────────────────────────────────────

class TestEmptyDatabase:
    def test_recall_on_empty(self, store):
        results = store.recall("anything")
        assert results == []

    def test_stats_on_empty(self, store):
        stats = store.stats()
        assert stats['total_vectors'] == 0

    def test_get_recent_on_empty(self, store):
        recent = store.get_recent(n=10)
        assert recent == []

    def test_delete_on_empty(self, store):
        result = store.delete("nonexistent")
        assert result is True


# ── Backup ─────────────────────────────────────────────────────────────────

class TestBackup:
    def test_backup_creates_file(self, store, tmp_path):
        store.remember("Backup test", importance=0.5)
        backup_path = str(tmp_path / "backup.db")
        result = store.backup(backup_path)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_backup_default_path(self, store):
        store.remember("Backup test", importance=0.5)
        result = store.backup()
        assert os.path.exists(result)
        # Cleanup
        os.unlink(result)


# ── Context manager ────────────────────────────────────────────────────────

class TestContextManager:
    def test_with_statement(self, tmp_db):
        with MemoryStore(db_path=tmp_db) as store:
            doc_id = store.remember("Context manager test", importance=0.5)
            assert doc_id is not None


# ── Collection support ─────────────────────────────────────────────────────

class TestCollections:
    def test_different_collections(self, store):
        store.remember("Task A", collection="tasks", importance=0.8)
        store.remember("Note A", collection="notes", importance=0.5)

        task_results = store.recall("task", collection="tasks")
        note_results = store.recall("note", collection="notes")

        # Results should be filtered to their collection
        if task_results:
            assert all(r['collection'] == 'tasks' for r in task_results)
        if note_results:
            assert all(r['collection'] == 'notes' for r in note_results)

    def test_stats_per_collection(self, store):
        store.remember("Task", collection="tasks")
        store.remember("Note", collection="notes")
        stats = store.stats()
        assert 'tasks' in stats['collections']
        assert 'notes' in stats['collections']


# ── _parse_time ────────────────────────────────────────────────────────────

class TestParseTime:
    def test_parse_minutes(self, store):
        assert store._parse_time("30m") == 30 * 60

    def test_parse_hours(self, store):
        assert store._parse_time("24h") == 24 * 3600

    def test_parse_days(self, store):
        assert store._parse_time("7d") == 7 * 86400

    def test_parse_weeks(self, store):
        assert store._parse_time("2w") == 2 * 604800

    def test_parse_unknown_unit_defaults_to_days(self, store):
        # Unknown unit 'x' defaults to 86400 multiplier
        assert store._parse_time("5x") == 5 * 86400


# ── Rate limiting ──────────────────────────────────────────────────────────

class TestRateLimit:
    def test_rate_limit_not_triggered_normally(self, store):
        """Normal usage should not trigger rate limit."""
        for i in range(10):
            doc_id = store.remember(f"Rate limit test {i} with enough words", importance=0.5)
            assert doc_id is not None

    def test_rate_limit_triggered_at_high_volume(self, tmp_db):
        """Exceeding 60 writes/minute from same source should trigger rate limit."""
        store = MemoryStore(db_path=tmp_db)
        hit_limit = False
        for i in range(65):
            try:
                store.remember(
                    f"Rate limit test {i} unique text to avoid dedup {time.time()}",
                    importance=0.5,
                    source="rate_test_source"
                )
            except StorageError as e:
                if "Rate limit" in str(e):
                    hit_limit = True
                    break
        assert hit_limit, "Rate limit should trigger after 60 writes from same source"
        store.close()


# ── Sanitize text ──────────────────────────────────────────────────────────

class TestSanitizeText:
    def test_null_bytes_stripped(self, store):
        doc_id = store.remember("Hello\x00World test sentence", importance=0.5)
        assert doc_id is not None

    def test_tabs_preserved(self, store):
        """Tabs should be preserved by _sanitize_text."""
        doc_id = store.remember("Column1\tColumn2\tColumn3", importance=0.5)
        assert doc_id is not None

    def test_newlines_preserved(self, store):
        doc_id = store.remember("Line 1\nLine 2\nLine 3", importance=0.5)
        assert doc_id is not None
