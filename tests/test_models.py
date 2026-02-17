#!/usr/bin/env python3
"""
Tests for Memento data models.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memento.models import Memory, SearchResult


class TestMemoryModel:
    def test_creation(self):
        m = Memory(id="abc", text="Hello", timestamp=1000)
        assert m.id == "abc"
        assert m.text == "Hello"
        assert m.timestamp == 1000

    def test_defaults(self):
        m = Memory(id="abc", text="Hello", timestamp=1000)
        assert m.source == "unknown"
        assert m.importance == 0.5
        assert m.tags == []
        assert m.collection == "knowledge"

    def test_to_dict(self):
        m = Memory(id="abc", text="Hello", timestamp=1000, tags=["a", "b"])
        d = m.to_dict()
        assert d['id'] == "abc"
        assert d['tags'] == ["a", "b"]

    def test_dict_like_access(self):
        m = Memory(id="abc", text="Hello", timestamp=1000)
        assert m['id'] == "abc"
        assert m['text'] == "Hello"
        assert m.get('id') == "abc"
        assert m.get('missing', 'default') == 'default'

    def test_contains(self):
        m = Memory(id="abc", text="Hello", timestamp=1000)
        assert 'id' in m
        assert 'text' in m
        assert 'nonexistent' not in m

    def test_extra_fields(self):
        m = Memory(id="abc", text="Hello", timestamp=1000)
        m['score'] = 0.95
        assert m['score'] == 0.95
        assert m.get('score') == 0.95

    def test_datetime_property(self):
        import datetime
        m = Memory(id="abc", text="Hello", timestamp=1000000000)
        dt = m.datetime
        assert isinstance(dt, datetime.datetime)


class TestSearchResultModel:
    def test_creation(self):
        sr = SearchResult(id="abc", text="Hello", timestamp=1000, score=0.95)
        assert sr.score == 0.95
        assert sr.id == "abc"

    def test_to_dict_includes_score(self):
        sr = SearchResult(id="abc", text="Hello", timestamp=1000, score=0.95)
        d = sr.to_dict()
        assert 'score' in d
        assert d['score'] == 0.95

    def test_inherits_memory(self):
        sr = SearchResult(id="abc", text="Hello", timestamp=1000, score=0.95)
        assert sr['text'] == "Hello"
        assert isinstance(sr, Memory)
