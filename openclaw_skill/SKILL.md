# Memento Skill for OpenClaw

**Version:** 0.2.2  
**Author:** Rollersrights  
**License:** MIT

## Overview

Memento provides persistent semantic memory for OpenClaw agents. It automatically stores and retrieves relevant context across sessions, enabling long-term memory persistence.

## Features

- **Auto-Store**: Significant conversations are automatically remembered
- **Auto-Retrieve**: Relevant context is retrieved before answering
- **Cross-Session Survival**: Memory persists across restarts
- **Health Monitoring**: Built-in health checks and fallback handling
- **Fast Queries**: Cache warming and background model loading for instant responses

## Installation

The skill is automatically available when Memento is installed:

```bash
pip install -e /home/brett/.openclaw/workspace/memento
```

## Configuration

Environment variables:
- `MEMORY_DB_PATH`: Path to SQLite database (default: `~/.memento/memory.db`)
- `MEMENTO_AUTO_MEMORY`: Enable auto-memory (default: `true`)
- `MEMENTO_WARMUP_ON_START`: Warm cache on startup (default: `true`)

## Usage

### Basic Memory Operations

```python
from openclaw.skills.memento import remember, recall

# Store a memory
remember(
    text="User prefers concise answers",
    importance=0.8,
    tags=["preference", "communication"]
)

# Retrieve memories
results = recall("What does the user prefer?", topk=3)
for r in results:
    print(f"{r.text} (score: {r.score:.2f})")
```

### Auto-Memory Hooks

```python
from openclaw.skills.memento import setup_hooks

# Install hooks for automatic memory management
setup_hooks()
```

### Health Check

```python
from openclaw.skills.memento import health_check

status = health_check()
print(f"Memento status: {status['status']}")
```

## Architecture

```
┌─────────────────────────────────────────┐
│           OpenClaw Agent               │
├─────────────────────────────────────────┤
│  Auto-Store ◄──► Memento Skill ◄──► Auto-Retrieve  │
├─────────────────────────────────────────┤
│  Health Monitor  │  Fallback Handler   │
└─────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Memento Core (Python)          │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐  │
│  │  Store  │ │ Search  │ │  Embed   │  │
│  └─────────┘ └─────────┘ └──────────┘  │
└─────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         SQLite + Embeddings            │
└─────────────────────────────────────────┘
```

## Files

- `__init__.py` - Skill entry point and API
- `memory.py` - Core memory operations
- `SKILL.md` - This documentation

## Related

- Issue #10: OpenClaw skill integration
- PR #5: Resilient memory infrastructure
- RFC-001: Rust architecture (Phase 2)
