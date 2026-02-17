#!/usr/bin/env python3
"""
Memento CLI - The command line interface for your semantic memory.
"""

import os
import sys
import argparse
import json
import time
from typing import List, Optional

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memento.store import MemoryStore
from memento.embed import get_cache_stats, _get_embedder_type

# Try to import Rich for pretty output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich import box
    CONSOLE = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    CONSOLE = None

def format_time(seconds: float) -> str:
    """Format time relative to now."""
    diff = time.time() - seconds
    if diff < 60:
        return f"{int(diff)}s ago"
    elif diff < 3600:
        return f"{int(diff/60)}m ago"
    elif diff < 86400:
        return f"{int(diff/3600)}h ago"
    else:
        return f"{int(diff/86400)}d ago"

def print_results(results: List[dict], output_format: str = 'table'):
    """Print search results in requested format."""
    if not results:
        if HAS_RICH and output_format == 'table':
            CONSOLE.print("[yellow]No memories found.[/yellow]")
        else:
            print("No memories found.")
        return

    # JSON output for piping/scripting
    if output_format == 'json' or not sys.stdout.isatty():
        print(json.dumps(results, indent=2))
        return

    # Plain text for simple grep
    if output_format == 'text':
        for r in results:
            print(f"[{r['score']:.3f}] {r['text']}")
        return

    # Rich Table (Human readable)
    if HAS_RICH:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Score", style="green", justify="right", width=6)
        table.add_column("Text", style="white")
        table.add_column("Time", style="blue", width=10)
        
        for r in results:
            # Highlight tags if present in text (naive)
            text = r['text'].replace('\n', ' ')
            if len(text) > 100:
                text = text[:97] + "..."
            
            table.add_row(
                r['id'][:8],
                f"{r['score']:.3f}",
                text,
                format_time(r['timestamp'])
            )
        CONSOLE.print(table)
    else:
        # Fallback table
        print(f"{'ID':<10} {'SCORE':<8} {'TEXT'}")
        print("-" * 60)
        for r in results:
            text = r['text'].replace('\n', ' ')
            if len(text) > 50: text = text[:47] + "..."
            print(f"{r['id'][:8]:<10} {r['score']:.3f}    {text}")

def cmd_remember(args: argparse.Namespace) -> None:
    """Store a memory."""
    store = MemoryStore()
    text = " ".join(args.text)
    
    # Read from stdin if text is "-"
    if text == "-" and not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    
    if not text:
        print("Error: No text provided")
        sys.exit(1)
        
    doc_id = store.remember(
        text, 
        importance=args.importance,
        tags=args.tags.split(',') if args.tags else []
    )
    
    if HAS_RICH and CONSOLE:
        CONSOLE.print(f"[bold green]✓ Remembered:[/bold green] [dim]{doc_id}[/dim]")
        CONSOLE.print(f"  \"{text[:100]}{'...' if len(text)>100 else ''}\"")
    else:
        print(f"Stored: {doc_id}")

def cmd_recall(args: argparse.Namespace) -> None:
    """Search memories."""
    store = MemoryStore()
    query = " ".join(args.query)
    
    results = store.recall(
        query, 
        topk=args.limit,
        min_importance=args.min_score
    )
    
    print_results(results, args.format)

def cmd_delete(args: argparse.Namespace) -> None:
    """Delete a memory."""
    store = MemoryStore()
    if store.delete(args.id):
        if HAS_RICH and CONSOLE:
            CONSOLE.print(f"[bold red]🗑️ Deleted:[/bold red] {args.id}")
        else:
            print(f"Deleted {args.id}")
    else:
        print(f"Error: Could not delete {args.id}")
        sys.exit(1)

def cmd_stats(args: argparse.Namespace) -> None:
    """Show statistics."""
    store = MemoryStore()
    stats = store.stats()
    
    # Add embedding stats
    cache_stats = get_cache_stats()
    
    if args.format == 'json':
        stats['cache'] = cache_stats
        print(json.dumps(stats, indent=2))
        return

    if HAS_RICH and CONSOLE:
        grid = Table.grid(padding=1)
        grid.add_column(style="bold cyan", justify="right")
        grid.add_column(style="white")
        
        grid.add_row("Total Memories:", str(stats['total_vectors']))
        grid.add_row("Database:", str(stats['db_path']))
        
        CONSOLE.print(Panel(grid, title="🧠 Memento Stats", border_style="blue"))
        
        # Cache Panel
        c_grid = Table.grid(padding=1)
        c_grid.add_column(style="bold yellow", justify="right")
        c_grid.add_column(style="white")
        
        c_grid.add_row("Backend:", str(cache_stats['embedder']).upper())
        c_grid.add_row("RAM Hits:", str(cache_stats['lru_hits']))
        c_grid.add_row("Disk Hits:", str(cache_stats['disk_hits']))
        c_grid.add_row("Computes:", str(cache_stats['misses']))
        
        CONSOLE.print(Panel(c_grid, title="⚡ Embedding Cache", border_style="yellow"))
    else:
        print("STATS")
        print(f"Memories: {stats['total_vectors']}")
        print(f"Path: {stats['db_path']}")
        print(f"Cache: {cache_stats}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Memento - Semantic Memory CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Remember
    p_store = subparsers.add_parser("remember", aliases=["store", "add"], help="Store a memory")
    p_store.add_argument("text", nargs="+", help="Text to remember (or - for stdin)")
    p_store.add_argument("-i", "--importance", type=float, default=0.5, help="Importance (0.0-1.0)")
    p_store.add_argument("-t", "--tags", help="Comma-separated tags")
    p_store.set_defaults(func=cmd_remember)
    
    # Recall
    p_search = subparsers.add_parser("recall", aliases=["search", "find", "q"], help="Search memories")
    p_search.add_argument("query", nargs="+", help="Search query")
    p_search.add_argument("-n", "--limit", type=int, default=5, help="Max results")
    p_search.add_argument("-s", "--min-score", type=float, default=0.0, help="Min importance")
    p_search.add_argument("-f", "--format", choices=['table', 'json', 'text'], default='table', help="Output format")
    p_search.set_defaults(func=cmd_recall)
    
    # Delete
    p_del = subparsers.add_parser("delete", aliases=["rm", "forget"], help="Delete a memory")
    p_del.add_argument("id", help="Memory ID")
    p_del.set_defaults(func=cmd_delete)
    
    # Stats
    p_stats = subparsers.add_parser("stats", aliases=["info"], help="Show statistics")
    p_stats.add_argument("-f", "--format", choices=['pretty', 'json'], default='pretty', help="Output format")
    p_stats.set_defaults(func=cmd_stats)
    
    # Dashboard redirect
    p_dash = subparsers.add_parser("dashboard", aliases=["dash"], help="Launch live dashboard")
    
    args = parser.parse_args()
    
    if args.command in ["dashboard", "dash"]:
        # Exec the dashboard script directly to take over process
        dash_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
        os.execl(sys.executable, sys.executable, dash_path)
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
