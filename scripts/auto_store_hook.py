#!/usr/bin/env python3
"""
Auto-store hook for OpenClaw
This module provides the interface for automatic conversation storage
"""

import os
import sys

# Ensure skill is available  
sys.path.insert(0, os.path.expanduser('~/.memento'))

from scripts.conversation_memory import ConversationMemory

# Configuration
AUTO_STORE_ENABLED = os.environ.get('AUTO_STORE', 'true').lower() == 'true'
ECHO_NOTIFICATIONS = os.environ.get('MEMORY_ECHO', 'true').lower() == 'true'

# Initialize conversation memory for significance detection
_conversation_memory = ConversationMemory()

def _echo_notification(user_msg: str, response: str, doc_id: str, confidence: float, reason: str):
    """Print inline notification when memory is stored"""
    if not ECHO_NOTIFICATIONS:
        return
    
    # Create compact preview (first 60 chars of user message)
    preview = user_msg[:60].replace('\n', ' ')
    if len(user_msg) > 60:
        preview += "..."
    
    # Use emoji for visual distinction, write to stderr so it doesn't pollute stdout
    icon = "💾"
    source_tag = "[explicit]" if confidence >= 0.9 else "[auto]"
    
    import sys
    print(f"{icon} Memory stored {source_tag}: \"{preview}\" (confidence: {confidence:.2f})", 
          file=sys.stderr, flush=True)

def store_exchange(user_msg: str, assistant_response: str, force: bool = False) -> str:
    """
    Store a conversation exchange.
    
    Args:
        user_msg: The user's message
        assistant_response: My response
        force: If True, store regardless of significance
    
    Returns:
        doc_id if stored, empty string if skipped
    """
    if not AUTO_STORE_ENABLED and not force:
        return ""
    
    # Handle None/empty
    if not user_msg or not assistant_response:
        return ""
    
    try:
        # Check significance first (for notification)
        should_store, confidence, reason = _conversation_memory.should_store(
            user_msg, assistant_response
        )
        
        # Force overrides significance check
        if force:
            should_store = True
            confidence = 1.0
            reason = "explicit_force"
        
        if not should_store:
            return ""
        
        # Store the memory
        doc_id = _conversation_memory.store(user_msg, assistant_response)
        
        if doc_id:
            # Echo notification
            _echo_notification(user_msg, assistant_response, doc_id, confidence, reason)
        
        return doc_id or ""
        
    except Exception as e:
        # Never let memory errors break the conversation
        print(f"[AutoStore] Silent error: {e}")
        return ""

def enable_auto_store():
    """Enable automatic storage"""
    global AUTO_STORE_ENABLED
    AUTO_STORE_ENABLED = True
    print("[AutoStore] Enabled")

def disable_auto_store():
    """Disable automatic storage"""
    global AUTO_STORE_ENABLED
    AUTO_STORE_ENABLED = False
    print("[AutoStore] Disabled")

def is_enabled() -> bool:
    """Check if auto-store is enabled"""
    return AUTO_STORE_ENABLED

def enable_echo():
    """Enable echo notifications"""
    global ECHO_NOTIFICATIONS
    ECHO_NOTIFICATIONS = True
    print("[AutoStore] Echo notifications enabled")

def disable_echo():
    """Disable echo notifications"""
    global ECHO_NOTIFICATIONS
    ECHO_NOTIFICATIONS = False
    print("[AutoStore] Echo notifications disabled")

# Hook function that can be called after each exchange
def after_exchange(user_msg: str, assistant_response: str):
    """
    Hook to call after every exchange.
    Automatically decides whether to store based on significance.
    """
    return store_exchange(user_msg, assistant_response)

if __name__ == "__main__":
    # Test the hook
    print("Auto-store hook ready")
    print(f"Status: {'enabled' if is_enabled() else 'disabled'}")
    print()
    print("Usage:")
    print("  from scripts.auto_store_hook import after_exchange")
    print("  after_exchange(user_msg, assistant_response)")
