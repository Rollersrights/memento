#!/usr/bin/env python3
"""
Intelligent Conversation Memory System
Automatically stores significant exchanges using multi-factor detection
"""

import os
import sys
import re
from datetime import datetime
from typing import Optional, List, Tuple

# Ensure skill is available
sys.path.insert(0, os.path.expanduser('~/.memento'))

class ConversationMemory:
    """Intelligent conversation memory with multi-factor significance detection"""
    
    def __init__(self):
        self.memory_store = None
        self.session_work_log = []  # Track what we've been working on
        
    def init_store(self):
        from scripts.store import MemoryStore
        if self.memory_store is None:
            self.memory_store = MemoryStore()
        return self.memory_store
    
    # === DETECTION LAYERS ===
    
    # Layer 1: Always-store phrases (user explicitly wants this remembered)
    ALWAYS_STORE_PHRASES = [
        'remember this', 'make sure you remember', 'store this',
        'keep this in mind', 'don\'t forget this', 'this is important'
    ]
    
    # Layer 2: Critical action keywords (we're doing work)
    ACTION_KEYWORDS = [
        # Implementation
        'implement', 'fix', 'repair', 'solve', 'resolve', 'build', 'create',
        'develop', 'code', 'script', 'configure', 'setup', 'deploy',
        # Analysis
        'analyze', 'audit', 'review', 'examine', 'investigate', 'assess',
        'diagnose', 'debug', 'troubleshoot', 'evaluate',
        # Changes
        'change', 'modify', 'update', 'edit', 'rewrite', 'refactor',
        'improve', 'optimize', 'enhance', 'upgrade', 'patch',
        # Planning
        'plan', 'design', 'architecture', 'structure', 'organize',
        'strategy', 'approach', 'method', 'solution',
        # Problems
        'issue', 'problem', 'bug', 'error', 'fault', 'defect',
        'broken', 'failing', 'crash', 'exception',
        # Testing
        'test', 'verify', 'validate', 'check', 'confirm', 'ensure',
        # Documentation
        'document', 'write', 'explain', 'describe', 'detail',
        # Critical
        'critical', 'crucial', 'essential', 'vital', 'important',
        'urgent', 'priority', 'key', 'fundamental'
    ]
    
    # Layer 3: Question types that indicate learning/information exchange
    QUESTION_PATTERNS = [
        r'^(what|why|how|when|where|who|which)\s',
        r'^(can you|could you|would you|will you)\s',
        r'^(is it|are they|does it|do they)\s',
        r'explain\s', r'tell me\s', r'show me\s',
        r'what\s+(is|are|does|did|will|would|should|can|could)',
        r'how\s+(do|does|did|can|could|should|to)'
    ]
    
    # Layer 4: Response quality indicators (I'm giving substantial answers)
    QUALITY_INDICATORS = [
        'because', 'therefore', 'however', 'although', 'meanwhile',
        'first', 'second', 'third', 'finally', 'next', 'then',
        'for example', 'such as', 'like', 'specifically',
        'in addition', 'furthermore', 'moreover', 'also',
        'on the other hand', 'conversely', 'alternatively',
        'in conclusion', 'to summarize', 'overall', 'essentially'
    ]
    
    # Layer 5: Technical/Project context
    TECHNICAL_CONTEXT = [
        'database', 'server', 'api', 'code', 'function', 'class', 'method',
        'variable', 'config', 'setting', 'parameter', 'argument',
        'error', 'exception', 'log', 'debug', 'trace',
        'file', 'folder', 'directory', 'path', 'location',
        'install', 'setup', 'configure', 'run', 'execute',
        'python', 'javascript', 'sql', 'bash', 'shell',
        'skill', 'agent', 'memory', 'vector', 'embedding'
    ]
    
    # Layer 6: Deep dive / comprehensive work indicators
    DEEP_DIVE_INDICATORS = [
        'deep dive', 'comprehensive', 'thorough', 'detailed', 'extensive',
        'complete', 'full', 'whole', 'entire', 'all',
        'step by step', 'line by line', 'one by one',
        'systematic', 'methodical', 'rigorous'
    ]
    
    def should_store(self, user_msg: str, response: str) -> Tuple[bool, float, str]:
        """
        Multi-factor significance detection.
        
        Returns: (should_store, confidence_score, reason)
        """
        combined = (user_msg + ' ' + response).lower()
        
        # Layer 1: Explicit remember request (highest priority)
        for phrase in self.ALWAYS_STORE_PHRASES:
            if phrase in combined:
                return True, 1.0, f"explicit_remember:'{phrase}'"
        
        # Short responses are rarely significant (but allow medium ones)
        if len(response) < 40:
            return False, 0.0, "too_short"
        
        score = 0.0
        reasons = []
        
        # Layer 2: Action keywords (we're doing work)
        action_matches = [kw for kw in self.ACTION_KEYWORDS if kw in combined]
        if action_matches:
            score += 0.25 * min(len(action_matches), 4)  # Cap at 4 matches
            reasons.append(f"actions:{len(action_matches)}")
        
        # Layer 3: Question indicates information need
        question_match = any(re.search(pattern, user_msg.lower()) 
                           for pattern in self.QUESTION_PATTERNS)
        if question_match:
            score += 0.15
            reasons.append("question")
        
        # Layer 4: Response has quality structure
        quality_matches = [kw for kw in self.QUALITY_INDICATORS if kw in response.lower()]
        if quality_matches:
            score += 0.15 * min(len(quality_matches), 3)
            reasons.append(f"quality:{len(quality_matches)}")
        
        # Layer 5: Technical context
        tech_matches = [kw for kw in self.TECHNICAL_CONTEXT if kw in combined]
        if tech_matches:
            score += 0.1 * min(len(tech_matches), 3)
            reasons.append(f"technical:{len(tech_matches)}")
        
        # Layer 6: Deep dive indicators
        deep_matches = [kw for kw in self.DEEP_DIVE_INDICATORS if kw in combined]
        if deep_matches:
            score += 0.2
            reasons.append(f"deep_dive:{deep_matches[0]}")
        
        # Layer 7: Length bonuses
        if len(response) > 500:
            score += 0.1
            reasons.append("long_response")
        if len(response) > 1000:
            score += 0.1
            reasons.append("very_long")
        
        # Layer 8: File modification detection
        file_patterns = [
            r'created\s+file', r'updated\s+file', r'modified\s+file',
            r'wrote\s+to', r'edited\s+', r'fixed\s+.*\.py',
            r'implemented\s+.*\.py', r'created\s+.*\.py'
        ]
        file_match = any(re.search(pattern, combined) for pattern in file_patterns)
        if file_match:
            score += 0.3
            reasons.append("file_modified")
        
        # Decision threshold (LOWERED to capture more conversations)
        threshold = 0.15  # Was 0.3 - now captures ~40% more casual chat
        should_store_flag = score >= threshold
        
        reason_str = ','.join(reasons) if reasons else 'low_score'
        return should_store_flag, round(score, 2), reason_str
    
    def calculate_importance(self, user_msg: str, response: str, reason: str) -> float:
        """Calculate importance score (0.5-0.95)"""
        importance = 0.5
        
        # Base on detection confidence
        if 'explicit_remember' in reason:
            importance = 0.95
        elif 'file_modified' in reason:
            importance = 0.85
        elif 'deep_dive' in reason:
            importance = 0.8
        elif 'actions' in reason:
            action_count = int(reason.split(':')[1].split(',')[0])
            importance = 0.6 + (0.05 * min(action_count, 5))
        
        # Boost for very long, detailed responses
        if len(response) > 1500:
            importance += 0.05
        
        # Cap at 0.95
        return min(importance, 0.95)
    
    def detect_topic(self, user_msg: str, response: str) -> str:
        """Enhanced topic detection"""
        content = (user_msg + ' ' + response).lower()
        
        # Priority topics (checked first)
        priority_topics = [
            (['memory', 'vector', 'embedding', 'zvec', 'sqlite', 'store.py'], 
             'Memory System Development'),
            (['auto-store', 'auto_store', 'conversation_memory', 'auto store'], 
             'Auto-Store System'),
            (['dalio', 'world order', 'empire', 'cycle', 'debt'], 
             'Dalio/World Order Analysis'),
            (['skill', 'agent', 'framework'], 
             'Agent Framework'),
            (['mac mini', 'hardware', 'power', 'crash', 'reboot'], 
             'Mac Mini/Hardware Issues'),
            (['samba', 'network', 'share', 'inbox', 'drop folder'], 
             'Network/File Sharing'),
            (['pdf', 'document', 'processor', 'ingest'], 
             'Document Processing'),
            (['cron', 'scheduled', 'automatic', 'backup'], 
             'Automation/Scheduling'),
        ]
        
        for keywords, topic_name in priority_topics:
            if any(kw in content for kw in keywords):
                return topic_name
        
        return 'General Discussion'
    
    def generate_tags(self, user_msg: str, response: str, topic: str) -> List[str]:
        """Generate contextual tags"""
        tags = ['conversation', 'auto-stored']
        content = (user_msg + ' ' + response).lower()
        
        # Topic-based tags
        topic_tags = {
            'Memory System Development': ['memory', 'database'],
            'Auto-Store System': ['auto-store', 'configuration'],
            'Dalio/World Order Analysis': ['dalio', 'macro'],
            'Agent Framework': ['skill', 'agent'],
            'Mac Mini/Hardware Issues': ['hardware', 'mac_mini'],
            'Network/File Sharing': ['network', 'samba'],
            'Document Processing': ['documents', 'rag'],
            'Automation/Scheduling': ['cron', 'automation'],
        }
        
        if topic in topic_tags:
            tags.extend(topic_tags[topic])
        
        # Action-based tags
        if any(kw in content for kw in ['fix', 'repair', 'solve', 'debug']):
            tags.append('fix')
        if any(kw in content for kw in ['implement', 'build', 'create', 'develop']):
            tags.append('implementation')
        if any(kw in content for kw in ['analyze', 'audit', 'review', 'examine']):
            tags.append('analysis')
        if any(kw in content for kw in ['plan', 'design', 'architecture']):
            tags.append('planning')
        
        return list(set(tags))  # Deduplicate
    
    def store(self, user_msg: str, assistant_response: str) -> Optional[str]:
        """
        Store exchange if significant.
        Returns doc_id if stored, None if skipped.
        """
        should_store_flag, confidence, reason = self.should_store(
            user_msg, assistant_response
        )
        
        if not should_store_flag:
            return None
        
        try:
            memory_store = self.init_store()
            
            # Generate metadata
            topic = self.detect_topic(user_msg, assistant_response)
            importance = self.calculate_importance(user_msg, assistant_response, reason)
            tags = self.generate_tags(user_msg, assistant_response, topic)
            
            # Create rich summary
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Truncate intelligently
            user_short = user_msg[:120] + '...' if len(user_msg) > 120 else user_msg
            response_short = assistant_response[:600] + '...' if len(assistant_response) > 600 else assistant_response
            
            summary = f"""[{timestamp}] {topic} (confidence: {confidence}, reason: {reason})

Q: {user_short}

A: {response_short}"""
            
            doc_id = memory_store.remember(
                text=summary,
                collection='conversations',
                importance=importance,
                source='conversation-auto',
                session_id=f"auto_{datetime.now().strftime('%Y%m%d_%H%M')}",
                tags=tags
            )
            
            # Log for debugging
            print(f"[Memory] Stored: {topic} (score:{confidence}, {reason})")
            
            return doc_id
            
        except Exception as e:
            print(f"[Memory] Auto-store ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None

# Global instance
_memory = ConversationMemory()

def auto_store(user_msg: str, assistant_response: str) -> Optional[str]:
    """Public API for auto-storing"""
    return _memory.store(user_msg, assistant_response)

def test_detection(user_msg: str, response: str):
    """Test the detection logic without storing"""
    mem = ConversationMemory()
    should, score, reason = mem.should_store(user_msg, response)
    topic = mem.detect_topic(user_msg, response)
    print(f"Should store: {should}")
    print(f"Score: {score}")
    print(f"Reason: {reason}")
    print(f"Topic: {topic}")
    return should, score, reason

if __name__ == "__main__":
    # Test examples
    test_cases = [
        (
            "ok why haven't you got any memories",
            "Good catch. Looking at what came back... [detailed explanation of memory system issues]"
        ),
        (
            "ok, we need to improve the auto-store",
            "Let's enhance the auto-store with better significance detection... [implementation details]"
        ),
        (
            "hi",
            "Hello! How can I help?"
        ),
        (
            "remember this: the example password is hunter2",
            "I'll store that securely."
        )
    ]
    
    print("Testing detection logic:\n")
    for user, resp in test_cases:
        print(f"User: {user[:50]}...")
        should, score, reason = test_detection(user, resp)
        print(f"→ Store: {should} | Score: {score} | {reason}\n")
