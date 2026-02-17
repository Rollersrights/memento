# Bug #17: SearchResult doesn't support item assignment

**Priority:** 🔴 HIGH  
**Component:** Models / Search  
**Labels:** `bug`, `tests`, `phase-1`

---

## Problem

`SearchResult` dataclass doesn't support dict-like item assignment (`obj['key'] = value`), causing `TypeError` in `vector_search()`.

### Error
```
TypeError: 'SearchResult' object does not support item assignment
  scripts/search.py:97: in vector_search
    r['vector_score'] = r.get('score', 0)
```

### Affected Tests
- `test_reranking_recency`
- `test_vector_fallback`

---

## Root Cause

`SearchResult` is a `@dataclass` with only `__getitem__` for read access. The `vector_search()` function tries to add dynamic fields (`vector_score`, `bm25_score`, `hybrid_score`) via item assignment.

---

## Solution

Add `__setitem__` method and `_extra` dict for dynamic fields:

```python
@dataclass
class Memory:
    # ... existing fields ...
    _extra: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like item assignment for dynamic fields."""
        self._extra[key] = value

    def __getitem__(self, key: str) -> Any:
        if key in self._extra:
            return self._extra[key]
        return self.to_dict()[key]
    
    def get(self, key: str, default: Any = None) -> Any:
        if key in self._extra:
            return self._extra[key]
        return self.to_dict().get(key, default)
```

---

## Files Changed

- `scripts/models.py`: Add `__setitem__` and `_extra` storage

---

## Testing

```bash
python3 -m pytest tests/test_search.py -v
```

All tests should pass.

---

**Fixed by:** PR #18  
**Status:** Fixed
