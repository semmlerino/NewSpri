"""
Unit tests for SpriteModel core functionality.
Tests the main model class and its modular components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSignalSpy

from sprite_model import SpriteModel


class TestSpriteModelInitialization:
    """Test SpriteModel initialization and setup."""
    
    def test_sprite_model_creation(self, sprite_model):
        """Test SpriteModel can be created successfully."""
        assert isinstance(sprite_model, SpriteModel)
    
    def test_initial_state(self, sprite_model):
        """Test SpriteModel starts in clean initial state."""
        assert sprite_model._sprite_frames == []
        assert sprite_model._file_path == ""
        assert sprite_model._frame_width == 0
        assert sprite_model._frame_height == 0
        assert sprite_model._offset_x == 0
        assert sprite_model._offset_y == 0
        assert sprite_model._spacing_x == 0
        assert sprite_model._spacing_y == 0
    
    def test_signals_exist(self, sprite_model):
        """Test all required signals are defined."""
        assert hasattr(sprite_model, 'frameChanged')
        assert hasattr(sprite_model, 'dataLoaded')
        assert hasattr(sprite_model, 'extractionCompleted')
        assert hasattr(sprite_model, 'playbackStateChanged')
        assert hasattr(sprite_model, 'errorOccurred')
        assert hasattr(sprite_model, 'configurationChanged')


class TestSpriteModelConfiguration:
    """Test SpriteModel configuration methods."""
    
    def test_set_frame_settings(self, sprite_model):
        """Test setting frame extraction parameters."""
        sprite_model.set_frame_settings(64, 48, 4, 2, 2, 1)
        
        assert sprite_model._frame_width == 64
        assert sprite_model._frame_height == 48
        assert sprite_model._offset_x == 4
        assert sprite_model._offset_y == 2
        assert sprite_model._spacing_x == 2
        assert sprite_model._spacing_y == 1
    
    @pytest.mark.parametrize("width,height", [
        (32, 32), (64, 48), (128, 128), (16, 24)
    ])
    def test_frame_size_validation(self, sprite_model, width, height):
        """Test various frame sizes are accepted."""
        sprite_model.set_frame_settings(width, height, 0, 0, 0, 0)
        assert sprite_model._frame_width == width
        assert sprite_model._frame_height == height
    
    def test_invalid_frame_settings(self, sprite_model):
        """Test handling of invalid frame settings."""
        # Test negative values
        with pytest.raises((ValueError, AssertionError)):
            sprite_model.set_frame_settings(-1, 32, 0, 0, 0, 0)
        
        with pytest.raises((ValueError, AssertionError)):
            sprite_model.set_frame_settings(32, -1, 0, 0, 0, 0)


class TestSpriteModelFrameManagement:
    """Test sprite frame management functionality."""
    
    def test_get_frame_count(self, configured_sprite_model):
        """Test getting frame count."""
        count = configured_sprite_model.get_frame_count()
        assert count == len(configured_sprite_model._sprite_frames)
        assert count > 0
    
    def test_get_frame_valid_index(self, configured_sprite_model):
        """Test getting frame with valid index."""
        frame = configured_sprite_model.get_frame(0)
        assert isinstance(frame, QPixmap)
        assert not frame.isNull()
    
    def test_get_frame_invalid_index(self, configured_sprite_model):
        """Test getting frame with invalid index."""
        # Test negative index
        frame = configured_sprite_model.get_frame(-1)
        assert frame is None or frame.isNull()
        
        # Test index beyond range
        frame_count = configured_sprite_model.get_frame_count()
        frame = configured_sprite_model.get_frame(frame_count + 10)
        assert frame is None or frame.isNull()
    
    def test_clear_frames(self, configured_sprite_model):
        """Test clearing sprite frames."""
        assert configured_sprite_model.get_frame_count() > 0
        
        configured_sprite_model.clear_frames()
        assert configured_sprite_model.get_frame_count() == 0


class TestSpriteModelProperties:
    """Test SpriteModel property accessors."""
    
    def test_frame_dimensions_properties(self, sprite_model):
        """Test frame dimension property accessors."""
        sprite_model.set_frame_settings(64, 48, 0, 0, 0, 0)
        
        assert sprite_model.frame_width == 64
        assert sprite_model.frame_height == 48
    
    def test_offset_properties(self, sprite_model):
        """Test offset property accessors."""
        sprite_model.set_frame_settings(32, 32, 5, 10, 0, 0)
        
        assert sprite_model.offset_x == 5
        assert sprite_model.offset_y == 10
    
    def test_spacing_properties(self, sprite_model):
        """Test spacing property accessors."""
        sprite_model.set_frame_settings(32, 32, 0, 0, 3, 7)
        
        assert sprite_model.spacing_x == 3
        assert sprite_model.spacing_y == 7
    
    def test_file_path_property(self, sprite_model):
        """Test file path property."""
        test_path = "/test/path/sprite.png"
        sprite_model._file_path = test_path
        
        assert sprite_model.file_path == test_path


class TestSpriteModelSignals:
    """Test SpriteModel signal emission."""
    
    def test_configuration_changed_signal(self, sprite_model, qapp):
        """Test configurationChanged signal is emitted."""
        spy = QSignalSpy(sprite_model.configurationChanged)
        
        sprite_model.set_frame_settings(64, 64, 0, 0, 0, 0)
        
        assert len(spy) > 0
    
    def test_frame_changed_signal(self, configured_sprite_model, qapp):
        """Test frameChanged signal with valid parameters."""
        spy = QSignalSpy(configured_sprite_model.frameChanged)
        
        # Simulate frame change
        configured_sprite_model.set_current_frame(1)
        
        # Should emit signal with current frame and total frames
        if len(spy) > 0:
            args = spy[0]
            assert len(args) == 2  # current_frame, total_frames
            assert isinstance(args[0], int)  # current_frame
            assert isinstance(args[1], int)  # total_frames


class TestSpriteModelIntegration:
    """Test SpriteModel integration with modular components."""
    
    def test_file_loader_integration(self, sprite_model):
        """Test integration with file loader component."""
        # Test that file loader is properly initialized
        assert hasattr(sprite_model, '_file_loader')
        assert sprite_model._file_loader is not None
    
    def test_grid_extractor_integration(self, sprite_model):
        """Test integration with grid extractor component."""
        assert hasattr(sprite_model, '_grid_extractor')
        assert sprite_model._grid_extractor is not None
    
    def test_animation_state_integration(self, sprite_model):
        """Test integration with animation state manager."""
        assert hasattr(sprite_model, '_animation_state')
        assert sprite_model._animation_state is not None
    
    def test_detection_coordinator_integration(self, sprite_model):
        """Test integration with detection coordinator."""
        assert hasattr(sprite_model, '_detection_coordinator')
        assert sprite_model._detection_coordinator is not None


@pytest.mark.parametrize("frame_count", [1, 4, 8, 16])
def test_sprite_model_with_various_frame_counts(sprite_model, mock_sprite_frames, frame_count):
    """Test SpriteModel behavior with different frame counts."""
    # Create the specified number of frames
    frames = mock_sprite_frames[:frame_count] if frame_count <= len(mock_sprite_frames) else mock_sprite_frames
    while len(frames) < frame_count:
        frames.extend(mock_sprite_frames[:frame_count - len(frames)])
    
    sprite_model._sprite_frames = frames[:frame_count]
    
    assert sprite_model.get_frame_count() == frame_count
    
    # Test accessing each frame
    for i in range(frame_count):
        frame = sprite_model.get_frame(i)
        assert frame is not None
        assert not frame.isNull()


class TestSpriteModelErrorHandling:
    """Test SpriteModel error handling and edge cases."""
    
    def test_empty_sprite_model_operations(self, sprite_model):
        """Test operations on empty sprite model don't crash."""
        assert sprite_model.get_frame_count() == 0
        assert sprite_model.get_frame(0) is None or sprite_model.get_frame(0).isNull()
        
        # These should not raise exceptions
        sprite_model.clear_frames()
        sprite_model.set_current_frame(0)
    
    def test_sprite_model_reset(self, configured_sprite_model):
        """Test resetting sprite model to initial state."""
        # Verify it's configured
        assert configured_sprite_model.get_frame_count() > 0
        assert configured_sprite_model._frame_width > 0
        
        # Reset to initial state
        configured_sprite_model.reset()
        
        # Verify reset worked
        assert configured_sprite_model.get_frame_count() == 0
        assert configured_sprite_model._frame_width == 0
        assert configured_sprite_model._frame_height == 0
        assert configured_sprite_model._file_path == ""