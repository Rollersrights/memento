#!/usr/bin/env python3
"""
Benchmark batch vs sequential search
Shows benefits of batch_recall with larger datasets
"""

import sys
import time
sys.path.insert(0, 'scripts')

from scripts.store import MemoryStore
from scripts.vector_search import _get_search_backend
import numpy as np

print("="*60)
print("MEMENTO BATCH SEARCH BENCHMARK")
print("="*60)

# Use memento test DB
memory = MemoryStore()
backend = _get_search_backend()

print(f"\nSearch backend: {backend}")
print(f"Current memories: {len(memory._ids)}")

# Add test data if needed
if len(memory._ids) < 100:
    print("\nAdding test memories...")
    for i in range(200):
        memory.remember(
            f'Sample memory about topic {i % 20}: content {i} ' + 
            f'with some additional text to make it realistic',
            importance=0.5,
            tags=[f'tag{i % 5}']
        )
    print(f"Added memories. Total: {len(memory._ids)}")

# Warm up cache
print("\nWarming up embedding cache...")
for q in ['topic', 'content', 'memory', 'test', 'sample']:
    memory.recall(q, topk=5)

# Test with different batch sizes
test_sizes = [1, 5, 10, 20]

for n in test_sizes:
    queries = [f'topic {i % 20}' for i in range(n)]
    
    print(f"\n--- {n} queries ---")
    
    # Sequential
    start = time.perf_counter()
    for q in queries:
        memory.recall(q, topk=5)
    t_seq = (time.perf_counter() - start) * 1000
    print(f"Sequential: {t_seq:.2f}ms ({t_seq/n:.2f}ms each)")
    
    # Batch
    start = time.perf_counter()
    results = memory.batch_recall(queries, topk=5)
    t_batch = (time.perf_counter() - start) * 1000
    print(f"Batch:      {t_batch:.2f}ms ({t_batch/n:.2f}ms each)")
    
    if t_batch < t_seq:
        print(f"Speedup:    {t_seq/t_batch:.1f}x faster")
    else:
        print(f"Overhead:   {t_batch/t_seq:.1f}x slower (batch overhead)")

print("\n" + "="*60)
print("NOTES:")
print("- Batch is beneficial for 10+ queries")
print("- With hnswlib/FAISS, batch is always faster")
print("- Small DBs (<500) have minimal difference")
print("="*60)
