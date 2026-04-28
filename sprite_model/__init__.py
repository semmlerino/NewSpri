"""
Sprite Model - Modular Architecture
====================================

A professional, modular sprite processing system for the Python Sprite Viewer.

Refactored from a 2,530-line monolithic file into clean, testable modules:
- core: Main SpriteModel class with Qt signals and coordination
- extraction: Frame extraction engines (grid and CCL-based)
- detection: Auto-detection algorithms for margins, spacing, frame size
- file_operations: File I/O and validation
"""

from .core import SpriteModel
from .extraction_mode import ExtractionMode, extraction_mode_label
from .sprite_detection import DetectionResult
from .sprite_extraction import CCLDetectionResult, GridConfig

__all__ = [
    "CCLDetectionResult",
    "DetectionResult",
    "ExtractionMode",
    "GridConfig",
    "SpriteModel",
    "extraction_mode_label",
]
