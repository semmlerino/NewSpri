"""
Base coordinator classes for SpriteViewer refactoring.
Provides abstract base class and registry for managing coordinators.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

logger = logging.getLogger(__name__)


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

    def cleanup_all(self):
        """Clean up all registered coordinators."""
        for coordinator in self._coordinators.values():
            try:
                coordinator.cleanup()
            except Exception as e:
                logger.error("Error during coordinator cleanup: %s", e)

        self._coordinators.clear()