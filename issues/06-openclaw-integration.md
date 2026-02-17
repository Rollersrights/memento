---
title: "[P1] Create OpenClaw integration hook - automatic memory storage"
labels: ["enhancement", "integration", "P1"]
assignees: ["Brett"]
---

## Problem
Memento is NOT "fully automatic" - user must manually run `memento remember`. No integration with OpenClaw core means conversations aren't automatically stored.

Vision: "User doesn't need to do anything if they so wish"

## Current State
- `auto_memory.py` exists but broken (#4)
- No hook in OpenClaw message handling
- User must manually remember

## Proposed Solution

### Option A: Middleware Pattern (Recommended)
```python
# In OpenClaw core
class OpenClawSession:
    def __init__(self):
        self.memory_bridge = MementoBridge(
            db_path="~/.openclaw/memento/memory.db"
        )
    
    async def process_message(self, user_message):
        # Get context from memory
        context = self.memory_bridge.recall_context(user_message)
        
        # Generate response with context
        response = await self.llm.generate(
            user_message,
            context=context
        )
        
        # Store interaction automatically
        self.memory_bridge.store_interaction(
            user_message,
            response
        )
        
        return response
```

### Option B: Event-Based
```python
# OpenClaw event system
from memento.openclaw_bridge import MementoListener

# Register listener
openclaw.events.on('message:complete', MementoListener())

class MementoListener:
    def on_event(self, event):
        self.store.remember(
            text=f"User: {event.user_msg}\nAgent: {event.response}",
            importance=self._calculate_importance(event),
            tags=self._auto_tag(event)
        )
```

## Implementation

### Step 1: Create Bridge Module
```python
# memento/openclaw_bridge.py
from memento import get_store
from typing import Optional, List, Dict
import json

class OpenClawMemoryBridge:
    """
    Bridge between OpenClaw and Memento.
    Automatically stores interactions and recalls context.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.store = get_store(db_path=db_path)
        self.significance_detector = SignificanceDetector()
    
    def store_interaction(
        self,
        user_message: str,
        agent_response: str,
        session_id: str = "default"
    ) -> Optional[str]:
        """Store conversation to memory."""
        
        # Detect significance
        is_significant, importance = self.significance_detector.detect(
            user_message,
            agent_response
        )
        
        if not is_significant:
            return None
        
        # Format memory
        memory_text = self._format_memory(
            user_message,
            agent_response
        )
        
        # Auto-generate tags
        tags = self._auto_tag(user_message, agent_response)
        
        # Store
        doc_id = self.store.remember(
            text=memory_text,
            importance=importance,
            tags=tags,
            session_id=session_id,
            source="openclaw_auto"
        )
        
        return doc_id
    
    def recall_context(
        self,
        query: str,
        topk: int = 5
    ) -> List[Dict]:
        """Recall relevant context for a query."""
        return self.store.recall(query, topk=topk)
    
    def _format_memory(self, user_msg: str, agent_resp: str) -> str:
        return f"Q: {user_msg}\nA: {agent_resp}"
    
    def _auto_tag(self, user_msg: str, agent_resp: str) -> List[str]:
        # Extract tags from content
        tags = []
        content = (user_msg + " " + agent_resp).lower()
        
        tag_keywords = {
            'decision': ['decided', 'agreed', 'approved', 'plan'],
            'error': ['error', 'bug', 'failed', 'fix'],
            'todo': ['todo', 'task', 'implement', 'create'],
            'question': ['?', 'how', 'what', 'why'],
        }
        
        for tag, keywords in tag_keywords.items():
            if any(kw in content for kw in keywords):
                tags.append(tag)
        
        return tags
```

### Step 2: Significance Detection
```python
class SignificanceDetector:
    """
    Detect if a conversation is worth storing.
    Like human memory - we don't remember everything.
    """
    
    HIGH_SIGNALS = [
        'decision', 'agreed', 'approved', 'rejected',
        'plan', 'architecture', 'design',
        'bug', 'error', 'fix', 'broke',
        'deploy', 'release', 'production'
    ]
    
    MEDIUM_SIGNALS = [
        'implement', 'create', 'add', 'feature',
        'test', 'verify', 'document'
    ]
    
    def detect(self, user_msg: str, agent_resp: str) -> Tuple[bool, float]:
        combined = f"{user_msg} {agent_resp}".lower()
        
        # High significance
        if any(s in combined for s in self.HIGH_SIGNALS):
            return True, 0.85
        
        # Medium significance
        if any(s in combined for s in self.MEDIUM_SIGNALS):
            return True, 0.7
        
        # Questions with answers
        if '?' in user_msg and len(agent_resp) > 50:
            return True, 0.6
        
        # Default: don't store
        return False, 0.0
```

### Step 3: Configuration
```yaml
# ~/.openclaw/memento/config.yaml
openclaw:
  auto_store: true
  storage_threshold: 0.6
  max_memories_per_session: 100
  context_window: 5  # How many memories to recall
```

## Acceptance Criteria
- [ ] Bridge module created
- [ ] OpenClaw can import and use bridge
- [ ] Every conversation auto-stored (if significant)
- [ ] Context automatically recalled
- [ ] No manual intervention required
- [ ] Configurable (can disable auto-store)
- [ ] Echo notifications when storing

## Testing
```python
# Test integration
bridge = OpenClawMemoryBridge()

# Simulate conversation
doc_id = bridge.store_interaction(
    "How do I fix the WiFi driver?",
    "You need to install the bcmwl-kernel-source package..."
)

# Verify stored
assert doc_id is not None

# Recall
results = bridge.recall_context("WiFi fix")
assert len(results) > 0
```

## Related
- #4 (Fix auto-memory - prerequisite)
- #3 (Unify database location)
- Vision: "Fully automatic"
