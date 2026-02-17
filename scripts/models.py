#!/usr/bin/env python3
"""
Shared type definitions for Memento.
"""

from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Memory:
    """Represents a single memory item."""
    id: str
    text: str
    timestamp: int
    source: str = "unknown"
    session_id: str = "default"
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    collection: str = "knowledge"
    embedding: Optional[bytes] = None  # Raw bytes from SQLite

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "timestamp": self.timestamp,
            "source": self.source,
            "session_id": self.session_id,
            "importance": self.importance,
            "tags": self.tags,
            "collection": self.collection
        }

@dataclass
class SearchResult(Memory):
    """A memory returned from search, with a relevance score."""
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['score'] = self.score
        return d
