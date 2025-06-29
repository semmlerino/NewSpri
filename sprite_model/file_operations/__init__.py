"""
File Operations Module
======================

File loading, validation, and metadata extraction for sprite sheets.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""

from .file_loader import FileLoader, load_sprite_sheet, reload_sprite_sheet
from .metadata_extractor import MetadataExtractor, extract_file_metadata, format_sprite_info
from .file_validator import FileValidator, validate_file_path

__all__ = [
    'FileLoader', 'load_sprite_sheet', 'reload_sprite_sheet',
    'MetadataExtractor', 'extract_file_metadata', 'format_sprite_info', 
    'FileValidator', 'validate_file_path'
]