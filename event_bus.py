"""
Event Bus System
Implements a centralized event system for loose coupling between components.
Part of Phase 4 refactoring: Design Pattern Implementation.
"""

from typing import Dict, List, Callable, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum, auto
from PySide6.QtCore import QObject, Signal
import weakref
import inspect
import time


class EventPriority(Enum):
    """Priority levels for event handlers."""
    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4


@dataclass
class Event:
    """Base class for all events."""
    name: str
    data: Dict[str, Any]
    timestamp: float = None
    source: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class EventHandler:
    """Wrapper for event handler functions."""
    callback: Callable
    priority: EventPriority
    filter_func: Optional[Callable[[Event], bool]] = None
    weak_ref: bool = True
    
    def __post_init__(self):
        # Store weak reference to method if it's a bound method
        if self.weak_ref and hasattr(self.callback, '__self__'):
            # It's a bound method
            obj = self.callback.__self__
            func = self.callback.__func__
            self._weak_obj = weakref.ref(obj)
            self._func_name = func.__name__
        else:
            self._weak_obj = None
            self._func_name = None
    
    def is_alive(self) -> bool:
        """Check if handler is still valid."""
        if self._weak_obj is not None:
            return self._weak_obj() is not None
        return True
    
    def call(self, event: Event) -> bool:
        """
        Call the handler with the event.
        
        Returns:
            bool: True if successfully called, False if handler is dead
        """
        # Apply filter if present
        if self.filter_func and not self.filter_func(event):
            return True
        
        # Get actual callback
        if self._weak_obj is not None:
            obj = self._weak_obj()
            if obj is None:
                return False  # Object has been garbage collected
            callback = getattr(obj, self._func_name)
        else:
            callback = self.callback
        
        # Call handler
        try:
            # Inspect handler signature to pass appropriate arguments
            sig = inspect.signature(callback)
            if len(sig.parameters) == 0:
                callback()
            elif len(sig.parameters) == 1:
                callback(event)
            else:
                # Pass event data as kwargs if handler accepts them
                callback(event, **event.data)
            return True
        except Exception as e:
            print(f"Error in event handler: {e}")
            return True  # Don't remove handler on error


