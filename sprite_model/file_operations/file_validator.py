#!/usr/bin/env python3
"""
File Validator Module
=====================

File validation logic for sprite sheets.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""

import os
from pathlib import Path


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


# Convenience function for direct usage
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
