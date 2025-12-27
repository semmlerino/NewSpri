"""
Core package - MVC controller components.

Contains the core Model-View-Controller components:
- Animation timing and playback control
- Auto-detection algorithms and processing
- Core business logic separate from UI
"""

# Import core MVC components
from .animation_controller import AnimationController
from .animation_segment_controller import AnimationSegmentController
from .auto_detection_controller import AutoDetectionController
from .export_coordinator import ExportCoordinator

__all__ = [
    "AnimationController",
    "AnimationSegmentController",
    "AutoDetectionController",
    "ExportCoordinator",
]
