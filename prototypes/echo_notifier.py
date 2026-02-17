"""
Echo Notification Module for Memory System Visibility

Provides lightweight CLI feedback when memories are stored.
Non-intrusive, one-line notifications that can be disabled.
"""

import sys
from typing import Optional
from dataclasses import dataclass


@dataclass
class StorageNotification:
    """Represents a memory storage event."""
    text: str
    confidence: float
    collection: str
    source: str = "auto"
    
    def format(self, compact: bool = True) -> str:
        """Format notification for display."""
        if compact:
            # Truncate text to ~50 chars
            preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
            return f"💾 Stored: \"{preview}\" (confidence: {self.confidence:.2f})"
        else:
            return f"""
💾 Memory Stored
   Preview: {self.text[:80]}...
   Confidence: {self.confidence:.2f}
   Collection: {self.collection}
   Source: {self.source}
"""


class EchoNotifier:
    """
    Handles inline notifications for memory storage events.
    
    Usage:
        notifier = EchoNotifier(enabled=True, min_confidence=0.6)
        notifier.notify("Important fact", confidence=0.85, collection="knowledge")
    
    Config:
        - enabled: Turn notifications on/off
        - min_confidence: Only show for scores above this
        - compact: One-line vs detailed output
        - emoji: Include visual indicator
    """
    
    def __init__(
        self,
        enabled: bool = True,
        min_confidence: float = 0.6,
        compact: bool = True,
        emoji: bool = True,
        output_stream = sys.stderr  # Use stderr to avoid polluting stdout
    ):
        self.enabled = enabled
        self.min_confidence = min_confidence
        self.compact = compact
        self.emoji = emoji
        self.output = output_stream
        self._stats = {"stored": 0, "notified": 0, "skipped": 0}
    
    def notify(
        self,
        text: str,
        confidence: float,
        collection: str = "conversations",
        source: str = "auto",
        force: bool = False
    ) -> bool:
        """
        Send notification if criteria met.
        
        Args:
            text: The memory text (preview shown)
            confidence: Storage confidence score (0.0-1.0)
            collection: Which collection was stored to
            source: 'auto', 'explicit', 'manual'
            force: Show even if below min_confidence
        
        Returns:
            True if notification was shown
        """
        if not self.enabled:
            self._stats["skipped"] += 1
            return False
        
        # Always show explicit "remember this" commands
        is_explicit = source == "explicit" or confidence >= 0.9
        
        if not force and confidence < self.min_confidence and not is_explicit:
            self._stats["skipped"] += 1
            return False
        
        notification = StorageNotification(
            text=text,
            confidence=confidence,
            collection=collection,
            source=source
        )
        
        message = notification.format(compact=self.compact)
        
        if not self.emoji:
            message = message.replace("💾 ", "")
        
        print(message, file=self.output, flush=True)
        self._stats["notified"] += 1
        return True
    
    def notify_explicit(self, text: str, collection: str = "knowledge") -> bool:
        """Shortcut for explicit 'remember this' commands."""
        return self.notify(
            text=text,
            confidence=1.0,
            collection=collection,
            source="explicit",
            force=True
        )
    
    def get_stats(self) -> dict:
        """Get notification statistics."""
        return self._stats.copy()
    
    def summary(self) -> str:
        """Get session summary."""
        return f"📊 Memory notifications: {self._stats['notified']} shown, {self._stats['skipped']} skipped"


# Global notifier instance (singleton pattern)
_default_notifier: Optional[EchoNotifier] = None


def get_notifier() -> EchoNotifier:
    """Get or create the default notifier."""
    global _default_notifier
    if _default_notifier is None:
        # Auto-detect: enabled if running in interactive terminal
        enabled = sys.stderr.isatty() if hasattr(sys.stderr, 'isatty') else True
        _default_notifier = EchoNotifier(enabled=enabled)
    return _default_notifier


def configure_notifier(**kwargs):
    """Configure the global notifier."""
    global _default_notifier
    _default_notifier = EchoNotifier(**kwargs)


# Convenience functions
def notify_storage(text: str, confidence: float, **kwargs) -> bool:
    """Quick notify using global notifier."""
    return get_notifier().notify(text, confidence, **kwargs)


def notify_explicit(text: str, **kwargs) -> bool:
    """Quick explicit notify using global notifier."""
    return get_notifier().notify_explicit(text, **kwargs)


# Example usage / demo
if __name__ == "__main__":
    print("=== Echo Notifier Demo ===\n")
    
    notifier = EchoNotifier(enabled=True, min_confidence=0.6)
    
    # Simulate various storage events
    print("1. High confidence auto-store:")
    notifier.notify(
        "Implement resilient memory system with auto-store and health monitoring",
        confidence=0.87,
        collection="conversations"
    )
    
    print("\n2. Explicit 'remember this':")
    notifier.notify_explicit(
        "Bob's SSH tunnel config: 192.168.1.155",
        collection="knowledge"
    )
    
    print("\n3. Low confidence (won't show):")
    notifier.notify(
        "ok, thanks",
        confidence=0.25,
        collection="conversations"
    )
    
    print("\n4. Detailed format:")
    notifier.compact = False
    notifier.notify(
        "Full system test passed with 274,235x speedup improvement",
        confidence=0.95,
        collection="conversations",
        source="test"
    )
    
    print("\n" + notifier.summary())
