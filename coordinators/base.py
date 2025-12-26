"""
Base coordinator class for SpriteViewer.
Provides abstract base class for coordinators.
"""

from abc import ABC, abstractmethod
from typing import Any


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
    def initialize(self, dependencies: dict[str, Any]):
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
