#!/usr/bin/env python3
"""
Memento Logging Configuration
Centralized logging setup for all modules.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Default log format
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
SIMPLE_FORMAT = "%(levelname)s: %(message)s"

# Module-level loggers cache
_loggers = {}

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging for Memento.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file to log to
        format_string: Custom format string
    
    Returns:
        Root logger
    """
    formatter = logging.Formatter(format_string or DEFAULT_FORMAT)
    
    # Root logger
    root_logger = logging.getLogger('memento')
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    root_logger.addHandler(console)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.
    
    Args:
        name: Module name (usually __name__)
    
    Returns:
        Logger instance
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(f'memento.{name}')
    return _loggers[name]

def set_level(level: str) -> None:
    """Set logging level for all memento loggers."""
    logging.getLogger('memento').setLevel(getattr(logging, level.upper()))

class LoggerMixin:
    """Mixin to add logger to classes."""
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger

# Convenience function for scripts
def enable_debug():
    """Enable debug logging."""
    setup_logging(level="DEBUG")
    get_logger('logging').debug("Debug logging enabled")
