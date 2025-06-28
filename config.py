#!/usr/bin/env python3
"""
Configuration and Constants for Sprite Viewer
Centralizes all magic numbers and settings for better maintainability.
"""

from typing import Tuple, List
from PySide6.QtCore import QSize
from PySide6.QtGui import QColor


class CanvasConfig:
    """Canvas display and interaction settings."""
    
    # Canvas dimensions
    MIN_WIDTH = 600
    MIN_HEIGHT = 400
    
    # Zoom settings
    ZOOM_MIN = 0.1
    ZOOM_MAX = 10.0
    ZOOM_FACTOR = 1.2  # Multiplier for zoom in/out
    ZOOM_FIT_MARGIN = 0.9  # 90% of window size when fitting
    
    # Auto-fit display settings
    AUTO_FIT_ON_LOAD = True
    MIN_DISPLAY_ZOOM = 2.0  # Minimum zoom for tiny sprites
    TINY_SPRITE_THRESHOLD = 32  # Pixels - sprites smaller than this get min zoom
    INITIAL_FIT_MARGIN = 0.85  # Tighter fit than standard zoom fit
    
    # Pan settings
    DEFAULT_PAN_OFFSET = [0, 0]
    
    # Default background
    DEFAULT_BG_COLOR = QColor(128, 128, 128)
    
    # Grid overlay
    DEFAULT_GRID_SIZE = 32
    GRID_LINE_ALPHA = 128  # Semi-transparent grid lines


class AnimationConfig:
    """Animation playback settings."""
    
    # FPS settings
    DEFAULT_FPS = 10
    MIN_FPS = 1
    MAX_FPS = 60
    
    # Timer calculation
    TIMER_BASE = 1000  # milliseconds
    
    # Frame limits for auto-detection
    MAX_REASONABLE_FRAMES = 100
    MIN_REASONABLE_FRAMES = 1


class FrameExtractionConfig:
    """Frame size and extraction settings."""
    
    # Frame size limits
    MIN_FRAME_SIZE = 1
    MAX_FRAME_SIZE = 2048
    
    # Default frame size (3x3 character sprites)
    DEFAULT_FRAME_WIDTH = 192
    DEFAULT_FRAME_HEIGHT = 192
    
    # Default to 192x192 preset (index 4 in square presets)
    DEFAULT_PRESET_INDEX = 4
    
    # Frame size presets organized by category: (label, width, height, tooltip)
    SQUARE_PRESETS = [
        ("16×16", 16, 16, "Small icons"),
        ("32×32", 32, 32, "Standard tiles"),
        ("64×64", 64, 64, "Large tiles"),
        ("128×128", 128, 128, "2×2 tiles"),
        ("192×192", 192, 192, "3×3 character sprites"),
        ("256×256", 256, 256, "4×4 large sprites"),
    ]
    
    RECTANGULAR_PRESETS = [
        ("16×32", 16, 32, "Tall character sprites"),
        ("32×16", 32, 16, "Wide platform tiles"),
        ("32×48", 32, 48, "RPG characters"),
        ("48×32", 48, 32, "Wide characters"),
        ("32×64", 32, 64, "Tall sprites"),
        ("64×32", 64, 32, "Wide tiles"),
        ("48×64", 48, 64, "Portrait sprites"),
        ("64×48", 64, 48, "Landscape sprites"),
        ("24×32", 24, 32, "Small characters"),
        ("40×48", 40, 48, "Medium portraits"),
    ]
    
    # Legacy combined presets (for backward compatibility)
    FRAME_PRESETS = SQUARE_PRESETS
    
    # Offset/margin settings
    MAX_OFFSET = 1000  # Maximum offset value for X and Y
    DEFAULT_OFFSET = 0  # Default offset value
    
    # Frame spacing settings
    MAX_SPACING = 20  # Maximum spacing between frames
    DEFAULT_SPACING = 0  # Default spacing (0 = no gaps)
    
    # Auto-detection settings
    AUTO_DETECT_SIZES = [256, 192, 128, 64, 32, 16]  # Try these sizes first (legacy square-only)
    MIN_SPRITE_SIZE = 16  # Minimum reasonable sprite size
    MARGIN_DETECTION_ALPHA_THRESHOLD = 10  # For detecting transparent margins
    
    # Enhanced auto-detection (Phase 2)
    BASE_SIZES = [8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128, 160, 192, 256]
    COMMON_ASPECT_RATIOS = [
        (1, 1),   # Square: 32×32, 64×64
        (1, 2),   # Tall: 16×32, 32×64, 48×96
        (2, 1),   # Wide: 32×16, 64×32, 96×48
        (2, 3),   # Character: 32×48, 64×96
        (3, 2),   # Wide char: 48×32, 96×64
        (3, 4),   # Portrait: 48×64, 72×96
        (4, 3),   # Landscape: 64×48, 96×72
    ]
    
    # Frame count constraints for detection
    MIN_REASONABLE_FRAMES = 2
    MAX_REASONABLE_FRAMES = 200
    OPTIMAL_FRAME_COUNT_MIN = 4
    OPTIMAL_FRAME_COUNT_MAX = 100


