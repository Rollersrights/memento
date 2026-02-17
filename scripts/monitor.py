#!/usr/bin/env python3
"""
Memory System Monitor & Maintenance Dashboard
Provides health checks, stats, and maintenance operations
"""

import os
import sys
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict

# Add skill path
sys.path.insert(0, os.path.expanduser('~/.memento'))

@dataclass
class SystemHealth:
    """Overall system health status."""
    status: str  # 'healthy', 'warning', 'critical'
    total_memories: int
    db_size_mb: float
    vectors_loaded: int
    collections: Dict[str, int]
    age_distribution: Dict[str, int]
    issues: List[str]
    recommendations: List[str]
    last_backup: Optional[str]
    cron_status: Dict[str, Any]

class MemoryMonitor:
    """Monitor and maintain the memory system."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.expanduser("~/.memento/memory.db")
        self.db_path = db_path
        self.memory_dir = Path(db_path).parent
        
    def get_db_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {
            'db_exists': os.path.exists(self.db_path),
            'db_size_bytes': 0,
            'db_size_mb': 0,
            'total_memories': 0,
            'collections': {},
            'avg_importance': 0,
            'oldest_memory': None,
            'newest_memory': None
        }
        
        if not stats['db_exists']:
            return stats
        
        # File size
        stats['db_size_bytes'] = os.path.getsize(self.db_path)
        stats['db_size_mb'] = round(stats['db_size_bytes'] / (1024 * 1024), 2)
        
        # Query stats
        conn = sqlite3.connect(self.db_path)
        
        # Total count
        cursor = conn.execute("SELECT COUNT(*), AVG(importance) FROM memories")
        row = cursor.fetchone()
        stats['total_memories'] = row[0]
        stats['avg_importance'] = round(row[1], 2) if row[1] else 0
        
        # Collections
        cursor = conn.execute("SELECT collection, COUNT(*) FROM memories GROUP BY collection")
        stats['collections'] = {row[0] or 'unknown': row[1] for row in cursor.fetchall()}
        
        # Date range
        cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM memories")
        row = cursor.fetchone()
        if row[0] and row[1]:
            stats['oldest_memory'] = datetime.fromtimestamp(row[0]).isoformat()
            stats['newest_memory'] = datetime.fromtimestamp(row[1]).isoformat()
        
        conn.close()
        return stats
    
    def get_age_distribution(self) -> Dict[str, int]:
        """Get memory age distribution."""
        conn = sqlite3.connect(self.db_path)
        now = int(time.time())
        
        cursor = conn.execute("""
            SELECT 
                CASE 
                    WHEN timestamp > ? THEN 'last_24h'
                    WHEN timestamp > ? THEN 'last_7d'
                    WHEN timestamp > ? THEN 'last_30d'
                    WHEN timestamp > ? THEN 'last_90d'
                    ELSE 'older'
                END as age_bucket,
                COUNT(*) as count
            FROM memories
            GROUP BY age_bucket
        """, (
            now - 86400,
            now - 7 * 86400,
            now - 30 * 86400,
            now - 90 * 86400
        ))
        
        result = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return result
    
    def check_backup_status(self) -> Dict[str, Any]:
        """Check backup files."""
        backup_dir = self.memory_dir
        backups = list(backup_dir.glob("memory.db.backup-*"))
        
        if not backups:
            return {
                'has_backup': False,
                'last_backup': None,
                'backup_count': 0,
                'backups': []
            }
        
        # Sort by mtime
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        latest = backups[0]
        
        return {
            'has_backup': True,
            'last_backup': datetime.fromtimestamp(latest.stat().st_mtime).isoformat(),
            'backup_age_hours': round((time.time() - latest.stat().st_mtime) / 3600, 1),
            'backup_count': len(backups),
            'backups': [b.name for b in backups[:5]]  # Last 5
        }
    
    def check_inbox_status(self) -> Dict[str, Any]:
        """Check inbox folder."""
        inbox_dir = self.memory_dir / "inbox"
        processed_dir = self.memory_dir / "processed"
        
        inbox_files = list(inbox_dir.iterdir()) if inbox_dir.exists() else []
        processed_files = list(processed_dir.iterdir()) if processed_dir.exists() else []
        
        return {
            'inbox_count': len(inbox_files),
            'processed_count': len(processed_files),
            'inbox_files': [f.name for f in inbox_files if f.is_file()][:10]
        }
    
    def check_cron_health(self) -> Dict[str, Any]:
        """Check cron job status."""
        # This would need to query the cron system
        # For now, return placeholder
        return {
            'session_watcher': {'status': 'unknown', 'last_run': None},
            'memory_processor': {'status': 'unknown', 'last_run': None},
            'daily_backup': {'status': 'unknown', 'last_run': None},
            'monthly_compaction': {'status': 'unknown', 'last_run': None}
        }
    
    def identify_issues(self, stats: Dict[str, Any]) -> List[str]:
        """Identify potential issues."""
        issues = []
        
        # Check database size
        if stats['db_size_mb'] > 100:
            issues.append(f"Database is large ({stats['db_size_mb']} MB). Consider compaction.")
        
        if stats['db_size_mb'] > 500:
            issues.append(f"Database is very large ({stats['db_size_mb']} MB). Compaction recommended.")
        
        # Check memory count
        if stats['total_memories'] > 10000:
            issues.append(f"High memory count ({stats['total_memories']}). Performance may degrade.")
        
        # Check backup
        backup = self.check_backup_status()
        if not backup['has_backup']:
            issues.append("No backups found. Run manual backup.")
        elif backup['backup_age_hours'] > 48:
            issues.append(f"Backup is {backup['backup_age_hours']} hours old.")
        
        # Check inbox
        inbox = self.check_inbox_status()
        if inbox['inbox_count'] > 10:
            issues.append(f"Inbox has {inbox['inbox_count']} unprocessed files.")
        
        return issues
    
    def get_recommendations(self, stats: Dict[str, Any], issues: List[str]) -> List[str]:
        """Get maintenance recommendations."""
        recommendations = []
        
        if 'compaction' in ' '.join(issues).lower():
            recommendations.append("Run: python3 scripts/compactor.py --days 30")
        
        if stats['total_memories'] > 1000:
            age_dist = self.get_age_distribution()
            if age_dist.get('older', 0) > 100:
                recommendations.append(f"Consider compacting {age_dist['older']} old memories")
        
        if not self.check_backup_status()['has_backup']:
            recommendations.append("Create backup: python3 -c \"from scripts.store import MemoryStore; MemoryStore().backup()\"")
        
        if stats.get('collections', {}).get('conversations', 0) > 500:
            recommendations.append("High conversation count. Old chats will be compacted monthly.")
        
        return recommendations
    
    def run_health_check(self) -> SystemHealth:
        """Run full health check."""
        stats = self.get_db_stats()
        age_dist = self.get_age_distribution()
        backup = self.check_backup_status()
        inbox = self.check_inbox_status()
        issues = self.identify_issues(stats)
        recommendations = self.get_recommendations(stats, issues)
        
        # Determine status
        if len(issues) == 0:
            status = 'healthy'
        elif any('very large' in i or 'High memory count' in i for i in issues):
            status = 'critical'
        else:
            status = 'warning'
        
        return SystemHealth(
            status=status,
            total_memories=stats['total_memories'],
            db_size_mb=stats['db_size_mb'],
            vectors_loaded=stats['total_memories'],  # Approximate
            collections=stats.get('collections', {}),
            age_distribution=age_dist,
            issues=issues,
            recommendations=recommendations,
            last_backup=backup.get('last_backup'),
            cron_status=self.check_cron_health()
        )
    
    def generate_report(self, format: str = 'text') -> str:
        """Generate health report."""
        health = self.run_health_check()
        
        if format == 'json':
            return json.dumps(asdict(health), indent=2)
        
        # Text format
        lines = [
            "=" * 60,
            "  MEMORY SYSTEM HEALTH REPORT",
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            f"Status: {health.status.upper()}",
            "",
            "Database:",
            f"  Total memories: {health.total_memories}",
            f"  Database size: {health.db_size_mb} MB",
            f"  Collections: {health.collections}",
            "",
            "Age Distribution:",
        ]
        
        for bucket, count in health.age_distribution.items():
            lines.append(f"  {bucket}: {count}")
        
        lines.extend([
            "",
            "Backup Status:",
            f"  Last backup: {health.last_backup or 'None'}",
            "",
        ])
        
        if health.issues:
            lines.extend([
                "Issues Found:",
                *[f"  ⚠️  {issue}" for issue in health.issues],
                "",
            ])
        
        if health.recommendations:
            lines.extend([
                "Recommendations:",
                *[f"  💡 {rec}" for rec in health.recommendations],
                "",
            ])
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Memory system monitor')
    parser.add_argument('--report', '-r', action='store_true', help='Show full report')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    parser.add_argument('--check', '-c', action='store_true', help='Quick health check')
    parser.add_argument('--watch', '-w', action='store_true', help='Watch mode (loop)')
    parser.add_argument('--interval', '-i', type=int, default=300, help='Watch interval')
    
    args = parser.parse_args()
    
    monitor = MemoryMonitor()
    
    if args.watch:
        print("Watching memory system (Ctrl+C to stop)...")
        while True:
            os.system('clear' if os.name != 'nt' else 'cls')
            print(monitor.generate_report('text'))
            time.sleep(args.interval)
    
    elif args.json:
        print(monitor.generate_report('json'))
    
    elif args.check:
        health = monitor.run_health_check()
        print(f"Status: {health.status}")
        print(f"Memories: {health.total_memories}")
        print(f"Size: {health.db_size_mb} MB")
        if health.issues:
            print(f"Issues: {len(health.issues)}")
        sys.exit(0 if health.status == 'healthy' else 1)
    
    else:
        print(monitor.generate_report('text'))

if __name__ == "__main__":
    main()
