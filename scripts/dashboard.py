#!/usr/bin/env python3
"""
Memory-zvec Real-Time Dashboard v2
Enhanced with history tracking, growth rates, and alerts.
"""

import os
import sys
import time
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque

# Try to import rich, install if missing
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.columns import Columns
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    print("Installing rich library...")
    os.system("pip install rich -q")
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.layout import Layout
        from rich.live import Live
        from rich.text import Text
        from rich.columns import Columns
        from rich import box
        RICH_AVAILABLE = True
    except ImportError:
        print("Failed to install rich. Please run: pip install rich")
        sys.exit(1)

# Paths
DB_PATH = Path.home() / ".memento/memory.db"
INBOX_PATH = Path.home() / ".memento/inbox"
PROCESSED_PATH = Path.home() / ".memento/processed"
HISTORY_FILE = Path.home() / ".memento/dashboard_history.json"
ALERT_STATE_FILE = Path.home() / ".memento/dashboard_alerts.json"

# In-memory history cache (last 60 data points = ~2 minutes at 2s refresh)
HISTORY_CACHE = {
    "timestamps": deque(maxlen=60),
    "vector_counts": deque(maxlen=60),
    "db_sizes": deque(maxlen=60)
}

def format_bytes(size_bytes):
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def load_history():
    """Load historical data from file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                # Convert lists back to deques
                for key in ['timestamps', 'vector_counts', 'db_sizes']:
                    if key in data:
                        HISTORY_CACHE[key] = deque(data[key], maxlen=60)
        except Exception:
            pass  # History file missing or corrupted, start fresh

def save_history():
    """Save historical data to file."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, 'w') as f:
            json.dump({
                'timestamps': list(HISTORY_CACHE['timestamps']),
                'vector_counts': list(HISTORY_CACHE['vector_counts']),
                'db_sizes': list(HISTORY_CACHE['db_sizes'])
            }, f)
    except Exception:
        pass  # Ignore write errors (permissions, disk full)

def update_history(stats):
    """Add current stats to history."""
    now = time.time()
    HISTORY_CACHE['timestamps'].append(now)
    HISTORY_CACHE['vector_counts'].append(stats['total_vectors'])
    HISTORY_CACHE['db_sizes'].append(stats['db_size'])

def calculate_growth_rate():
    """Calculate growth rate (vectors per hour)."""
    if len(HISTORY_CACHE['vector_counts']) < 2:
        return 0
    
    vectors = list(HISTORY_CACHE['vector_counts'])
    timestamps = list(HISTORY_CACHE['timestamps'])
    
    if len(vectors) < 2 or len(timestamps) < 2:
        return 0
    
    vector_diff = vectors[-1] - vectors[0]
    time_diff_hours = (timestamps[-1] - timestamps[0]) / 3600
    
    if time_diff_hours == 0:
        return 0
    
    return vector_diff / time_diff_hours

