# Performance Bottleneck #14: No Query Timeout

**Priority:** 🟠 HIGH  
**Component:** Search / Recall  
**Labels:** `performance`, `reliability`, `phase-1`

---

## Problem

Search operations can hang indefinitely:
- No timeout on `recall()` calls
- Large databases could cause 30s+ queries
- No way to cancel stuck searches
- Cron jobs could hang forever

---

## Impact

- ❌ Stuck queries block everything
- ❌ No graceful degradation
- ❌ Could hang cron jobs
- ❌ Poor user experience on large DBs

---

## Solution

Add timeout parameter to all search operations:

```python
# store.py
import signal
from contextlib import contextmanager

class TimeoutError(Exception):
    pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutError(f"Query timed out after {seconds}s")
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def recall(self, query, topk=5, timeout=10):
    """
    Search memories with timeout protection.
    
    Args:
        query: Search text
        topk: Number of results
        timeout: Max seconds to wait (default 10)
    
    Raises:
        TimeoutError: If search takes longer than timeout
    """
    with time_limit(timeout):
        # ... existing search logic ...
        return results
```

---

## Files to Update

- `scripts/store.py` - Add timeout to `recall()`
- `scripts/search.py` - Add timeout to `search()` and `hybrid_search()`
- `scripts/cli.py` - Handle TimeoutError gracefully

---

## Acceptance Criteria

- [ ] All search methods accept `timeout` parameter
- [ ] Default timeout is 10 seconds
- [ ] TimeoutError raised gracefully
- [ ] CLI shows friendly message on timeout
- [ ] Tests verify timeout works
- [ ] Documentation updated

---

## Testing

```python
# Test timeout
import time
start = time.time()
try:
    store.recall("test", timeout=1)
except TimeoutError:
    elapsed = time.time() - start
    assert elapsed < 1.5, "Timeout didn't work"
```

---

**Assigned to:** Autonomous worker  
**Target:** v0.2.2
