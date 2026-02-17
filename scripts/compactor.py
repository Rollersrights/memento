#!/usr/bin/env python3
"""
Memory Compaction System
Summarizes old memories to reduce storage while preserving key information
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Add skill path
sys.path.insert(0, os.path.expanduser('~/.memento'))

@dataclass
class CompactionStats:
    """Statistics from a compaction run."""
    memories_scanned: int
    memories_compacted: int
    summaries_created: int
    bytes_saved: int
    topics_compacted: List[str]

class MemoryCompactor:
    """
    Compacts old memories by summarizing them.
    
    Strategy:
    1. Find memories older than threshold (e.g., 30 days)
    2. Group by collection/topic
    3. Summarize groups using lightweight local model or extractive summarization
    4. Replace detailed memories with summaries
    5. Mark summaries with high importance to preserve them
    """
    
    def __init__(
        self,
        store=None,
        age_threshold_days: int = 30,
        min_memories_to_compact: int = 5,
        compact_importance_threshold: float = 0.6,  # Don't compact high-importance
        summary_importance: float = 0.85,  # Summaries are important
        dry_run: bool = False
    ):
        from scripts.store import MemoryStore
        self.store = store or MemoryStore()
        
        self.age_threshold_days = age_threshold_days
        self.min_memories_to_compact = min_memories_to_compact
        self.compact_importance_threshold = compact_importance_threshold
        self.summary_importance = summary_importance
        self.dry_run = dry_run
        
        self.cutoff_timestamp = int(time.time()) - (age_threshold_days * 86400)
    
    def find_compactable_memories(self) -> List[Dict[str, Any]]:
        """
        Find memories that are candidates for compaction.
        
        Criteria:
        - Older than age_threshold_days
        - Not already a summary
        - Importance <= compact_importance_threshold
        - Not explicitly protected
        """
        query = """
            SELECT id, text, timestamp, source, collection, importance, tags
            FROM memories
            WHERE timestamp < ?
            AND importance <= ?
            AND (tags IS NULL OR tags NOT LIKE '%compacted%')
            AND (tags IS NULL OR tags NOT LIKE '%summary%')
            AND (tags IS NULL OR tags NOT LIKE '%protected%')
            ORDER BY timestamp ASC
        """
        
        cursor = self.store.conn.execute(query, (
            self.cutoff_timestamp,
            self.compact_importance_threshold
        ))
        
        memories = []
        for row in cursor.fetchall():
            memories.append({
                'id': row[0],
                'text': row[1],
                'timestamp': row[2],
                'source': row[3],
                'collection': row[4] or 'knowledge',
                'importance': row[5],
                'tags': row[6].split(',') if row[6] else []
            })
        
        return memories
    
    def group_memories_by_topic(
        self,
        memories: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group memories by collection and time window.
        
        Creates groups like:
        - conversations_2026_01 (January chats)
        - documents_project_ideas (project docs)
        """
        groups = {}
        
        for mem in memories:
            collection = mem.get('collection', 'knowledge')
            
            # Create time bucket (month-year)
            dt = datetime.fromtimestamp(mem['timestamp'])
            time_bucket = f"{dt.year}_{dt.month:02d}"
            
            # Try to detect topic from text
            topic = self._detect_topic(mem['text'])
            
            # Create group key
            if collection == 'conversations':
                group_key = f"{collection}_{time_bucket}"
            elif topic:
                group_key = f"{collection}_{topic}"
            else:
                group_key = f"{collection}_{time_bucket}"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(mem)
        
        # Filter to groups with enough memories
        return {
            k: v for k, v in groups.items()
            if len(v) >= self.min_memories_to_compact
        }
    
    def _detect_topic(self, text: str) -> Optional[str]:
        """Simple topic detection from text."""
        text_lower = text.lower()
        
        # Priority topics
        topics = [
            (['federation', 'ssh', 'tunnel'], 'federation'),
            (['memory', 'vector', 'embedding'], 'memory_system'),
            (['wifi', 'network', 'driver'], 'network'),
            (['server', 'hardware'], 'hardware'),
            (['agent', 'skill', 'framework'], 'agent_framework'),
            (['dalio', 'world order'], 'dalio'),
            (['cron', 'backup', 'scheduled'], 'automation'),
        ]
        
        for keywords, topic_name in topics:
            if any(kw in text_lower for kw in keywords):
                return topic_name
        
        return None
    
    def summarize_group(
        self,
        group_key: str,
        memories: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Create a summary of a group of memories.
        
        Uses extractive summarization (pick best sentences)
        or can call an LLM for abstractive summary.
        """
        if len(memories) < self.min_memories_to_compact:
            return None
        
        # Get date range
        timestamps = [m['timestamp'] for m in memories]
        start_date = datetime.fromtimestamp(min(timestamps)).strftime('%Y-%m-%d')
        end_date = datetime.fromtimestamp(max(timestamps)).strftime('%Y-%m-%d')
        
        # Extract key points (extractive approach)
        key_points = []
        
        # Sort by importance and pick top items
        sorted_memories = sorted(
            memories,
            key=lambda m: m.get('importance', 0.5),
            reverse=True
        )
        
        # Take top N most important memories as key points
        top_memories = sorted_memories[:min(5, len(sorted_memories))]
        
        for mem in top_memories:
            # Truncate long texts
            text = mem['text'][:200] + '...' if len(mem['text']) > 200 else mem['text']
            key_points.append(f"- {text}")
        
        # Build summary
        collection = group_key.split('_')[0]
        date_range = f"{start_date} to {end_date}" if start_date != end_date else start_date
        
        summary_parts = [
            f"[COMPACTED SUMMARY] {collection.title()} from {date_range}",
            f"Original memories: {len(memories)}",
            "",
            "Key points:",
            *key_points[:5],  # Top 5 points
            "",
            f"[This summary replaces {len(memories)} individual memories to save space]"
        ]
        
        return '\n'.join(summary_parts)
    
    def compact_group(
        self,
        group_key: str,
        memories: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Compact a group of memories into a summary.
        
        Returns: (success, summary_id)
        """
        if len(memories) < self.min_memories_to_compact:
            return False, None
        
        # Generate summary
        summary_text = self.summarize_group(group_key, memories)
        if not summary_text:
            return False, None
        
        if self.dry_run:
            print(f"[DRY RUN] Would compact {len(memories)} memories in '{group_key}'")
            print(f"  Summary preview: {summary_text[:100]}...")
            return True, "dry_run_id"
        
        # Store summary
        summary_id = self.store.remember(
            text=summary_text,
            collection='compacted',  # Special collection
            importance=self.summary_importance,
            source='compaction',
            tags=['compacted', 'summary', group_key, 'auto-generated'],
        )
        
        # Delete old memories
        deleted_count = 0
        for mem in memories:
            if self.store.delete(mem['id']):
                deleted_count += 1
        
        print(f"  Compacted {deleted_count} memories → summary {summary_id[:8]}")
        
        return True, summary_id
    
    def run_compaction(self) -> CompactionStats:
        """
        Run full compaction process.
        
        Returns statistics about what was compacted.
        """
        print(f"[{datetime.now().strftime('%H:%M')}] Memory Compaction Starting...")
        print(f"  Age threshold: {self.age_threshold_days} days")
        print(f"  Importance threshold: {self.compact_importance_threshold}")
        print(f"  Dry run: {self.dry_run}")
        print()
        
        # Find memories to compact
        candidates = self.find_compactable_memories()
        print(f"Found {len(candidates)} memories eligible for compaction")
        
        if len(candidates) < self.min_memories_to_compact:
            print("Not enough memories to compact.")
            return CompactionStats(0, 0, 0, 0, [])
        
        # Group by topic/time
        groups = self.group_memories_by_topic(candidates)
        print(f"Grouped into {len(groups)} compaction groups")
        print()
        
        # Compact each group
        total_compacted = 0
        total_summaries = 0
        topics_compacted = []
        
        for group_key, memories in groups.items():
            print(f"Compacting '{group_key}': {len(memories)} memories...")
            
            success, summary_id = self.compact_group(group_key, memories)
            
            if success:
                total_compacted += len(memories)
                total_summaries += 1
                topics_compacted.append(group_key)
        
        # Calculate stats
        stats = CompactionStats(
            memories_scanned=len(candidates),
            memories_compacted=total_compacted,
            summaries_created=total_summaries,
            bytes_saved=total_compacted * 500,  # Rough estimate
            topics_compacted=topics_compacted
        )
        
        print()
        print("=== Compaction Complete ===")
        print(f"Scanned: {stats.memories_scanned} memories")
        print(f"Compacted: {stats.memories_compacted} → {stats.summaries_created} summaries")
        print(f"Estimated space saved: {stats.bytes_saved / 1024:.1f} KB")
        print(f"Topics: {', '.join(stats.topics_compacted)}")
        
        return stats
    
    def get_compaction_report(self) -> Dict[str, Any]:
        """Get a report of current memory state and compaction recommendations."""
        # Count memories by age
        now = int(time.time())
        
        cursor = self.store.conn.execute("""
            SELECT 
                CASE 
                    WHEN timestamp > ? THEN 'last_7d'
                    WHEN timestamp > ? THEN 'last_30d'
                    WHEN timestamp > ? THEN 'last_90d'
                    ELSE 'older'
                END as age_bucket,
                COUNT(*) as count,
                AVG(importance) as avg_importance
            FROM memories
            GROUP BY age_bucket
        """, (
            now - 7 * 86400,
            now - 30 * 86400,
            now - 90 * 86400
        ))
        
        age_distribution = {}
        for row in cursor.fetchall():
            age_distribution[row[0]] = {
                'count': row[1],
                'avg_importance': round(row[2], 2) if row[2] else 0
            }
        
        # Count by collection
        cursor = self.store.conn.execute("""
            SELECT collection, COUNT(*) 
            FROM memories 
            GROUP BY collection
        """)
        
        collection_counts = {row[0] or 'unknown': row[1] for row in cursor.fetchall()}
        
        # Total stats
        cursor = self.store.conn.execute("SELECT COUNT(*), COUNT(DISTINCT source) FROM memories")
        total_row = cursor.fetchone()
        
        return {
            'total_memories': total_row[0],
            'unique_sources': total_row[1],
            'age_distribution': age_distribution,
            'collection_counts': collection_counts,
            'compaction_candidates': len(self.find_compactable_memories()),
            'recommendation': 'Run compaction' if len(self.find_compactable_memories()) > 50 else 'No action needed'
        }


def main():
    """Main entry point for cron or manual execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compact old memories')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be compacted')
    parser.add_argument('--days', type=int, default=30, help='Age threshold in days')
    parser.add_argument('--report', action='store_true', help='Show compaction report only')
    args = parser.parse_args()
    
    compactor = MemoryCompactor(
        age_threshold_days=args.days,
        dry_run=args.dry_run
    )
    
    if args.report:
        report = compactor.get_compaction_report()
        print(json.dumps(report, indent=2))
    else:
        stats = compactor.run_compaction()
        sys.exit(0 if stats.memories_compacted > 0 else 0)


if __name__ == "__main__":
    main()
