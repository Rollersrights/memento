# Memento v0.2.0 - "The Speed & Persistence Update"
*Released: Feb 17, 2026*

A massive performance and usability overhaul for the local semantic memory system.

## 🚀 Highlights

### ⚡ Sub-Millisecond Search
Integrated **LRU caching** (RAM) and **Persistent Caching** (SQLite).
- **Repeated queries:** 0.03ms (was ~9ms) -> **300x speedup**
- **Cold start:** Instant warm-up via disk cache (survives restarts)
- **Hardware Acceleration:** Auto-detects AVX2 and uses **ONNX Runtime** for faster embeddings (~50% speedup on cold compute).

### 🖥️ New CLI
A brand new Python-based CLI replacing the old bash wrapper.
- **Rich Output:** Beautifully formatted tables for search results.
- **Smart Piping:** Auto-detects pipes (`|`) and outputs raw JSON for scripting.
- **Commands:** `remember`, `recall`, `stats`, `delete`, `dashboard`.

### 🛡️ Reliability
- **Test Suite:** Full coverage for core logic and cache hierarchy (`./run_tests.sh`).
- **Conflict Resolution:** Merged divergent optimizations (Bob's Persistence + Rita's ONNX).

## 📊 Benchmarks

| Operation | v0.1 (Baseline) | v0.2 (Cached) | Improvement |
|-----------|-----------------|---------------|-------------|
| Embed (1) | ~7ms | **0.00ms** | Instant |
| Search (1k)| 8.9ms | **0.03ms** | **296x** |
| Boot Time | ~4s | **Instant** | (via disk cache) |

## 📦 Installation

```bash
# Update dependencies
pip install -r requirements.txt

# Run the new CLI
memento --help
```

## 👥 Credits
- **Rita:** LRU Cache, ONNX Optimization
- **Bob:** Persistent Disk Cache, Test Suite, CLI Rewrite
- **Brett:** Architecture & Direction
