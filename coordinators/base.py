"""
Base coordinator classes for SpriteViewer refactoring.
Provides abstract base class and registry for managing coordinators.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class CoordinatorBase(ABC):
    """
    Base class for all coordinators.
    
    Coordinators are responsible for extracting specific functionality
    from the main SpriteViewer window class to improve maintainability
    and testability.
    """
    
    def __init__(self, main_window):
        """
        Initialize coordinator with reference to main window.
        
        Args:
            main_window: The SpriteViewer QMainWindow instance
        """
        self.main_window = main_window
        self._initialized = False
    
    @abstractmethod
    def initialize(self, dependencies: Dict[str, Any]):
        """
        Initialize coordinator with required dependencies.
        
        Args:
            dependencies: Dictionary of dependencies needed by the coordinator
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        Clean up resources and disconnect signals.
        
        Called during application shutdown or coordinator replacement.
        """
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if coordinator has been initialized."""
        return self._initialized


class CoordinatorRegistry:
    """
    Registry for managing coordinators.
    
    Provides centralized access to all coordinators and manages
    their lifecycle including initialization and cleanup.
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._coordinators: Dict[str, CoordinatorBase] = {}
    
    def register(self, name: str, coordinator: CoordinatorBase):
        """
        Register a coordinator with the registry.
        
        Args:
            name: Unique name for the coordinator
            coordinator: CoordinatorBase instance to register
        """
        if name in self._coordinators:
            # Clean up existing coordinator before replacing
            self._coordinators[name].cleanup()
        
        self._coordinators[name] = coordinator
    
    def get(self, name: str) -> Optional[CoordinatorBase]:
        """
        Get a coordinator by name.
        
        Args:
            name: Name of the coordinator to retrieve
            
        Returns:
            Coordinator instance or None if not found
        """
        return self._coordinators.get(name)
    
    def remove(self, name: str) -> bool:
        """
        Remove a coordinator from the registry.
        
        Args:
            name: Name of the coordinator to remove
            
        Returns:
            True if removed, False if not found
        """
        if name in self._coordinators:
            self._coordinators[name].cleanup()
            del self._coordinators[name]
            return True
        return False
    
    def initialize_all(self, dependencies: Dict[str, Any]):
        """
        Initialize all registered coordinators.
        
        Args:
            dependencies: Dictionary of dependencies to pass to coordinators
        """
        for name, coordinator in self._coordinators.items():
            if not coordinator.is_initialized:
                try:
                    coordinator.initialize(dependencies)
                    coordinator._initialized = True
                except Exception as e:
                    print(f"Failed to initialize coordinator '{name}': {e}")
    
    def cleanup_all(self):
        """Clean up all registered coordinators."""
        for coordinator in self._coordinators.values():
            try:
                coordinator.cleanup()
            except Exception as e:
                print(f"Error during coordinator cleanup: {e}")
        
        self._coordinators.clear()
    
    def list_coordinators(self) -> list:
        """
        Get list of registered coordinator names.
        
        Returns:
            List of coordinator names
        """
        return list(self._coordinators.keys())