class UIConfig:
    """User interface layout and sizing settings."""
    
    # Main window (optimized sizing - 17% smaller)
    DEFAULT_WINDOW_WIDTH = 1000
    DEFAULT_WINDOW_HEIGHT = 700
    DEFAULT_WINDOW_X = 100
    DEFAULT_WINDOW_Y = 100
    
    # Minimum window size for usability
    MIN_WINDOW_WIDTH = 800   # Ensures canvas + controls are usable
    MIN_WINDOW_HEIGHT = 600  # Ensures all controls are accessible
    
    # Controls panel (optimized responsive sizing)
    CONTROLS_WIDTH_RATIO = 0.22  # 22% of window width (was 25%)
    CONTROLS_MIN_WIDTH = 250     # Reduced minimum for better proportions
    CONTROLS_MAX_WIDTH = 350     # Reduced maximum to improve canvas space
    
    # Info group constraints
    INFO_GROUP_MAX_HEIGHT = 120
    
    # Layout spacing (standardized to 6px for consistency)
    MAIN_LAYOUT_SPACING = 6
    CONTROLS_LAYOUT_SPACING = 6  # Consistent spacing throughout
    PRESET_GRID_SPACING = 6      # Consistent grid spacing
    SIZE_LAYOUT_SPACING = 5      # Keep size layout compact
    NAV_BUTTON_SPACING = 6       # Consistent button spacing
    COLLAPSIBLE_SECTION_SPACING = 8  # Spacing within collapsible sections
    
    # Button dimensions (compacted by 20-25%)
    PLAYBACK_BUTTON_MIN_HEIGHT = 32   # Reduced from 40
    NAV_BUTTON_MIN_WIDTH = 28         # Reduced from 35
    NAV_BUTTON_MIN_HEIGHT = 28        # Reduced from 35
    COLOR_BUTTON_MAX_WIDTH = 50       # Reduced from 60
    AUTO_BUTTON_MAX_WIDTH = 50        # Keep for usability
    ZOOM_PRESET_BUTTON_MAX_WIDTH = 42 # Reduced from 50
    
    # Navigation button style values (updated to match new dimensions)
    NAV_BUTTON_WIDTH_PX = "28px"
    NAV_BUTTON_HEIGHT_PX = "28px"
    
    # Zoom display
    ZOOM_LABEL_MIN_WIDTH = 60


class DrawingConfig:
    """Drawing and rendering settings."""
    
    # Checkerboard background
    CHECKERBOARD_TILE_SIZE = 16
    CHECKERBOARD_LIGHT_COLOR = QColor(255, 255, 255)
    CHECKERBOARD_DARK_COLOR = QColor(192, 192, 192)
    
    # Frame info overlay
    FRAME_INFO_WIDTH = 140
    FRAME_INFO_HEIGHT = 30
    FRAME_INFO_MARGIN_RIGHT = 150
    FRAME_INFO_MARGIN_TOP = 10
    FRAME_INFO_BG_ALPHA = 180  # Semi-transparent background
    FRAME_INFO_TEXT_COLOR = QColor(255, 255, 255)
    
    # Grid overlay
    GRID_PEN_WIDTH = 1
    GRID_COLOR = QColor(255, 0, 0, 128)  # Semi-transparent red


