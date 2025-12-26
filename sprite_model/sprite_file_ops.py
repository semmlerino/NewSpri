#!/usr/bin/env python3
"""
Sprite File Operations
=======================

File loading, validation, and metadata extraction for sprite sheets.
Consolidated from file_operations/ subpackage.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtGui import QPixmap

try:
    from PySide6.QtGui import QPixmap as _QPixmapRuntime
    PYSIDE6_AVAILABLE = True
    if not TYPE_CHECKING:
        QPixmap = _QPixmapRuntime  # type: ignore[misc]
except ImportError:
    PYSIDE6_AVAILABLE = False
    if not TYPE_CHECKING:
        # Minimal QPixmap stub for when PySide6 unavailable
        class QPixmap:  # type: ignore[no-redef]
            def __init__(self, *args):
                self._null = True
            def isNull(self):
                return self._null
            def width(self):
                return 0
            def height(self):
                return 0


class FileValidator:
    """
    File validation functionality for sprite sheets.

    Validates file paths, formats, and accessibility.
    """

    # Supported image formats (must match Config.File.SUPPORTED_EXTENSIONS)
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}

    def __init__(self):
        """Initialize file validator."""
        pass

    def validate_file_path(self, file_path: str) -> tuple[bool, str]:
        """
        Validate that a file path is accessible and has a supported format.

        Args:
            file_path: Path to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file is valid and accessible
            - error_message: Description of validation error, empty if valid
        """
        try:
            # Check if path is provided
            if not file_path or not file_path.strip():
                return False, "No file path provided"

            # Convert to Path object for easier handling
            path_obj = Path(file_path)

            # Check if file exists
            if not path_obj.exists():
                return False, f"File does not exist: {file_path}"

            # Check if it's actually a file (not a directory)
            if not path_obj.is_file():
                return False, f"Path is not a file: {file_path}"

            # Check file format
            if not self._is_supported_format(path_obj):
                supported = ', '.join(sorted(self.SUPPORTED_FORMATS))
                return False, f"Unsupported file format. Supported: {supported}"

            # Check file accessibility
            if not os.access(file_path, os.R_OK):
                return False, f"File is not readable: {file_path}"

            # Check file size (basic sanity check)
            file_size = path_obj.stat().st_size
            if file_size == 0:
                return False, "File is empty"

            # Basic size limit check (prevent loading huge files accidentally)
            max_size = 100 * 1024 * 1024  # 100MB limit
            if file_size > max_size:
                size_mb = file_size / (1024 * 1024)
                return False, f"File too large: {size_mb:.1f}MB (limit: 100MB)"

            return True, ""

        except Exception as e:
            return False, f"Error validating file: {e!s}"

    def _is_supported_format(self, path: Path) -> bool:
        """
        Check if file has a supported image format.

        Args:
            path: Path object to check

        Returns:
            True if format is supported
        """
        return path.suffix.lower() in self.SUPPORTED_FORMATS

    def get_supported_formats(self) -> set[str]:
        """
        Get set of supported file formats.

        Returns:
            Set of supported file extensions (including dots)
        """
        return self.SUPPORTED_FORMATS.copy()


class MetadataExtractor:
    """
    File metadata extraction functionality for sprite sheets.

    Extracts comprehensive metadata from sprite sheet files including
    file information, image dimensions, format details, and timestamps.
    """

    def __init__(self):
        """Initialize metadata extractor."""
        pass

    def extract_file_metadata(self, file_path: str, pixmap: QPixmap) -> dict[str, Any]:
        """
        Extract comprehensive metadata from a sprite sheet file.

        Args:
            file_path: Path to the sprite sheet file
            pixmap: Loaded QPixmap for dimension extraction

        Returns:
            Dictionary containing file metadata:
            {
                'file_path': str,           # Full file path
                'file_name': str,           # File name only
                'sheet_width': int,         # Image width in pixels
                'sheet_height': int,        # Image height in pixels
                'file_format': str,         # File format (PNG, JPG, etc.)
                'file_size': int,           # File size in bytes
                'last_modified': float,     # Last modification timestamp
                'sprite_sheet_info': str    # Formatted info string for display
            }
        """
        if not PYSIDE6_AVAILABLE:
            return {
                'file_path': file_path,
                'file_name': Path(file_path).name if file_path else "Unknown",
                'sheet_width': 0,
                'sheet_height': 0,
                'file_format': "UNKNOWN",
                'file_size': 0,
                'last_modified': 0.0,
                'sprite_sheet_info': "PySide6 not available - metadata extraction limited"
            }

        try:
            path_obj = Path(file_path)
            file_stats = path_obj.stat()

            # Basic file information
            file_name = path_obj.name
            file_format = path_obj.suffix.upper()[1:] if path_obj.suffix else "UNKNOWN"
            file_size = file_stats.st_size
            last_modified = file_stats.st_mtime

            # Image dimensions
            sheet_width = pixmap.width()
            sheet_height = pixmap.height()

            # Generate formatted info string for UI display
            sprite_sheet_info = self.format_sprite_info(
                file_name, sheet_width, sheet_height, file_format, file_size
            )

            return {
                'file_path': file_path,
                'file_name': file_name,
                'sheet_width': sheet_width,
                'sheet_height': sheet_height,
                'file_format': file_format,
                'file_size': file_size,
                'last_modified': last_modified,
                'sprite_sheet_info': sprite_sheet_info
            }

        except Exception as e:
            # Return minimal metadata on error
            return {
                'file_path': file_path,
                'file_name': Path(file_path).name if file_path else "Unknown",
                'sheet_width': pixmap.width() if pixmap else 0,
                'sheet_height': pixmap.height() if pixmap else 0,
                'file_format': "UNKNOWN",
                'file_size': 0,
                'last_modified': 0.0,
                'sprite_sheet_info': f"Error extracting metadata: {e!s}"
            }

    def format_sprite_info(self, file_name: str, width: int, height: int,
                          file_format: str, file_size: int = 0) -> str:
        """
        Format sprite sheet information for display.

        Args:
            file_name: Name of the file
            width: Image width in pixels
            height: Image height in pixels
            file_format: File format (PNG, JPG, etc.)
            file_size: File size in bytes (optional)

        Returns:
            HTML-formatted string for display in UI
        """
        info_parts = [
            f"<b>File:</b> {file_name}",
            f"<b>Size:</b> {width} × {height} px",
            f"<b>Format:</b> {file_format}"
        ]

        # Add file size if provided
        if file_size > 0:
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            info_parts.append(f"<b>File Size:</b> {size_str}")

        return "<br>".join(info_parts)

    def update_sprite_info_with_frames(self, current_info: str, frame_count: int,
                                     frames_per_row: int = 0, frames_per_col: int = 0) -> str:
        """
        Update sprite info string with frame information.

        Args:
            current_info: Current sprite info string
            frame_count: Number of extracted frames
            frames_per_row: Frames per row (optional)
            frames_per_col: Frames per column (optional)

        Returns:
            Updated info string with frame information
        """
        # Remove any existing frame information
        base_info = current_info.split('<br><b>Frames:</b>')[0]

        if frame_count > 0:
            if frames_per_row > 0 and frames_per_col > 0:
                frame_info = f"<br><b>Frames:</b> {frame_count} ({frames_per_row}×{frames_per_col})"
            else:
                frame_info = f"<br><b>Frames:</b> {frame_count}"
        else:
            frame_info = "<br><b>Frames:</b> 0"

        return base_info + frame_info


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


# Convenience functions for backwards compatibility
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


def validate_file_path(file_path: str) -> tuple[bool, str]:
    """
    Convenience function for file path validation.

    Args:
        file_path: Path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = FileValidator()
    return validator.validate_file_path(file_path)
