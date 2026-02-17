# Memento Core

Rust-based embedding engine for Memento with PyO3 bindings.

## Status

**Phase 2a Foundation** - Skeleton implementation in place.

This crate provides the foundation for Rust-based embeddings. The full ONNX
implementation requires model export and integration work.

## Building

```bash
cd memento-core
maturin develop  # For development
maturin build    # For distribution
```

## Usage

```python
import memento_core

# Initialize model
info = memento_core.init_model()

# Embed text
embedding = memento_core.embed_text("Hello world")

# Embed batch
texts = ["Hello", "World"]
embeddings = memento_core.embed_batch(texts)
```

## Architecture

- `lib.rs` - PyO3 module exports
- `embed.rs` - Embedding engine (ONNX)
- `model.rs` - Model management

## Roadmap

1. ✅ PyO3 bindings skeleton
2. ✅ Module structure
3. ⬜ Export MiniLM to ONNX
4. ⬜ Integrate ONNX Runtime
5. ⬜ Tokenizer integration
6. ⬜ Performance benchmarks

## Related

- Issue #7: Phase 2a Rust Embeddings
- Issue #9: memento-core Rust crate
- RFC-001: Rust-forward hybrid architecture
