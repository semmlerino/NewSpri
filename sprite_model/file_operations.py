"""
File Operations Module
=====================

Handles file loading, validation, and metadata extraction for sprite sheets.
Independent module with no dependencies on the main SpriteModel.

Features:
- File format validation and loading
- Metadata extraction (dimensions, format, modification time)
- Error handling and validation
- File change detection
"""

import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from PySide6.QtGui import QPixmap


class FileOperations:
    """
    Service class for sprite sheet file operations.
    Handles loading, validation, and metadata extraction.
    """
    
    def __init__(self):
        """Initialize file operations service."""
        self._file_path: str = ""
        self._file_name: str = ""
        self._file_format: str = ""
        self._last_modified: float = 0.0
        self._sheet_width: int = 0
        self._sheet_height: int = 0
        self._sprite_sheet_info: str = ""
        self._original_sprite_sheet: Optional[QPixmap] = None
        
    def load_sprite_sheet(self, file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Load and validate sprite sheet from file path.
        
        Args:
            file_path: Path to the sprite sheet image file
            
        Returns:
            Tuple of (success, error_message, metadata_dict)
            
        Example:
            >>> file_ops = FileOperations()
            >>> success, error, metadata = file_ops.load_sprite_sheet("sprites.png")
            >>> if success:
            ...     pixmap = metadata['pixmap']
            ...     width = metadata['width']
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}", {}
            
            # Load pixmap from file
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                return False, "Failed to load image file - invalid format or corrupted", {}
            
            # Extract file metadata
            file_path_obj = Path(file_path)
            self._file_path = file_path
            self._file_name = file_path_obj.name
            self._sheet_width = pixmap.width()
            self._sheet_height = pixmap.height()
            self._file_format = file_path_obj.suffix.upper()[1:] if file_path_obj.suffix else "UNKNOWN"
            self._last_modified = os.path.getmtime(file_path)
            self._original_sprite_sheet = pixmap
            
            # Generate sprite sheet info string
            self._sprite_sheet_info = (
                f"<b>File:</b> {self._file_name}<br>"
                f"<b>Size:</b> {self._sheet_width} × {self._sheet_height} px<br>"
                f"<b>Format:</b> {self._file_format}"
            )
            
            # Prepare metadata dictionary
            metadata = {
                'pixmap': pixmap,
                'file_path': self._file_path,
                'file_name': self._file_name,
                'width': self._sheet_width,
                'height': self._sheet_height,
                'format': self._file_format,
                'last_modified': self._last_modified,
                'info_html': self._sprite_sheet_info
            }
            
            return True, "", metadata
            
        except Exception as e:
            error_msg = f"Error loading sprite sheet: {str(e)}"
            return False, error_msg, {}
    
    def reload_current_sheet(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Reload the current sprite sheet (for file changes).
        
        Returns:
            Tuple of (success, error_message, metadata_dict)
        """
        if not self._file_path:
            return False, "No sprite sheet currently loaded", {}
        return self.load_sprite_sheet(self._file_path)
    
    def clear_file_data(self) -> None:
        """Clear all file data and reset to empty state."""
        self._original_sprite_sheet = None
        self._file_path = ""
        self._file_name = ""
        self._sprite_sheet_info = ""
        self._sheet_width = 0
        self._sheet_height = 0
        self._file_format = ""
        self._last_modified = 0.0
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        Get current file information.
        
        Returns:
            Dictionary with current file metadata
        """
        return {
            'file_path': self._file_path,
            'file_name': self._file_name,
            'width': self._sheet_width,
            'height': self._sheet_height,
            'format': self._file_format,
            'last_modified': self._last_modified,
            'info_html': self._sprite_sheet_info,
            'pixmap': self._original_sprite_sheet
        }
    
    def is_file_loaded(self) -> bool:
        """Check if a file is currently loaded."""
        return bool(self._file_path and self._original_sprite_sheet)
    
    def has_file_changed(self) -> bool:
        """
        Check if the current file has been modified since loading.
        
        Returns:
            True if file has been modified, False otherwise
        """
        if not self._file_path or not os.path.exists(self._file_path):
            return False
        
        try:
            current_mtime = os.path.getmtime(self._file_path)
            return current_mtime > self._last_modified
        except Exception:
            return False
    
    def validate_image_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate that a file is a supported image format.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file extension
            file_path_obj = Path(file_path)
            extension = file_path_obj.suffix.lower()
            supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif', '.tiff'}
            
            if extension not in supported_extensions:
                return False, f"Unsupported file format: {extension}"
            
            # Try to load as QPixmap to validate format
            test_pixmap = QPixmap(file_path)
            if test_pixmap.isNull():
                return False, "Invalid or corrupted image file"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"


def load_sprite_sheet(file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Standalone function for loading sprite sheets.
    Convenience function that creates a FileOperations instance.
    
    Args:
        file_path: Path to the sprite sheet image
        
    Returns:
        Tuple of (success, error_message, metadata_dict)
        
    Example:
        >>> success, error, metadata = load_sprite_sheet("sprites.png")
        >>> if success:
        ...     pixmap = metadata['pixmap']
    """
    file_ops = FileOperations()
    return file_ops.load_sprite_sheet(file_path)


def validate_image_file(file_path: str) -> Tuple[bool, str]:
    """
    Standalone function for validating image files.
    
    Args:
        file_path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    file_ops = FileOperations()
    return file_ops.validate_image_file(file_path)