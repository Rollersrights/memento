---
title: "[P1] Implement Rust embedding engine (RFC-001 Phase 2a)"
labels: ["enhancement", "performance", "rust", "P1"]
assignees: ["Rita"]
---

## Problem
Cold start is ~10 seconds due to Python/PyTorch model loading. Vision requires "extremely fast" performance using "right programming language for each module."

Current state: 99% Python, Rust barely started (145 LOC)

## Goal
Reduce cold start from ~10s to <2s using Rust + ONNX Runtime

## Architecture
```
Python API (memento/embed.py)
    │
    ├─ Fast path: Rust Engine (if MEMENTO_RUST=1)
    │   ├─ ONNX Runtime inference
    │   ├─ PyO3 Python bindings
    │   └─ ~1-2s cold start
    │
    └─ Fallback: Python Engine (default)
        ├─ PyTorch/SentenceTransformers
        └─ ~10s cold start
```

## Implementation Plan

### Step 1: Set up Rust Project Structure
```bash
cd memento-core/
# Already exists but incomplete
# Needs:
# - pyproject.toml with maturin
# - Proper Cargo.toml with ort dependency
```

### Step 2: Implement Rust Embedding
```rust
// memento-core/src/embed.rs
use ort::Environment;
use pyo3::prelude::*;

pub struct RustEmbedder {
    session: ort::Session,
    tokenizer: Tokenizer,
}

impl RustEmbedder {
    pub fn new() -> Result<Self, Box<dyn Error>> {
        // Load ONNX model
        // ~1-2s vs PyTorch ~10s
    }
    
    pub fn embed(&self, text: &str) -> Vec<f32> {
        // ONNX inference
    }
}

#[pyfunction]
fn embed_text(text: String) -> PyResult<Vec<f32>> {
    // Called from Python
}
```

### Step 3: PyO3 Bindings
```rust
// memento-core/src/lib.rs
use pyo3::prelude::*;

#[pymodule]
fn memento_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(embed_text, m)?)?;
    m.add_class::&lt;RustEmbedder&gt;()?;
    Ok(())
}
```

### Step 4: Python Integration
```python
# memento/embed.py
import os

USE_RUST = os.environ.get('MEMENTO_RUST', '0') == '1'

if USE_RUST:
    try:
        from memento_core import embed_text
        EMBEDDER = 'rust'
    except ImportError:
        EMBEDDER = 'python'
else:
    EMBEDDER = 'python'

def embed(text):
    if EMBEDDER == 'rust':
        return embed_text(text)
    else:
        return _embed_python(text)
```

### Step 5: Build System
```toml
# memento-core/pyproject.toml
[build-system]
requires = ["maturin>=1.0"]
build-backend = "maturin"

[project]
name = "memento-core"
version = "0.1.0"
```

## Acceptance Criteria
- [ ] Rust embeds text in <100ms (vs Python ~7ms warm, 10s cold)
- [ ] Cold start <2s total
- [ ] PyO3 bindings working
- [ ] Feature flag: MEMENTO_RUST=1
- [ ] Fallback to Python if Rust fails
- [ ] CI builds wheels for Linux/macOS/Windows
- [ ] All existing tests pass

## Success Metrics
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Cold Start | ~10s | <2s | 5x faster |
| Warm Embed | ~7ms | ~0.04ms | 175x faster |
| Memory | ~500MB | ~200MB | 2.5x less |

## Related
- RFC-001-RUST-ARCHITECTURE.md
- #8 (Raspberry Pi optimization)
