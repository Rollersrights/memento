#!/usr/bin/env python3
"""
Cache warmup script for Memento.
Pre-compute embeddings for common queries to ensure fast responses.

Usage:
    python warmup.py                    # Warm common queries only
    python warmup.py --custom "query1" "query2"  # Add custom queries
    python warmup.py --no-common        # Skip common queries, warm custom only
    python warmup.py --json             # Output stats as JSON
    python warmup.py --model-only       # Only warm the model, skip cache

Exit codes:
    0 - Success
    1 - Model warmup failed
    2 - Cache warmup failed

For cron jobs:
    */30 * * * * cd /path/to/memento && python scripts/warmup.py --json >> /var/log/memento-warmup.log
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from embed import warmup, warmup_cache, is_model_ready, get_warmup_queries


def main():
    parser = argparse.ArgumentParser(
        description="Warm up Memento model and cache for fast queries"
    )
    parser.add_argument(
        "--custom",
        nargs="+",
        help="Custom queries to warm (in addition to common queries)"
    )
    parser.add_argument(
        "--no-common",
        action="store_true",
        help="Skip common queries, only warm custom ones"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--model-only",
        action="store_true",
        help="Only warm up the model, skip cache warming"
    )
    parser.add_argument(
        "--list-queries",
        action="store_true",
        help="List common warmup queries and exit"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output (use with --json for scripting)"
    )
    
    args = parser.parse_args()
    
    # List queries mode
    if args.list_queries:
        queries = get_warmup_queries()
        print("Common warmup queries:")
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q}")
        return 0
    
    results = {
        "success": True,
        "model_ready": False,
        "cache_warmed": False,
        "stats": {}
    }
    
    # Step 1: Warm up the model
    if not args.quiet:
        print("[Warmup] Warming up model...", file=sys.stderr)
    
    if not warmup():
        results["success"] = False
        results["error"] = "Model warmup failed"
        if args.json:
            print(json.dumps(results))
        elif not args.quiet:
            print("[Warmup] ❌ Model warmup failed", file=sys.stderr)
        return 1
    
    results["model_ready"] = True
    
    if not args.quiet:
        print("[Warmup] ✅ Model ready", file=sys.stderr)
    
    # Step 2: Warm up the cache (unless --model-only)
    if not args.model_only:
        if not args.quiet:
            print("[Warmup] Warming cache...", file=sys.stderr)
        
        try:
            stats = warmup_cache(
                queries=args.custom,
                include_common=not args.no_common
            )
            results["cache_warmed"] = True
            results["stats"] = stats
            
            if not args.quiet:
                print(f"[Warmup] ✅ Warmed {stats['warmed']} queries in {stats['time_ms']:.0f}ms", file=sys.stderr)
                print(f"[Warmup]    Average: {stats['time_per_query_ms']:.1f}ms per query", file=sys.stderr)
                
        except Exception as e:
            results["success"] = False
            results["error"] = f"Cache warmup failed: {str(e)}"
            if args.json:
                print(json.dumps(results))
            elif not args.quiet:
                print(f"[Warmup] ❌ Cache warmup failed: {e}", file=sys.stderr)
            return 2
    
    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    elif not args.quiet:
        print("[Warmup] ✅ Warmup complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
