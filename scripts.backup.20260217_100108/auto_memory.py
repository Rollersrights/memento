#!/usr/bin/env python3
"""
Memento Auto-Store System
Automatically stores significant conversations to Memento
Survives session restarts, model reboots
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

# Ensure Memento is available
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/skills/memory-zvec/scripts'))

class AutoMemory:
    """Automatic memory storage with significance detection."""
    
    def __init__(self):
        self.store = None
        self._init_store()
        
    def _init_store(self):
        """Initialize Memento store with fallback."""
        try:
            from store import MemoryStore
            self.store = MemoryStore()
            self.db_path = self.store.db_path
            self._log_status(f"✅ Memento initialized: {self.db_path}")
        except Exception as e:
            self._log_status(f"❌ Memento init failed: {e}")
            self.store = None
            
    def _log_status(self, msg):
        """Log to file for persistence across sessions."""
        log_file = Path.home() / ".openclaw/memory/automemory.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    
    def is_significant(self, text, response):
        """Detect if conversation is worth storing."""
        combined = f"{text} {response}".lower()
        
        # High significance indicators
        if any(kw in combined for kw in [
            'decision', 'agreed', 'approved', 'rejected', 'deferred',
            'rfc', 'architecture', 'design', 'plan', 'roadmap',
            'bug', 'fix', 'error', 'failed', 'broke',
            'release', 'deploy', 'production', 'update',
            'bob', 'collaboration', 'team', 'roles',
            'performance', 'benchmark', 'optimization'
        ]):
            return True, 0.85
            
        # Medium significance
        if any(kw in combined for kw in [
            'implement', 'create', 'add', 'feature',
            'test', 'verify', 'check', 'validate',
            'document', 'readme', 'wiki'
        ]):
            return True, 0.7
            
        # Code/technical
        if re.search(r'\b(def |class |import |function|script)\b', combined):
            return True, 0.6
            
        return False, 0.0
    
    def save(self, query, response, context=None):
        """Store significant conversation to Memento."""
        if not self.store:
            self._init_store()
            if not self.store:
                return False
        
        is_sig, importance = self.is_significant(query, response)
        if not is_sig:
            return False
        
        try:
            # Format memory text
            memory_text = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] "
            memory_text += f"Q: {query}\nA: {response[:200]}"
            if context:
                memory_text += f"\nContext: {context}"
            
            # Auto-detect tags
            tags = []
            combined = f"{query} {response}".lower()
            tag_map = {
                'rfc': ['rfc', 'architecture', 'proposal'],
                'bob': ['bob', 'collaboration'],
                'brett': ['brett', 'user'],
                'performance': ['benchmark', 'speed', 'cache', 'optimization'],
                'github': ['pr', 'issue', 'merge', 'branch', 'workflow'],
                'bug': ['bug', 'error', 'fail', 'crash', 'fix'],
                'feature': ['feature', 'implement', 'add', 'create'],
                'memento': ['memory', 'memento', 'store', 'recall'],
                'rust': ['rust', 'cargo', 'onnx']
            }
            for tag, keywords in tag_map.items():
                if any(kw in combined for kw in keywords):
                    tags.append(tag)
            
            # Store to Memento
            self.store.remember(
                memory_text,
                importance=importance,
                tags=list(set(tags)) if tags else ['conversation'],
                source='auto_store'
            )
            
            self._log_status(f"✅ Stored: {query[:60]}...")
            return True
            
        except Exception as e:
            self._log_status(f"❌ Store failed: {e}")
            self._handle_failure(e)
            return False
    
    def _handle_failure(self, error):
        """Handle Memento failure - rollback and alert."""
        self._log_status(f"🔴 CRITICAL: Memento failure - {error}")
        
        # Try rollback
        try:
            backup = Path.home() / ".openclaw/memory/memory.db.backup"
            db = Path.home() / ".openclaw/memory/memory.db"
            if backup.exists():
                import shutil
                shutil.copy(backup, db)
                self._log_status("✅ Rollback completed")
        except Exception as e:
            self._log_status(f"❌ Rollback failed: {e}")
        
        # Create GitHub issue (would need API call in real scenario)
        self._log_status("📝 GitHub issue should be created: Memento failure")
    
    def recall(self, query, topk=5):
        """Recall from Memento with fallback."""
        if not self.store:
            self._init_store()
        
        if not self.store:
            return []
        
        try:
            return self.store.recall(query, topk=topk)
        except Exception as e:
            self._log_status(f"❌ Recall failed: {e}")
            return []
    
    def backup(self):
        """Create backup of memory database."""
        try:
            import shutil
            from datetime import datetime
            
            db = Path.home() / ".openclaw/memory/memory.db"
            backup = Path.home() / f".openclaw/memory/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            if db.exists():
                shutil.copy(db, backup)
                self._log_status(f"✅ Backup created: {backup}")
                return True
        except Exception as e:
            self._log_status(f"❌ Backup failed: {e}")
        return False

# Global instance for session persistence
_auto_memory = None

def get_memory():
    """Get or create auto-memory instance."""
    global _auto_memory
    if _auto_memory is None:
        _auto_memory = AutoMemory()
    return _auto_memory

def store_interaction(query, response, context=None):
    """Store interaction to Memento."""
    mem = get_memory()
    return mem.save(query, response, context)

def recall_memories(query, topk=5):
    """Recall memories from Memento."""
    mem = get_memory()
    return mem.recall(query, topk)

def backup_memories():
    """Backup memory database."""
    mem = get_memory()
    return mem.backup()

if __name__ == "__main__":
    # Test
    print("Testing AutoMemory...")
    mem = get_memory()
    
    # Test store
    store_interaction(
        "What did we decide about Rust?",
        "RFC-001 approved with Phase 1 and Phase 2a only"
    )
    
    # Test recall
    results = recall_memories("Rust architecture", topk=3)
    print(f"Recalled {len(results)} memories")
    for r in results:
        print(f"  - {r['text'][:80]}...")
