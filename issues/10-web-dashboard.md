---
title: "[P2] Web dashboard - browse, search, and manage memories"
labels: ["enhancement", "ui", "P2"]
assignees: []
---

## Problem
No visual interface for browsing memories. CLI is good but limited.

Vision: User should be able to see and manage what Memento remembers.

## Proposed Solution

### Option A: Built-in Web Server (Recommended)
```python
# memento/server.py
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

app = FastAPI()

@app.get("/api/memories")
async def list_memories(
    search: str = None,
    collection: str = None,
    limit: int = 50
):
    store = get_store()
    if search:
        return store.recall(search, topk=limit)
    return store.get_recent(n=limit)

@app.get("/api/memories/{memory_id}")
async def get_memory(memory_id: str):
    # Get single memory with associations
    pass

@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: str):
    store = get_store()
    store.delete(memory_id)
    return {"status": "deleted"}

# Serve static files (built-in UI)
app.mount("/", StaticFiles(directory="static"), name="static")
```

### Option B: External Dashboard
Separate project that connects to Memento DB.

## Dashboard Features

### 1. Memory Browser
- List all memories
- Filter by collection, tags, date
- Search with semantic + keyword
- Sort by relevance, date, importance

### 2. Memory Detail View
- Full text
- Metadata (tags, source, importance)
- Associations (related memories)
- Timeline (when remembered)

### 3. Visualizations
- Timeline of memories
- Tag cloud
- Collection breakdown
- Search history

### 4. Management
- Delete memories
- Edit tags/importance
- Merge duplicates
- Export to JSON/Markdown

## Tech Stack Options

### Modern Stack
```
Backend: FastAPI + WebSocket
Frontend: HTMX + Alpine.js (minimal JS)
Or: React/Vue SPA

Pros: Modern, fast
Cons: More dependencies
```

### Simple Stack
```
Backend: Flask
Frontend: Jinja2 templates
JS: Vanilla JS

Pros: Simple, fewer deps
Cons: Less interactive
```

### CLI Dashboard (Enhancement)
```python
# Current: memento dashboard
# Enhanced with more views
```

## UI Mockup

```
┌────────────────────────────────────────────────────────────┐
│  🧠 Memento Dashboard                          [Search...] │
├────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────────────────────────┐ │
│  │ Collections │  │  Memories                            │ │
│  │             │  │                                      │ │
│  │ ◉ All       │  │  💾 Today                            │ │
│  │ ○ Knowledge │  │  ┌────────────────────────────────┐  │ │
│  │ ● Conversations│  │ Q: How do I fix WiFi?          │  │ │
│  │ ○ Tasks     │  │ A: Install bcmwl-kernel-source   │  │ │
│  │             │  │ Tags: #wifi #fix          0.89 ⭐  │  │ │
│  │ Tags        │  └────────────────────────────────┘  │ │
│  │             │  │                                      │ │
│  │ #rust (12)  │  │  💾 Yesterday                        │ │
│  │ #bob (8)    │  │  ┌────────────────────────────────┐  │ │
│  │ #github (5) │  │  Approved RFC-001 for Rust...    │  │ │
│  │             │  │ Tags: #rfc #rust #decision 0.95⭐ │  │ │
│  └─────────────┘  └──────────────────────────────────────┘ │
│                                                             │
│  Stats: 142 memories | 3 collections | Last backup: 2h ago │
└────────────────────────────────────────────────────────────┘
```

## Implementation

### Phase 1: Basic API
- REST endpoints for CRUD
- JSON responses

### Phase 2: Simple UI
- HTML templates
- Basic styling

### Phase 3: Enhanced UI
- HTMX for interactivity
- Real-time search

### Phase 4: Advanced Features
- Visualizations
- Export
- Import

## Acceptance Criteria
- [ ] `memento server` starts web dashboard
- [ ] Browse memories with filters
- [ ] Search memories
- [ ] Delete/edit memories
- [ ] Mobile-friendly
- [ ] Optional: Real-time updates

## Related
- Vision: "Never forgets, works, easy to use"
