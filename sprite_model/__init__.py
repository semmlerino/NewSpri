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

# Import standalone functions that external code expects
from .extraction.background_detector import detect_background_color
from .extraction.ccl_extractor import detect_sprites_ccl_enhanced
from .file_operations import FileOperations, load_sprite_sheet, validate_image_file

# Version info
__version__ = "2.0.0-refactored"
__author__ = "Python Sprite Viewer Team"

# Public API
__all__ = [
    'SpriteModel',
    'detect_background_color', 
    'detect_sprites_ccl_enhanced',
    'FileOperations',
    'load_sprite_sheet',
    'validate_image_file'
]