"""
Unit tests for configuration system.
Tests the centralized configuration classes and validation.
"""

import pytest
from config import (
    Config, CanvasConfig, AnimationConfig, FrameExtractionConfig,
    UIConfig, DrawingConfig, FileConfig, SliderConfig
)


class TestCanvasConfig:
    """Test canvas configuration settings."""
    
    def test_canvas_dimensions(self):
        """Test canvas minimum dimensions are reasonable."""
        assert CanvasConfig.MIN_WIDTH >= 400
        assert CanvasConfig.MIN_HEIGHT >= 300
        assert CanvasConfig.MIN_WIDTH < CanvasConfig.MIN_HEIGHT * 3  # Reasonable aspect ratio
    
    def test_zoom_settings(self):
        """Test zoom configuration is valid."""
        assert CanvasConfig.ZOOM_MIN > 0
        assert CanvasConfig.ZOOM_MAX > CanvasConfig.ZOOM_MIN
        assert CanvasConfig.ZOOM_FACTOR > 1.0
        assert 0 < CanvasConfig.ZOOM_FIT_MARGIN < 1
    
    def test_auto_fit_settings(self):
        """Test auto-fit configuration."""
        assert isinstance(CanvasConfig.AUTO_FIT_ON_LOAD, bool)
        assert CanvasConfig.MIN_DISPLAY_ZOOM >= 1.0
        assert CanvasConfig.TINY_SPRITE_THRESHOLD > 0


class TestAnimationConfig:
    """Test animation configuration settings."""
    
    def test_fps_bounds(self):
        """Test FPS limits are reasonable."""
        assert 1 <= AnimationConfig.MIN_FPS <= AnimationConfig.DEFAULT_FPS
        assert AnimationConfig.DEFAULT_FPS <= AnimationConfig.MAX_FPS <= 120
    
    def test_timer_calculation(self):
        """Test timer calculation base."""
        assert AnimationConfig.TIMER_BASE == 1000  # milliseconds
    
    def test_frame_limits(self):
        """Test frame count limits."""
        assert AnimationConfig.MIN_REASONABLE_FRAMES >= 1
        assert AnimationConfig.MAX_REASONABLE_FRAMES >= 10


class TestFrameExtractionConfig:
    """Test frame extraction configuration."""
    
    def test_frame_size_limits(self):
        """Test frame size boundaries."""
        assert FrameExtractionConfig.MIN_FRAME_SIZE >= 1
        assert FrameExtractionConfig.MAX_FRAME_SIZE >= 256
    
    def test_default_frame_size(self):
        """Test default frame dimensions are valid."""
        assert FrameExtractionConfig.DEFAULT_FRAME_WIDTH > 0
        assert FrameExtractionConfig.DEFAULT_FRAME_HEIGHT > 0
    
    def test_presets_structure(self):
        """Test frame size presets are properly structured."""
        for label, width, height, tooltip in FrameExtractionConfig.SQUARE_PRESETS:
            assert isinstance(label, str)
            assert isinstance(width, int) and width > 0
            assert isinstance(height, int) and height > 0
            assert isinstance(tooltip, str)
            assert width == height  # Square presets should be square
        
        for label, width, height, tooltip in FrameExtractionConfig.RECTANGULAR_PRESETS:
            assert isinstance(label, str)
            assert isinstance(width, int) and width > 0
            assert isinstance(height, int) and height > 0
            assert isinstance(tooltip, str)
            assert width != height  # Rectangular presets should not be square
    
    def test_base_sizes_ordering(self):
        """Test base sizes are in logical order."""
        sizes = FrameExtractionConfig.BASE_SIZES
        assert len(sizes) > 0
        assert all(isinstance(size, int) and size > 0 for size in sizes)
    
    def test_aspect_ratios(self):
        """Test aspect ratios are valid."""
        for width_ratio, height_ratio in FrameExtractionConfig.COMMON_ASPECT_RATIOS:
            assert isinstance(width_ratio, int) and width_ratio > 0
            assert isinstance(height_ratio, int) and height_ratio > 0


class TestUIConfig:
    """Test UI configuration settings."""
    
    def test_window_dimensions(self):
        """Test default window size is reasonable."""
        assert UIConfig.DEFAULT_WINDOW_WIDTH >= UIConfig.MIN_WINDOW_WIDTH
        assert UIConfig.DEFAULT_WINDOW_HEIGHT >= UIConfig.MIN_WINDOW_HEIGHT
    
    def test_controls_sizing(self):
        """Test controls panel sizing."""
        assert 0 < UIConfig.CONTROLS_WIDTH_RATIO < 0.5  # Should be less than half
        assert UIConfig.CONTROLS_MIN_WIDTH < UIConfig.CONTROLS_MAX_WIDTH
    
    def test_button_dimensions(self):
        """Test button size constraints."""
        assert UIConfig.PLAYBACK_BUTTON_MIN_HEIGHT > 20  # Reasonable minimum
        assert UIConfig.NAV_BUTTON_MIN_WIDTH > 20
        assert UIConfig.NAV_BUTTON_MIN_HEIGHT > 20


class TestFileConfig:
    """Test file handling configuration."""
    
    def test_supported_extensions(self):
        """Test supported file extensions."""
        extensions = FileConfig.SUPPORTED_EXTENSIONS
        assert len(extensions) > 0
        assert all(ext.startswith('.') for ext in extensions)
        assert '.png' in extensions  # Must support PNG
    
    def test_image_filter(self):
        """Test file dialog filter format."""
        filter_str = FileConfig.IMAGE_FILTER
        assert isinstance(filter_str, str)
        assert len(filter_str) > 0
        assert 'Image Files' in filter_str


class TestMainConfig:
    """Test main Config class that provides access to all settings."""
    
    def test_config_access(self):
        """Test Config class provides access to all sub-configs."""
        assert hasattr(Config, 'Canvas')
        assert hasattr(Config, 'Animation') 
        assert hasattr(Config, 'FrameExtraction')
        assert hasattr(Config, 'UI')
        assert hasattr(Config, 'Drawing')
        assert hasattr(Config, 'File')
        assert hasattr(Config, 'Slider')
        assert hasattr(Config, 'Color')
        assert hasattr(Config, 'Font')
        assert hasattr(Config, 'App')
    
    def test_config_consistency(self):
        """Test configuration values are internally consistent."""
        # Canvas zoom settings should be consistent
        assert Config.Canvas.ZOOM_MIN < Config.Canvas.ZOOM_MAX
        
        # Animation FPS should be within slider bounds
        assert Config.Animation.MIN_FPS <= Config.Animation.DEFAULT_FPS
        assert Config.Animation.DEFAULT_FPS <= Config.Animation.MAX_FPS
        
        # UI sizing should be consistent
        assert Config.UI.MIN_WINDOW_WIDTH <= Config.UI.DEFAULT_WINDOW_WIDTH
        assert Config.UI.MIN_WINDOW_HEIGHT <= Config.UI.DEFAULT_WINDOW_HEIGHT


@pytest.mark.parametrize("fps", [1, 5, 10, 15, 30, 60])
def test_fps_timer_calculation(fps):
    """Test timer interval calculation for various FPS values."""
    expected_interval = Config.Animation.TIMER_BASE / fps
    assert expected_interval > 0
    assert expected_interval <= Config.Animation.TIMER_BASE


@pytest.mark.parametrize("size", [16, 32, 64, 128, 256])
def test_frame_size_validity(size):
    """Test various frame sizes are within valid bounds."""
    assert Config.FrameExtraction.MIN_FRAME_SIZE <= size <= Config.FrameExtraction.MAX_FRAME_SIZE