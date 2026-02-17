#!/usr/bin/env python3
"""
Shared type definitions for Memento.
"""

from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Memory:
    """Represents a single memory item.
    
    Supports dict-like access (result['text'], result.get('score'))
    for backward compatibility with code expecting dicts.
    """
    id: str
    text: str
    timestamp: int
    source: str = "unknown"
    session_id: str = "default"
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    collection: str = "knowledge"
    embedding: Optional[bytes] = None  # Raw bytes from SQLite

    # Extra fields storage for dynamic attributes
    _extra: Dict[str, Any] = field(default_factory=dict, repr=False)

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
            "collection": self.collection,
            **self._extra
        }

    # Dict-like access for backward compatibility
    def __getitem__(self, key: str) -> Any:
        if key in self._extra:
            return self._extra[key]
        return self.to_dict()[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like item assignment for dynamic fields."""
        self._extra[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._extra:
            return self._extra[key]
        return self.to_dict().get(key, default)

@dataclass
class SearchResult(Memory):
    """A memory returned from search, with a relevance score."""
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['score'] = self.score
        return d
