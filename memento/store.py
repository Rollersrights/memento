#!/usr/bin/env python3
"""
Vector storage using sqlite-vec only.
"""

import os
import time
import hashlib
import sqlite3
import threading
import uuid
from typing import List, Dict, Optional, Any
from pathlib import Path

import numpy as np
import sqlite_vec

try:
    from memento.logging_config import get_logger
    from memento.config import get_config
    from memento.migrations import run_migrations
    from memento.exceptions import StorageError, ValidationError
    from memento.models import Memory, SearchResult
    from memento.timeout import optional_timeout, QueryTimeoutError
except ImportError:
    import logging
    def get_logger(name): return logging.getLogger(name)
    class MockConfig:
        class Storage:
            db_path = os.environ.get('MEMORY_DB_PATH', os.path.expanduser("~/.openclaw/memento/memory.db"))
        storage = Storage()
    def get_config(): return MockConfig()
    def run_migrations(conn): pass
    class StorageError(Exception): pass
    class ValidationError(Exception): pass
    class Memory: pass
    class SearchResult: pass
    from contextlib import contextmanager
    @contextmanager
    def optional_timeout(seconds):
        yield
    class QueryTimeoutError(TimeoutError): pass

logger = get_logger("store")
config = get_config()
DEFAULT_DB_PATH = os.environ.get('MEMORY_DB_PATH', config.storage.db_path)

_stores: Dict[str, 'MemoryStore'] = {}
_stores_lock = threading.Lock()


def get_store(db_path: str = DEFAULT_DB_PATH) -> 'MemoryStore':
    """Factory function to get or create a MemoryStore."""
    with _stores_lock:
        if db_path not in _stores:
            _stores[db_path] = MemoryStore(db_path)
        return _stores[db_path]


