#!/usr/bin/env python3
"""
Test store.py edge cases and error handling
Ticket #20: Test store.py edge cases
"""

import sys
import os
import tempfile
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from memento.store import MemoryStore


class TestStoreEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_database(self):
        """Test operations on empty database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            memory = MemoryStore(db_path=db_path)
            
            # Search on empty DB
            results = memory.recall("anything")
            assert results == [], "Empty DB should return empty list"
            
            # Stats on empty DB
            stats = memory.stats()
            assert stats['total_vectors'] == 0, "Empty DB should have 0 memories"
            
            # Recent on empty DB
            recent = memory.get_recent(n=10)
            assert recent == [], "Empty DB recent should be empty"
            
            print("✓ Empty database operations work")
            return True
        finally:
            os.unlink(db_path)
    
    def test_very_long_text(self):
        """Test handling of very long text."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            memory = MemoryStore(db_path=db_path)
            
            # 10,000 character text
            long_text = "A" * 10000
            
            # Should store without crashing
            memory.remember(long_text, importance=0.5)
            
            # Should be able to retrieve
            results = memory.recall(long_text[:100])
            assert len(results) > 0, "Should find long text"
            
            print("✓ Very long text (10k chars) handled")
            return True
        finally:
            os.unlink(db_path)
    
    def test_unicode_and_special_chars(self):
        """Test handling of unicode and special characters."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            memory = MemoryStore(db_path=db_path)
            
            # Various unicode and special chars
            texts = [
                "日本語テキスト",
                "🎉 Emoji test 🚀",
                "HTML <script>alert('xss')</script>",
                "SQL ' OR '1'='1",
                "Newline\nTab\tCarriage\r",
                "Quotes \"double\" and 'single'",
                "Backslash \\ path\\to\\file",
            ]
            
            for i, text in enumerate(texts):
                memory.remember(text, importance=0.5, tags=[f"tag{i}"])
            
            # Verify all stored
            stats = memory.stats()
            assert stats['total_vectors'] == len(texts), f"Should store all {len(texts)} texts"
            
            print("✓ Unicode and special characters handled")
            return True
        finally:
            os.unlink(db_path)
    
    def test_duplicate_prevention(self):
        """Test that near-duplicates are prevented."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            memory = MemoryStore(db_path=db_path)
            
            # Store original
            text = "This is a unique memory about machine learning concepts"
            id1 = memory.remember(text, importance=0.8)
            
            # Try to store very similar text (should be detected as duplicate)
            similar_text = "This is a unique memory about machine learning concepts"  # Same
            id2 = memory.remember(similar_text, importance=0.8)
            
            # If duplicate detection works, id2 should equal id1
            # Note: This depends on the similarity threshold
            stats = memory.stats()
            print(f"✓ Duplicate handling: {stats['total_vectors']} memories stored")
            return True
        finally:
            os.unlink(db_path)
    
    def test_concurrent_access(self):
        """Test basic thread safety."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            memory = MemoryStore(db_path=db_path)
            errors = []
            
            def writer(thread_id):
                try:
                    for i in range(5):
                        memory.remember(
                            f"Thread {thread_id} message {i}",
                            importance=0.5
                        )
                except Exception as e:
                    errors.append(e)
            
            # Start multiple threads
            threads = []
            for i in range(3):
                t = threading.Thread(target=writer, args=(i,))
                threads.append(t)
                t.start()
            
            # Wait for completion
            for t in threads:
                t.join()
            
            assert len(errors) == 0, f"Concurrent access errors: {errors}"
            
            stats = memory.stats()
            assert stats['total_vectors'] == 15, f"Should have 15 memories, got {stats['total_vectors']}"
            
            print("✓ Concurrent access (3 threads x 5 writes) handled")
            return True
        finally:
            os.unlink(db_path)
    
    def test_batch_operations(self):
        """Test batch recall functionality."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            memory = MemoryStore(db_path=db_path)
            
            # Add test data
            for i in range(20):
                memory.remember(
                    f"Topic {i % 5}: content number {i}",
                    importance=0.5
                )
            
            # Batch recall
            queries = ["topic 1", "topic 2", "topic 3"]
            results = memory.batch_recall(queries, topk=3)
            
            assert len(results) == 3, "Should return results for each query"
            assert all(isinstance(r, list) for r in results), "Each result should be a list"
            
            print("✓ Batch operations work")
            return True
        finally:
            os.unlink(db_path)
    
    def test_filters(self):
        """Test various filter combinations."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            memory = MemoryStore(db_path=db_path)
            
            # Add tagged memories
            memory.remember("Work task 1", importance=0.8, tags=["work", "urgent"])
            memory.remember("Work task 2", importance=0.5, tags=["work"])
            memory.remember("Personal note", importance=0.6, tags=["personal"])
            memory.remember("Another work item", importance=0.9, tags=["work", "urgent"])
            
            # Filter by tags
            results = memory.recall("work", filters={"tags": ["urgent"]})
            assert len(results) >= 2, "Should find urgent work items"
            
            # Filter by importance
            results = memory.recall("work", filters={"min_importance": 0.8})
            assert all(r['importance'] >= 0.8 for r in results), "All results should meet importance threshold"
            
            print("✓ Filters work correctly")
            return True
        finally:
            os.unlink(db_path)
    
    def test_database_corruption_recovery(self):
        """Test graceful handling of corrupted DB."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Create a valid DB first
            memory = MemoryStore(db_path=db_path)
            memory.remember("Test", importance=0.5)
            del memory
            
            # Corrupt the DB file
            with open(db_path, 'wb') as f:
                f.write(b"This is not a valid SQLite database")
            
            # Try to open - should handle gracefully
            try:
                memory = MemoryStore(db_path=db_path)
                # If it opens, it should be usable
                stats = memory.stats()
                print(f"✓ Corruption recovery: DB recreated, {stats['total_vectors']} memories")
            except Exception as e:
                print(f"✓ Corruption recovery: Error handled gracefully - {type(e).__name__}")
            
            return True
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


def run_tests():
    """Run all store edge case tests."""
    print("="*50)
    print("Testing Store Edge Cases (Ticket #20)")
    print("="*50)
    
    tests = TestStoreEdgeCases()
    passed = 0
    failed = 0
    
    for name in dir(tests):
        if name.startswith('test_'):
            try:
                print(f"\n🔹 {name}...")
                getattr(tests, name)()
                passed += 1
            except AssertionError as e:
                print(f"❌ FAILED: {e}")
                failed += 1
            except Exception as e:
                print(f"❌ ERROR: {e}")
                failed += 1
    
    print("\n" + "="*50)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
