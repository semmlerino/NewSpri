#!/usr/bin/env python3
"""
Comprehensive Tests for File Operations
========================================

Tests for all file operations in the modular sprite model:
- File loading with validation and error handling
- File validation with format and accessibility checks
- Metadata extraction with comprehensive information

Covers file I/O, validation logic, metadata processing, and error handling.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from sprite_model.sprite_file_ops import FileLoader, FileValidator, MetadataExtractor


class TestFileValidator:
    """Test file validation functionality."""
    
    def test_validator_initialization(self):
        """Test FileValidator can be created."""
        validator = FileValidator()
        assert validator is not None
        assert len(validator.SUPPORTED_FORMATS) > 0
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        validator = FileValidator()
        formats = validator.get_supported_formats()
        
        assert isinstance(formats, set)
        assert '.png' in formats
        assert '.jpg' in formats
        assert '.jpeg' in formats
        assert '.bmp' in formats
        assert '.gif' in formats
        # Should be a copy, not the original
        formats.add('.test')
        assert '.test' not in validator.SUPPORTED_FORMATS
    
    def test_validate_empty_path(self):
        """Test validation with empty or None path."""
        validator = FileValidator()
        
        # Test None
        is_valid, error = validator.validate_file_path(None)
        assert not is_valid
        assert "No file path provided" in error
        
        # Test empty string
        is_valid, error = validator.validate_file_path("")
        assert not is_valid
        assert "No file path provided" in error
        
        # Test whitespace only
        is_valid, error = validator.validate_file_path("   ")
        assert not is_valid
        assert "No file path provided" in error
    
    def test_validate_nonexistent_file(self):
        """Test validation with non-existent file."""
        validator = FileValidator()
        
        nonexistent_path = "/path/that/does/not/exist.png"
        is_valid, error = validator.validate_file_path(nonexistent_path)
        
        assert not is_valid
        assert "File does not exist" in error
    
    def test_validate_directory_as_file(self, temp_dir):
        """Test validation when path points to directory."""
        validator = FileValidator()
        
        # temp_dir is a directory, not a file
        is_valid, error = validator.validate_file_path(str(temp_dir))
        
        assert not is_valid
        assert "Path is not a file" in error
    
    def test_validate_unsupported_format(self, temp_dir):
        """Test validation with unsupported file format."""
        validator = FileValidator()
        
        # Create a file with unsupported extension
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_text("test content")
        
        is_valid, error = validator.validate_file_path(str(unsupported_file))
        
        assert not is_valid
        assert "Unsupported file format" in error
        assert "Supported:" in error
    
    def test_validate_empty_file(self, temp_dir):
        """Test validation with empty file."""
        validator = FileValidator()
        
        # Create empty PNG file
        empty_file = temp_dir / "empty.png"
        empty_file.touch()  # Creates empty file
        
        is_valid, error = validator.validate_file_path(str(empty_file))
        
        assert not is_valid
        assert "File is empty" in error
    
    def test_validate_large_file(self, temp_dir):
        """Test validation with overly large file."""
        validator = FileValidator()
        
        # Create file that appears very large (mock the path object)
        large_file = temp_dir / "large.png"
        large_file.write_bytes(b"fake image data")
        
        # Mock the entire Path object and its stat method
        with patch('sprite_model.sprite_file_ops.Path') as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = True
            mock_path.suffix.lower.return_value = '.png'
            mock_stat = Mock()
            mock_stat.st_size = 200 * 1024 * 1024  # 200MB
            mock_path.stat.return_value = mock_stat
            mock_path_class.return_value = mock_path
            
            # Mock os.access to return True for read permission
            with patch('os.access', return_value=True):
                is_valid, error = validator.validate_file_path(str(large_file))
                
                assert not is_valid
                assert "File too large" in error
                assert "limit: 100MB" in error
    
    def test_validate_valid_png_file(self, temp_dir):
        """Test validation with valid PNG file."""
        validator = FileValidator()
        
        # Create a small PNG file
        png_file = temp_dir / "test.png"
        png_file.write_bytes(b"fake PNG content")  # Not real PNG but enough for validation
        
        is_valid, error = validator.validate_file_path(str(png_file))
        
        assert is_valid
        assert error == ""
    
    def test_validate_case_insensitive_extensions(self, temp_dir):
        """Test that file extensions are case-insensitive."""
        validator = FileValidator()
        
        # Test various case combinations
        test_files = [
            "test.PNG",
            "test.Png",
            "test.JPG",
            "test.jpeg",
            "test.JPEG"
        ]
        
        for filename in test_files:
            test_file = temp_dir / filename
            test_file.write_bytes(b"fake image content")
            
            is_valid, error = validator.validate_file_path(str(test_file))
            assert is_valid, f"Failed for {filename}: {error}"
    
    def test_is_supported_format_private_method(self, temp_dir):
        """Test the private _is_supported_format method."""
        validator = FileValidator()
        
        # Test supported formats
        assert validator._is_supported_format(Path("test.png"))
        assert validator._is_supported_format(Path("test.PNG"))
        assert validator._is_supported_format(Path("test.jpg"))
        assert validator._is_supported_format(Path("test.jpeg"))
        
        # Test unsupported formats
        assert not validator._is_supported_format(Path("test.txt"))
        assert not validator._is_supported_format(Path("test.xyz"))
        assert not validator._is_supported_format(Path("test"))  # No extension
    
    def test_validate_file_path_exception_handling(self):
        """Test exception handling in file validation."""
        validator = FileValidator()
        
        # Create a mock path that raises an exception during stat()
        with patch('sprite_model.sprite_file_ops.Path') as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = True
            mock_path.suffix.lower.return_value = '.png'
            mock_path.stat.side_effect = Exception("Simulated error")
            mock_path_class.return_value = mock_path
            
            # Also mock os.access to return True to avoid early exit
            with patch('os.access', return_value=True):
                is_valid, error = validator.validate_file_path("any_path")
                
                assert not is_valid
                assert "Error validating file" in error
                assert "Simulated error" in error
    

class TestMetadataExtractor:
    """Test metadata extraction functionality."""
    
    def test_extractor_initialization(self):
        """Test MetadataExtractor can be created."""
        extractor = MetadataExtractor()
        assert extractor is not None
    
    def test_extract_file_metadata_success(self, qapp, temp_dir):
        """Test successful metadata extraction."""
        extractor = MetadataExtractor()
        
        # Create test file
        test_file = temp_dir / "sprite_sheet.png"
        test_file.write_bytes(b"fake PNG content")
        
        # Create mock pixmap
        mock_pixmap = Mock()
        mock_pixmap.width.return_value = 256
        mock_pixmap.height.return_value = 128
        
        metadata = extractor.extract_file_metadata(str(test_file), mock_pixmap)
        
        assert metadata['file_path'] == str(test_file)
        assert metadata['file_name'] == "sprite_sheet.png"
        assert metadata['sheet_width'] == 256
        assert metadata['sheet_height'] == 128
        assert metadata['file_format'] == "PNG"
        assert metadata['file_size'] > 0
        assert metadata['last_modified'] > 0
        assert 'sprite_sheet_info' in metadata
    
    def test_extract_file_metadata_with_real_pixmap(self, qapp, temp_dir):
        """Test metadata extraction with real pixmap."""
        extractor = MetadataExtractor()
        
        # Create a real pixmap
        pixmap = QPixmap(64, 32)
        pixmap.fill(Qt.red)
        
        # Create test file path (doesn't need to exist for this test)
        test_file = temp_dir / "test.jpg"
        test_file.write_bytes(b"fake JPEG content")
        
        metadata = extractor.extract_file_metadata(str(test_file), pixmap)
        
        assert metadata['sheet_width'] == 64
        assert metadata['sheet_height'] == 32
        assert metadata['file_format'] == "JPG"
    
    def test_extract_file_metadata_no_extension(self, qapp, temp_dir):
        """Test metadata extraction with file having no extension."""
        extractor = MetadataExtractor()
        
        test_file = temp_dir / "no_extension"
        test_file.write_bytes(b"content")
        
        mock_pixmap = Mock()
        mock_pixmap.width.return_value = 100
        mock_pixmap.height.return_value = 100
        
        metadata = extractor.extract_file_metadata(str(test_file), mock_pixmap)
        
        assert metadata['file_format'] == "UNKNOWN"
    
    def test_extract_file_metadata_exception_handling(self, qapp):
        """Test metadata extraction exception handling."""
        extractor = MetadataExtractor()
        
        # Mock Path to raise exception
        with patch('pathlib.Path') as mock_path:
            mock_path.side_effect = Exception("File error")
            
            mock_pixmap = Mock()
            mock_pixmap.width.return_value = 50
            mock_pixmap.height.return_value = 50
            
            metadata = extractor.extract_file_metadata("test_path", mock_pixmap)
            
            # Should return minimal metadata on error
            assert metadata['file_path'] == "test_path"
            assert metadata['sheet_width'] == 50
            assert metadata['sheet_height'] == 50
            assert "Error extracting metadata" in metadata['sprite_sheet_info']
    
    def test_format_sprite_info_basic(self):
        """Test basic sprite info formatting."""
        extractor = MetadataExtractor()
        
        info = extractor.format_sprite_info("test.png", 128, 64, "PNG")
        
        assert "<b>File:</b> test.png" in info
        assert "<b>Size:</b> 128 × 64 px" in info
        assert "<b>Format:</b> PNG" in info
        assert "<br>" in info  # Should be HTML formatted
    
    def test_format_sprite_info_with_file_size(self):
        """Test sprite info formatting with file size."""
        extractor = MetadataExtractor()
        
        # Test bytes
        info = extractor.format_sprite_info("small.png", 32, 32, "PNG", 512)
        assert "<b>File Size:</b> 512 bytes" in info
        
        # Test KB
        info = extractor.format_sprite_info("medium.png", 64, 64, "PNG", 2048)
        assert "<b>File Size:</b> 2.0 KB" in info
        
        # Test MB
        info = extractor.format_sprite_info("large.png", 512, 512, "PNG", 2 * 1024 * 1024)
        assert "<b>File Size:</b> 2.0 MB" in info
    
    def test_update_sprite_info_with_frames(self):
        """Test updating sprite info with frame information."""
        extractor = MetadataExtractor()
        
        base_info = "<b>File:</b> test.png<br><b>Size:</b> 128 × 64 px"
        
        # Test with frame count only
        updated = extractor.update_sprite_info_with_frames(base_info, 8)
        assert "<b>Frames:</b> 8" in updated
        assert base_info in updated
        
        # Test with grid information
        updated = extractor.update_sprite_info_with_frames(base_info, 12, 4, 3)
        assert "<b>Frames:</b> 12 (4×3)" in updated
        
        # Test with zero frames
        updated = extractor.update_sprite_info_with_frames(base_info, 0)
        assert "<b>Frames:</b> 0" in updated
    
    def test_update_sprite_info_removes_existing_frames(self):
        """Test that updating sprite info removes existing frame information."""
        extractor = MetadataExtractor()
        
        # Start with info that already has frame data
        existing_info = "<b>File:</b> test.png<br><b>Frames:</b> 5 (old)"
        
        updated = extractor.update_sprite_info_with_frames(existing_info, 10, 5, 2)
        
        # Should have new frame info, not old
        assert "<b>Frames:</b> 10 (5×2)" in updated
        assert "5 (old)" not in updated
    
class TestFileLoader:
    """Test file loading functionality."""
    
    def test_loader_initialization(self):
        """Test FileLoader can be created."""
        loader = FileLoader()
        assert loader is not None
        assert loader.validator is not None
        assert loader.metadata_extractor is not None
    
    def test_load_sprite_sheet_validation_failure(self):
        """Test loading with validation failure."""
        loader = FileLoader()
        
        # Mock validator to fail
        loader.validator.validate_file_path = Mock(return_value=(False, "Test validation error"))
        
        success, pixmap, metadata, error = loader.load_sprite_sheet("invalid_path")
        
        assert not success
        assert pixmap is None
        assert metadata == {}
        assert "Test validation error" in error
    
    def test_load_sprite_sheet_pixmap_failure(self, temp_dir):
        """Test loading when QPixmap fails to load."""
        loader = FileLoader()
        
        # Create a valid file path but mock QPixmap to fail
        test_file = temp_dir / "test.png"
        test_file.write_bytes(b"fake PNG content")
        
        with patch('sprite_model.sprite_file_ops.QPixmap') as mock_pixmap_class:
            # Mock QPixmap constructor to return null pixmap
            mock_pixmap = Mock()
            mock_pixmap.isNull.return_value = True
            mock_pixmap_class.return_value = mock_pixmap
            
            success, pixmap, metadata, error = loader.load_sprite_sheet(str(test_file))
            
            assert not success
            assert pixmap is None
            assert metadata == {}
            assert "Failed to load image file" in error
    
    def test_load_sprite_sheet_success(self, qapp, temp_dir):
        """Test successful sprite sheet loading."""
        loader = FileLoader()
        
        # Create test file
        test_file = temp_dir / "sprite.png"
        test_file.write_bytes(b"fake PNG content")
        
        # Mock successful pixmap loading
        with patch('sprite_model.sprite_file_ops.QPixmap') as mock_pixmap_class:
            mock_pixmap = Mock()
            mock_pixmap.isNull.return_value = False
            mock_pixmap.width.return_value = 128
            mock_pixmap.height.return_value = 64
            mock_pixmap_class.return_value = mock_pixmap
            
            success, pixmap, metadata, error = loader.load_sprite_sheet(str(test_file))
            
            assert success
            assert pixmap == mock_pixmap
            assert isinstance(metadata, dict)
            assert 'file_path' in metadata
            assert 'sheet_width' in metadata
            assert error == ""
    
    def test_load_sprite_sheet_exception_handling(self):
        """Test exception handling in sprite sheet loading."""
        loader = FileLoader()
        
        # Mock validator to raise exception
        loader.validator.validate_file_path = Mock(side_effect=Exception("Test exception"))
        
        success, pixmap, metadata, error = loader.load_sprite_sheet("any_path")
        
        assert not success
        assert pixmap is None
        assert metadata == {}
        assert "Error loading sprite sheet" in error
        assert "Test exception" in error
    
    def test_reload_sprite_sheet_no_path(self):
        """Test reloading with no file path."""
        loader = FileLoader()
        
        success, pixmap, metadata, error = loader.reload_sprite_sheet("")
        
        assert not success
        assert pixmap is None
        assert metadata == {}
        assert "No sprite sheet path provided" in error
    
    def test_reload_sprite_sheet_delegates_to_load(self, temp_dir):
        """Test that reload delegates to load_sprite_sheet."""
        loader = FileLoader()
        
        test_file = temp_dir / "test.png"
        test_file.write_bytes(b"content")
        
        # Mock load_sprite_sheet
        loader.load_sprite_sheet = Mock(return_value=(True, "mock_pixmap", {"test": "data"}, ""))
        
        success, pixmap, metadata, error = loader.reload_sprite_sheet(str(test_file))
        
        loader.load_sprite_sheet.assert_called_once_with(str(test_file))
        assert success
        assert pixmap == "mock_pixmap"
        assert metadata == {"test": "data"}
    
class TestFileOperationsIntegration:
    """Test integration between file operations components."""
    
    def test_full_file_loading_workflow(self, qapp, temp_dir):
        """Test complete file loading workflow with all components."""
        # Create a realistic test file
        test_file = temp_dir / "complete_test.png"
        test_file.write_bytes(b"PNG file content" * 100)  # Make it a reasonable size
        
        # Use real components (but mock QPixmap loading)
        with patch('sprite_model.sprite_file_ops.QPixmap') as mock_pixmap_class:
            mock_pixmap = Mock()
            mock_pixmap.isNull.return_value = False
            mock_pixmap.width.return_value = 256
            mock_pixmap.height.return_value = 128
            mock_pixmap_class.return_value = mock_pixmap
            
            loader = FileLoader()
            success, pixmap, metadata, error = loader.load_sprite_sheet(str(test_file))
            
            # Should succeed with complete workflow
            assert success
            assert pixmap == mock_pixmap
            assert error == ""
            
            # Validate metadata structure
            assert metadata['file_name'] == "complete_test.png"
            assert metadata['sheet_width'] == 256
            assert metadata['sheet_height'] == 128
            assert metadata['file_format'] == "PNG"
            assert metadata['file_size'] > 0
            assert 'sprite_sheet_info' in metadata
            
            # Validate formatted info
            info = metadata['sprite_sheet_info']
            assert "complete_test.png" in info
            assert "256 × 128 px" in info
            assert "PNG" in info
    
    def test_error_propagation_through_workflow(self):
        """Test that errors propagate correctly through the workflow."""
        loader = FileLoader()
        
        # Test with completely invalid path
        success, pixmap, metadata, error = loader.load_sprite_sheet("/definitely/does/not/exist.png")
        
        assert not success
        assert pixmap is None
        assert metadata == {}
        assert "File does not exist" in error
    
    def test_validator_and_loader_consistency(self, temp_dir):
        """Test that validator and loader have consistent behavior."""
        validator = FileValidator()
        loader = FileLoader()
        
        # Create file with unsupported format
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_bytes(b"content")
        
        # Validator should reject it
        is_valid, validation_error = validator.validate_file_path(str(unsupported_file))
        assert not is_valid
        assert "Unsupported file format" in validation_error
        
        # Loader should also reject it (via validator)
        success, pixmap, metadata, loader_error = loader.load_sprite_sheet(str(unsupported_file))
        assert not success
        assert "Unsupported file format" in loader_error
    
    def test_metadata_consistency_with_pixmap(self, qapp):
        """Test that metadata dimensions match pixmap dimensions."""
        extractor = MetadataExtractor()
        
        # Create pixmap with specific dimensions
        pixmap = QPixmap(123, 456)
        pixmap.fill(Qt.blue)
        
        # Extract metadata (mock file path)
        with patch('pathlib.Path') as mock_path:
            mock_path.return_value.name = "test.png"
            mock_path.return_value.suffix = ".png"
            mock_path.return_value.stat.return_value.st_size = 1000
            mock_path.return_value.stat.return_value.st_mtime = 1234567890
            
            metadata = extractor.extract_file_metadata("test.png", pixmap)
            
            # Metadata dimensions should match pixmap
            assert metadata['sheet_width'] == 123
            assert metadata['sheet_height'] == 456


@pytest.mark.parametrize("file_size,expected_unit", [
    (500, "bytes"),
    (1536, "KB"),      # 1.5 KB
    (2048000, "MB"),   # ~2 MB
])
def test_file_size_formatting_parametrized(file_size, expected_unit):
    """Test file size formatting with various sizes."""
    extractor = MetadataExtractor()
    
    info = extractor.format_sprite_info("test.png", 100, 100, "PNG", file_size)
    
    assert expected_unit in info
    assert "<b>File Size:</b>" in info


@pytest.mark.parametrize("extension,should_be_valid", [
    (".png", True),
    (".PNG", True),
    (".jpg", True),
    (".JPEG", True),
    (".bmp", True),
    (".gif", True),
    # Note: .tiff and .webp removed - not supported by Config.File.SUPPORTED_EXTENSIONS
    (".tiff", False),
    (".webp", False),
    (".txt", False),
    (".doc", False),
    (".xyz", False),
    ("", False),
])
def test_file_extension_validation_parametrized(temp_dir, extension, should_be_valid):
    """Test file extension validation with various formats."""
    validator = FileValidator()
    
    # Create test file with given extension
    if extension:
        test_file = temp_dir / f"test{extension}"
    else:
        test_file = temp_dir / "test"
    
    test_file.write_bytes(b"test content")
    
    is_valid, error = validator.validate_file_path(str(test_file))
    
    if should_be_valid:
        assert is_valid, f"Expected {extension} to be valid but got error: {error}"
    else:
        assert not is_valid, f"Expected {extension} to be invalid but validation passed"
        if extension and extension not in [".txt", ".doc", ".xyz"]:
            # For empty extension, different error message
            assert "Unsupported file format" in error


@pytest.mark.performance
def test_file_operations_performance(qapp, temp_dir):
    """Test performance of file operations with realistic files."""
    import time
    
    # Create multiple test files of different sizes
    test_files = []
    for i, size in enumerate([1024, 10240, 51200]):  # 1KB, 10KB, 50KB
        test_file = temp_dir / f"perf_test_{i}.png"
        test_file.write_bytes(b"x" * size)
        test_files.append(test_file)
    
    loader = FileLoader()
    
    start_time = time.time()
    
    # Process all files
    for test_file in test_files:
        with patch('sprite_model.sprite_file_ops.QPixmap') as mock_pixmap_class:
            mock_pixmap = Mock()
            mock_pixmap.isNull.return_value = False
            mock_pixmap.width.return_value = 64
            mock_pixmap.height.return_value = 64
            mock_pixmap_class.return_value = mock_pixmap
            
            success, pixmap, metadata, error = loader.load_sprite_sheet(str(test_file))
            assert success
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Should process multiple files quickly (under 0.5 seconds)
    assert total_time < 0.5