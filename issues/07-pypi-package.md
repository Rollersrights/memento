---
title: "[P1] Package for PyPI - pip install memento-openclaw"
labels: ["enhancement", "packaging", "P1"]
assignees: ["Bob"]
---

## Problem
Installation requires git clone and manual setup. Vision requires "easy to install and run with minimum user intervention."

Current:
```bash
git clone https://github.com/rollersrights/memento.git
cd memento
pip install -e .
```

Target:
```bash
pip install memento-openclaw
```

## Proposed Solution

### Step 1: Fix Package Name
```toml
# pyproject.toml
[project]
name = "memento-openclaw"  # More specific than just 'memento'
version = "0.3.0"
description = "Persistent semantic memory for OpenClaw AI agents"
```

### Step 2: Proper Dependencies
```toml
dependencies = [
    "sentence-transformers>=2.0.0",
    "numpy>=1.20.0",
    "rich>=13.0.0",
    "py-cpuinfo>=9.0.0",
]

[project.optional-dependencies]
fast = ["onnxruntime>=1.15.0"]
faiss = ["faiss-cpu>=1.7.0"]
rust = ["memento-core>=0.1.0"]  # When ready
```

### Step 3: Entry Points
```toml
[project.scripts]
memento = "memento.cli:main"
memento-server = "memento.server:main"  # Future web API
```

### Step 4: Classifiers
```toml
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Rust",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
```

### Step 5: Build and Release

#### Local Build Test
```bash
# Clean build
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Test install
pip install dist/memento_openclaw-0.3.0-py3-none-any.whl

# Verify
memento --version
```

#### PyPI Upload
```bash
# Test PyPI first
python -m twine upload --repository testpypi dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ memento-openclaw

# Real PyPI
python -m twine upload dist/*
```

### Step 6: GitHub Actions Release
```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    
    - name: Install dependencies
      run: |
        pip install build twine
    
    - name: Build
      run: python -m build
    
    - name: Publish
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

### Step 7: Post-Install Hook
```python
# memento/__init__.py
import os
from pathlib import Path

def _ensure_directories():
    """Create necessary directories on first import."""
    base = Path.home() / ".openclaw" / "memento"
    base.mkdir(parents=True, exist_ok=True)
    (base / "logs").mkdir(exist_ok=True)
    (base / "backups").mkdir(exist_ok=True)

_ensure_directories()
```

## Acceptance Criteria
- [ ] Package name: `memento-openclaw`
- [ ] Installs with: `pip install memento-openclaw`
- [ ] CLI available: `memento` command works
- [ ] All dependencies auto-installed
- [ ] Works on Python 3.8-3.12
- [ ] GitHub Actions auto-releases on tag
- [ ] README updated with pip install instructions

## Related
- #5 (Rust engine - optional dependency)
- All P0 issues should be fixed first
