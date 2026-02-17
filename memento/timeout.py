#!/usr/bin/env python3
"""
Timeout utilities for Memento
Cross-platform query timeout support
"""

import signal
import sys
import threading
import time
from typing import Optional, Callable, Any
from contextlib import contextmanager

class QueryTimeoutError(TimeoutError):
    """Raised when a query exceeds its timeout."""
    pass

# Platform-specific timeout implementation
_is_windows = sys.platform == 'win32'

if not _is_windows:
    # Unix: Use SIGALRM
    @contextmanager
    def query_timeout(seconds: float):
        """Context manager for query timeout (Unix)."""
        def signal_handler(signum, frame):
            raise QueryTimeoutError(f"Query timed out after {seconds}s")
        
        # Set up signal handler
        old_handler = signal.signal(signal.SIGALRM, signal_handler)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)

else:
    # Windows: Use threading-based timeout
    @contextmanager
    def query_timeout(seconds: float):
        """Context manager for query timeout (Windows)."""
        timer = threading.Timer(seconds, lambda: None)
        timer.start()
        
        start_time = time.time()
        try:
            yield
            timer.cancel()
        except Exception:
            timer.cancel()
            raise
        finally:
            if timer.is_alive():
                timer.cancel()
            else:
                raise QueryTimeoutError(f"Query timed out after {seconds}s")

@contextmanager  
def optional_timeout(seconds: Optional[float]):
    """Context manager that optionally applies timeout."""
    if seconds is None or seconds <= 0:
        yield
    else:
        with query_timeout(seconds):
            yield

def with_timeout(func: Callable, timeout: float, *args, **kwargs) -> Any:
    """
    Execute a function with timeout.
    
    Args:
        func: Function to execute
        timeout: Timeout in seconds
        *args, **kwargs: Arguments to pass to function
    
    Returns:
        Function result
    
    Raises:
        QueryTimeoutError: If function exceeds timeout
    """
    with query_timeout(timeout):
        return func(*args, **kwargs)

if __name__ == "__main__":
    # Test timeout
    print(f"Platform: {'Windows' if _is_windows else 'Unix'}")
    
    # Test 1: Normal operation (should succeed)
    try:
        with query_timeout(5.0):
            time.sleep(0.1)
            print("✅ Test 1 passed: Normal operation")
    except QueryTimeoutError:
        print("❌ Test 1 failed: Should not timeout")
    
    # Test 2: Timeout (should fail)
    try:
        with query_timeout(0.1):
            time.sleep(1.0)
        print("❌ Test 2 failed: Should have timed out")
    except QueryTimeoutError as e:
        print(f"✅ Test 2 passed: Caught timeout - {e}")
    
    # Test 3: Optional timeout (None = no timeout)
    try:
        with optional_timeout(None):
            time.sleep(0.1)
        print("✅ Test 3 passed: Optional timeout (None) works")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
    
    print("\nAll tests complete!")
