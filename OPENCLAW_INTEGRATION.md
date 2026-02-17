# OpenClaw Integration Guide

## Quick Setup

### 1. Auto-store all conversations

Add to OpenClaw's message handler (in your OpenClaw config or main loop):

```python
from memento.openclaw_bridge import store_conversation, recall_for_context

# After each agent response:
memory_id = store_conversation(
    user_msg=user_message,
    agent_response=agent_response,
    channel=channel_name,
    agent_id=agent_id
)

# To include context in agent's prompt:
relevant_memories = recall_for_context(user_message, topk=3)
context_text = "\\n".join([m.text for m in relevant_memories])
prompt = f"Context: {context_text}\\n\\nUser: {user_message}"
```

### 2. Import the bridge in OpenClaw

Add to OpenClaw's startup:

```python
import sys
sys.path.insert(0, '/home/brett/.openclaw/workspace/memento')
from memento.openclaw_bridge import get_bridge

# Initialize
bridge = get_bridge(auto_store=True)
```

### 3. Verification

Test that it's working:
```bash
cd /home/brett/.openclaw/workspace/memento
python3 memento/openclaw_bridge.py
```

Should store a test memory and recall it.

## Features

- **Auto-importance**: Calculates importance based on content
- **Auto-tags**: Detects tags like github, bug, feature, etc.
- **Session tracking**: Groups conversations by session
- **Context recall**: Get relevant memories for any query

## Disable Auto-store

```python
bridge = get_bridge(auto_store=False)
```