class MemoryStore:
    """High-level interface for semantic memory using sqlite-vec."""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._write_lock = threading.Lock()
        self._rate_limit_cache: Dict[str, List[float]] = {}
        self._rate_limit_lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        
        run_migrations(self.conn)
        self._init_tables()
        self._init_fts5()
        
        self._initialized = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def _init_tables(self) -> None:
        """Initialize database tables."""
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
                embedding BLOB
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_collection ON memories(collection)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
        
        # sqlite-vec virtual table
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(
                id TEXT PRIMARY KEY,
                embedding FLOAT[384]
            )
        """)
        
        # Backfill if needed
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
        """Initialize FTS5 full-text search."""
        self._fts5_available = False
        try:
            cursor = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='memories_fts'"
            )
            if not cursor.fetchone():
                self.conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                        text, content='memories', content_rowid='rowid'
                    )
                """)
                self.conn.execute("""
                    INSERT INTO memories_fts(rowid, text)
                    SELECT rowid, text FROM memories WHERE text IS NOT NULL
                """)
                self.conn.commit()
            self._fts5_available = True
        except Exception:
            pass
    
    def _check_rate_limit(self, key: str, limit: int = 60, window: int = 60) -> bool:
        """Simple rate limiter."""
        now = time.time()
        with self._rate_limit_lock:
            if key not in self._rate_limit_cache:
                self._rate_limit_cache[key] = []
            self._rate_limit_cache[key] = [t for t in self._rate_limit_cache[key] if t > now - window]
            if len(self._rate_limit_cache[key]) >= limit:
                return False
            self._rate_limit_cache[key].append(now)
            return True

    def _sanitize_text(self, text: str) -> str:
        """Sanitize input text."""
        if not text:
            return ""
        return "".join(char for char in text if char.isprintable() or char in "\n\r\t")

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
        """Store a memory."""
        rl_key = source or "global"
        if not self._check_rate_limit(rl_key):
            logger.warning(f"Rate limit exceeded for source: {rl_key}")
            raise StorageError(f"Rate limit exceeded for source: {rl_key}")

        text = self._sanitize_text(text)
        if not text or not text.strip():
            raise ValidationError("Memory text cannot be empty")
        if len(text) > 100000:
            raise ValidationError(f"Memory text too long ({len(text)} > 100000 chars)")
        if tags and len(tags) > 50:
            raise ValidationError(f"Too many tags ({len(tags)} > 50)")

        try:
            from memento.embed import embed
        except ImportError:
            from embed import embed
        
        # Check for near-duplicate
        if len(text) > 50:
            try:
                dup_check = self.recall(text, collection=collection, topk=1)
                if dup_check and dup_check[0].get('score', 0) > 0.95:
                    return dup_check[0]['id']
            except Exception:
                pass
        
        doc_id = hashlib.blake2b(
            f"{text}:{time.time()}:{uuid.uuid4()}".encode(), digest_size=8
        ).hexdigest()
        
        embedding = embed(text)
        embedding_np = np.array(embedding, dtype=np.float32)
        norm = np.linalg.norm(embedding_np)
        if norm > 0:
            embedding_np = embedding_np / norm
        embedding_bytes = embedding_np.tobytes()
        
        with self._write_lock:
            self.conn.execute(
                """INSERT INTO memories 
                   (id, text, timestamp, source, session_id, importance, tags, collection, embedding)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (doc_id, text, int(time.time()), source, session_id, 
                 float(importance), ','.join(tags) if tags else '', collection, embedding_bytes)
            )
            
            try:
                self.conn.execute(
                    "INSERT INTO memories_fts(rowid, text) VALUES (last_insert_rowid(), ?)", (text,)
                )
            except Exception:
                pass

            try:
                self.conn.execute(
                    "INSERT INTO memories_vec(id, embedding) VALUES (?, ?)",
                    (doc_id, embedding_bytes)
                )
            except Exception as e:
                logger.warning(f"Failed to sync to sqlite-vec: {e}")
            
            self.conn.commit()
        
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
        timeout_ms: int = 5000
    ) -> List[Dict[str, Any]]:
        """Search memories by semantic similarity."""
        if not query or not query.strip():
            return []
        if len(query) > 1000:
            raise ValidationError(f"Query too long ({len(query)} > 1000 chars)")
        
        timeout_sec = timeout_ms / 1000.0 if timeout_ms > 0 else None
        try:
            with optional_timeout(timeout_sec):
                return self._recall_internal(query, collection, topk, filters, 
                                             min_importance, since, before)
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
        """Internal recall using sqlite-vec."""
        try:
            from memento.embed import embed
        except ImportError:
            from embed import embed
        
        query_vector = np.array(embed(query), dtype=np.float32)
        query_norm = np.linalg.norm(query_vector)
        if query_norm > 0:
            query_vector = query_vector / query_norm
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        ALLOWED_FILTERS = {'collection', 'min_importance', 'since', 'before', 
                          'after_timestamp', 'before_timestamp', 'source', 
                          'session_id', 'tags', 'text_like'}
        
        if filters:
            for key in filters:
                if key not in ALLOWED_FILTERS:
                    logger.warning(f"Ignoring invalid filter key: {key}")
        
        if collection:
            where_clauses.append("collection = ?")
            params.append(collection)
        elif filters and 'collection' in filters:
            where_clauses.append("collection = ?")
            params.append(filters['collection'])
        
        if min_importance is not None:
            where_clauses.append("importance >= ?")
            params.append(min_importance)
        elif filters and 'min_importance' in filters:
            where_clauses.append("importance >= ?")
            params.append(filters['min_importance'])
        
        if since:
            cutoff = int(time.time()) - self._parse_time(since)
            where_clauses.append("timestamp >= ?")
            params.append(cutoff)
        elif filters and 'since' in filters:
            cutoff = int(time.time()) - self._parse_time(filters['since'])
            where_clauses.append("timestamp >= ?")
            params.append(cutoff)
        
        if before:
            cutoff = int(time.time()) - self._parse_time(before)
            where_clauses.append("timestamp <= ?")
            params.append(cutoff)
        elif filters and 'before' in filters:
            cutoff = int(time.time()) - self._parse_time(filters['before'])
            where_clauses.append("timestamp <= ?")
            params.append(cutoff)
        
        if filters:
            if 'after_timestamp' in filters:
                where_clauses.append("timestamp >= ?")
                params.append(int(filters['after_timestamp']))
            if 'before_timestamp' in filters:
                where_clauses.append("timestamp <= ?")
                params.append(int(filters['before_timestamp']))
            if 'source' in filters:
                where_clauses.append("source = ?")
                params.append(filters['source'])
            if 'session_id' in filters:
                where_clauses.append("session_id = ?")
                params.append(filters['session_id'])
            if 'tags' in filters:
                tags = filters['tags'] if isinstance(filters['tags'], list) else [filters['tags']]
                tag_conditions = ["tags LIKE ?" for _ in tags]
                params.extend([f"%{tag}%" for tag in tags])
                if tag_conditions:
                    where_clauses.append(f"({' OR '.join(tag_conditions)})")
            if 'text_like' in filters:
                where_clauses.append("text LIKE ?")
                params.append(f"%{filters['text_like']}%")
        
        # Use sqlite-vec for vector search
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # sqlite-vec requires k = ? for KNN queries
        cursor = self.conn.execute(
            f"""
            SELECT v.id, v.distance
            FROM memories_vec v
            JOIN memories m ON m.id = v.id
            WHERE v.embedding MATCH ?
            AND k = ?
            AND {where_sql}
            ORDER BY v.distance
            """,
            (query_vector.tobytes(), topk, *params)
        )
        
        similarities = [(row[0], 1.0 - row[1]) for row in cursor.fetchall()]
        top_ids = [s[0] for s in similarities]
        
        if not top_ids:
            return []
        
        placeholders = ','.join('?' * len(top_ids))
        cursor = self.conn.execute(
            f"""SELECT id, text, timestamp, source, session_id, 
                      importance, tags, collection
               FROM memories WHERE id IN ({placeholders})""",
            top_ids
        )
        
        rows = {row[0]: row for row in cursor.fetchall()}
        results = []
        
        for doc_id, score in similarities:
            if doc_id in rows:
                row = rows[doc_id]
                result = SearchResult(
                    id=row[0], text=row[1], timestamp=row[2], source=row[3],
                    session_id=row[4], importance=row[5],
                    tags=row[6].split(',') if row[6] else [],
                    collection=row[7], score=score
                )
                results.append(result)
        
        return results
    
    def get_recent(self, n: int = 10, collection: str = "knowledge") -> List[Dict[str, Any]]:
        """Get the N most recent memories."""
        cursor = self.conn.execute(
            """SELECT id, text, timestamp, source, session_id, 
                      importance, tags, collection
               FROM memories WHERE collection = ? ORDER BY timestamp DESC LIMIT ?""",
            (collection, n)
        )
        return [{
            'id': row[0], 'text': row[1], 'timestamp': row[2], 'source': row[3],
            'session_id': row[4], 'importance': row[5],
            'tags': row[6].split(',') if row[6] else [], 'collection': row[7]
        } for row in cursor.fetchall()]
    
    def delete(self, doc_id: str, collection: str = "knowledge") -> bool:
        """Delete a memory by ID."""
        try:
            with self._write_lock:
                self.conn.execute("DELETE FROM memories WHERE id = ?", (doc_id,))
                self.conn.execute("DELETE FROM memories_vec WHERE id = ?", (doc_id,))
                self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics."""
        cursor = self.conn.execute("SELECT collection, COUNT(*) FROM memories GROUP BY collection")
        counts = {row[0]: row[1] for row in cursor.fetchall()}
        cursor = self.conn.execute("SELECT COUNT(*) FROM memories_vec")
        vec_count = cursor.fetchone()[0]
        return {'collections': counts, 'total_vectors': vec_count, 'db_path': self.db_path, 'backend': 'sqlite-vec'}
    
    def _parse_time(self, time_str: str) -> int:
        """Parse time strings like '7d', '24h', '30m' to seconds."""
        unit = time_str[-1]
        value = int(time_str[:-1])
        multipliers = {'m': 60, 'h': 3600, 'd': 86400, 'w': 604800}
        return value * multipliers.get(unit, 86400)
    
    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
    
    def backup(self, backup_path: Optional[str] = None) -> str:
        """Create a backup of the database."""
        from datetime import datetime
        import shutil
        
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            backup_path = f"{self.db_path}.backup-{timestamp}"
        
        os.makedirs(os.path.dirname(backup_path) or '.', exist_ok=True)
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    
    def __del__(self) -> None:
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == "__main__":
    print("Initializing MemoryStore (sqlite-vec)...")
    memory = MemoryStore()
    
    print("\nStoring test memories...")
    id1 = memory.remember("I need to fix the WiFi driver", importance=0.8, tags=["todo"])
    print(f"Stored: {id1}")
    id2 = memory.remember("Zvec is a vector database", importance=0.9, tags=["tech"])
    print(f"Stored: {id2}")
    
    print("\nSearching for 'WiFi'...")
    results = memory.recall("WiFi", topk=3)
    for r in results:
        print(f"  - {r['id']}: {r['text'][:50]}... (score: {r['score']:.3f})")
    
    print("\nStats:", memory.stats())
