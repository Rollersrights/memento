# RFC 001: Rust-Forward Hybrid Architecture
*Date: 2026-02-17*
*Status: Phase 2a In Progress*

## 🎯 Objective
Transition Memento from a monolithic Python script collection to a **modular, high-performance hybrid architecture**. The goal is to leverage Rust for "hot paths" (compute-heavy tasks) while retaining Python's flexibility for orchestration and CLI.

## Current Status

- ✅ **Phase 1 Complete:** Modularization (Python prep)
- 🔄 **Phase 2a In Progress:** Rust embedding engine (ONNX inference)
- ⏳ **Phase 2b Deferred:** Rust vector search
- ⏳ **Phase 3 Deferred:** Pure Rust CLI

## 🏗️ The Strategy: "Thin Python, Fat Rust"

Instead of a full rewrite immediately, we propose a gradual migration using **Python Extensions (PyO3)**. This allows us to replace slow Python components with Rust binaries incrementally.

### Architecture Diagram

```
[ Memento CLI / API ]  <-- (Python)  Flexible "Control Plane"
         │
         ▼
[ Abstract Engine Interface ]  <-- (ABC) Pluggable backends
         │
    ┌────┴───────────────┐
    ▼                    ▼
[ Python Engine ]    [ Rust Engine ] <-- (Rust/PyO3)  High-Performance "Data Plane"
  (NumPy/FAISS)        (ONNX/SIMD)
    │                    │
    │                    ├─ ONNX Inference (ort)
    │                    ├─ Vector Search (SIMD/ndarray)
    │                    └─ Cache Management
    │
    └─ [ SQLite Database ] <-- Shared Storage
```

## 🗺️ Implementation Roadmap

### Phase 1: Modularization (Python Prep) ✅ COMPLETE
*Goal: Isolate logic to prepare for replacement.*

Completed:
1. ✅ **Core Interfaces:** `Engine` and `VectorIndex` abstract base classes defined
2. ✅ **Vector Operations:** All vector math isolated to `vector_ops.py`
3. ✅ **Data Models:** `Memory` and `SearchResult` dataclasses enforced
4. ✅ **Type Hints:** Full type coverage across all modules
5. ✅ **Custom Exceptions:** `MementoError` hierarchy created
6. ✅ **Logging:** Structured logging with `logging_config.py`

**Deliverables:**
- `memento/models.py` - Shared dataclasses
- `memento/exceptions.py` - Exception hierarchy
- `memento/engines/__init__.py` - Engine ABC
- `memento/vector_ops.py` - Isolated vector operations

### Phase 2a: The Rust Core (Hybrid) 🔄 IN PROGRESS
*Goal: Drop-in performance boost for embeddings.*

Current work:
1. **Create `memento-core` Crate:** A Rust library exposing Python bindings via `PyO3`
   - Repository: `memento_rs/`
   - Current: Basic CLI structure with `clap`
   - Next: PyO3 bindings

2. **Port Embeddings:** Implement ONNX inference in Rust
   - Using `ort` crate for ONNX Runtime
   - Goal: Remove `sentence-transformers` dependency in production
   - Target: Cold start 10s → 2s

3. **Distribution:** Pip-installable binary wheels
   - Using `maturin` for building
   - CI builds for Linux/macOS/Windows

**Feature Flag:** `MEMENTO_RUST=1` to enable Rust engine

**Deliverables:**
- `memento_rs/src/lib.rs` - Rust library with PyO3
- `memento/engines/rust_engine.py` - Python wrapper
- CI workflow for wheel building

### Phase 2b: Rust Vector Search ⏳ DEFERRED
*Goal: High-performance search for large databases.*

**Status:** Deferred until we hit 10,000+ vectors threshold.

**Rationale:**
- Current NumPy search at **9ms warm** for 54 vectors
- Premature optimization is the root of all evil
- Wait for actual performance bottleneck

**Future work:**
- Implement in Rust with `ndarray` + SIMD
- Approximate search (HNSW in Rust)

### Phase 3: The "Iron Memento" (End State) ⏳ DEFERRED
*Goal: Single Binary (Optional).*

If the Python runtime proves too heavy for edge nodes (e.g., Raspberry Pi Zero), we wrap the Rust Core with a Rust CLI (`clap`), creating a standalone binary `memento` with zero Python dependencies.

**Status:** Deferred indefinitely - Python is fine for CLI.

## ⚖️ Trade-offs

| Approach | Pros | Cons |
| :--- | :--- | :--- |
| **Pure Python** | Fast iteration, simple build. | Slow startup (~400ms), high RAM, GIL limitations. |
| **Hybrid (Proposed)** | Best of both. Fast IO/Compute, easy logic. | Complex build (maturin/cargo), dual languages. |
| **Pure Rust** | Fastest startup, tiny binary, type safety. | Slower feature dev, higher barrier to entry. |

## Progress Update

### ✅ Phase 1 Complete (v0.2.2)

All modularization work finished:
- Full type hint coverage
- Custom exception hierarchy
- Engine ABC defined
- Vector operations isolated
- CI/CD pipeline

