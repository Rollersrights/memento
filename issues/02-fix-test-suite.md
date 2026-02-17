---
title: "[P0] Fix failing test suite - only 40% pass rate"
labels: ["bug", "testing", "P0"]
assignees: ["Rita"]
---

## Problem
Test suite is failing with only 10/25 tests passing (40% pass rate). This blocks CI/CD and indicates broken functionality.

## Current Failures
```
tests/test_cache.py::TestMementoCache::test_cache_hierarchy FAILED
tests/test_cache.py::TestMementoCache::test_persistence FAILED
tests/test_embed_cache.py::TestEmbeddingCache::test_ram_cache_hit FAILED
tests/test_embed_cache.py::TestEmbeddingCache::test_disk_cache_persistence FAILED
tests/test_embed_cache.py::TestEmbeddingCache::test_cache_bypass FAILED
tests/test_embed_cache.py::TestEmbeddingCache::test_batch_caching FAILED
tests/test_embed_cache.py::TestEmbeddingCache::test_cache_stats FAILED
tests/test_store_edge_cases.py::TestStoreEdgeCases::test_very_long_text FAILED
tests/test_store_edge_cases.py::TestStoreEdgeCases::test_unicode_and_special_chars FAILED
tests/test_store_edge_cases.py::TestStoreEdgeCases::test_duplicate_prevention FAILED
tests/test_store_edge_cases.py::TestStoreEdgeCases::test_concurrent_access FAILED
tests/test_store_edge_cases.py::TestStoreEdgeCases::test_batch_operations FAILED
tests/test_store_edge_cases.py::TestStoreEdgeCases::test_filters FAILED
tests/test_store_edge_cases.py::TestStoreEdgeCases::test_database_corruption_recovery FAILED
```

## Root Causes

### 1. Missing Dependencies
```
ModuleNotFoundError: No module named 'sentence_transformers'
```

### 2. Import Path Issues
Tests import from `scripts.embed` instead of `memento.embed`

### 3. Test Environment Not Isolated
Tests share state between runs

## Proposed Solution

### Step 1: Fix Dependencies
Update CI and local dev setup:
```yaml
# .github/workflows/ci.yml
- name: Install dependencies
  run: |
    pip install sentence-transformers numpy rich pytest
    pip install -e .
```

### Step 2: Fix Import Paths
```python
# OLD (broken)
import embed
from scripts import embed

# NEW (correct)
from memento.embed import embed
from memento import get_store
```

### Step 3: Add Test Fixtures
```python
# tests/conftest.py
import pytest
from memento import get_store

@pytest.fixture
def temp_store(tmp_path):
    db_path = tmp_path / "test_memory.db"
    store = get_store(db_path=str(db_path))
    yield store
    store.close()
```

### Step 4: Create Proper Test Isolation
- Use `tmp_path` for temporary databases
- Clear caches between tests
- Mock embedding for unit tests

## Acceptance Criteria
- [ ] All 25 tests passing
- [ ] CI/CD pipeline green
- [ ] Tests run in < 30 seconds
- [ ] Test coverage report generated
- [ ] Tests isolated (no shared state)

## Related
- #1 (Clean up legacy scripts)
- Blocked by: #1 (path issues)
