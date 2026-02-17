#!/usr/bin/env python3
"""
Session Log Watcher for Auto-Store (Option 2)
Reads session transcript, stores significant exchanges retroactively
Lightweight - runs via cron every few minutes
"""

import os
import sys
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path

# Add skill path
sys.path.insert(0, os.path.expanduser('~/.memento'))
from scripts.conversation_memory import ConversationMemory

class SessionLogWatcher:
    """Watches session logs and stores significant exchanges"""
    
    def __init__(self):
        self.memory = ConversationMemory()
        self.state_file = Path.home() / ".memento" / ".session_watcher_state"
        # Note: session_dir should be configured for your specific agent framework
        self.session_dir = Path.home() / ".memento" / "sessions"
        
    def get_latest_session_file(self) -> Path:
        """Find the most recent session file (json or jsonl)"""
        if not self.session_dir.exists():
            return None
        
        # Look for both .json and .jsonl files
        session_files = list(self.session_dir.glob("*.json")) + list(self.session_dir.glob("*.jsonl"))
        if not session_files:
            return None
        
        # Get most recent by mtime, exclude .lock files
        session_files = [f for f in session_files if not f.name.endswith('.lock')]
        if not session_files:
            return None
        
        return max(session_files, key=lambda p: p.stat().st_mtime)
    
    def load_processed_hashes(self) -> set:
        """Load hashes of already processed exchanges"""
        if not self.state_file.exists():
            return set()
        
        try:
            with open(self.state_file) as f:
                data = json.load(f)
                return set(data.get('processed_hashes', []))
        except:
            return set()
    
    def save_processed_hashes(self, hashes: set):
        """Save hashes of processed exchanges"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                'last_run': datetime.now().isoformat(),
                'processed_hashes': list(hashes)
            }, f)
    
    def extract_exchanges(self, session_file: Path) -> list:
        """Extract user/assistant exchanges from session log (OpenClaw format)"""
        entries = []
        
        try:
            # Handle JSON Lines format (.jsonl)
            if session_file.suffix == '.jsonl':
                with open(session_file) as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                entries.append(entry)
                            except:
                                continue
            else:
                # Handle regular JSON format
                with open(session_file) as f:
                    data = json.load(f)
                    entries = data.get('messages', [])
        except Exception as e:
            print(f"[Watcher] Error reading session file: {e}")
            return []
        
        exchanges = []
        i = 0
        
        # Process OpenClaw format: {"type": "message", "message": {"role": "...", "content": [...]}}
        while i < len(entries):
            entry = entries[i]
            
            if entry.get('type') != 'message':
                i += 1
                continue
            
            msg = entry.get('message', {})
            if msg.get('role') != 'user':
                i += 1
                continue
            
            # Extract user message content
            user_content = msg.get('content', [])
            if isinstance(user_content, list):
                user_text = ' '.join(c.get('text', '') for c in user_content if isinstance(c, dict))
            else:
                user_text = str(user_content)
            
            # Look ahead for assistant response (search remaining entries)
            j = i + 1
            while j < len(entries):
                if entries[j].get('type') != 'message':
                    j += 1
                    continue
                
                next_msg = entries[j].get('message', {})
                if next_msg.get('role') == 'assistant':
                    assistant_content = next_msg.get('content', [])
                    if isinstance(assistant_content, list):
                        # Handle array of content objects (may include tool calls, thinking, etc.)
                        text_parts = []
                        for c in assistant_content:
                            if isinstance(c, dict):
                                if c.get('type') == 'text':
                                    text_parts.append(c.get('text', ''))
                                elif 'text' in c:
                                    text_parts.append(c.get('text', ''))
                        assistant_text = ' '.join(text_parts)
                    else:
                        assistant_text = str(assistant_content)
                    
                    # Skip empty responses but keep shorter ones now (threshold lowered)
                    if len(assistant_text.strip()) < 30:
                        j += 1
                        continue
                    
                    # Create hash for deduplication
                    content_hash = hashlib.md5(
                        f"{user_text[:100]}:{assistant_text[:100]}".encode()
                    ).hexdigest()[:16]
                    
                    exchanges.append({
                        'user': user_text,
                        'assistant': assistant_text,
                        'hash': content_hash,
                        'timestamp': entry.get('timestamp', datetime.now().isoformat())
                    })
                    i = j  # Move to after this assistant message
                    break
                elif next_msg.get('role') == 'user':
                    # Found another user message without assistant response
                    break
                j += 1
            
            i += 1
        
        return exchanges
    
    def process_new_exchanges(self, max_per_run: int = 10) -> int:
        """
        Process new exchanges from session log.
        Returns number stored.
        """
        session_file = self.get_latest_session_file()
        if not session_file:
            print("[Watcher] No session file found")
            return 0
        
        # Load already processed hashes
        processed = self.load_processed_hashes()
        
        # Extract all exchanges
        exchanges = self.extract_exchanges(session_file)
        
        # Filter to new ones
        new_exchanges = [e for e in exchanges if e['hash'] not in processed]
        
        if not new_exchanges:
            print("[Watcher] No new exchanges to process")
            return 0
        
        print(f"[Watcher] Found {len(new_exchanges)} new exchanges")
        
        stored_count = 0
        for exchange in new_exchanges[:max_per_run]:  # Limit per run
            try:
                # Use the conversation memory to check significance and store
                should_store, confidence, reason = self.memory.should_store(
                    exchange['user'], exchange['assistant']
                )
                
                if should_store:
                    doc_id = self.memory.store(
                        exchange['user'], 
                        exchange['assistant']
                    )
                    if doc_id:
                        print(f"  Stored: {doc_id[:8]}... (score:{confidence}, {reason})")
                        stored_count += 1
                
                # Mark as processed either way
                processed.add(exchange['hash'])
                
            except Exception as e:
                print(f"  Error processing exchange: {e}")
                continue
        
        # Save state
        self.save_processed_hashes(processed)
        
        print(f"[Watcher] Stored {stored_count}/{len(new_exchanges[:max_per_run])} exchanges")
        return stored_count

def main():
    """Main entry point for cron"""
    print(f"[{datetime.now().strftime('%H:%M')}] Session Watcher starting...")
    
    watcher = SessionLogWatcher()
    count = watcher.process_new_exchanges(max_per_run=20)  # Process more per run
    
    if count > 0:
        print(f"✅ Stored {count} new memories")
    else:
        print("ℹ️ No new memories to store")
    
    return count

if __name__ == "__main__":
    main()