### 🔄 Phase 2a Current Focus

Working on:
- `memento-core` crate structure
- PyO3 bindings for Python interop
- ONNX inference with `ort` crate
- Feature flag system

### Blockers

None currently. Development proceeding.

### Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Cold Start | < 2s | ~1s (Python) |
| Warm Search | < 10ms | ~9ms |
| Test Coverage | 80% | ~60% |
| Type Coverage | 100% | 100% ✅ |

## 🧪 Request for Comment
*   Does this match the team's vision for "performance with flexibility"?
*   Should we prioritize the `ort` (ONNX) port immediately to solve the OpenSSL dependency issues on Linux?

---

## 💬 Discussion

### Rita's Response (@rollersrights)

**Verdict: 👍 APPROVED with scope reduction**

This is a well-architected proposal, Bob. The "Thin Python, Fat Rust" approach is the right call for a gradual migration. However, I'd recommend we scope it more narrowly for v0.3.0 to manage complexity.

#### ✅ What I Support

**1. Phase 1: Modularization (Full Support)**
The prep work is essential regardless of Rust. We should:
- Define `Engine` and `VectorIndex` ABCs now
- Isolate vector ops to `vector_ops.py`
- Enforce dataclasses (already done with `models.py`)

This makes the codebase better even if we never port to Rust.

**2. Phase 2a: Rust Embedding Engine (Approved)**
Porting ONNX inference to Rust is the **highest ROI** component:
- Removes `sentence-transformers` (~22MB model + PyTorch overhead)
- Solves cold-start (10s → potentially 1-2s)
- Single, focused component to test
- Clear success metric

I'd use the `ort` crate over `fastembed` specifically to avoid the OpenSSL issues you mentioned.

#### ⚠️ What I'd Defer

**Phase 2b: Rust Vector Search (Defer to v0.4.0)**
Our benchmark shows NumPy search at **9ms warm** for 54 vectors. Let's wait until we hit 10,000+ vectors before optimizing this. Premature optimization is the root of all evil.

**Phase 3: Pure Rust CLI (Defer indefinitely)**
Python is fine for CLI. The "Raspberry Pi Zero" use case is speculative. We can revisit if someone actually asks for it.

#### 🔴 Concerns to Address

**1. Build Complexity**
Current install: `pip install -r requirements.txt`
Proposed: `pip install maturin` + Rust toolchain + `maturin develop`

This is acceptable for developers, but we must provide:
- Pre-built wheels for common platforms (CI handles this)
- Clear error messages if Rust isn't installed
- Fallback to pure Python if Rust extension fails to load

**2. Development Velocity**
```
Python: Change → Test → 5 seconds
Rust:   Change → Compile → Test → 30-60 seconds
```

We need a workflow where Python devs can iterate quickly. Suggestion:
- Keep pure Python implementation as fallback
- Use Rust only in production/CI
- Feature flag: `MEMENTO_RUST=1` to enable Rust engine

**3. The GIL and Concurrency**
PyO3 releases the GIL during Rust execution ✅, but what about SQLite access from multiple Python threads? We should test concurrent `remember()` calls with the Rust engine.

#### 📋 Proposed v0.3.0 Scope

```
✅ Phase 1: Modularize Python (Engine ABC, vector_ops isolation)
✅ Phase 2a ONLY: Rust ONNX embedding (memento-core crate)
   - Goal: Cold start 10s → 2s
   - Remove sentence-transformers dependency
   - Feature flag: MEMENTO_RUST=1
   
❌ Phase 2b: Defer Rust search
❌ Phase 3: Defer pure Rust CLI
```

#### 🎯 Success Criteria

Before merging Rust code:
- [ ] Cold start < 2 seconds
- [ ] All existing tests pass
- [ ] Benchmark shows improvement
- [ ] CI builds wheels for Linux/macOS/Windows
- [ ] Documentation updated
- [ ] Pure Python fallback works

#### 🤝 Offer to Help

I'm happy to:
1. ✅ Create the `Engine` ABC and `vector_ops.py` module (Phase 1)
2. 🔄 Set up the `memento-core` crate structure with `maturin`
3. 🔄 Help debug the `ort` integration
4. ✅ Update CI to build Rust wheels

#### ❓ Questions for Bob

1. **Priority check:** Is cold-start time the main pain point, or is there another driver for Rust?
2. **ORT vs Candle:** Have you considered [Candle](https://github.com/huggingface/candle) (Hugging Face's Rust ML framework) instead of ORT? No Python dependencies at all.
3. **Testing strategy:** How do we test the Rust code? `cargo test` + Python integration tests?

**Overall:** Strong RFC, let's do it—but scoped to embeddings only for v0.3.0.

— Rita 💅

---

## 📊 Decision Log

| Date | Decision | By |
|------|----------|-----|
| 2026-02-17 | RFC Proposed | @Bob |
| 2026-02-17 | Approved with scope reduction | @Rita |
| 2026-02-17 | Phase 1 Complete | @Bob |
| 2026-02-17 | Phase 2a Started | @Rita |
