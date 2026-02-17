# Issue #15: Fix analyze_bottlenecks.py import errors

**Priority:** 🔴 CRITICAL  
**Component:** Diagnostic / Analysis Tools  
**Labels:** `bug`, `imports`, `phase-1`

---

## Problem

The `analyze_bottlenecks.py` script fails with import errors:
```
No module named 'scripts'
```

Additionally, it tries to import `get_embedder` from `scripts.embed`, but this function doesn't exist.

### Current broken code:
```python
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/memento/scripts'))
from scripts.embed import get_embedder  # ERROR: get_embedder doesn't exist!
```

## Root Causes

1. **Wrong import path**: The script adds `.../memento/scripts` to path but then tries to import from `scripts.X` which doesn't work
2. **Missing function**: `embed.py` exports `embed()`, `get_cache_stats()`, `warmup()` but NOT `get_embedder()`
3. **Circular import risk**: Importing embed at module level can trigger model loading

## Solution

Fix the import paths in `analyze_bottlenecks.py`:
- Add parent directory to path (not scripts/)
- Use correct import: `from scripts.embed import embed`
- Or use lazy imports inside functions

## Files to Update

- `scripts/analyze_bottlenecks.py` - Fix imports and use correct function names

## Acceptance Criteria

- [ ] Script runs without import errors
- [ ] Can detect embedder availability correctly
- [ ] Doesn't trigger unwanted model loading
- [ ] Returns accurate bottleneck analysis

## Testing

```bash
python3 scripts/analyze_bottlenecks.py
# Should complete without errors and generate bottlenecks.json
```

---

**Assigned to:** Autonomous worker  
**Target:** v0.2.2
