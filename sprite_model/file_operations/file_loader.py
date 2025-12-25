#!/usr/bin/env python3
"""
File Loader Module
==================

Core file loading logic for sprite sheets.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""

from typing import Tuple, Optional

try:
    from PySide6.QtGui import QPixmap
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    # Minimal QPixmap stub for when PySide6 unavailable
    class QPixmap:
        def __init__(self, *args): 
            self._null = True
        def isNull(self): 
            return self._null
        def width(self): 
            return 0
        def height(self): 
            return 0

from .file_validator import FileValidator

# Conditional import of metadata extractor to handle PySide6 dependency
try:
    from .metadata_extractor import MetadataExtractor
    METADATA_AVAILABLE = True
except ImportError:
    METADATA_AVAILABLE = False
    # Fallback metadata extractor
    class MetadataExtractor:
        def extract_file_metadata(self, file_path, pixmap):
            from pathlib import Path
            return {
                'file_path': file_path,
                'file_name': Path(file_path).name if file_path else "Unknown",
                'sheet_width': 0,
                'sheet_height': 0,
                'file_format': "UNKNOWN",
                'file_size': 0,
                'last_modified': 0.0,
                'sprite_sheet_info': "Metadata extraction not available"
            }


class FileLoader:
    """
    Core file loading functionality for sprite sheets.
    
    Handles loading sprite sheets from disk with validation and metadata extraction.
    """
    
    def __init__(self):
        """Initialize file loader with validator and metadata extractor."""
        self.validator = FileValidator()
        self.metadata_extractor = MetadataExtractor()
    
    def load_sprite_sheet(self, file_path: str) -> Tuple[bool, Optional[QPixmap], dict, str]:
        """
        Load and validate sprite sheet from file path.
        
        Args:
            file_path: Path to the sprite sheet file
            
        Returns:
            Tuple of (success, pixmap, metadata, error_message)
            - success: True if loading succeeded
            - pixmap: Loaded QPixmap or None if failed
            - metadata: Dictionary containing file metadata
            - error_message: Error description if failed, empty string if succeeded
        """
        if not PYSIDE6_AVAILABLE:
            return False, None, {}, "PySide6 not available - required for image loading"
        
        try:
            # Validate file path first
            is_valid, validation_error = self.validator.validate_file_path(file_path)
            if not is_valid:
                return False, None, {}, validation_error
            
            # Load pixmap from file
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                return False, None, {}, "Failed to load image file"
            
            # Extract file metadata
            metadata = self.metadata_extractor.extract_file_metadata(file_path, pixmap)
            
            return True, pixmap, metadata, ""
            
        except Exception as e:
            return False, None, {}, f"Error loading sprite sheet: {str(e)}"
    
    def reload_sprite_sheet(self, file_path: str) -> Tuple[bool, Optional[QPixmap], dict, str]:
        """
        Reload a sprite sheet from disk.
        
        Args:
            file_path: Path to the sprite sheet file
            
        Returns:
            Tuple of (success, pixmap, metadata, error_message)
        """
        if not PYSIDE6_AVAILABLE:
            return False, None, {}, "PySide6 not available - required for image loading"
        
        if not file_path:
            return False, None, {}, "No sprite sheet path provided"
        
        return self.load_sprite_sheet(file_path)


# Convenience functions for direct usage
def load_sprite_sheet(file_path: str) -> Tuple[bool, Optional[QPixmap], dict, str]:
    """
    Convenience function for loading sprite sheets.
    
    Args:
        file_path: Path to the sprite sheet file
        
    Returns:
        Tuple of (success, pixmap, metadata, error_message)
    """
    if not PYSIDE6_AVAILABLE:
        return False, None, {}, "PySide6 not available - required for image loading"
    
    loader = FileLoader()
    return loader.load_sprite_sheet(file_path)


def reload_sprite_sheet(file_path: str) -> Tuple[bool, Optional[QPixmap], dict, str]:
    """
    Convenience function for reloading sprite sheets.
    
    Args:
        file_path: Path to the sprite sheet file
        
    Returns:
        Tuple of (success, pixmap, metadata, error_message)
    """
    if not PYSIDE6_AVAILABLE:
        return False, None, {}, "PySide6 not available - required for image loading"
    
    loader = FileLoader()
    return loader.reload_sprite_sheet(file_path)