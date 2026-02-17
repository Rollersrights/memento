---
title: "[P0] Fix auto_memory.py import paths - broken since package restructure"
labels: ["bug", "P0"]
assignees: ["Bob"]
---

## Problem
`scripts/auto_memory.py` uses wrong import paths that reference old directory structure:

```python
# CURRENT (broken)
sys.path.insert(0, os.path.expanduser(
    '~/.openclaw/workspace/skills/memory-zvec/scripts'
))
from store import MemoryStore  # ❌ ImportError
```

This causes auto-store to fail silently with log entries like:
```
[2026-02-17T12:44:06.329039] ❌ Memento init failed: No module named 'memento'
```

## Impact
- No automatic memory storage
- User conversations not remembered
- "Fully automatic" vision not achieved

## Proposed Solution

### Step 1: Fix Imports
```python
# scripts/auto_memory.py
import sys
import os

# Add workspace to path for development
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/memento'))

from memento import get_store  # ✅ Correct import
default_db_path = os.path.expanduser("~/.openclaw/memento/memory.db")
```

### Step 2: Use Unified Database
```python
def __init__(self):
    self.store = None
    self.db_path = os.path.expanduser("~/.openclaw/memento/memory.db")
    self._init_store()
```

### Step 3: Better Error Handling
```python
def _init_store(self):
    try:
        from memento import get_store
        self.store = get_store(db_path=self.db_path)
        self._log_status(f"✅ Memento initialized: {self.db_path}")
    except ImportError as e:
        self._log_status(f"❌ Import error: {e}")
        self._log_status("Hint: Run 'pip install -e ~/.openclaw/workspace/memento'")
        self.store = None
    except Exception as e:
        self._log_status(f"❌ Memento init failed: {e}")
        self.store = None
```

### Step 4: Add to Package
Consider moving `auto_memory.py` to `memento/openclaw_bridge.py`:
```python
# memento/openclaw_bridge.py
class OpenClawMemoryBridge:
    """Bridge between OpenClaw and Memento."""
    def store_interaction(self, user_msg, agent_response):
        ...
    def recall_context(self, query):
        ...
```

## Acceptance Criteria
- [ ] Auto-memory initializes without import errors
- [ ] Uses unified database location
- [ ] Stores interactions successfully
- [ ] Clear error messages when dependencies missing
- [ ] Integration documented

## Testing
```python
# Test the fix
python3 -c "
import sys
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/memento'))
from scripts.auto_memory import get_memory
mem = get_memory()
print(f'Store initialized: {mem.store is not None}')
"
```

## Related
- #3 (Unify database location)
- #6 (Create OpenClaw integration hook)
