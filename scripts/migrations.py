#!/usr/bin/env python3
"""
Database Migration System
Handles schema versioning and updates for SQLite.
"""

import sqlite3
import logging
from typing import List, Callable

logger = logging.getLogger("memento.migrations")

# Current schema version
CURRENT_VERSION = 1

def run_migrations(conn: sqlite3.Connection):
    """Check schema version and apply pending migrations."""
    logger.info("Checking database schema version...")
    
    # Ensure migrations table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Get current version
    cursor = conn.execute("SELECT MAX(version) FROM schema_version")
    current = cursor.fetchone()[0] or 0
    
    logger.debug(f"Current DB version: {current}")
    
    if current < CURRENT_VERSION:
        _apply_updates(conn, current, CURRENT_VERSION)
    else:
        logger.debug("Schema is up to date.")

def _apply_updates(conn: sqlite3.Connection, start_ver: int, target_ver: int):
    """Apply migration steps sequentially."""
    for ver in range(start_ver + 1, target_ver + 1):
        logger.info(f"Applying migration v{ver}...")
        try:
            if ver == 1:
                _migration_v1(conn)
            # Future migrations:
            # elif ver == 2:
            #     _migration_v2(conn)
            
            # Record success
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (ver,))
            conn.commit()
            logger.info(f"Migration v{ver} complete.")
            
        except Exception as e:
            logger.error(f"Migration v{ver} failed: {e}")
            conn.rollback()
            raise RuntimeError(f"Database migration failed at v{ver}") from e

def _migration_v1(conn: sqlite3.Connection):
    """v1: Initial schema setup (idempotent)."""
    # Just ensure tables exist (store.py does this, but we formalize it here)
    # This acts as the baseline
    pass
