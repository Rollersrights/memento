#!/usr/bin/env python3
"""
Memento Performance Profiler
Measures embedding, search, and storage performance
"""

import time
import sys
import os
import tempfile
import statistics
from pathlib import Path

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from scripts.store import MemoryStore
from scripts.embed import embed, embed_chunks

class Profiler:
    def __init__(self):
        self.results = []
        
    def time_it(self, name, fn, iterations=10):
        """Time a function over multiple iterations."""
        times = []
        for i in range(iterations):
            start = time.perf_counter()
            result = fn()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms
        
        avg = statistics.mean(times)
        median = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        
        self.results.append({
            'name': name,
            'avg': avg,
            'median': median,
            'min': min_time,
            'max': max_time,
            'iterations': iterations
        })
        
        return result
    
    def print_results(self):
        print("\n" + "="*70)
        print("PROFILING RESULTS")
        print("="*70)
        print(f"{'Operation':<40} {'Avg':>8} {'Median':>8} {'Min':>8} {'Max':>8}")
        print("-"*70)
        for r in self.results:
            print(f"{r['name']:<40} {r['avg']:>7.2f}ms {r['median']:>7.2f}ms {r['min']:>7.2f}ms {r['max']:>7.2f}ms")
        print("="*70)


def profile_embedding():
    """Profile embedding speed."""
    print("\n📊 Profiling Embedding...")
    
    profiler = Profiler()
    
    # Single text embedding
    test_text = "This is a test sentence for embedding performance profiling."
    profiler.time_it("Embed single text (1)", lambda: embed(test_text), iterations=20)
    
    # Batch embedding - small
    small_batch = [f"Test sentence number {i} for batch embedding" for i in range(10)]
    profiler.time_it("Embed batch (10 texts)", lambda: embed(small_batch), iterations=10)
    
    # Batch embedding - medium
    medium_batch = [f"Test sentence number {i} for batch embedding performance testing" for i in range(50)]
    profiler.time_it("Embed batch (50 texts)", lambda: embed(medium_batch), iterations=5)
    
    # Batch embedding - large
    large_batch = [f"Test sentence number {i} for comprehensive batch embedding performance evaluation" for i in range(100)]
    profiler.time_it("Embed batch (100 texts)", lambda: embed(large_batch), iterations=3)
    
    profiler.print_results()
    return profiler.results


def profile_storage():
    """Profile storage operations."""
    print("\n📊 Profiling Storage...")
    
    # Use temp database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        memory = MemoryStore(db_path=db_path)
        profiler = Profiler()
        
        # Single store
        profiler.time_it("Store single memory", 
            lambda: memory.remember(f"Test memory at {time.time()}", importance=0.5), 
            iterations=50)
        
        # Bulk store (measure total time for 100 stores)
        def bulk_store_100():
            for i in range(100):
                memory.remember(f"Bulk test memory {i} at {time.time()}", importance=0.5)
        profiler.time_it("Bulk store (100 memories)", bulk_store_100, iterations=5)
        
        profiler.print_results()
        return profiler.results
        
    finally:
        os.unlink(db_path)


def profile_search():
    """Profile search operations with different database sizes."""
    print("\n📊 Profiling Search...")
    
    results = []
    
    for db_size in [100, 500, 1000]:
        print(f"\n  Testing with {db_size} memories...")
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            memory = MemoryStore(db_path=db_path)
            
            # Populate database
            for i in range(db_size):
                memory.remember(
                    f"Test memory about topic {i % 10}: this is sample content for search testing",
                    importance=0.5,
                    tags=[f"tag{i % 5}"]
                )
            
            profiler = Profiler()
            
            # Vector search
            profiler.time_it(f"Vector search (db={db_size})", 
                lambda: memory.recall("topic search testing", topk=10), 
                iterations=20)
            
            results.extend(profiler.results)
            profiler.print_results()
            
        finally:
            os.unlink(db_path)
    
    return results


def profile_hybrid_search():
    """Profile hybrid BM25 + Vector search."""
    print("\n📊 Profiling Hybrid Search...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        memory = MemoryStore(db_path=db_path)
        
        # Populate with varied content
        for i in range(500):
            memory.remember(
                f"Memory {i}: Server configuration on 10.0.{i % 256}.5 with topic {i % 20}",
                importance=0.6,
                tags=["network", "server"] if i % 3 == 0 else ["general"]
            )
        
        from scripts.search import hybrid_bm25_vector_search
        
        profiler = Profiler()
        
        # Hybrid search with IP address (good for BM25)
        profiler.time_it("Hybrid search (IP address)", 
            lambda: hybrid_bm25_vector_search(memory, "10.0.0.5", topk=10), 
            iterations=20)
        
        # Hybrid search with concept
        profiler.time_it("Hybrid search (concept)", 
            lambda: hybrid_bm25_vector_search(memory, "server configuration", topk=10), 
            iterations=20)
        
        profiler.print_results()
        return profiler.results
        
    finally:
        os.unlink(db_path)


def profile_imports():
    """Profile import/load times."""
    print("\n📊 Profiling Import/Load Times...")
    
    profiler = Profiler()
    
    # Fresh Python process to test import time
    def test_import():
        import subprocess
        result = subprocess.run(
            [sys.executable, '-c', 'from scripts.store import MemoryStore; from scripts.embed import embed'],
            capture_output=True,
            cwd=os.path.dirname(__file__)
        )
        return result.returncode == 0
    
    profiler.time_it("Module import (cold)", test_import, iterations=5)
    
    profiler.print_results()
    return profiler.results


def main():
    print("="*70)
    print("MEMENTO PERFORMANCE PROFILER")
    print("="*70)
    print("\nThis will test various operations and report timing.")
    print("First run downloads the model (~22MB) if not cached.")
    input("\nPress Enter to start...")
    
    all_results = []
    
    try:
        all_results.extend(profile_imports())
    except Exception as e:
        print(f"Import profiling failed: {e}")
    
    try:
        all_results.extend(profile_embedding())
    except Exception as e:
        print(f"Embedding profiling failed: {e}")
    
    try:
        all_results.extend(profile_storage())
    except Exception as e:
        print(f"Storage profiling failed: {e}")
    
    try:
        all_results.extend(profile_search())
    except Exception as e:
        print(f"Search profiling failed: {e}")
    
    try:
        all_results.extend(profile_hybrid_search())
    except Exception as e:
        print(f"Hybrid search profiling failed: {e}")
    
    print("\n" + "="*70)
    print("PROFILING COMPLETE")
    print("="*70)
    print("\nBottlenecks identified will help guide optimization efforts.")


if __name__ == "__main__":
    main()
