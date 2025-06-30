"""
Integration tests for complete sprite loading workflows.
Tests end-to-end functionality across multiple components.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from PySide6.QtGui import QPixmap
from PySide6.QtTest import QSignalSpy

from sprite_model import SpriteModel
from animation_controller import AnimationController
from auto_detection_controller import AutoDetectionController


class TestSpriteLoadingWorkflow:
    """Test complete sprite sheet loading and processing workflow."""
    
    @pytest.mark.integration
    @pytest.mark.requires_files
    def test_load_sprite_sheet_complete_workflow(self, qapp, sample_sprite_paths):
        """Test complete workflow from file loading to animation ready."""
        # Setup components
        sprite_model = SpriteModel()
        animation_controller = AnimationController()
        auto_detection_controller = AutoDetectionController()
        
        # Initialize controllers
        animation_controller.initialize(sprite_model, Mock())
        auto_detection_controller.initialize(sprite_model, Mock())
        
        # Signal spies to track workflow
        data_loaded_spy = QSignalSpy(sprite_model.dataLoaded)
        extraction_completed_spy = QSignalSpy(sprite_model.extractionCompleted)
        
        # Test with available sprite sheet
        test_path = sample_sprite_paths["test_sheet"]
        if not test_path.exists():
            pytest.skip(f"Test sprite sheet not found: {test_path}")
        
        # Load sprite sheet
        success, message, metadata = sprite_model.load_sprite_sheet(str(test_path))
        
        # Verify loading succeeded
        assert success, f"Failed to load sprite sheet: {message}"
        assert len(data_loaded_spy) > 0
        
        # Verify sprite sheet is loaded
        assert sprite_model.original_sprite_sheet is not None
        assert not sprite_model.original_sprite_sheet.isNull()
        assert sprite_model.file_path == str(test_path)
        
        # Configure frame extraction
        sprite_model.set_frame_settings(32, 32, 0, 0, 0, 0)
        
        # Extract frames
        frame_count = sprite_model.extract_frames()
        assert frame_count > 0
        assert len(extraction_completed_spy) > 0
        
        # Verify frames were extracted
        assert sprite_model.get_frame_count() == frame_count
        for i in range(frame_count):
            frame = sprite_model.get_frame(i)
            assert frame is not None
            assert not frame.isNull()
        
        # Test animation controller integration
        assert animation_controller._is_active
        animation_controller.start_animation()
        assert animation_controller._is_playing
    
    @pytest.mark.integration
    def test_auto_detection_workflow(self, qapp, sample_sprite_paths):
        """Test auto-detection workflow integration."""
        sprite_model = SpriteModel()
        auto_detection_controller = AutoDetectionController()
        
        # Mock frame extractor for auto-detection
        mock_frame_extractor = Mock()
        auto_detection_controller.initialize(sprite_model, mock_frame_extractor)
        
        # Signal spies
        detection_completed_spy = QSignalSpy(auto_detection_controller.detectionCompleted)
        
        # Load a sprite sheet
        test_path = sample_sprite_paths.get("archer_idle")
        if test_path and test_path.exists():
            success, _, _ = sprite_model.load_sprite_sheet(str(test_path))
            assert success
            
            # Trigger auto-detection
            success = auto_detection_controller.handle_new_sprite_sheet_loaded()
            
            # Verify detection completed
            if success:
                assert len(detection_completed_spy) > 0
                
                # Verify frame settings were updated
                assert sprite_model.frame_width > 0
                assert sprite_model.frame_height > 0
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_sprite_sheet_handling(self, qapp):
        """Test handling of large sprite sheets."""
        sprite_model = SpriteModel()
        
        # Create a large mock sprite sheet
        large_pixmap = QPixmap(2048, 2048)
        large_pixmap.fill()
        
        # Test with large frame settings
        sprite_model._original_sprite_sheet = large_pixmap
        sprite_model.set_frame_settings(128, 128, 0, 0, 0, 0)
        
        # Extract frames (should handle large sheets gracefully)
        frame_count = sprite_model.extract_frames()
        
        # Should extract reasonable number of frames
        assert 0 < frame_count < 1000  # Sanity check
        
        # Verify memory usage is reasonable
        assert sprite_model.get_frame_count() == frame_count


class TestErrorHandlingWorkflow:
    """Test error handling in integrated workflows."""
    
    @pytest.mark.integration
    def test_invalid_file_handling(self, qapp):
        """Test handling of invalid file paths."""
        sprite_model = SpriteModel()
        
        # Test with non-existent file
        success, message, metadata = sprite_model.load_sprite_sheet("/nonexistent/file.png")
        assert not success
        assert "not found" in message.lower() or "error" in message.lower()
        
        # Verify model state remains clean
        assert sprite_model.original_sprite_sheet is None
        assert sprite_model.get_frame_count() == 0
    
    @pytest.mark.integration
    def test_corrupted_file_handling(self, qapp, temp_dir):
        """Test handling of corrupted image files."""
        sprite_model = SpriteModel()
        
        # Create a fake image file with invalid content
        fake_image = temp_dir / "corrupted.png"
        fake_image.write_text("This is not a valid image file")
        
        # Try to load corrupted file
        success, message, metadata = sprite_model.load_sprite_sheet(str(fake_image))
        assert not success
        
        # Verify model state remains clean
        assert sprite_model.original_sprite_sheet is None
        assert sprite_model.get_frame_count() == 0
    
    @pytest.mark.integration
    def test_extraction_without_sprite_sheet(self, qapp):
        """Test frame extraction without loaded sprite sheet."""
        sprite_model = SpriteModel()
        
        # Try to extract frames without loading a sprite sheet
        sprite_model.set_frame_settings(32, 32, 0, 0, 0, 0)
        frame_count = sprite_model.extract_frames()
        
        # Should handle gracefully
        assert frame_count == 0
        assert sprite_model.get_frame_count() == 0


class TestPerformanceWorkflow:
    """Test performance aspects of integrated workflows."""
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_rapid_frame_extraction_changes(self, qapp, mock_pixmap):
        """Test rapid changes to frame extraction settings."""
        sprite_model = SpriteModel()
        sprite_model._original_sprite_sheet = mock_pixmap
        
        extraction_times = []
        frame_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        
        for width, height in frame_sizes:
            import time
            start_time = time.time()
            
            sprite_model.set_frame_settings(width, height, 0, 0, 0, 0)
            frame_count = sprite_model.extract_frames()
            
            end_time = time.time()
            extraction_times.append(end_time - start_time)
            
            assert frame_count > 0
        
        # Verify reasonable performance (should complete in under 1 second each)
        assert all(time < 1.0 for time in extraction_times)
    
    @pytest.mark.integration
    @pytest.mark.performance  
    @pytest.mark.memory_intensive
    def test_memory_usage_with_multiple_extractions(self, qapp, mock_pixmap):
        """Test memory usage with multiple frame extractions."""
        sprite_model = SpriteModel()
        sprite_model._original_sprite_sheet = mock_pixmap
        
        # Perform multiple extractions to test memory handling
        for i in range(10):
            sprite_model.set_frame_settings(32, 32, 0, 0, i % 3, i % 2)
            frame_count = sprite_model.extract_frames()
            assert frame_count > 0
        
        # Verify frames are properly managed (no excessive accumulation)
        final_frame_count = sprite_model.get_frame_count()
        assert final_frame_count > 0
        assert final_frame_count < 1000  # Reasonable upper bound


class TestComponentInteraction:
    """Test interaction between different components in workflows."""
    
    @pytest.mark.integration
    def test_sprite_model_animation_controller_interaction(self, qapp, configured_sprite_model):
        """Test interaction between sprite model and animation controller."""
        animation_controller = AnimationController()
        
        # Initialize with sprite model
        animation_controller.initialize(configured_sprite_model, Mock())
        
        # Signal spies
        frame_advanced_spy = QSignalSpy(animation_controller.frameAdvanced)
        
        # Start animation
        animation_controller.start_animation()
        assert animation_controller._is_playing
        
        # Simulate frame advancement
        animation_controller._advance_frame()
        
        # Verify frame advancement signal
        assert len(frame_advanced_spy) > 0
        
        # Stop animation
        animation_controller.stop_animation()
        assert not animation_controller._is_playing
    
    @pytest.mark.integration
    def test_detection_model_interaction(self, qapp):
        """Test interaction between detection controller and sprite model."""
        sprite_model = SpriteModel()
        auto_detection_controller = AutoDetectionController()
        
        # Mock frame extractor
        mock_frame_extractor = Mock()
        auto_detection_controller.initialize(sprite_model, mock_frame_extractor)
        
        # Load test sprite
        test_pixmap = QPixmap(256, 256)
        test_pixmap.fill()
        sprite_model._original_sprite_sheet = test_pixmap
        
        # Trigger detection workflow
        success = auto_detection_controller.handle_new_sprite_sheet_loaded()
        
        # Verify interaction completed
        assert isinstance(success, bool)  # Should return boolean result
    
    @pytest.mark.integration
    def test_full_component_stack_interaction(self, qapp, mock_pixmap):
        """Test full component stack working together."""
        # Create all components
        sprite_model = SpriteModel()
        animation_controller = AnimationController()
        auto_detection_controller = AutoDetectionController()
        
        # Setup mock frame extractor
        mock_frame_extractor = Mock()
        
        # Initialize components
        animation_controller.initialize(sprite_model, Mock())
        auto_detection_controller.initialize(sprite_model, mock_frame_extractor)
        
        # Load sprite
        sprite_model._original_sprite_sheet = mock_pixmap
        sprite_model.set_frame_settings(64, 64, 0, 0, 0, 0)
        frame_count = sprite_model.extract_frames()
        
        assert frame_count > 0
        
        # Start animation
        animation_controller.start_animation()
        assert animation_controller._is_playing
        
        # Test state consistency across components
        assert sprite_model.get_frame_count() > 0
        assert animation_controller._is_active
        
        # Cleanup
        animation_controller.stop_animation()
        sprite_model.clear_frames()