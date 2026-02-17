# Performance Bottleneck #19: Model Stays in RAM When Idle

**Priority:** 🟡 MEDIUM  
**Component:** Embedding / Model Management  
**Labels:** `performance`, `memory`, `phase-1`

---

## Problem

The MiniLM model (~80MB RAM) stays loaded indefinitely after first use:
- No way to free RAM when not needed
- Long-running processes waste memory
- No idle timeout mechanism
- Can cause OOM on memory-constrained systems

### Current Behavior
```
1. First embed() call loads model (80MB)
2. Model stays in RAM forever
3. No way to release it
```

---

## Impact

- ❌ Wasted RAM on idle systems
- ❌ No graceful memory management
- ❌ Could cause OOM in long-running processes
- ❌ No control for resource-constrained environments

---

## Solution

Add `unload_model()` function and optional idle timeout:

```python
# embed.py
_idle_timer = None
_idle_timeout_minutes = 30  # Configurable
_last_activity = time.time()

def unload_model():
    """Free model from RAM to save memory."""
    global _model, _onnx_session
    _model = None
    _onnx_session = None
    # Force garbage collection
    import gc
    gc.collect()

def _reset_idle_timer():
    """Reset idle timer on activity."""
    global _last_activity, _idle_timer
    _last_activity = time.time()
    if _idle_timer:
        _idle_timer.cancel()
    _idle_timer = threading.Timer(
        _idle_timeout_minutes * 60, 
        unload_model
    )
    _idle_timer.daemon = True
    _idle_timer.start()
```

---

## Files to Update

- `scripts/embed.py` - Add unload_model() and idle timeout
- `scripts/config.py` - Add idle_timeout config option
- `CHANGELOG.md` - Document new feature

---

## Acceptance Criteria

- [ ] `unload_model()` frees model RAM
- [ ] `get_memory_usage()` reports current RAM usage
- [ ] Idle timeout auto-unloads after configurable period
- [ ] Model reloads transparently on next embed() call
- [ ] Tests verify unload/reload cycle
- [ ] Documentation updated

---

## Testing

```python
# Test unload
from scripts.embed import embed, unload_model, get_memory_usage
embed("test")  # Load model
usage1 = get_memory_usage()  # ~80MB
unload_model()
usage2 = get_memory_usage()  # ~0MB
embed("test")  # Reloads transparently
usage3 = get_memory_usage()  # ~80MB again
```

---

**Assigned to:** Autonomous worker  
**Target:** v0.2.2
