#!/usr/bin/env python3
"""
Pure Python + NumPy vector storage - fallback for older hardware
No AVX2 required, runs on anything
"""

import os
import json
import time
import hashlib
import sqlite3
import threading
import uuid
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

import numpy as np

try:
    import sqlite_vec
    HAS_SQLITE_VEC = True
except ImportError:
    HAS_SQLITE_VEC = False

try:
    from memento.logging_config import get_logger
    from memento.config import get_config
    from memento.migrations import run_migrations
    from memento.exceptions import StorageError, ValidationError
    from memento.models import Memory, SearchResult
    from memento.vector_ops import normalize, batch_cosine_similarity
    from memento.timeout import optional_timeout, QueryTimeoutError
except ImportError:
    # Fallback if running directly without package structure
    import logging
    def get_logger(name): return logging.getLogger(name)
    class MockConfig:
        class Storage:
            db_path = os.environ.get('MEMORY_DB_PATH', os.path.expanduser("~/.memento/memory.db"))
        storage = Storage()
    def get_config(): return MockConfig()
    def run_migrations(conn): pass
    class StorageError(Exception): pass
    class ValidationError(Exception): pass
    class Memory: pass
    class SearchResult: pass
    # Timeout fallback
    from contextlib import contextmanager
    @contextmanager
    def optional_timeout(seconds):
        yield
    class QueryTimeoutError(TimeoutError): pass

logger = get_logger("store")
config = get_config()

# Default storage path (override with MEMORY_DB_PATH env var)
DEFAULT_DB_PATH = os.environ.get('MEMORY_DB_PATH', os.path.expanduser("~/.memento/memory.db"))

# Store instance cache — keyed by db_path for reuse
_stores: Dict[str, 'MemoryStore'] = {}
_stores_lock = threading.Lock()


def get_store(db_path: str = DEFAULT_DB_PATH) -> 'MemoryStore':
    """
    Factory function to get or create a MemoryStore.
    
    Reuses existing instances for the same db_path.
    Preferred over direct instantiation for singleton behavior.
    """
    with _stores_lock:
        if db_path not in _stores:
            _stores[db_path] = MemoryStore(db_path)
        return _stores[db_path]


