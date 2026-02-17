#!/usr/bin/env python3
"""
OpenClaw Bridge - Auto-store every conversation to Memento
Integrates with OpenClaw to automatically capture interactions.
"""

import os
import sys
from typing import Optional, Dict, Any
from datetime import datetime

# Ensure memento is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class OpenClawMemoryBridge:
    """Bridge between OpenClaw and Memento memory system."""
    
    def __init__(self, auto_store: bool = True, min_importance: float = 0.3):
        """
        Initialize the bridge.
        
        Args:
            auto_store: Whether to auto-store conversations
            min_importance: Minimum importance for auto-stored memories
        """
        self.auto_store = auto_store
        self.min_importance = min_importance
        self._store = None
        self._session_id = datetime.now().strftime("%Y-%m-%d-%H%M")
        
    def _get_store(self):
        """Lazy load the memory store."""
        if self._store is None:
            from memento.store import get_store
            self._store = get_store()
        return self._store
    
    def store_interaction(self, 
                         user_message: str, 
                         agent_response: str,
                         context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Store a conversation interaction to Memento.
        
        Args:
            user_message: What the user said
            agent_response: What the agent replied
            context: Additional context (channel, agent name, etc.)
            
        Returns:
            Memory ID if stored, None if skipped
        """
        if not self.auto_store:
            return None
            
        # Skip trivial messages
        if len(user_message.strip()) < 3:
            return None
            
        # Auto-calculate importance based on content
        importance = self._calculate_importance(user_message, agent_response)
        
        if importance < self.min_importance:
            return None
            
        # Format memory text
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        memory_text = f"[{timestamp}] Q: {user_message}\nA: {agent_response[:500]}"
        
        # Auto-detect tags
        tags = self._detect_tags(user_message + " " + agent_response)
        
        # Store it
        try:
            store = self._get_store()
            memory_id = store.remember(
                text=memory_text,
                importance=importance,
                tags=tags,
                source='openclaw',
                session_id=self._session_id
            )
            return memory_id
        except Exception as e:
            print(f"[OpenClawBridge] Storage failed: {e}", file=sys.stderr)
            return None
    
    def _calculate_importance(self, user_msg: str, agent_response: str) -> float:
        """Auto-calculate importance score."""
        combined = f"{user_msg} {agent_response}".lower()
        importance = self.min_importance
        
        # High importance keywords
        high_keywords = ['fix', 'bug', 'error', 'critical', 'deploy', 'production',
                        'decision', 'agreed', 'approved', 'rejected', 'architecture',
                        'design', 'security', 'password', 'token', 'secret']
        if any(kw in combined for kw in high_keywords):
            importance = 0.8
            
        # Medium importance keywords
        med_keywords = ['implement', 'create', 'add', 'feature', 'test', 'verify',
                       'github', 'pr', 'merge', 'issue', 'milestone']
        if any(kw in combined for kw in med_keywords):
            importance = max(importance, 0.6)
            
        # Length-based importance (substantial conversations)
        if len(agent_response) > 500:
            importance = max(importance, 0.5)
            
        return min(importance, 1.0)
    
    def _detect_tags(self, text: str) -> list:
        """Auto-detect relevant tags."""
        text = text.lower()
        tags = ['conversation']
        
        tag_map = {
            'github': ['github', 'pr', 'issue', 'merge', 'branch'],
            'bug': ['bug', 'error', 'fail', 'crash', 'fix'],
            'feature': ['feature', 'implement', 'add', 'create'],
            'memento': ['memento', 'memory', 'store', 'recall'],
            'rust': ['rust', 'cargo', 'onnx'],
            'performance': ['speed', 'fast', 'slow', 'optimize', 'cache'],
            'security': ['security', 'password', 'token', 'secret', 'auth'],
            'brett': ['brett'],
            'bob': ['bob', 'rita'],
        }
        
        for tag, keywords in tag_map.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)
                
        return list(set(tags))
    
    def recall_context(self, query: str, topk: int = 3) -> list:
        """
        Recall relevant memories for context.
        
        Args:
            query: Search query
            topk: Number of results
            
        Returns:
            List of relevant memories
        """
        try:
            store = self._get_store()
            return store.recall(query, topk=topk)
        except Exception as e:
            print(f"[OpenClawBridge] Recall failed: {e}", file=sys.stderr)
            return []


# Global bridge instance
_bridge_instance = None

def get_bridge(auto_store: bool = True) -> OpenClawMemoryBridge:
    """Get or create the global bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = OpenClawMemoryBridge(auto_store=auto_store)
    return _bridge_instance


def store_conversation(user_msg: str, agent_response: str, **context) -> Optional[str]:
    """Convenience function to store a conversation."""
    bridge = get_bridge()
    return bridge.store_interaction(user_msg, agent_response, context)


def recall_for_context(query: str, topk: int = 3) -> list:
    """Convenience function to recall memories."""
    bridge = get_bridge()
    return bridge.recall_context(query, topk)


if __name__ == "__main__":
    # Test the bridge
    print("Testing OpenClaw Bridge...")
    
    # Store a test interaction
    mid = store_conversation(
        "What did we decide about the database location?",
        "We unified everything to ~/.openclaw/memento/ for single source of truth."
    )
    print(f"Stored: {mid}")
    
    # Recall relevant memories
    results = recall_for_context("database location", topk=3)
    print(f"\nRecalled {len(results)} memories:")
    for r in results:
        print(f"  - {r.text[:60]}...")
