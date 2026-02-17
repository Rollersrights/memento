#!/usr/bin/env python3
"""
Shared fixtures for Memento tests.
"""

import os
import sys
import tempfile
import shutil
import pytest

# Ensure the project root is on path so `memento` package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def tmp_db(tmp_path):
    """Provide a fresh temp DB path (file doesn't exist yet)."""
    return str(tmp_path / "test_memory.db")


@pytest.fixture
def store(tmp_db):
    """Provide a fresh MemoryStore backed by a temp DB."""
    from memento.store import MemoryStore
    s = MemoryStore(db_path=tmp_db)
    yield s
    s.close()


@pytest.fixture
def seeded_store(store):
    """A MemoryStore pre-loaded with diverse test data."""
    store.remember("The server IP is 192.168.1.155", importance=0.9, tags=["infra", "network"])
    store.remember("Buy milk and eggs from the grocery store", importance=0.4, tags=["shopping", "personal"])
    store.remember("Deploy the new model to production on Friday", importance=0.95, tags=["work", "deploy"])
    store.remember("The cat sat on the mat", importance=0.3, tags=["random"])
    store.remember("Machine learning uses gradient descent for optimization", importance=0.8, tags=["tech", "ml"])
    return store
