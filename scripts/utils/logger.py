import logging
import sys
import os

def setup_logger(name: str = "memento") -> logging.Logger:
    """Set up a logger with a nice format."""
    logger = logging.getLogger(name)
    
    # Don't add handlers if they already exist (avoid duplicate logs)
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Check if DEBUG env var is set
    if os.environ.get("MEMENTO_DEBUG", "").lower() in ("1", "true", "yes"):
        logger.setLevel(logging.DEBUG)
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Default instance
logger = setup_logger()
