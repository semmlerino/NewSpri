#!/usr/bin/env python3
"""
Metadata Extractor Module
=========================

File metadata extraction for sprite sheets.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""

from pathlib import Path
from typing import Any

try:
    from PySide6.QtGui import QPixmap
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    # Minimal QPixmap stub for when PySide6 unavailable
    class QPixmap:
        def __init__(self, *args):
            pass
        def width(self):
            return 0
        def height(self):
            return 0


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