class FileConfig:
    """File handling and I/O settings."""
    
    # Supported image formats
    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    
    # File dialog filter
    IMAGE_FILTER = "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
    
    # Test sprite locations
    TEST_SPRITE_PATHS = [
        "test_sprite_sheet.png",
        "Archer/*.png",
        "sprites/*.png", 
        "assets/*.png"
    ]
    
    # Common frame sizes for auto-detection (ordered by preference)
    COMMON_FRAME_SIZES = [16, 32, 64, 128, 192, 256]


class SliderConfig:
    """Slider and control widget settings."""
    
    # Zoom slider
    ZOOM_SLIDER_MIN = 10    # 0.1x zoom (10%)
    ZOOM_SLIDER_MAX = 1000  # 10x zoom (1000%)
    ZOOM_SLIDER_DEFAULT = 100  # 1x zoom (100%)
    
    # FPS slider
    FPS_SLIDER_TICK_INTERVAL = 10
    
    # Frame slider
    FRAME_SLIDER_MIN = 0
    
    # FPS value label (compacted)
    FPS_VALUE_MIN_WIDTH = 35  # Reduced from 50


class ColorConfig:
    """Color constants used throughout the application."""
    
    # Status and feedback colors
    SUCCESS_COLOR = "#4CAF50"
    WARNING_COLOR = "#ff9800"
    ERROR_COLOR = "#f44336"
    INFO_COLOR = "#2196F3"
    
    # UI element colors
    BORDER_COLOR = "#ccc"
    BACKGROUND_COLOR = "#f5f5f5"
    TEXT_COLOR = "#666"
    DISABLED_COLOR = "#999"
    
    # Button colors
    BUTTON_NORMAL = "#e0e0e0"
    BUTTON_HOVER = "#d0d0d0"
    BUTTON_PRESSED = "#c0c0c0"
    BUTTON_DISABLED = "#f0f0f0"


class FontConfig:
    """Font and text styling settings."""
    
    # Font sizes (in points)
    LARGE_FONT_SIZE = 14
    MEDIUM_FONT_SIZE = 12
    SMALL_FONT_SIZE = 10
    TINY_FONT_SIZE = 9
    
    # Frame info overlay font
    FRAME_INFO_FONT_SIZE = 11


class AppConfig:
    """Application-wide settings."""
    
    # Application metadata
    APP_NAME = "Python Sprite Viewer"
    APP_VERSION = "2.0"
    
    # Window title
    WINDOW_TITLE = "Python Sprite Viewer"
    
    # Status messages
    WELCOME_MESSAGE = "Welcome! Drag & drop sprite sheets or click Open to get started"
    READY_MESSAGE = "Ready. Drag & drop sprite sheets or use File > Open"
    NO_SPRITE_MESSAGE = "No sprite sheet loaded"
    
    # Keyboard shortcuts (for documentation)
    SHORTCUTS = {
        "Space": "Play/Pause animation",
        "← / →": "Previous/Next frame", 
        "Home/End": "First/Last frame",
        "Ctrl+O": "Open sprite sheet",
        "Ctrl++/-": "Zoom in/out",
        "Ctrl+0": "Fit to window",
        "Ctrl+1": "Reset zoom (100%)",
        "G": "Toggle grid overlay",
        "Mouse wheel": "Zoom in/out",
        "Click+drag": "Pan view"
    }


# Convenience access to all configs
class Config:
    """Main configuration class providing access to all settings."""
    
    Canvas = CanvasConfig
    Animation = AnimationConfig
    FrameExtraction = FrameExtractionConfig
    UI = UIConfig
    Drawing = DrawingConfig
    File = FileConfig
    Slider = SliderConfig
    Color = ColorConfig
    Font = FontConfig
    App = AppConfig


# Export for easy importing
__all__ = [
    'Config',
    'CanvasConfig', 
    'AnimationConfig',
    'FrameExtractionConfig',
    'UIConfig',
    'DrawingConfig', 
    'FileConfig',
    'SliderConfig',
    'ColorConfig',
    'FontConfig',
    'AppConfig'
]