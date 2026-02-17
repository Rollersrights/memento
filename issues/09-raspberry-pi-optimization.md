---
title: "[P2] Raspberry Pi optimization - lightweight mode for ARM/embedded"
labels: ["enhancement", "performance", "arm", "P2"]
assignees: []
---

## Problem
Vision: "Run on anything from Raspberry Pi to server"

Current issues for Pi:
- PyTorch: ~500MB RAM, slow on ARM
- Model: 22MB download, slow loading
- Cold start: ~10s (unacceptable on Pi)
- No ARM-optimized builds

## Target Specs (Raspberry Pi Zero 2 W)
- RAM: <100MB total
- Storage: <50MB installed
- Cold start: <3s
- Warm query: <100ms

## Optimization Strategies

### 1. Rust Embedding (Primary Solution)
See #5 for Rust embedding engine
- ONNX Runtime has ARM builds
- Much lighter than PyTorch
- Faster cold start

### 2. Smaller Model Option
```python
# Use 9MB model instead of 22MB
EMBEDDING_MODELS = {
    "default": "sentence-transformers/all-MiniLM-L6-v2",  # 22MB
    "light": "sentence-transformers/paraphrase-MiniLM-L3-v2",  # 9MB
    "tiny": "sentence-transformers/all-MiniLM-L6-v2-int8",  # Quantized
}

# Auto-detect based on hardware
if is_raspberry_pi():
    config.embedding.model = "light"
```

### 3. SQLite-Only Mode (No Embeddings)
```python
class LightweightStore:
    """
    For minimal deployments - no embeddings,
    just keyword search + tags.
    """
    def remember(self, text, **kwargs):
        # Store text only
        pass
    
    def recall(self, query):
        # Use FTS5 (SQLite full-text search)
        # No vectors, no ML
        pass
```

### 4. Cross-Compilation for ARM
```dockerfile
# Dockerfile for ARM build
FROM messense/manylinux_2_28-cross:aarch64

# Build Rust extension for ARM
RUN cargo build --release --target aarch64-unknown-linux-gnu

# Build Python wheel
RUN maturin build --release --target aarch64-unknown-linux-gnu
```

### 5. Pre-built ARM Wheels
```yaml
# .github/workflows/arm.yml
strategy:
  matrix:
    include:
      - os: ubuntu-latest
        target: aarch64
        arch: arm64
      - os: ubuntu-latest
        target: armv7
        arch: armv7
```

## Installation Options

### Full Install (Server)
```bash
pip install memento-openclaw[fast]
# All features, PyTorch/ONNX
```

### Light Install (Pi 4)
```bash
pip install memento-openclaw[light]
# Small model, ONNX only
```

### Minimal Install (Pi Zero)
```bash
pip install memento-openclaw[minimal]
# SQLite only, no embeddings
```

## Hardware Detection
```python
def detect_hardware_tier():
    """Auto-detect what mode to run in."""
    
    # Check RAM
    ram_gb = psutil.virtual_memory().total / (1024**3)
    
    # Check CPU
    cpu_count = os.cpu_count()
    
    # Check if ARM
    is_arm = platform.machine() in ('arm64', 'aarch64', 'armv7l')
    
    if ram_gb < 1 or (is_arm and cpu_count <= 2):
        return "minimal"
    elif ram_gb < 4:
        return "light"
    else:
        return "full"
```

## Acceptance Criteria
- [ ] Installs on Raspberry Pi Zero
- [ ] Cold start <3s on Pi
- [ ] RAM usage <100MB
- [ ] ARM wheels on PyPI
- [ ] Auto-detects hardware and adjusts
- [ ] Minimal mode works without embeddings

## Related
- #5 (Rust embedding - key to Pi performance)
- Vision: "Raspberry Pi to server"
