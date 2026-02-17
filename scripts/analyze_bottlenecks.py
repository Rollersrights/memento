#!/usr/bin/env python3
"""
Memento Bottleneck Analyzer
Identifies performance issues and prioritizes fixes
"""

import sys
import os
import json
import time
from pathlib import Path

# Add parent directory to path for proper 'scripts.X' imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def analyze_bottlenecks():
    """Analyze current system for bottlenecks"""
    
    bottlenecks = []
    
    # 1. Check cold start issue
    print("🔍 Analyzing cold start...")
    try:
        from scripts.embed import embed
        start = time.time()
        # Test embedding - this will trigger model load if not already loaded
        _ = embed("test query for cold start analysis")
        cold_time = (time.time() - start) * 1000
        
        if cold_time > 5000:  # > 5 seconds is bad
            bottlenecks.append({
                'priority': 'CRITICAL',
                'issue': 'Cold start too slow',
                'metric': f'{cold_time:.0f}ms',
                'target': '<1000ms',
                'solution': 'Pre-load model in background / lazy init optimization'
            })
        else:
            print(f"   ✅ Cold start: {cold_time:.0f}ms")
            
    except Exception as e:
        bottlenecks.append({
            'priority': 'CRITICAL',
            'issue': 'Embedder fails to load',
            'error': str(e),
            'solution': 'Fix import paths / dependency issues'
        })
    
    # 2. Check database size
    print("🔍 Checking database...")
    db_path = Path.home() / '.openclaw/memory/memory.db'
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        if size_mb > 50:
            bottlenecks.append({
                'priority': 'HIGH',
                'issue': 'Database getting large',
                'metric': f'{size_mb:.1f}MB',
                'target': '<50MB',
                'solution': 'Run compaction / implement pagination'
            })
    
    # 3. Check cache status
    print("🔍 Checking cache...")
    try:
        from scripts.store import MemoryStore
        store = MemoryStore()
        stats = store.stats()
        
        if stats.get('total_vectors', 0) > 1000:
            bottlenecks.append({
                'priority': 'MEDIUM',
                'issue': 'Vector count growing',
                'metric': f"{stats['total_vectors']} vectors",
                'target': 'Consider FAISS/hnswlib',
                'solution': 'Implement vector index backend selection'
            })
    except Exception as e:
        pass
    
    # 4. Check for timeout configuration
    print("🔍 Checking timeouts...")
    try:
        from scripts.store import MemoryStore
        import inspect
        store = MemoryStore()
        recall_sig = inspect.signature(store.recall)
        if 'timeout_ms' in recall_sig.parameters:
            print("   ✅ Query timeout configured (timeout_ms parameter)")
        else:
            bottlenecks.append({
                'priority': 'HIGH',
                'issue': 'No query timeout configured',
                'metric': 'None',
                'target': '5-10s max',
                'solution': 'Add timeout parameter to search operations'
            })
    except Exception:
        # If we can't check, assume it's not configured
        bottlenecks.append({
            'priority': 'HIGH',
            'issue': 'No query timeout configured',
            'metric': 'None',
            'target': '5-10s max',
            'solution': 'Add timeout parameter to search operations'
        })
    
    # Sort by priority
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    bottlenecks.sort(key=lambda x: priority_order.get(x['priority'], 99))
    
    return bottlenecks

def print_report(bottlenecks):
    """Print formatted report"""
    print("\n" + "="*60)
    print("  MEMENTO BOTTLENECK ANALYSIS")
    print("="*60)
    
    if not bottlenecks:
        print("✅ No significant bottlenecks detected!")
        return
    
    for i, b in enumerate(bottlenecks, 1):
        icon = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🔵'}.get(b['priority'], '⚪')
        print(f"\n{i}. {icon} [{b['priority']}] {b['issue']}")
        print(f"   Current: {b.get('metric', 'N/A')}")
        print(f"   Target:  {b.get('target', 'N/A')}")
        print(f"   Fix:     {b['solution']}")
    
    print("\n" + "="*60)
    print(f"Found {len(bottlenecks)} bottleneck(s) to fix")
    print("="*60)

if __name__ == "__main__":
    bottlenecks = analyze_bottlenecks()
    print_report(bottlenecks)
    
    # Save to file for cron job
    output = Path.home() / '.openclaw/memory/bottlenecks.json'
    with open(output, 'w') as f:
        json.dump(bottlenecks, f, indent=2)
    
    print(f"\n💾 Saved to {output}")
