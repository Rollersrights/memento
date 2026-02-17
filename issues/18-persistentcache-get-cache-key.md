# Bug #18: PersistentCache missing get_cache_key method

**Priority:** 🟡 MEDIUM  
**Component:** Embed / Cache  
**Labels:** `bug`, `tests`, `phase-1`

---

## Problem

Test `test_disk_cache_persistence` tries to access `_get_cache_key` via `_disk_cache.get.__self__._get_cache_key`, but this method doesn't exist on `PersistentCache` class.

### Error
```
AttributeError: 'PersistentCache' object has no attribute '_get_cache_key'
  tests/test_embed_cache.py:57
```

---

## Root Cause

`_get_cache_key` is a module-level function in `embed.py`, not a method of `PersistentCache`. The test incorrectly tries to access it as an instance method.

---

## Solution

Add `get_cache_key()` method to `PersistentCache` class:

```python
def get_cache_key(self, text: str) -> str:
    """Generate cache key for text (convenience method)."""
    return _get_cache_key(text)
```

Update test to use new method:
```python
text_hash = _disk_cache.get_cache_key(text)
```

---

## Files Changed

- `scripts/embed.py`: Add `get_cache_key()` method
- `tests/test_embed_cache.py`: Use new method

---

## Testing

```bash
python3 -m pytest tests/test_embed_cache.py::TestEmbeddingCache::test_disk_cache_persistence -v
```

---

**Fixed by:** PR #18  
**Status:** Fixed
