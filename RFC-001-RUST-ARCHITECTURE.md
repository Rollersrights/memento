# RFC 001: Rust-Forward Hybrid Architecture
*Date: 2026-02-17*
*Status: Proposed*

## 🎯 Objective
Transition Memento from a monolithic Python script collection to a **modular, high-performance hybrid architecture**. The goal is to leverage Rust for "hot paths" (compute-heavy tasks) while retaining Python's flexibility for orchestration and CLI.

## 🏗️ The Strategy: "Thin Python, Fat Rust"

Instead of a full rewrite immediately, we propose a gradual migration using **Python Extensions (PyO3)**. This allows us to replace slow Python components with Rust binaries incrementally.

### Architecture Diagram

```
[ Memento CLI / API ]  <-- (Python)  Flexible "Control Plane"
         │
         ▼
[ Abstract Engine Interface ]
         │
    ┌────┴───────────────┐
    ▼                    ▼
[ Python Engine ]    [ Rust Engine ] <-- (Rust/PyO3)  High-Performance "Data Plane"
  (Legacy/Dev)         (Production)
    │                    │
    │                    ├─ ONNX Inference (ort)
    │                    ├─ Vector Search (SIMD/ndarray)
    │                    └─ Cache Management
    │
    └─ [ SQLite Database ] <-- Shared Storage
```

## 🗺️ Implementation Roadmap

### Phase 1: Modularization (Python Prep)
*Goal: Isolate logic to prepare for replacement.*

1.  **Define Core Interfaces:** Create `Engine` and `VectorIndex` abstract base classes.
2.  **Isolate NumPy:** Move all vector math (`dot_product`, `normalize`) to a single `vector_ops.py` module.
3.  **Strict Data Models:** Enforce `dataclass` usage (`Memory`, `SearchResult`) everywhere. Eliminate loose dictionaries.

### Phase 2: The Rust Core (Hybrid)
*Goal: Drop-in performance boost.*

1.  **Create `memento-core` Crate:** A Rust library exposing Python bindings via `PyO3`.
2.  **Port Embeddings:** Implement ONNX inference in Rust (removing `sentence-transformers` dependency in production).
3.  **Port Search:** Implement vector similarity search in Rust (replacing `numpy` logic).
4.  **Distribution:** Pip-installable binary wheels (`pip install memento-core`).

### Phase 3: The "Iron Memento" (End State)
*Goal: Single Binary (Optional).*

If the Python runtime proves too heavy for edge nodes (e.g., Raspberry Pi Zero), we wrap the Rust Core with a Rust CLI (`clap`), creating a standalone binary `memento` with zero Python dependencies.

## ⚖️ Trade-offs

| Approach | Pros | Cons |
| :--- | :--- | :--- |
| **Pure Python** | Fast iteration, simple build. | Slow startup (~400ms), high RAM, GIL limitations. |
| **Hybrid (Proposed)** | Best of both. Fast IO/Compute, easy logic. | Complex build (maturin/cargo), dual languages. |
| **Pure Rust** | Fastest startup, tiny binary, type safety. | Slower feature dev, higher barrier to entry. |

## 🧪 Request for Comment
*   Does this match the team's vision for "performance with flexibility"?
*   Should we prioritize the `ort` (ONNX) port immediately to solve the OpenSSL dependency issues on Linux?
