#!/usr/bin/env python3
"""
Advanced search with hybrid filters, reranking, and BM25 + Vector combination
"""

import time
import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime

def init_fts5(conn: sqlite3.Connection):
    """Initialize FTS5 full-text search on memories table."""
    try:
        # Check if FTS5 table exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories_fts'")
        if not cursor.fetchone():
            # Create FTS5 virtual table
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    text,
                    content='memories',
                    content_rowid='rowid'
                )
            """)
            # Populate with existing data
            conn.execute("""
                INSERT INTO memories_fts(rowid, text)
                SELECT rowid, text FROM memories WHERE text IS NOT NULL
            """)
            conn.commit()
            print("[Search] FTS5 index initialized")
    except Exception as e:
        print(f"[Search] FTS5 init error (expected if FTS5 not available): {e}")

def bm25_search(
    conn: sqlite3.Connection,
    query: str,
    topk: int = 20
) -> List[Dict[str, Any]]:
    """
    Search using BM25 (FTS5) for keyword matching.
    Great for exact matches like IP addresses, names, etc.
    """
    try:
        # Escape special FTS5 characters: " . * ( )
        # Wrap in double quotes to treat as literal phrase
        escaped_query = query.replace('"', '""')
        fts_query = f'"{escaped_query}"'
        
        # Use FTS5 rank for BM25 scoring
        cursor = conn.execute("""
            SELECT m.id, m.text, m.timestamp, m.source, m.session_id,
                   m.importance, m.tags, m.collection,
                   rank AS bm25_score
            FROM memories_fts fts
            JOIN memories m ON m.rowid = fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (fts_query, topk))
        
        results = []
        for row in cursor.fetchall():
            # BM25 rank is negative (lower is better), convert to positive score 0-1
            bm25_raw = row[8] if row[8] is not None else -10
            # Normalize: typical BM25 ranges from ~-1 (best) to ~-10 (worst)
            bm25_score = min(1.0, max(0.0, (10 + bm25_raw) / 9))
            
            results.append({
                'id': row[0],
                'text': row[1],
                'timestamp': row[2],
                'source': row[3],
                'session_id': row[4],
                'importance': row[5],
                'tags': row[6].split(',') if row[6] else [],
                'collection': row[7],
                'bm25_score': bm25_score
            })
        return results
    except Exception as e:
        print(f"[Search] BM25 search error: {e}")
        return []

def vector_search(
    store,
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    topk: int = 20
) -> List[Dict[str, Any]]:
    """Wrapper around store.recall for consistent interface."""
    results = store.recall(query, filters=filters, topk=topk)
    # Ensure vector_score field exists
    for r in results:
        r['vector_score'] = r.get('score', 0)
    return results

def hybrid_bm25_vector_search(
    store,
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    topk: int = 5,
    vector_weight: float = 0.6,
    bm25_weight: float = 0.4,
    rerank: bool = True
) -> List[Dict[str, Any]]:
    """
    Hybrid search combining BM25 (keyword) + Vector (semantic) scores.
    
    Best of both worlds:
    - BM25: Great for exact matches (IP addresses, names, specific terms)
    - Vector: Great for semantic similarity (concepts, paraphrases)
    
    Args:
        store: MemoryStore instance
        query: Search query
        filters: Metadata filters (tags, since, source, etc.)
        topk: Number of results
        vector_weight: Weight for vector similarity (default 0.6)
        bm25_weight: Weight for BM25 score (default 0.4)
        rerank: Whether to rerank by recency + importance
    
    Returns:
        Combined results sorted by hybrid score
    """
    # Ensure FTS5 is initialized
    init_fts5(store.conn)
    
    # Get vector results
    vector_results = vector_search(store, query, filters, topk=topk * 3)
    vector_by_id = {r['id']: r for r in vector_results}
    
    # Get BM25 results
    bm25_results = bm25_search(store.conn, query, topk=topk * 3)
    bm25_by_id = {r['id']: r for r in bm25_results}
    
    # Combine results
    all_ids = set(vector_by_id.keys()) | set(bm25_by_id.keys())
    
    combined = []
    for doc_id in all_ids:
        v_result = vector_by_id.get(doc_id, {})
        b_result = bm25_by_id.get(doc_id, {})
        
        # Get best available data
        result = v_result if v_result else b_result
        
        # Compute hybrid score
        v_score = v_result.get('vector_score', 0)
        b_score = b_result.get('bm25_score', 0)
        
        # Weighted combination
        hybrid_score = (v_score * vector_weight) + (b_score * bm25_weight)
        
        result['vector_score'] = v_score
        result['bm25_score'] = b_score
        result['hybrid_score'] = hybrid_score
        
        combined.append(result)
    
    # Sort by hybrid score
    combined.sort(key=lambda x: x['hybrid_score'], reverse=True)
    
    # Apply reranking if requested
    if rerank:
        combined = _rerank_results(combined, score_key='hybrid_score')
    
    return combined[:topk]

