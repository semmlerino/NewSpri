"""
File Operations Module
======================

File loading, validation, and metadata extraction for sprite sheets.
"""

from .file_loader import FileLoader, load_sprite_sheet
from .file_validator import FileValidator, validate_file_path
from .metadata_extractor import MetadataExtractor

__all__ = [
    'FileLoader',
    'FileValidator',
    'MetadataExtractor',
    'load_sprite_sheet',
    'validate_file_path',
]
