import unittest
import os
import shutil
import tempfile
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.store import MemoryStore

class TestMementoSearch(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_memory.db')
        self.store = MemoryStore(db_path=self.db_path)
        
        # Seed data
        self.store.remember("The IP address is 192.168.1.155", tags=["infra"])
        self.store.remember("The server is named bob", tags=["infra"])
        self.store.remember("Buy milk and eggs", tags=["shopping"])
        self.store.remember("Bob likes milk", tags=["personal"])

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

if __name__ == '__main__':
    unittest.main()
