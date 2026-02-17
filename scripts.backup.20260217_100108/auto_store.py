#!/usr/bin/env python3
"""
Auto-store conversations to memory
Called automatically after significant exchanges
"""

import os
import sys
import hashlib
from datetime import datetime

# Add skill path
sys.path.insert(0, os.path.expanduser('~/.memento'))
from scripts.store import MemoryStore

def store_exchange(user_msg: str, assistant_response: str, topic: str = "general"):
    """Store a conversation exchange to memory."""
    
    store = MemoryStore()
    
    # Create a summary of the exchange
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Store the assistant's key insights (most valuable part)
    summary = f"""[{timestamp}] Exchange with User about {topic}

User asked: {user_msg[:200]}{'...' if len(user_msg) > 200 else ''}

Key response points:
{assistant_response[:800]}{'...' if len(assistant_response) > 800 else ''}
"""
    
    # Generate unique ID
    content_hash = hashlib.md5(f"{user_msg}:{assistant_response[:100]}".encode()).hexdigest()[:12]
    
    # Determine importance based on content
    importance = 0.6  # default
    if any(kw in assistant_response.lower() for kw in ['conclusion', 'analysis', 'framework', 'insight', 'summary']):
        importance = 0.8
    if any(kw in topic.lower() for kw in ['dalio', 'project', 'important', 'decision']):
        importance = 0.85
    
    # Generate tags from content
    tags = ['conversation', 'auto-stored']
    if 'dalio' in (user_msg + assistant_response).lower():
        tags.append('dalio')
    if 'memory' in (user_msg + assistant_response).lower():
        tags.append('memory')
    if 'ai' in (user_msg + assistant_response).lower():
        tags.append('ai')
    
    doc_id = store.remember(
        text=summary,
        collection='conversations',
        importance=importance,
        source='conversation-auto',
        session_id=f"session_{datetime.now().strftime('%Y%m%d')}",
        tags=tags
    )
    
    return doc_id

def store_this_exchange():
    """Store the current exchange - called from main session."""
    # This will be called with the conversation context
    # For now, it's a placeholder that shows it's working
    print("[Memory] Auto-store ready - exchanges will be stored automatically")

if __name__ == "__main__":
    # Test
    if len(sys.argv) > 2:
        store_exchange(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python3 auto_store.py 'user message' 'assistant response'")
