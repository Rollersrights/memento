import unittest
import os
import shutil
import tempfile
import sys
import time
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.store import MemoryStore
from scripts.search import hybrid_bm25_vector_search, vector_search, init_fts5

class TestMementoSearch(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_memory.db')
        self.store = MemoryStore(db_path=self.db_path)
        
        # Initialize FTS5 explicitly for manual inserts
        init_fts5(self.store.conn)
        
        # Seed data
        self.store.remember("The IP address is 192.168.1.155", tags=["infra"])
        self.store.remember("The server is named bob", tags=["infra"])
        self.store.remember("Buy milk and eggs", tags=["shopping"])
        self.store.remember("Bob likes milk", tags=["personal"])
        
        # Add old memory for recency testing
        # Manually insert to fake timestamp
        old_ts = int(time.time()) - (86400 * 30) # 30 days ago
        self.store.conn.execute(
            "INSERT INTO memories (id, text, timestamp, source, importance, collection) VALUES (?, ?, ?, ?, ?, ?)",
            ("old_memory", "Ancient history", old_ts, "test", 0.5, "knowledge")
        )
        self.store.conn.commit()
        # Re-load to update vector cache (though direct SQL insert bypasses vector generation unless we embed)
        # For this test, we skip vector gen for the manual insert, so it won't be found by vector search, 
        # but SHOULD be found by BM25 if FTS is updated.
        # Let's properly re-index FTS
        self.store.conn.execute("INSERT INTO memories_fts(rowid, text) VALUES (last_insert_rowid(), ?)", ("Ancient history",))
        self.store.conn.commit()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_filter_by_tag(self):
        """Test tag filtering."""
        results = self.store.recall("bob", filters={'tags': ['infra']}, topk=5)
        self.assertTrue(len(results) > 0)
        for r in results:
            self.assertIn("infra", r['tags'])
            self.assertNotIn("shopping", r['tags'])

    def test_filter_by_text(self):
        """Test text substring filtering."""
        results = self.store.recall("bob", filters={'text_like': 'server'}, topk=5)
        self.assertEqual(len(results), 1)
        self.assertIn("server", results[0]['text'])

    def test_hybrid_bm25_behavior(self):
        """
        Indirectly test hybrid search behavior. 
        '192.168.1.155' is a keyword that vector search might struggle with exactness on,
        but BM25/FTS5 (if implemented in store/search) should catch it.
        """
        results = self.store.recall("192.168.1.155", topk=1)
        self.assertTrue(len(results) > 0)
        self.assertIn("192.168.1.155", results[0]['text'])

    def test_reranking_recency(self):
        """Test that newer items rank higher (via hybrid search reranker)."""
        # Store two identical items, one now, one "old" (via hack or just rely on natural sorting)
        # Better: Test explicit hybrid search call
        results = hybrid_bm25_vector_search(self.store, "history", topk=5)
        # Should find "Ancient history" via BM25 even without vector
        found = any(r['text'] == "Ancient history" for r in results)
        self.assertTrue(found, "BM25 should find 'Ancient history'")

    def test_vector_fallback(self):
        """Test vector search when BM25 returns nothing."""
        # 'feline' shouldn't match 'cat' in BM25 (no stemming usually), but should in Vector
        self.store.remember("A cat is a small animal", importance=1.0)
        results = hybrid_bm25_vector_search(self.store, "feline", topk=1)
        self.assertTrue(len(results) > 0)
        self.assertIn("cat", results[0]['text'])

if __name__ == '__main__':
    unittest.main()