def create_sparkline(data, width=20):
    """Create ASCII sparkline from data."""
    if not data or len(data) < 2:
        return "─" * width
    
    blocks = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    data = list(data)
    min_val = min(data)
    max_val = max(data)
    
    if max_val == min_val:
        return "─" * width
    
    # Sample data to fit width
    step = max(1, len(data) // width)
    sampled = data[::step][:width]
    
    spark = ""
    for val in sampled:
        idx = int((val - min_val) / (max_val - min_val) * (len(blocks) - 1))
        spark += blocks[idx]
    
    return spark

def get_db_stats():
    """Get database statistics."""
    stats = {
        "db_size": 0,
        "db_size_human": "0 B",
        "total_vectors": 0,
        "collections": {},
        "recent_additions": [],
        "avg_vector_size": 0
    }
    
    if not DB_PATH.exists():
        return stats
    
    file_size = DB_PATH.stat().st_size
    stats["db_size"] = file_size
    stats["db_size_human"] = format_bytes(file_size)
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM memories")
        stats["total_vectors"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT collection, COUNT(*) FROM memories GROUP BY collection")
        stats["collections"] = dict(cursor.fetchall())
        
        cursor.execute("SELECT LENGTH(embedding) FROM memories LIMIT 100")
        vector_sizes = [r[0] for r in cursor.fetchall() if r[0]]
        if vector_sizes:
            stats["avg_vector_size"] = sum(vector_sizes) / len(vector_sizes)
        
        cursor.execute("""
            SELECT id, collection, text, source, importance 
            FROM memories 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        stats["recent_additions"] = cursor.fetchall()
        
        conn.close()
    except Exception as e:
        stats["error"] = str(e)
        stats["recent_additions"] = []
    
    return stats

def get_inbox_stats():
    """Get document inbox statistics."""
    stats = {
        "inbox_count": 0,
        "inbox_size": 0,
        "processed_count": 0,
        "inbox_files": [],
        "recent_processed": []
    }
    
    if INBOX_PATH.exists():
        files = list(INBOX_PATH.iterdir())
        stats["inbox_count"] = len(files)
        stats["inbox_size"] = sum(f.stat().st_size for f in files)
        stats["inbox_files"] = [f.name for f in files][:5]
    
    if PROCESSED_PATH.exists():
        files = sorted(PROCESSED_PATH.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
        stats["processed_count"] = len(files)
        stats["recent_processed"] = [f.name for f in files[:5]]
    
    return stats

def get_cron_status():
    """Check cron job status with alerts."""
    status = {
        "session_watcher": "unknown",
        "processor": "unknown",
        "last_session_run": None,
        "last_processor_run": None,
        "alerts": []
    }
    
    try:
        import subprocess
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            output = result.stdout
            
            for line in output.split('\n'):
                if 'ID' in line and 'Name' in line:
                    continue
                    
                if 'session-watcher' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part in ['ok', 'error', 'idle']:
                            job_status = part
                            if i >= 2:
                                last_run = parts[i-2] + " " + parts[i-1] if i > 2 else parts[i-1]
                                status["session_watcher"] = f"✓ {job_status}" if job_status == "ok" else f"✗ {job_status}"
                                status["last_session_run"] = last_run
                                if job_status == "error":
                                    status["alerts"].append("Session watcher failed!")
                            break
                
                if 'memory-processor' in line and 'session-watcher' not in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part in ['ok', 'error', 'idle']:
                            job_status = part
                            if i >= 2:
                                last_run = parts[i-2] + " " + parts[i-1] if i > 2 else parts[i-1]
                                status["processor"] = f"✓ {job_status}" if job_status == "ok" else f"✗ {job_status}"
                                status["last_processor_run"] = last_run
                                if job_status == "error":
                                    status["alerts"].append("Document processor failed!")
                            break
    except Exception:
        pass  # openclaw not installed or cron not accessible
    
    # Fallback
    if status["session_watcher"] == "unknown":
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM memories 
                WHERE collection = 'conversations' 
                AND id > (SELECT MAX(id) - 10 FROM memories)
            """)
            if cursor.fetchone()[0] > 0:
                status["session_watcher"] = "✓ working"
                status["last_session_run"] = "recent"
            conn.close()
        except Exception:
            pass  # Database not accessible
    
    return status

def create_dashboard():
    """Create the dashboard layout."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="alerts", size=3),
        Layout(name="main"),
        Layout(name="recent", size=8),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="db_stats", ratio=1),
        Layout(name="graphs", ratio=1),
        Layout(name="system_stats", ratio=1)
    )
    return layout

def update_dashboard(layout):
    """Update dashboard with current data."""
    db_stats = get_db_stats()
    inbox_stats = get_inbox_stats()
    cron_stats = get_cron_status()
    
    # Update history
    update_history(db_stats)
    
    # Calculate growth rate
    growth_rate = calculate_growth_rate()
    
    # Header
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_text = Text()
    header_text.append("🧠 Memory-zvec Dashboard v2  |  ", style="bold cyan")
    header_text.append(now, style="cyan")
    header_text.append("  |  Ctrl+C to exit", style="dim")
    layout["header"].update(Panel(header_text, border_style="cyan"))
    
    # Alerts panel
    if cron_stats.get('alerts'):
        alert_text = Text("⚠️  ", style="bold red")
        alert_text.append("  |  ".join(cron_stats['alerts']), style="red")
        layout["alerts"].update(Panel(alert_text, title="[bold red]Alerts[/bold red]", border_style="red"))
    else:
        alert_text = Text("✓ All systems operational", style="green")
        layout["alerts"].update(Panel(alert_text, title="[bold green]Status[/bold green]", border_style="green"))
    
    # DB Stats panel
    db_table = Table(show_header=False, box=None)
    db_table.add_column("Key", style="dim cyan", width=20)
    db_table.add_column("Value", style="white")
    
    db_table.add_row("Database Size", f"{db_stats['db_size_human']} ({db_stats['total_vectors']} vectors)")
    db_table.add_row("Avg Vector Size", f"{db_stats.get('avg_vector_size', 0):.0f} bytes")
    db_table.add_row("Growth Rate", f"{growth_rate:+.1f} vectors/hour")
    db_table.add_row("", "")
    db_table.add_row("[bold bright_cyan]Collections[/bold bright_cyan]", "")
    
    for collection, count in db_stats.get('collections', {}).items():
        db_table.add_row(f"  {collection}", f"{count} vectors")
    
    layout["db_stats"].update(Panel(db_table, title="[bold green]Database[/bold green]", border_style="green"))
    
    # Graphs panel
    graph_table = Table(show_header=False, box=None)
    graph_table.add_column("Metric", style="dim blue", width=12)
    graph_table.add_column("Sparkline", style="blue")
    graph_table.add_column("Trend", style="white", width=8)
    
    vectors = list(HISTORY_CACHE['vector_counts'])
    sizes = list(HISTORY_CACHE['db_sizes'])
    
    if len(vectors) >= 2:
        vector_trend = "↑" if vectors[-1] > vectors[0] else "↓" if vectors[-1] < vectors[0] else "→"
        size_trend = "↑" if sizes[-1] > sizes[0] else "↓" if sizes[-1] < sizes[0] else "→"
    else:
        vector_trend = size_trend = "→"
    
    graph_table.add_row("Vectors", create_sparkline(vectors, 20), vector_trend)
    graph_table.add_row("Size", create_sparkline(sizes, 20), size_trend)
    
    layout["graphs"].update(Panel(graph_table, title="[bold blue]History (Last 2 min)[/bold blue]", border_style="blue"))
    
    # System Stats panel
    sys_table = Table(show_header=False, box=None)
    sys_table.add_column("Key", style="dim yellow", width=20)
    sys_table.add_column("Value", style="white")
    
    sys_table.add_row("Session Watcher", f"{cron_stats['session_watcher']} ({cron_stats['last_session_run'] or 'N/A'})")
    sys_table.add_row("Doc Processor", f"{cron_stats['processor']} ({cron_stats['last_processor_run'] or 'N/A'})")
    sys_table.add_row("", "")
    sys_table.add_row("[bold bright_yellow]Document Inbox[/bold bright_yellow]", "")
    sys_table.add_row("Pending Files", f"{inbox_stats['inbox_count']} ({format_bytes(inbox_stats['inbox_size'])})")
    sys_table.add_row("Processed", str(inbox_stats['processed_count']))
    
    if inbox_stats['inbox_files']:
        sys_table.add_row("", "")
        sys_table.add_row("[bold bright_yellow]Inbox Files[/bold bright_yellow]", "")
        for f in inbox_stats['inbox_files']:
            sys_table.add_row(f"  📄 {f[:30]}...", "")
    
    layout["system_stats"].update(Panel(sys_table, title="[bold yellow]System[/bold yellow]", border_style="yellow"))
    
    # Recent additions panel
    recent_table = Table(box=None, padding=(0, 1))
    recent_table.add_column("ID", style="dim", width=6)
    recent_table.add_column("Collection", style="cyan", width=14)
    recent_table.add_column("Source", style="yellow", width=12)
    recent_table.add_column("Text Preview", style="white", no_wrap=True)
    
    recent = db_stats.get('recent_additions', [])
    if recent:
        for r in recent[:5]:
            mem_id = str(r[0])[-5:] if r[0] else "N/A"
            collection = r[1] or "unknown"
            text_preview = (r[2] or "")[:40] + "..." if r[2] and len(r[2]) > 40 else (r[2] or "N/A")
            source = r[3] or "unknown"
            
            recent_table.add_row(mem_id, collection, source, text_preview)
    else:
        recent_table.add_row("", "", "", "[dim]No memories found[/dim]")
    
    layout["recent"].update(Panel(recent_table, title="[bold magenta]Recent Memories (Last 5)[/bold magenta]", border_style="magenta"))
    
    # Footer
    footer_text = Text()
    footer_text.append("💡 Tips: ", style="bold")
    footer_text.append("Drop files in ~/.memento/inbox | ", style="dim")
    footer_text.append("Say 'remember this' to force store | ", style="dim")
    footer_text.append("History auto-saves every 60s", style="dim")
    
    layout["footer"].update(Panel(footer_text, border_style="bright_black"))

def main():
    """Main dashboard loop."""
    console = Console()
    
    # Load history
    load_history()
    
    # Check for command-line args
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--once', '-o', '--snapshot']:
            console.print("\n[bold cyan]🧠 Memory-zvec Snapshot[/bold cyan]\n")
            
            db_stats = get_db_stats()
            inbox_stats = get_inbox_stats()
            cron_stats = get_cron_status()
            
            console.print(f"[green]Database:[/green] {db_stats['db_size_human']} | {db_stats['total_vectors']} vectors")
            for collection, count in db_stats.get('collections', {}).items():
                console.print(f"  • {collection}: {count}")
            
            console.print(f"\n[yellow]Inbox:[/yellow] {inbox_stats['inbox_count']} pending | {inbox_stats['processed_count']} processed")
            console.print(f"[yellow]Cron:[/yellow] Session Watcher {cron_stats['session_watcher']} | Processor {cron_stats['processor']}")
            
            if cron_stats.get('alerts'):
                console.print(f"\n[red]⚠️ Alerts: {' | '.join(cron_stats['alerts'])}[/red]")
            
            if db_stats.get('recent_additions'):
                console.print("\n[magenta]Recent memories:[/magenta]")
                for r in db_stats['recent_additions'][:3]:
                    text = (r[2] or "")[:60] + "..." if r[2] else "N/A"
                    console.print(f"  [{r[1]}] {text}")
            
            console.print()
            return
        
        elif sys.argv[1] in ['--help', '-h']:
            console.print("""
[bold cyan]Memory-zvec Dashboard v2[/bold cyan]

Usage: python3 scripts/dashboard.py [option]

Options:
  (no args)     Start live dashboard with graphs and alerts
  --once, -o    Show one-time snapshot and exit
  --help, -h    Show this help message

Features:
  • Real-time vector count and storage size
  • ASCII sparkline graphs (2-minute history)
  • Growth rate calculation (vectors/hour)
  • Cron job health monitoring with alerts
  • Recent memories list
  • Auto-saves history for trend analysis

Press Ctrl+C in live mode to exit.
""")
            return
    
    # Live dashboard mode
    if not DB_PATH.exists():
        console.print(f"[bold red]Error: Database not found at {DB_PATH}[/bold red]")
        sys.exit(1)
    
    console.print("[bold cyan]🧠 Starting Memory-zvec Dashboard v2...[/bold cyan]")
    console.print(f"[dim]Database: {DB_PATH}[/dim]")
    console.print(f"[dim]History file: {HISTORY_FILE}[/dim]\n")
    time.sleep(1)
    
    layout = create_dashboard()
    last_save = time.time()
    
    try:
        with Live(layout, refresh_per_second=1, screen=True):
            while True:
                update_dashboard(layout)
                
                # Save history every 60 seconds
                if time.time() - last_save > 60:
                    save_history()
                    last_save = time.time()
                
                time.sleep(2)
    except KeyboardInterrupt:
        save_history()
        console.print("\n[bold green]Dashboard closed. History saved.[/bold green]")
        sys.exit(0)

if __name__ == "__main__":
    main()
