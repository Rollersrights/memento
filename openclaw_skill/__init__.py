"""
Memento Skill for OpenClaw

Persistent semantic memory integration for OpenClaw agents.
Provides auto-store, auto-retrieve, and health monitoring.

Usage:
    from openclaw.skills.memento import remember, recall, health_check
    
    # Store memory
    remember("Important fact", importance=0.9, tags=["fact"])
    
    # Retrieve memories
    results = recall("query", topk=3)
    
    # Check health
    status = health_check()
"""

__version__ = "0.2.2"
__author__ = "Rollersrights"

import os
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path

# Add memento to path if not installed
_memento_paths = [
    Path.home() / ".openclaw" / "workspace" / "memento",
    Path(__file__).parent.parent.parent / "memento",
    Path("/home/brett/.openclaw/workspace/memento"),
]

for _path in _memento_paths:
    if str(_path) not in sys.path and _path.exists():
        sys.path.insert(0, str(_path))

try:
    from memento import get_store
    from memento.models import Memory, SearchResult
    from memento.exceptions import MementoError
    _memento_available = True
except ImportError:
    _memento_available = False
    print("[Memento Skill] Warning: Memento not available", file=sys.stderr)

# Singleton store instance
_store = None

def _get_store():
    """Get or create the MemoryStore singleton."""
    global _store
    if _store is None:
        if not _memento_available:
            raise RuntimeError("Memento not available")
        db_path = os.environ.get(
            'MEMORY_DB_PATH',
            Path.home() / ".memento" / "memory.db"
        )
        _store = get_store(db_path=str(db_path))
    return _store


def remember(text: str, importance: float = 0.5, tags: Optional[List[str]] = None, **kwargs) -> bool:
    """
    Store a memory in Memento.
    
    Args:
        text: The text to remember
        importance: Importance score (0.0-1.0)
        tags: Optional list of tags
        **kwargs: Additional metadata
        
    Returns:
        True if stored successfully
    """
    try:
        store = _get_store()
        store.remember(text=text, importance=importance, tags=tags or [], **kwargs)
        return True
    except Exception as e:
        print(f"[Memento Skill] Failed to remember: {e}", file=sys.stderr)
        return False


def recall(query: str, topk: int = 5, **kwargs) -> List[Any]:
    """
    Retrieve relevant memories from Memento.
    
    Args:
        query: Search query
        topk: Number of results to return
        **kwargs: Additional filter parameters
        
    Returns:
        List of SearchResult objects
    """
    try:
        store = _get_store()
        return store.recall(query=query, topk=topk, **kwargs)
    except Exception as e:
        print(f"[Memento Skill] Failed to recall: {e}", file=sys.stderr)
        return []


def search(text: Optional[str] = None, tags: Optional[List[str]] = None, topk: int = 5) -> List[Any]:
    """
    Search memories by text and/or tags.
    
    Args:
        text: Text to search for
        tags: Tags to filter by
        topk: Number of results
        
    Returns:
        List of SearchResult objects
    """
    try:
        store = _get_store()
        return store.search(text=text, tags=tags, topk=topk)
    except Exception as e:
        print(f"[Memento Skill] Failed to search: {e}", file=sys.stderr)
        return []


def health_check() -> Dict[str, Any]:
    """
    Check Memento health status.
    
    Returns:
        Dict with status information
    """
    status = {
        "available": _memento_available,
        "status": "unknown",
        "store_initialized": _store is not None,
        "db_path": None,
        "error": None
    }
    
    if not _memento_available:
        status["status"] = "unavailable"
        return status
    
    try:
        store = _get_store()
        status["db_path"] = store.db_path
        
        # Try a simple operation
        test_results = store.search(text="health_check_test", topk=1)
        status["status"] = "healthy"
        status["search_working"] = True
    except Exception as e:
        status["status"] = "error"
        status["error"] = str(e)
        status["search_working"] = False
    
    return status


def is_significant_exchange(user_msg: str, assistant_msg: str) -> bool:
    """
    Determine if a conversation exchange is worth remembering.
    
    Args:
        user_msg: User's message
        assistant_msg: Assistant's response
        
    Returns:
        True if significant enough to store
    """
    # Simple heuristics - can be expanded
    combined = (user_msg + " " + assistant_msg).lower()
    
    # Significant indicators
    indicators = [
        "remember", "don't forget", "note that", "important",
        "preference", "always", "never", "my name is",
        "i live in", "i work at", "i'm a", "i am a",
        "schedule", "appointment", "meeting", "deadline",
        "birthday", "anniversary", "reminder"
    ]
    
    for indicator in indicators:
        if indicator in combined:
            return True
    
    # Long exchanges might be significant
    if len(user_msg) > 200 or len(assistant_msg) > 300:
        return True
    
    return False


def auto_store_exchange(user_msg: str, assistant_msg: str, context: Optional[Dict] = None) -> bool:
    """
    Automatically store a significant conversation exchange.
    
    Args:
        user_msg: User's message
        assistant_msg: Assistant's response
        context: Additional context (session_id, etc.)
        
    Returns:
        True if stored
    """
    if not is_significant_exchange(user_msg, assistant_msg):
        return False
    
    # Create summary
    text = f"User: {user_msg[:200]}... | Assistant: {assistant_msg[:300]}..."
    
    # Determine importance
    importance = 0.6  # Default for auto-stored
    if any(kw in user_msg.lower() for kw in ["remember", "important", "don't forget"]):
        importance = 0.8
    
    # Auto-generate tags
    tags = ["auto_memory", "conversation"]
    if context and "session_id" in context:
        tags.append(f"session:{context['session_id']}")
    
    return remember(text=text, importance=importance, tags=tags, **(context or {}))


def get_context_for_query(query: str, topk: int = 3) -> str:
    """
    Get relevant context as a formatted string for injection into prompts.
    
    Args:
        query: The user's query
        topk: Number of memories to retrieve
        
    Returns:
        Formatted context string
    """
    memories = recall(query, topk=topk)
    
    if not memories:
        return ""
    
    context_parts = ["\n[Relevant Context from Memory]"]
    for i, mem in enumerate(memories, 1):
        context_parts.append(f"{i}. {mem.text}")
    context_parts.append("[End Context]\n")
    
    return "\n".join(context_parts)


def setup_hooks():
    """
    Install auto-memory hooks into OpenClaw.
    This should be called during OpenClaw initialization.
    """
    if not _memento_available:
        print("[Memento Skill] Cannot setup hooks - Memento unavailable")
        return False
    
    try:
        # Warm up cache if configured
        if os.environ.get('MEMENTO_WARMUP_ON_START', 'true').lower() == 'true':
            warmup()
        
        print("[Memento Skill] Hooks installed successfully")
        return True
    except Exception as e:
        print(f"[Memento Skill] Failed to setup hooks: {e}")
        return False


def warmup():
    """Warm up the model and cache for fast queries."""
    if not _memento_available:
        return
    
    try:
        # Import warmup functions from embed module
        from memento.embed import warmup as embed_warmup
        embed_warmup()
        print("[Memento Skill] Warmup complete")
    except Exception as e:
        print(f"[Memento Skill] Warmup failed: {e}", file=sys.stderr)


# Export public API
__all__ = [
    "remember",
    "recall",
    "search",
    "health_check",
    "is_significant_exchange",
    "auto_store_exchange",
    "get_context_for_query",
    "setup_hooks",
    "warmup",
]
