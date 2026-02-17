"""
Sprite Model - Modular Architecture
====================================

A professional, modular sprite processing system for the Python Sprite Viewer.

Refactored from a 2,530-line monolithic file into clean, testable modules:
- core: Main SpriteModel class with Qt signals and coordination
- extraction: Frame extraction engines (grid and CCL-based)
- detection: Auto-detection algorithms for margins, spacing, frame size
- file_operations: File I/O and validation

Public API maintained for backwards compatibility.
"""

# Import main public interface for backwards compatibility
from .core import SpriteModel

# Import detection functions
from .sprite_detection import (
    DetectionResult,
    comprehensive_auto_detect,
    detect_frame_size,
    detect_margins,
    detect_spacing,
)

# Import standalone functions that external code expects
from .sprite_extraction import detect_background_color, detect_sprites_ccl_enhanced

# Version info
__version__ = "2.0.0-refactored"
__author__ = "Python Sprite Viewer Team"

# Public API
__all__ = [
    "DetectionResult",
    "SpriteModel",
    "comprehensive_auto_detect",
    "detect_background_color",
    "detect_frame_size",
    "detect_margins",
    "detect_spacing",
    "detect_sprites_ccl_enhanced",
]
