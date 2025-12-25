"""
Base Manager Classes
===================

Provides base classes and utilities for implementing singleton managers with consistent patterns.
All manager classes now use the consolidated singleton pattern for consistency and maintainability.

Consolidated Singleton Pattern:
------------------------------
All managers now implement the same simplified singleton pattern:

```python
# Singleton implementation (consolidated pattern)
_manager_instance: Optional[ManagerClass] = None

def get_manager_class(*args, **kwargs) -> ManagerClass:
    \"\"\"Get the global manager instance.\"\"\"
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ManagerClass(*args, **kwargs)
    return _manager_instance

def reset_manager_class():  # Optional - only for managers that support reset
    \"\"\"Reset the global manager instance (for testing).\"\"\"
    global _manager_instance
    _manager_instance = None
```

This approach:
- Eliminates code duplication across 5 manager classes
- Maintains consistent API patterns
- Handles QObject metaclass compatibility issues
- Preserves existing functionality and performance
- Provides clear, readable implementation
"""

from typing import TypeVar, Dict, Any
from abc import ABC
import threading

# Type variable for generic singleton support
T = TypeVar('T', bound='SingletonManager')


class SingletonManager(ABC):
    """
    Base class for singleton managers.
    
    Provides thread-safe singleton pattern implementation with:
    - Lazy initialization
    - Thread safety using double-checked locking
    - Reset functionality for testing
    - Type-safe factory functions
    """
    
    _instances: Dict[str, Any] = {}
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Prevent direct instantiation - use factory functions instead."""
        # Allow instantiation only through factory functions
        # This is indicated by the presence of _allow_instantiation flag
        if not hasattr(cls, '_allow_instantiation') or not cls._allow_instantiation:
            raise TypeError(f"Cannot instantiate {cls.__name__} directly. Use get_{cls.__name__.lower()}() instead.")
        return super().__new__(cls)
    
    @classmethod
    def _get_instance(cls, *args, **kwargs):
        """
        Thread-safe singleton instance retrieval.
        
        Uses double-checked locking pattern for optimal performance.
        """
        instance_key = cls.__name__
        
        # First check (without lock) - fast path for existing instances
        if instance_key not in cls._instances:
            with cls._lock:
                # Second check (with lock) - ensure thread safety
                if instance_key not in cls._instances:
                    # Temporarily allow instantiation
                    cls._allow_instantiation = True
                    try:
                        cls._instances[instance_key] = cls(*args, **kwargs)
                    finally:
                        cls._allow_instantiation = False
        
        return cls._instances[instance_key]
    
    @classmethod
    def _reset_instance(cls):
        """Reset the singleton instance for testing purposes."""
        instance_key = cls.__name__
        with cls._lock:
            if instance_key in cls._instances:
                del cls._instances[instance_key]


class ParameterizedSingletonManager(SingletonManager):
    """
    Singleton manager that accepts initialization parameters.
    
    Suitable for managers that need parent widgets or configuration parameters.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with parameters - to be overridden by subclasses."""
        super().__init__()


class ParameterlessSingletonManager(SingletonManager):
    """
    Singleton manager that requires no initialization parameters.
    
    Suitable for managers that are self-contained.
    """
    
    def __init__(self):
        """Initialize without parameters - to be overridden by subclasses."""
        super().__init__()


# Factory function generators for consistent API
def create_singleton_factory(manager_class: type, has_reset: bool = True) -> tuple:
    """
    Create factory and reset functions for a singleton manager class.
    
    Args:
        manager_class: The manager class to create factories for
        has_reset: Whether to create a reset function
        
    Returns:
        Tuple of (factory_function, reset_function) or (factory_function, None)
    """
    def factory_function(*args, **kwargs):
        """Get or create the singleton instance."""
        return manager_class._get_instance(*args, **kwargs)
    
    def reset_function():
        """Reset the singleton instance."""
        manager_class._reset_instance()
    
    # Set proper function names for debugging
    factory_name = f"get_{manager_class.__name__.lower()}"
    reset_name = f"reset_{manager_class.__name__.lower()}"
    
    factory_function.__name__ = factory_name
    factory_function.__qualname__ = factory_name
    
    if has_reset:
        reset_function.__name__ = reset_name
        reset_function.__qualname__ = reset_name
        return factory_function, reset_function
    else:
        return factory_function, None


# Decorator for easy singleton conversion
def singleton_manager(has_reset: bool = True):
    """
    Decorator to convert a regular manager class into a singleton.
    
    Usage:
        @singleton_manager(has_reset=True)
        class MyManager(ParameterizedSingletonManager):
            def __init__(self, parent=None):
                super().__init__(parent)
                # ... rest of initialization
    
    This automatically creates get_mymanager() and reset_mymanager() functions.
    """
    def decorator(cls):
        # Make the class inherit from appropriate base if it doesn't already
        if not issubclass(cls, SingletonManager):
            raise TypeError(f"Class {cls.__name__} must inherit from SingletonManager or its subclasses")
        
        # Create factory functions
        factory_func, reset_func = create_singleton_factory(cls, has_reset)
        
        # Add functions to the class module
        import sys
        module = sys.modules[cls.__module__]
        setattr(module, factory_func.__name__, factory_func)
        if reset_func:
            setattr(module, reset_func.__name__, reset_func)
        
        return cls
    
    return decorator


# Thread-safe singleton metaclass (alternative implementation)
class SingletonMeta(type):
    """
    Metaclass implementation of singleton pattern.
    
    Alternative to inheritance-based approach for cases where inheritance
    is not suitable or when working with existing class hierarchies.
    """
    
    _instances = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
    
    def reset_instance(cls):
        """Reset the singleton instance."""
        with cls._lock:
            if cls in cls._instances:
                del cls._instances[cls]