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

# Phase 6: Import file operations with fallback handling
try:
    # Try Phase 6 module structure first
    from .file_operations import FileLoader, load_sprite_sheet, validate_file_path
    FileOperations = FileLoader  # Backwards compatibility alias
    validate_image_file = validate_file_path  # Backwards compatibility alias
except ImportError:
    try:
        # Fallback to legacy file_operations.py
        from .file_operations import FileOperations, load_sprite_sheet, validate_image_file
    except ImportError:
        # Final fallback - create minimal stub implementations
        class FileOperations:
            def __init__(self):
                pass
            def load_sprite_sheet(self, file_path): 
                return False, "File operations not available - PySide6 required", {}
            def reload_sprite_sheet(self, file_path): 
                return False, "File operations not available - PySide6 required", {}
        
        def load_sprite_sheet(file_path): 
            return False, "File operations not available - PySide6 required", {}
        
        def validate_image_file(file_path): 
            return False, "File operations not available - PySide6 required"

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