class MemoryStore:
    """High-level interface for semantic memory using NumPy + SQLite.
    
    Use get_store() for cached/singleton access.
    Direct instantiation always creates a new instance (useful for testing).
    """
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """Initialize the memory store."""
        
        self.db_path = db_path
        self._write_lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect to SQLite with thread safety
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # Load sqlite-vec extension if available
        if HAS_SQLITE_VEC:
            self.conn.enable_load_extension(True)
            sqlite_vec.load(self.conn)
            self.conn.enable_load_extension(False)
            logger.info("Loaded sqlite-vec extension")
        
        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        
        # Run migrations
        run_migrations(self.conn)
        
        # In-memory vector cache for fast search
        self._vectors = {}  # id -> numpy array
        self._ids = []      # ordered list of ids
        
        # Search index cache
        self._search_index = None
        self._search_ids = None
        self._index_needs_refresh = True
        
        self._init_tables()
        self._init_fts5()
        self._load_vectors()
        
        # Mark as initialized
        self._initialized = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def _init_tables(self) -> None:
        """Initialize database tables."""
        # Note: embedding stored as BLOB (binary) for performance
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                source TEXT NOT NULL,
                session_id TEXT,
                importance REAL DEFAULT 0.5,
                tags TEXT,
                collection TEXT DEFAULT 'knowledge',
                embedding BLOB  -- Stored as binary (384 * 4 = 1536 bytes)
            )
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_collection ON memories(collection)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)
        """)
        
        # Initialize sqlite-vec table if available
        if HAS_SQLITE_VEC:
            self.conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding FLOAT[384]
                )
            """)
            
            # Backfill existing memories into memories_vec if needed
            cursor = self.conn.execute("SELECT COUNT(*) FROM memories_vec")
            vec_count = cursor.fetchone()[0]
            
            cursor = self.conn.execute("SELECT COUNT(*) FROM memories WHERE embedding IS NOT NULL")
            mem_count = cursor.fetchone()[0]
            
            if vec_count < mem_count:
                logger.info(f"Backfilling {mem_count - vec_count} memories into sqlite-vec")
                self.conn.execute("""
                    INSERT INTO memories_vec(id, embedding)
                    SELECT id, embedding FROM memories 
                    WHERE embedding IS NOT NULL 
                    AND id NOT IN (SELECT id FROM memories_vec)
                """)
                self.conn.commit()
        
        self.conn.commit()

    def _init_fts5(self) -> None:
        """Initialize FTS5 full-text search (one-time setup)."""
        self._fts5_available = False
        try:
            cursor = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='memories_fts'"
            )
            if not cursor.fetchone():
                self.conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                        text,
                        content='memories',
                        content_rowid='rowid'
                    )
                """)
                self.conn.execute("""
                    INSERT INTO memories_fts(rowid, text)
                    SELECT rowid, text FROM memories WHERE text IS NOT NULL
                """)
                self.conn.commit()
            self._fts5_available = True
        except Exception:
            pass  # FTS5 not available on this SQLite build
    
    def _load_vectors(self) -> None:
        """Load all vectors into memory for fast search (binary format)."""
        cursor = self.conn.execute(
            "SELECT id, embedding FROM memories WHERE embedding IS NOT NULL"
        )
        
        for row in cursor.fetchall():
            try:
                # Load from binary blob (fast) not JSON
                vec = np.frombuffer(row[1], dtype=np.float32)
                if len(vec) == 384:  # Verify correct dimension
                    self._vectors[row[0]] = vec
                    self._ids.append(row[0])
            except Exception:
                pass
        
        logger.info(f"Loaded {len(self._ids)} vectors into memory")
    
    def remember(
        self,
        text: str,
        collection: str = "knowledge",
        importance: float = 0.5,
        source: str = "conversation",
        session_id: str = "default",
        tags: Optional[List[str]] = None,
        **extra_metadata
    ) -> str:
        """
        Store a memory. Checks for near-duplicates before storing.
        
        Args:
            text: The text to remember
            collection: Which collection (conversations/documents/knowledge)
            importance: 0.0-1.0 relevance score
            source: Where this came from
            session_id: Session identifier
            tags: Optional list of tags
            **extra_metadata: Additional fields (ignored for now)
        
        Returns:
            Document ID (existing or new)
        
        Raises:
            ValidationError: If input is invalid
        """
        # Validate inputs
        if not text or not text.strip():
            raise ValidationError("Memory text cannot be empty")
            
        if len(text) > 100000:
            raise ValidationError(f"Memory text too long ({len(text)} > 100000 chars)")
            
        if tags and len(tags) > 50:
             raise ValidationError(f"Too many tags ({len(tags)} > 50)")

        # Handle imports for both module and direct execution
        try:
            from memento.embed import embed
        except ImportError:
            from embed import embed
        
        # Check for near-duplicate (same collection, similar text)
        if len(text) > 50:  # Only check substantial texts
            try:
                dup_check = self.recall(text, collection=collection, topk=1)
                if dup_check and dup_check[0].get('score', 0) > 0.95:
                    # Near-duplicate found, return existing ID
                    return dup_check[0]['id']
            except Exception:
                pass  # If check fails, proceed with store
        
        # Generate ID from content + timestamp + random salt
        doc_id = hashlib.blake2b(
            f"{text}:{time.time()}:{uuid.uuid4()}".encode(),
            digest_size=8
        ).hexdigest()
        
        # Embed the text
        embedding = embed(text)
        embedding_np = np.array(embedding, dtype=np.float32)
        
        # Normalize for cosine similarity
        norm = np.linalg.norm(embedding_np)
        if norm > 0:
            embedding_np = embedding_np / norm
        
        # Store in SQLite as binary blob (fast) not JSON (slow)
        embedding_bytes = embedding_np.tobytes()
        
        with self._write_lock:
            self.conn.execute(
                """INSERT INTO memories 
                   (id, text, timestamp, source, session_id, importance, tags, collection, embedding)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (doc_id, text, int(time.time()), source, session_id, 
                 float(importance), ','.join(tags) if tags else '', collection,
                 embedding_bytes)
            )
            
            self.conn.commit()
            
            # Sync to FTS5 for BM25 search
            try:
                self.conn.execute(
                    "INSERT INTO memories_fts(rowid, text) VALUES (last_insert_rowid(), ?)",
                    (text,)
                )
            except Exception:
                # FTS5 table might not exist, ignore
                pass

            # Sync to sqlite-vec
            if HAS_SQLITE_VEC:
                try:
                    self.conn.execute(
                        "INSERT INTO memories_vec(id, embedding) VALUES (?, ?)",
                        (doc_id, embedding_bytes)
                    )
                except Exception as e:
                    logger.warning(f"Failed to sync to sqlite-vec: {e}")
            
            self.conn.commit()
        
        # Update in-memory cache
        self._vectors[doc_id] = embedding_np
        self._ids.append(doc_id)
        
        # Mark search index as needing refresh
        self._index_needs_refresh = True
        
        return doc_id
    
    def recall(
        self,
        query: str,
        collection: Optional[str] = None,
        topk: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_importance: Optional[float] = None,
        since: Optional[str] = None,
        before: Optional[str] = None,
        timeout_ms: int = 5000  # 5 second default timeout
    ) -> List[Dict[str, Any]]:
        """
        Search memories by semantic similarity using cosine similarity.
        
        Args:
            query: Search query text
            collection: Specific collection or None (searches all)
            topk: Number of results
            filters: Additional filter criteria:
                - tags: list of tags to match (any)
                - source: exact source match
                - session_id: exact session_id match
                - text_like: substring search in text (LIKE pattern)
            min_importance: Filter by importance threshold
            since: Time filter like "7d", "24h", "30m" (after this time)
            before: Time filter like "7d", "24h", "30m" (before this time)
            timeout_ms: Query timeout in milliseconds (default 5000ms)
        
        Returns:
            List of result dicts with id, text, score, metadata
        
        Raises:
            ValidationError: If query is invalid
            QueryTimeoutError: If query exceeds timeout
        """
        if not query or not query.strip():
            return []
            
        if len(query) > 1000:
             raise ValidationError(f"Query too long ({len(query)} > 1000 chars)")
        
        # Convert timeout_ms to seconds for timeout context
        timeout_sec = timeout_ms / 1000.0 if timeout_ms > 0 else None
        
        try:
            with optional_timeout(timeout_sec):
                return self._recall_internal(
                    query, collection, topk, filters, 
                    min_importance, since, before
                )
        except QueryTimeoutError:
            logger.warning(f"Query timed out after {timeout_ms}ms: {query[:50]}...")
            raise QueryTimeoutError(f"Query timed out after {timeout_ms}ms")
    
    def _recall_internal(
        self,
        query: str,
        collection: Optional[str] = None,
        topk: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_importance: Optional[float] = None,
        since: Optional[str] = None,
        before: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Internal recall implementation (called with timeout wrapper)."""
        # Handle imports for both module and direct execution
        try:
            from memento.embed import embed
        except ImportError:
            from embed import embed
        
        if len(self._ids) == 0:
            return []
        
        # Embed query
        query_vector = np.array(embed(query), dtype=np.float32)
        
        # Normalize query
        query_norm = np.linalg.norm(query_vector)
        if query_norm > 0:
            query_vector = query_vector / query_norm
        
        # Build WHERE clause from all filters
        where_clauses = []
        params = []
        
        # Valid filter keys whitelist
        ALLOWED_FILTERS = {
            'collection', 'min_importance', 'since', 'before', 
            'after_timestamp', 'before_timestamp', 'source', 
            'session_id', 'tags', 'text_like'
        }

        # Validate filters
        if filters:
            for key in filters:
                if key not in ALLOWED_FILTERS:
                    logger.warning(f"Ignoring invalid filter key: {key}")
        
        # Legacy collection filter (can also be in filters dict)
        if collection:
            where_clauses.append("collection = ?")
            params.append(collection)
        elif filters and 'collection' in filters:
            where_clauses.append("collection = ?")
            params.append(filters['collection'])
        
        # Legacy min_importance filter
        if min_importance is not None:
            where_clauses.append("importance >= ?")
            params.append(min_importance)
        elif filters and 'min_importance' in filters:
            where_clauses.append("importance >= ?")
            params.append(filters['min_importance'])
        
        # Time filters
        if since:
            seconds = self._parse_time(since)
            cutoff = int(time.time()) - seconds
            where_clauses.append("timestamp >= ?")
            params.append(cutoff)
        elif filters and 'since' in filters:
            seconds = self._parse_time(filters['since'])
            cutoff = int(time.time()) - seconds
            where_clauses.append("timestamp >= ?")
            params.append(cutoff)
        
        if before:
            seconds = self._parse_time(before)
            cutoff = int(time.time()) - seconds
            where_clauses.append("timestamp <= ?")
            params.append(cutoff)
        elif filters and 'before' in filters:
            seconds = self._parse_time(filters['before'])
            cutoff = int(time.time()) - seconds
            where_clauses.append("timestamp <= ?")
            params.append(cutoff)
        
        # Date range filters (absolute timestamps)
        if filters:
            if 'after_timestamp' in filters:
                where_clauses.append("timestamp >= ?")
                params.append(int(filters['after_timestamp']))
            if 'before_timestamp' in filters:
                where_clauses.append("timestamp <= ?")
                params.append(int(filters['before_timestamp']))
        
        # Source filter
        if filters and 'source' in filters:
            where_clauses.append("source = ?")
            params.append(filters['source'])
        
        # Session ID filter
        if filters and 'session_id' in filters:
            where_clauses.append("session_id = ?")
            params.append(filters['session_id'])
        
        # Tags filter (stored as comma-separated, use LIKE for each tag)
        if filters and 'tags' in filters:
            tags = filters['tags']
            if isinstance(tags, str):
                tags = [tags]
            # Match any of the provided tags
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
            if tag_conditions:
                where_clauses.append(f"({' OR '.join(tag_conditions)})")
        
        # Text substring search (LIKE pattern)
        if filters and 'text_like' in filters:
            where_clauses.append("text LIKE ?")
            params.append(f"%{filters['text_like']}%")
        
        # Execute filtered query
        if where_clauses:
            where_sql = " AND ".join(where_clauses)
            cursor = self.conn.execute(
                f"SELECT id FROM memories WHERE {where_sql}",
                params
            )
            candidate_ids = [row[0] for row in cursor.fetchall()]
        else:
            candidate_ids = self._ids
        
        if not candidate_ids:
            return []
        
        # Use optimized vector search backend
        try:
            # Prefer sqlite-vec if available
            if HAS_SQLITE_VEC:
                cursor = self.conn.execute(
                    """
                    SELECT id, distance
                    FROM memories_vec
                    WHERE embedding MATCH ?
                    AND id IN (SELECT id FROM memories WHERE id IN ({placeholders}))
                    ORDER BY distance
                    LIMIT ?
                    """.replace("{placeholders}", ",".join("?" * len(candidate_ids))),
                    (query_vector.tobytes(), *candidate_ids, topk)
                )
                # sqlite-vec returns distance (lower is better), we want similarity
                similarities = [(row[0], 1.0 - row[1]) for row in cursor.fetchall()]
            else:
                from memento.vector_search import build_index, search_index
                
                # Build index from candidate vectors (cached in memory for repeated queries)
                if not hasattr(self, '_search_index') or self._index_needs_refresh:
                    candidate_vectors = {doc_id: self._vectors[doc_id] for doc_id in candidate_ids if doc_id in self._vectors}
                    self._search_index, self._search_ids = build_index(candidate_vectors, dim=384)
                    self._index_needs_refresh = False
                
                # Search using optimized backend
                search_results = search_index(self._search_index, query_vector, topk=topk)
                similarities = [(self._search_ids[idx], score) for idx, score in search_results]
            
            top_ids = [s[0] for s in similarities]
            
        except Exception as e:
            # Fallback to simple dot product
            similarities = []
            for doc_id in candidate_ids:
                if doc_id in self._vectors:
                    vec = self._vectors[doc_id]
                    sim = np.dot(query_vector, vec)
                    similarities.append((doc_id, float(sim)))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_ids = [s[0] for s in similarities[:topk]]
        
        if not top_ids:
            return []
        
        # Fetch full records
        placeholders = ','.join('?' * len(top_ids))
        cursor = self.conn.execute(
            f"""SELECT id, text, timestamp, source, session_id, 
                      importance, tags, collection
               FROM memories WHERE id IN ({placeholders})""",
            top_ids
        )
        
        # Build results preserving order
        rows = {row[0]: row for row in cursor.fetchall()}
        results = []
        
        for doc_id, score in similarities[:topk]:
            if doc_id in rows:
                row = rows[doc_id]
                result = SearchResult(
                    id=row[0],
                    text=row[1],
                    timestamp=row[2],
                    source=row[3],
                    session_id=row[4],
                    importance=row[5],
                    tags=row[6].split(',') if row[6] else [],
                    collection=row[7],
                    score=score
                )
                results.append(result)
        
        return results
    
    def batch_recall(
        self,
        queries: List[str],
        collection: Optional[str] = None,
        topk: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch search for multiple queries.
        Optimized to embed all queries at once and search efficiently.
        
        Args:
            queries: List of query strings
            collection: Optional collection filter
            topk: Results per query
            filters: Optional metadata filters
        
        Returns:
            List of result lists (one per query)
        """
        from memento.embed import embed
        
        if len(self._ids) == 0:
            return [[] for _ in queries]
        
        # Batch embed all queries at once (much faster!)
        query_vectors = embed(queries, use_cache=True)
        query_vectors_np = [np.array(qv, dtype=np.float32) for qv in query_vectors]
        
        # Normalize all queries
        for qv in query_vectors_np:
            norm = np.linalg.norm(qv)
            if norm > 0:
                qv /= norm
        
        # Build WHERE clause (same for all queries)
        where_clauses = []
        params = []
        
        if collection:
            where_clauses.append("collection = ?")
            params.append(collection)
        
        if filters:
            if 'min_importance' in filters:
                where_clauses.append("importance >= ?")
                params.append(filters['min_importance'])
            if 'source' in filters:
                where_clauses.append("source = ?")
                params.append(filters['source'])
            if 'tags' in filters:
                tags = filters['tags']
                if isinstance(tags, str):
                    tags = [tags]
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                if tag_conditions:
                    where_clauses.append(f"({' OR '.join(tag_conditions)})")
        
        # Get candidate IDs (same for all queries in batch)
        if where_clauses:
            where_sql = " AND ".join(where_clauses)
            cursor = self.conn.execute(
                f"SELECT id FROM memories WHERE {where_sql}",
                params
            )
            candidate_ids = [row[0] for row in cursor.fetchall()]
        else:
            candidate_ids = self._ids
        
        if not candidate_ids:
            return [[] for _ in queries]
        
        # Batch search using optimized backend
        try:
            from memento.vector_search import build_index, batch_search
            
            # Build index once
            if not hasattr(self, '_search_index') or self._index_needs_refresh:
                candidate_vectors = {doc_id: self._vectors[doc_id] for doc_id in candidate_ids if doc_id in self._vectors}
                self._search_index, self._search_ids = build_index(candidate_vectors, dim=384)
                self._index_needs_refresh = False
            
            # Batch search all queries at once
            batch_results = batch_search(self._search_index, query_vectors_np, topk=topk)
            
        except Exception as e:
            # Fallback: search each query individually
            batch_results = []
            for query_vector in query_vectors_np:
                similarities = []
                for doc_id in candidate_ids:
                    if doc_id in self._vectors:
                        vec = self._vectors[doc_id]
                        sim = np.dot(query_vector, vec)
                        similarities.append((doc_id, float(sim)))
                similarities.sort(key=lambda x: x[1], reverse=True)
                batch_results.append([(self._ids.index(s[0]) if s[0] in self._ids else 0, s[1]) for s in similarities[:topk]])
        
        # Fetch all unique IDs needed
        all_top_ids = set()
        for results in batch_results:
            for idx, _ in results:
                if idx < len(self._search_ids):
                    all_top_ids.add(self._search_ids[idx])
        
        if not all_top_ids:
            return [[] for _ in queries]
        
        # Batch fetch all records
        placeholders = ','.join('?' * len(all_top_ids))
        cursor = self.conn.execute(
            f"""SELECT id, text, timestamp, source, session_id, 
                      importance, tags, collection
               FROM memories WHERE id IN ({placeholders})""",
            list(all_top_ids)
        )
        rows = {row[0]: row for row in cursor.fetchall()}
        
        # Build results for each query
        all_results = []
        for query_idx, results in enumerate(batch_results):
            query_results = []
            for idx, score in results:
                if idx < len(self._search_ids):
                    doc_id = self._search_ids[idx]
                    if doc_id in rows:
                        row = rows[doc_id]
                        query_results.append({
                            'id': row[0],
                            'text': row[1],
                            'timestamp': row[2],
                            'source': row[3],
                            'session_id': row[4],
                            'importance': row[5],
                            'tags': row[6].split(',') if row[6] else [],
                            'collection': row[7],
                            'score': score
                        })
            all_results.append(query_results)
        
        return all_results
    
    def get_recent(
        self,
        n: int = 10,
        collection: str = "knowledge"
    ) -> List[Dict[str, Any]]:
        """Get the N most recent memories from a collection."""
        cursor = self.conn.execute(
            """SELECT id, text, timestamp, source, session_id, 
                      importance, tags, collection
               FROM memories
               WHERE collection = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (collection, n)
        )
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'text': row[1],
                'timestamp': row[2],
                'source': row[3],
                'session_id': row[4],
                'importance': row[5],
                'tags': row[6].split(',') if row[6] else [],
                'collection': row[7]
            })
        
        return results
    
    def delete(self, doc_id: str, collection: str = "knowledge") -> bool:
        """Delete a memory by ID."""
        try:
            with self._write_lock:
                self.conn.execute("DELETE FROM memories WHERE id = ?", (doc_id,))
                self.conn.commit()
            
            # Update cache - remove from both dict and list
            if doc_id in self._vectors:
                del self._vectors[doc_id]
                self._ids = [id for id in self._ids if id != doc_id]
            
            return True
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics about all collections."""
        cursor = self.conn.execute(
            "SELECT collection, COUNT(*) FROM memories GROUP BY collection"
        )
        counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        backend = "sqlite-vec" if HAS_SQLITE_VEC else "numpy"
        
        return {
            'collections': counts,
            'total_vectors': len(self._ids),
            'db_path': self.db_path,
            'backend': backend
        }
    
    def _parse_time(self, time_str: str) -> int:
        """Parse time strings like '7d', '24h', '30m' to seconds."""
        unit = time_str[-1]
        value = int(time_str[:-1])
        
        multipliers = {
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800
        }
        
        return value * multipliers.get(unit, 86400)
    
    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
    
    def backup(self, backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the memory database.
        
        Args:
            backup_path: Path for backup (default: memory.db.backup-TIMESTAMP)
        
        Returns:
            Path to backup file
        """
        from datetime import datetime
        import shutil
        
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            backup_path = f"{self.db_path}.backup-{timestamp}"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(backup_path) or '.', exist_ok=True)
        
        # Copy database file
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    
    def export_json(self, export_path: Optional[str] = None) -> str:
        """
        Export all memories to JSON format.
        
        Args:
            export_path: Path for export (default: memory-export-TIMESTAMP.json)
        
        Returns:
            Path to export file
        """
        from datetime import datetime
        import json
        
        if export_path is None:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            export_path = f"memory-export-{timestamp}.json"
        
        # Fetch all memories
        cursor = self.conn.execute(
            """SELECT id, text, timestamp, source, session_id, 
                      importance, tags, collection
               FROM memories ORDER BY timestamp DESC"""
        )
        
        memories = []
        for row in cursor.fetchall():
            memories.append({
                'id': row[0],
                'text': row[1],
                'timestamp': row[2],
                'source': row[3],
                'session_id': row[4],
                'importance': row[5],
                'tags': row[6].split(',') if row[6] else [],
                'collection': row[7]
            })
        
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_memories': len(memories),
            'db_path': self.db_path,
            'memories': memories
        }
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(memories)} memories to: {export_path}")
        return export_path
    
    def __del__(self) -> None:
        """Destructor to ensure connection closes."""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    # Test
    print("Initializing MemoryStore (NumPy backend)...")
    memory = MemoryStore()
    
    print("\nStoring test memories...")
    id1 = memory.remember(
        "I need to fix the WiFi driver on the Mac Mini",
        importance=0.8,
        tags=["todo", "mac_mini", "wifi"]
    )
    print(f"Stored: {id1}")
    
    id2 = memory.remember(
        "Zvec is Alibaba's new embedded vector database",
        importance=0.9,
        tags=["tech", "vector_db"]
    )
    print(f"Stored: {id2}")
    
    id3 = memory.remember(
        "I had breakfast at 8am today",
        importance=0.3,
        tags=["personal"]
    )
    print(f"Stored: {id3}")
    
    print("\nSearching for 'WiFi'...")
    results = memory.recall("WiFi", topk=3)
    for r in results:
        print(f"  - {r['id']}: {r['text'][:50]}... (score: {r['score']:.3f})")
    
    print("\nSearching for 'database'...")
    results = memory.recall("database", topk=3)
    for r in results:
        print(f"  - {r['id']}: {r['text'][:50]}... (score: {r['score']:.3f})")
    
    print("\nStats:")
    print(memory.stats())
