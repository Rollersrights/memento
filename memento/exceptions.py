#!/usr/bin/env python3
"""
Memento Exceptions
Custom exception classes for better error handling.
"""


class MementoError(Exception):
    """Base exception for all Memento errors."""
    pass


class StorageError(MementoError):
    """Raised when storage operations fail."""
    pass


class EmbeddingError(MementoError):
    """Raised when embedding generation fails."""
    pass


class SearchError(MementoError):
    """Raised when search operations fail."""
    pass


class ValidationError(MementoError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(MementoError):
    """Raised when configuration is invalid."""
    pass


class IngestError(MementoError):
    """Raised when document ingestion fails."""
    pass
