#!/usr/bin/env python3
"""
Memento - Example Usage

Simple examples showing how to use the memory system.
"""

from scripts.store import MemoryStore

# Initialize memory store
memory = MemoryStore()

# Store some memories
print("Storing memories...")
memory.remember("Learned about vector databases today", importance=0.8, tags=["learning"])
memory.remember("Remember to buy milk", importance=0.6, tags=["todo", "shopping"])
memory.remember("Server IP is 10.0.0.5", importance=0.9, tags=["server", "network"])

# Search memories
print("\nSearching for 'shopping':")
results = memory.recall("shopping", topk=5)
for r in results:
    print(f"  [{r['score']:.3f}] {r['text']}")

print("\nSearching for 'database':")
results = memory.recall("database", topk=5)
for r in results:
    print(f"  [{r['score']:.3f}] {r['text']}")

# Show stats
print("\nMemory stats:")
import json
print(json.dumps(memory.stats(), indent=2))