class EventBus(QObject):
    """Central event bus for application-wide events."""
    
    # Qt signal for thread-safe event delivery
    eventPosted = Signal(Event)
    
    def __init__(self):
        super().__init__()
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._subscribers_count: Dict[str, int] = {}
        self._paused_events: Set[str] = set()
        
        # Connect Qt signal for thread safety
        self.eventPosted.connect(self._process_event)
    
    def subscribe(self, event_name: str, handler: Callable,
                 priority: EventPriority = EventPriority.NORMAL,
                 filter_func: Optional[Callable[[Event], bool]] = None,
                 weak_ref: bool = True):
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of the event to subscribe to
            handler: Callable to handle the event
            priority: Priority for handler execution order
            filter_func: Optional filter function to conditionally handle events
            weak_ref: Whether to use weak references (prevents memory leaks)
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = []
            self._subscribers_count[event_name] = 0
        
        # Create handler wrapper
        event_handler = EventHandler(handler, priority, filter_func, weak_ref)
        
        # Insert handler sorted by priority
        handlers = self._handlers[event_name]
        insert_index = 0
        for i, existing in enumerate(handlers):
            if existing.priority.value < priority.value:
                insert_index = i + 1
            else:
                break
        
        handlers.insert(insert_index, event_handler)
        self._subscribers_count[event_name] += 1
    
    def unsubscribe(self, event_name: str, handler: Callable):
        """Unsubscribe from an event."""
        if event_name not in self._handlers:
            return
        
        handlers = self._handlers[event_name]
        
        # Find and remove handler
        for i, event_handler in enumerate(handlers):
            if event_handler._weak_obj is not None:
                # Compare weak referenced method
                obj = event_handler._weak_obj()
                if obj and hasattr(handler, '__self__') and obj is handler.__self__:
                    if event_handler._func_name == handler.__func__.__name__:
                        handlers.pop(i)
                        self._subscribers_count[event_name] -= 1
                        break
            else:
                # Compare regular function
                if event_handler.callback is handler:
                    handlers.pop(i)
                    self._subscribers_count[event_name] -= 1
                    break
        
        # Clean up empty handler lists
        if not handlers:
            del self._handlers[event_name]
            del self._subscribers_count[event_name]
    
    def publish(self, event_name: str, data: Dict[str, Any] = None,
               source: Optional[str] = None):
        """
        Publish an event.
        
        Args:
            event_name: Name of the event
            data: Event data
            source: Optional source identifier
        """
        if data is None:
            data = {}
        
        # Create event
        event = Event(event_name, data, source=source)
        
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Emit Qt signal for thread-safe processing
        self.eventPosted.emit(event)
    
    def _process_event(self, event: Event):
        """Process event (called from Qt event loop)."""
        # Check if event is paused
        if event.name in self._paused_events:
            return
        
        # Get handlers for this event
        if event.name not in self._handlers:
            return
        
        # Clean up dead handlers and call live ones
        handlers = self._handlers[event.name]
        live_handlers = []
        
        for handler in handlers:
            if handler.is_alive():
                handler.call(event)
                live_handlers.append(handler)
        
        # Update handler list with only live handlers
        self._handlers[event.name] = live_handlers
        self._subscribers_count[event.name] = len(live_handlers)
        
        # Clean up empty handler lists
        if not live_handlers:
            del self._handlers[event.name]
            del self._subscribers_count[event.name]
    
    def pause_event(self, event_name: str):
        """Pause processing of specific event type."""
        self._paused_events.add(event_name)
    
    def resume_event(self, event_name: str):
        """Resume processing of specific event type."""
        self._paused_events.discard(event_name)
    
    def is_paused(self, event_name: str) -> bool:
        """Check if event type is paused."""
        return event_name in self._paused_events
    
    def get_subscriber_count(self, event_name: str) -> int:
        """Get number of subscribers for an event."""
        return self._subscribers_count.get(event_name, 0)
    
    def get_all_events(self) -> List[str]:
        """Get list of all event types with subscribers."""
        return list(self._handlers.keys())
    
    def get_event_history(self, event_name: Optional[str] = None,
                         last_n: Optional[int] = None) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_name: Filter by event name
            last_n: Get only last N events
        """
        history = self._event_history
        
        if event_name:
            history = [e for e in history if e.name == event_name]
        
        if last_n:
            history = history[-last_n:]
        
        return history
    
    def clear_history(self):
        """Clear event history."""
        self._event_history.clear()
    
    def clear_all_handlers(self):
        """Remove all event handlers."""
        self._handlers.clear()
        self._subscribers_count.clear()


# Global event bus instance
_global_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return _global_event_bus


# Convenience decorators

def on_event(event_name: str, priority: EventPriority = EventPriority.NORMAL):
    """
    Decorator to automatically subscribe a method to an event.
    
    Usage:
        @on_event('sprite_loaded')
        def handle_sprite_loaded(self, event):
            print(f"Sprite loaded: {event.data['file_path']}")
    """
    def decorator(func):
        # Store event subscription info on the function
        if not hasattr(func, '_event_subscriptions'):
            func._event_subscriptions = []
        func._event_subscriptions.append((event_name, priority))
        return func
    
    return decorator


class EventBusMixin:
    """
    Mixin class to automatically handle event subscriptions from decorators.
    
    Usage:
        class MyClass(EventBusMixin):
            @on_event('sprite_loaded')
            def handle_sprite_loaded(self, event):
                pass
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event_bus = get_event_bus()
        self._subscribe_decorated_methods()
    
    def _subscribe_decorated_methods(self):
        """Subscribe all methods decorated with @on_event."""
        for name in dir(self):
            attr = getattr(self, name)
            if hasattr(attr, '_event_subscriptions'):
                for event_name, priority in attr._event_subscriptions:
                    self._event_bus.subscribe(event_name, attr, priority)
    
    def publish_event(self, event_name: str, data: Dict[str, Any] = None):
        """Convenience method to publish events."""
        self._event_bus.publish(event_name, data, source=self.__class__.__name__)


# Common event types
class CommonEvents:
    """Common event names used throughout the application."""
    
    # File events
    FILE_LOADED = "file_loaded"
    FILE_SAVED = "file_saved"
    FILE_CLOSED = "file_closed"
    
    # Sprite events
    SPRITE_LOADED = "sprite_loaded"
    SPRITE_EXTRACTED = "sprite_extracted"
    FRAME_CHANGED = "frame_changed"
    
    # UI events
    ZOOM_CHANGED = "zoom_changed"
    PAN_CHANGED = "pan_changed"
    MODE_CHANGED = "mode_changed"
    
    # Detection events
    DETECTION_STARTED = "detection_started"
    DETECTION_COMPLETED = "detection_completed"
    DETECTION_FAILED = "detection_failed"
    
    # Animation events
    ANIMATION_STARTED = "animation_started"
    ANIMATION_STOPPED = "animation_stopped"
    ANIMATION_PAUSED = "animation_paused"
    
    # Settings events
    SETTINGS_CHANGED = "settings_changed"
    THEME_CHANGED = "theme_changed"