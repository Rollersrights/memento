#!/usr/bin/env python3
"""
Vector Backfill Script
Re-embeds memories with NULL embeddings
"""

import os
import sys
import sqlite3
import numpy as np
from pathlib import Path

# Add skill path
sys.path.insert(0, os.path.expanduser('~/.memento'))

def backfill_null_embeddings(db_path: str = None, dry_run: bool = False):
    """
    Find memories with NULL embeddings and re-embed them.
    
    Args:
        db_path: Path to memory database
        dry_run: Show what would be done without doing it
    """
    if db_path is None:
        db_path = os.path.expanduser("~/.memento/memory.db")
    
    # Connect to database
    conn = sqlite3.connect(db_path, check_same_thread=False)
    
    # Find memories with NULL embeddings
    cursor = conn.execute(
        "SELECT id, text FROM memories WHERE embedding IS NULL"
    )
    
    null_memories = cursor.fetchall()
    
    if not null_memories:
        print("✅ No memories with NULL embeddings found!")
        conn.close()
        return 0
    
    print(f"Found {len(null_memories)} memories with NULL embeddings")
    print()
    
    if dry_run:
        print("[DRY RUN] Would re-embed these memories:")
        for mem_id, text in null_memories[:10]:
            print(f"  - {mem_id}: {text[:60]}...")
        if len(null_memories) > 10:
            print(f"  ... and {len(null_memories) - 10} more")
        conn.close()
        return len(null_memories)
    
    # Import embed function
    try:
        from scripts.embed import embed
    except ImportError:
        from embed import embed
    
    print("Re-embedding memories...")
    fixed_count = 0
    error_count = 0
    
    for mem_id, text in null_memories:
        try:
            # Generate embedding
            embedding = embed(text)
            embedding_np = np.array(embedding, dtype=np.float32)
            
            # Normalize
            norm = np.linalg.norm(embedding_np)
            if norm > 0:
                embedding_np = embedding_np / norm
            
            # Store as binary
            embedding_bytes = embedding_np.tobytes()
            
            # Update database
            conn.execute(
                "UPDATE memories SET embedding = ? WHERE id = ?",
                (embedding_bytes, mem_id)
            )
            
            fixed_count += 1
            
            if fixed_count % 10 == 0:
                print(f"  Progress: {fixed_count}/{len(null_memories)}")
                conn.commit()  # Periodic commit
        
        except Exception as e:
            print(f"  Error re-embedding {mem_id}: {e}")
            error_count += 1
    
    # Final commit
    conn.commit()
    conn.close()
    
    print()
    print(f"✅ Backfill complete:")
    print(f"   Fixed: {fixed_count}")
    print(f"   Errors: {error_count}")
    
    return fixed_count


def check_embedding_health(db_path: str = None):
    """Check the health of embeddings in the database."""
    if db_path is None:
        db_path = os.path.expanduser("~/.memento/memory.db")
    
    conn = sqlite3.connect(db_path)
    
    # Total memories
    cursor = conn.execute("SELECT COUNT(*) FROM memories")
    total = cursor.fetchone()[0]
    
    # Memories with embeddings
    cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE embedding IS NOT NULL")
    with_embedding = cursor.fetchone()[0]
    
    # Memories without embeddings
    cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE embedding IS NULL")
    without_embedding = cursor.fetchone()[0]
    
    conn.close()
    
    print("=== Embedding Health Check ===")
    print(f"Total memories: {total}")
    print(f"With embeddings: {with_embedding} ({100*with_embedding/total:.1f}%)")
    print(f"Without embeddings: {without_embedding} ({100*without_embedding/total:.1f}%)")
    print()
    
    if without_embedding == 0:
        print("✅ All memories have embeddings!")
        return True
    else:
        print(f"⚠️  {without_embedding} memories need backfill")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill NULL embeddings')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would be done')
    parser.add_argument('--check', '-c', action='store_true', help='Check health only')
    args = parser.parse_args()
    
    if args.check:
        check_embedding_health()
    else:
        if not args.dry_run:
            # Check first
            if check_embedding_health():
                return
            print()
        
        # Run backfill
        count = backfill_null_embeddings(dry_run=args.dry_run)
        
        if not args.dry_run and count > 0:
            print()
            check_embedding_health()


if __name__ == "__main__":
    main()
