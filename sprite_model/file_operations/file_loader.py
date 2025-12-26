#!/usr/bin/env python3
"""
File Loader Module
==================

Core file loading logic for sprite sheets.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""


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
from .metadata_extractor import MetadataExtractor


class FileLoader:
    """
    Core file loading functionality for sprite sheets.

    Handles loading sprite sheets from disk with validation and metadata extraction.
    """

    def __init__(self):
        """Initialize file loader with validator and metadata extractor."""
        self.validator = FileValidator()
        self.metadata_extractor = MetadataExtractor()

    def load_sprite_sheet(self, file_path: str) -> tuple[bool, QPixmap | None, dict, str]:
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
            return False, None, {}, f"Error loading sprite sheet: {e!s}"

    def reload_sprite_sheet(self, file_path: str) -> tuple[bool, QPixmap | None, dict, str]:
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


# Convenience function for backwards compatibility
def load_sprite_sheet(file_path: str) -> tuple[bool, str]:
    """
    Convenience function to load and validate a sprite sheet.

    Args:
        file_path: Path to the sprite sheet file

    Returns:
        Tuple of (success, error_message)
    """
    loader = FileLoader()
    success, _pixmap, _metadata, error = loader.load_sprite_sheet(file_path)
    return success, error if not success else ""