def hybrid_search(
    store,
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    topk: int = 5,
    rerank: bool = True
) -> List[Dict[str, Any]]:
    """
    Hybrid search combining semantic similarity with metadata filters.
    
    Args:
        store: MemoryStore instance
        query: Search query
        filters: Dict with keys like:
            - tags: List[str]
            - since: str ("7d", "24h")
            - source: str
            - min_importance: float
            - session_id: str
        topk: Number of results
        rerank: Whether to rerank by recency + importance
    
    Returns:
        List of results sorted by relevance
    """
    # Parse filters
    min_importance = filters.get('min_importance') if filters else None
    since = filters.get('since') if filters else None
    
    # Get semantic results
    results = store.recall(
        query,
        topk=topk * 2,  # Get more for filtering
        min_importance=min_importance,
        since=since
    )
    
    # Apply additional filters in Python (since Zvec filter syntax is limited)
    if filters:
        if 'tags' in filters:
            # This would need tags stored as scalars
            pass
        if 'source' in filters:
            results = [r for r in results if r.get('source') == filters['source']]
        if 'session_id' in filters:
            results = [r for r in results if r.get('session_id') == filters['session_id']]
    
    # Rerank combining semantic score with importance and recency
    if rerank:
        results = _rerank_results(results)
    
    return results[:topk]

def _rerank_results(results: List[Dict[str, Any]], score_key: str = 'score') -> List[Dict[str, Any]]:
    """
    Rerank results combining:
    - Semantic/BM25 similarity score (0.6 weight)
    - Importance (0.2 weight)
    - Recency (0.2 weight)
    """
    now = time.time()
    
    def compute_score(r):
        base_score = r.get(score_key, 0.5)
        importance = r.get('importance', 0.5)
        
        # Recency score: 1.0 if now, decaying to 0.0 after 30 days
        timestamp = r.get('timestamp', 0)
        age_days = (now - timestamp) / 86400
        recency = max(0, 1 - (age_days / 30))
        
        return (base_score * 0.6) + (importance * 0.2) + (recency * 0.2)
    
    # Add combined score and sort
    for r in results:
        r['combined_score'] = compute_score(r)
    
    results.sort(key=lambda x: x['combined_score'], reverse=True)
    return results

def find_similar(
    store,
    text: str,
    exclude_id: Optional[str] = None,
    topk: int = 3
) -> List[Dict[str, Any]]:
    """
    Find memories similar to given text.
    Useful for "find related to this" queries.
    """
    results = store.recall(text, topk=topk + 1)
    
    if exclude_id:
        results = [r for r in results if r.get('id') != exclude_id]
    
    return results[:topk]

def search_by_tag(
    store,
    tags: List[str],
    topk: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for memories with specific tags.
    Uses the new filter system.
    """
    return store.recall("", filters={"tags": tags}, topk=topk)

if __name__ == "__main__":
    from scripts.store import MemoryStore
    
    print("Testing hybrid search...")
    memory = MemoryStore()
    
    # Add some test data
    memory.remember("Learn about semantic vector search", importance=0.9, tags=["learning"])
    memory.remember("Fix server network driver on 10.0.0.5", importance=0.8, tags=["todo", "network"])
    memory.remember("Buy groceries for dinner", importance=0.3, tags=["personal"])
    memory.remember("SSH tunnel established with server at 10.0.0.5:2222", importance=0.9, tags=["server", "federation"])
    
    # Test BM25 + Vector hybrid search
    print("\n=== Hybrid BM25 + Vector Search ===")
    results = hybrid_bm25_vector_search(memory, "10.0.0.5", topk=5)
    print(f"\nFound {len(results)} results for '10.0.0.5':")
    for r in results:
        print(f"  [{r.get('hybrid_score', 0):.3f}] v:{r.get('vector_score', 0):.3f} b:{r.get('bm25_score', 0):.3f} | {r.get('text', 'N/A')[:50]}...")
    
    # Test regular semantic search
    print("\n=== Vector-Only Search ===")
    results = vector_search(memory, "10.0.0.5", topk=5)
    print(f"\nFound {len(results)} results:")
    for r in results:
        print(f"  [{r.get('vector_score', 0):.3f}] | {r.get('text', 'N/A')[:50]}...")
