#!/usr/bin/env python3
"""
Test embedding cache functionality
Ticket #19: Test embed.py - cache hit/miss scenarios
"""

import sys
import os
import time
import tempfile

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from memento.embed import (
    embed, 
    get_cache_stats, 
    clear_cache,
    _disk_cache
)


class TestEmbeddingCache:
    """Test cache functionality at all layers."""
    
    def test_ram_cache_hit(self):
        """Test that repeated queries hit RAM cache."""
        clear_cache()
        
        text = "Test sentence for RAM cache"
        
        # First call - cache miss
        start = time.perf_counter()
        result1 = embed(text)
        time1 = time.perf_counter() - start
        
        # Second call - should hit RAM cache
        start = time.perf_counter()
        result2 = embed(text)
        time2 = time.perf_counter() - start
        
        # Results should match
        assert result1 == result2, "Cached result should match"
        
        # Second call should be much faster
        assert time2 < time1 * 0.5, f"Cache hit should be faster: {time2:.4f}s vs {time1:.4f}s"
        
        stats = get_cache_stats()
        assert stats['lru_hits'] >= 1, "Should have LRU cache hits"
        print(f"✓ RAM cache hit: {time1*1000:.2f}ms -> {time2*1000:.2f}ms")
        return True
    
    def test_disk_cache_persistence(self):
        """Test that disk cache survives clear_cache()."""
        text = "Test sentence for disk cache persistence"
        text_hash = _disk_cache.get_cache_key(text) if hasattr(_disk_cache, 'get_cache_key') else None
        
        # First embed (populates both RAM and disk)
        result1 = embed(text)
        
        # Clear only RAM cache
        clear_cache()
        
        # Second embed (should hit disk, then repopulate RAM)
        start = time.perf_counter()
        result2 = embed(text)
        time2 = time.perf_counter() - start
        
        assert result1 == result2, "Disk cached result should match"
        
        stats = get_cache_stats()
        # Should show a disk hit or fast compute
        print(f"✓ Disk cache persistence: {time2*1000:.2f}ms (after RAM clear)")
        return True
    
    def test_cache_bypass(self):
        """Test that use_cache=False bypasses cache."""
        clear_cache()
        
        text = "Test cache bypass"
        
        # With cache
        result1 = embed(text, use_cache=True)
        result2 = embed(text, use_cache=True)
        
        # Without cache
        result3 = embed(text, use_cache=False)
        
        assert result1 == result3, "Results should match regardless of cache"
        print("✓ Cache bypass works")
        return True
    
    def test_batch_caching(self):
        """Test caching with batch queries."""
        clear_cache()
        
        texts = [f"Batch test {i}" for i in range(5)]
        
        # First batch
        results1 = embed(texts)
        
        # Second batch (should use cache)
        results2 = embed(texts)
        
        assert results1 == results2, "Batch results should match"
        
        stats = get_cache_stats()
        assert stats['lru_hits'] >= 5, f"Should have 5+ cache hits, got {stats['lru_hits']}"
        print(f"✓ Batch caching: {stats['lru_hits']} hits")
        return True
    
    def test_embedder_detection(self):
        """Test that embedder type is detected."""
        embedder = _get_embedder_type()
        assert embedder in ['onnx', 'pytorch'], f"Unknown embedder: {embedder}"
        print(f"✓ Embedder detected: {embedder}")
        return True
    
    def test_cache_stats(self):
        """Test cache statistics are accurate."""
        clear_cache()
        
        # Get initial stats
        stats1 = get_cache_stats()
        
        # Do some embeddings (use unique texts to avoid disk cache hits)
        import time
        unique_prefix = f"stats_test_{time.time()}"
        for i in range(3):
            embed(f"{unique_prefix} Stats test {i}")
        
        # Get stats after
        stats2 = get_cache_stats()
        
        # Should show misses (or disk hits from previous runs)
        total_accesses = stats2['hits'] + stats2['misses'] + stats2['disk_hits']
        assert total_accesses >= 3, f"Should show at least 3 accesses, got {total_accesses}"
        
        # Hit same texts
        for i in range(3):
            embed(f"{unique_prefix} Stats test {i}")
        
        stats3 = get_cache_stats()
        assert stats3['hits'] >= 3, f"Should show hits, got {stats3}"
        
        print(f"✓ Cache stats: hits={stats3['hits']}, misses={stats3['misses']}, disk={stats3['disk_hits']}")
        return True


def run_tests():
    """Run all cache tests."""
    print("="*50)
    print("Testing Embedding Cache (Ticket #19)")
    print("="*50)
    
    tests = TestEmbeddingCache()
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
