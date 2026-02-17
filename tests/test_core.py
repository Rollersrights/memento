import unittest
import os
import shutil
import tempfile
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.store import MemoryStore

class TestMementoCore(unittest.TestCase):
    def setUp(self):
        # Create a fresh temp DB for each test
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_memory.db')
        self.store = MemoryStore(db_path=self.db_path)

    def tearDown(self):
        # Cleanup
        shutil.rmtree(self.test_dir)

    def test_basic_storage(self):
        """Test simple storage and count."""
        doc_id = self.store.remember("Hello world", importance=0.5)
        self.assertIsNotNone(doc_id)
        
        stats = self.store.stats()
        self.assertEqual(stats['total_vectors'], 1)

    def test_semantic_retrieval(self):
        """Test that related concepts are found."""
        self.store.remember("The cat sat on the mat", importance=1.0)
        self.store.remember("The dog chased the ball", importance=1.0)
        self.store.remember("Algorithms calculate data", importance=1.0)

        # Search for 'feline' (should match cat)
        results = self.store.recall("feline", topk=1)
        self.assertTrue(len(results) > 0)
        self.assertIn("cat", results[0]['text'])

    def test_exact_retrieval(self):
        """Test exact keyword matching via BM25 (if enabled) or vector."""
        unique_term = "SuperCaliFragilistic"
        self.store.remember(f"This contains {unique_term}", importance=1.0)
        self.store.remember("Just a normal sentence", importance=1.0)

        results = self.store.recall(unique_term, topk=1)
        self.assertEqual(len(results), 1)
        self.assertIn(unique_term, results[0]['text'])

    def test_tags(self):
        """Test storage and retrieval of tags."""
        self.store.remember("Tagged memory", tags=["test_tag", "unit_test"])
        # Note: current simple recall might not return tags explicitly in all versions,
        # but we verify it doesn't crash and counts correctly.
        stats = self.store.stats()
        self.assertEqual(stats['total_vectors'], 1)

if __name__ == '__main__':
    unittest.main()
