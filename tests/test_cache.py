import unittest
import os
import shutil
import time
import sys
import sqlite3
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import scripts.embed as embed_module

class TestMementoCache(unittest.TestCase):
    def setUp(self):
        # Point Memento to a temp directory for cache
        self.test_dir = os.path.expanduser("~/.memento_test")
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Monkey patch the cache DB path in the module for testing
        self.original_db_path = embed_module._disk_cache.db_path
        embed_module._disk_cache.db_path = os.path.join(self.test_dir, "cache.db")
        # Re-init db at new path
        embed_module._disk_cache._init_db()
        
        # Clear RAM cache
        embed_module._embed_single_cached.cache_clear()
        embed_module._cache_hits = 0
        embed_module._cache_misses = 0
        embed_module._disk_hits = 0

    def tearDown(self):
        # Restore original path
        embed_module._disk_cache.db_path = self.original_db_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cache_hierarchy(self):
        """Test RAM -> Disk -> Compute flow."""
        text = f"Unique cache test string {time.time()}"
        
        # 1. First run: Should be a MISS (Compute)
        embed_module.embed(text)
        self.assertEqual(embed_module._cache_misses, 1)
        self.assertEqual(embed_module._cache_hits, 0)
        self.assertEqual(embed_module._disk_hits, 0)

        # 2. Second run: Should be a HIT (RAM)
        embed_module.embed(text)
        self.assertEqual(embed_module._cache_misses, 1) # Unchanged
        self.assertEqual(embed_module._cache_hits, 1)   # +1
        self.assertEqual(embed_module._disk_hits, 0)

        # 3. Clear RAM, run again: Should be a DISK HIT
        embed_module._embed_single_cached.cache_clear()
        embed_module.embed(text)
        self.assertEqual(embed_module._cache_misses, 1) # Unchanged
        # Hits metric logic in embed.py compares cache info, which reset. 
        # But _disk_hits should definitely increment.
        self.assertEqual(embed_module._disk_hits, 1)

    def test_persistence(self):
        """Verify data actually exists in SQLite."""
        text = "Persistence verification"
        embed_module.embed(text)
        
        # Check SQLite directly
        conn = sqlite3.connect(embed_module._disk_cache.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM embeddings")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)

if __name__ == '__main__':
    unittest.main()
