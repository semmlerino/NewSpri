"""
Core package - MVC controller components.

Contains the core Model-View-Controller components:
- Animation timing and playback control
- Auto-detection algorithms and processing
- Core business logic separate from UI
"""

# Import core MVC components
from .animation_controller import AnimationController
from .auto_detection_controller import AutoDetectionController

__all__ = [
    'AnimationController',
    'AutoDetectionController'
]