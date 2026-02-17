#!/usr/bin/env python3
"""
Document drop folder processor
Watches inbox, extracts summaries/context, adds to memory
"""

import os
import sys
import hashlib
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.store import MemoryStore
from scripts.ingest import read_file, chunk_text

def summarize_text(text: str, max_chars: int = 500) -> str:
    """
    Simple extractive summary - first chunk + key sentences.
    For better summaries, could use an LLM API, but keeping it local for now.
    """
    lines = text.split('\n')
    
    # Get first paragraph that's substantial
    first_chunk = ""
    for line in lines:
        if len(line.strip()) > 50:
            first_chunk = line.strip()
            break
    
    # Get any headings (lines starting with # or in CAPS)
    headings = []
    for line in lines[:50]:  # Check first 50 lines
        line = line.strip()
        if line.startswith('#') or (line.isupper() and len(line) > 10):
            headings.append(line.lstrip('#').strip())
    
    # Build summary
    summary_parts = []
    
    if first_chunk:
        summary_parts.append(first_chunk[:max_chars])
    
    if headings[:3]:  # Top 3 headings
        summary_parts.append("\nKey sections: " + ", ".join(headings[:3]))
    
    return "\n".join(summary_parts) if summary_parts else text[:max_chars]

def process_file(filepath: str, store: MemoryStore, move_to_processed: bool = True) -> bool:
    """
    Process a single file: extract, summarize, store in memory.
    
    Args:
        filepath: Path to file
        store: MemoryStore instance
        move_to_processed: Whether to move file after processing
    
    Returns:
        True if successful
    """
    path = Path(filepath)
    
    if not path.exists():
        print(f"File not found: {filepath}")
        return False
    
    print(f"Processing: {path.name}")
    
    # Read file
    text = read_file(filepath)
    if not text:
        print(f"  Could not read file or empty")
        return False
    
    # Calculate file hash for deduplication
    file_hash = hashlib.md5(text.encode()).hexdigest()[:16]
    
    # Check if already processed
    existing = store.recall(f"doc:{file_hash}", topk=1)
    if existing and existing[0].get('score', 0) > 0.95:
        print(f"  Already processed (hash match)")
        if move_to_processed:
            processed_path = Path.home() / ".memento" / "processed" / path.name
            path.rename(processed_path)
        return True
    
    # Get file info
    stat = path.stat()
    file_size_kb = stat.st_size / 1024
    
    # Create summary
    summary = summarize_text(text)
    
    # Determine collection based on file type
    suffix = path.suffix.lower()
    if suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
        collection = "code"
        doc_type = "code"
    elif suffix in ['.md', '.txt', '.rst']:
        collection = "documents"
        doc_type = "document"
    elif suffix in ['.pdf', '.doc', '.docx']:
        collection = "documents"
        doc_type = "document"
    else:
        collection = "documents"
        doc_type = "file"
    
    # Store main summary
    summary_id = store.remember(
        text=f"Document: {path.name}\n\nSummary:\n{summary}",
        collection=collection,
        importance=0.7,
        source=f"file:{filepath}",
        tags=["document", doc_type, suffix.lstrip('.')],
        file_hash=file_hash,
        file_size_kb=round(file_size_kb, 2)
    )
    print(f"  Stored summary: {summary_id}")
    
    # Store key chunks for RAG (not the whole file, just important parts)
    # Chunk and store first few chunks + any chunks with important keywords
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    
    important_keywords = ['todo', 'fixme', 'important', 'note', 'summary', 'conclusion', 
                         'key', 'main', 'critical', 'warning', 'error']
    
    chunks_stored = 0
    max_chunks = 5  # Limit to prevent memory bloat
    
    for i, chunk in enumerate(chunks[:20]):  # Check first 20 chunks
        if chunks_stored >= max_chunks:
            break
        
        # Store if: first chunk, last chunk, or contains important keywords
        is_important = (
            i == 0 or 
            i == len(chunks) - 1 or
            any(kw in chunk.lower() for kw in important_keywords)
        )
        
        if is_important:
            chunk_id = store.remember(
                text=f"[From {path.name}]\n{chunk}",
                collection=collection,
                importance=0.6,
                source=f"file:{filepath}#chunk{i}",
                tags=["document_chunk", doc_type],
                parent_doc=file_hash,
                chunk_idx=i
            )
            chunks_stored += 1
    
    print(f"  Stored {chunks_stored} key chunks")
    
    # Move to processed folder
    if move_to_processed:
        processed_dir = Path.home() / ".memento" / "processed"
        processed_path = processed_dir / f"{file_hash[:8]}_{path.name}"
        
        # Handle duplicates
        counter = 1
        while processed_path.exists():
            processed_path = processed_dir / f"{file_hash[:8]}_{counter}_{path.name}"
            counter += 1
        
        path.rename(processed_path)
        print(f"  Moved to processed: {processed_path.name}")
    
    return True

def process_inbox(store: Optional[MemoryStore] = None) -> int:
    """
    Process all files in the inbox folder.
    
    Returns:
        Number of files processed
    """
    if store is None:
        store = MemoryStore()
    
    inbox_dir = Path.home() / ".memento" / "inbox"
    
    if not inbox_dir.exists():
        print(f"Inbox folder not found: {inbox_dir}")
        return 0
    
    files = [f for f in inbox_dir.iterdir() if f.is_file()]
    
    if not files:
        print("Inbox is empty")
        return 0
    
    print(f"Found {len(files)} file(s) in inbox")
    print("-" * 50)
    
    processed = 0
    for filepath in files:
        try:
            if process_file(str(filepath), store):
                processed += 1
            print()
        except Exception as e:
            print(f"  ERROR processing {filepath.name}: {e}\n")
    
    print(f"Processed {processed}/{len(files)} files")
    return processed

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process documents into memory")
    parser.add_argument("--file", "-f", help="Process single file")
    parser.add_argument("--watch", "-w", action="store_true", help="Watch inbox folder")
    parser.add_argument("--interval", "-i", type=int, default=60, 
                       help="Watch interval in seconds (default: 60)")
    
    args = parser.parse_args()
    
    store = MemoryStore()
    
    if args.file:
        # Process single file
        process_file(args.file, store, move_to_processed=False)
    elif args.watch:
        # Watch mode
        import time
        print(f"Watching inbox every {args.interval}s... (Ctrl+C to stop)")
        while True:
            count = process_inbox(store)
            if count == 0:
                print("No new files. Waiting...")
            time.sleep(args.interval)
    else:
        # Process inbox once
        process_inbox(store)
