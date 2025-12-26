#!/usr/bin/env python3
"""
Configuration and Constants for Sprite Viewer
Centralizes all magic numbers and settings for better maintainability.
"""

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

    # Speed stepping (for increase/decrease speed controls)
    SPEED_STEPS = (1, 2, 4, 6, 8, 10, 12, 15, 20, 24, 30, 60)

    # Timer calculation
    TIMER_BASE = 1000  # milliseconds  # milliseconds


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
    PRESET_GRID_SPACING = 6      # Consistent grid spacing
    SIZE_LAYOUT_SPACING = 5      # Keep size layout compact
    NAV_BUTTON_SPACING = 6       # Consistent button spacing

    # Button dimensions (compacted by 20-25%)
    PLAYBACK_BUTTON_MIN_HEIGHT = 32   # Reduced from 40
    NAV_BUTTON_MIN_WIDTH = 28         # Reduced from 35
    NAV_BUTTON_MIN_HEIGHT = 28        # Reduced from 35
    COLOR_BUTTON_MAX_WIDTH = 50       # Reduced from 60
    AUTO_BUTTON_MAX_WIDTH = 50        # Keep for usability

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

    @staticmethod
    def get_default_export_directory():
        """Get default export directory."""
        import os
        from pathlib import Path

        # Try Desktop first
        desktop = Path.home() / "Desktop"
        if desktop.exists() and os.access(desktop, os.W_OK):
            return desktop / "sprite_exports"

        # Fallback to Documents
        documents = Path.home() / "Documents"
        if documents.exists() and os.access(documents, os.W_OK):
            return documents / "sprite_exports"

        # Last resort: current directory
        return Path.cwd() / "sprite_exports"


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


class FontConfig:
    """Font and text styling settings."""

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


class SettingsConfig:
    """Settings persistence and application preferences."""

    # QSettings configuration
    ORGANIZATION_NAME = "PythonSpriteViewer"
    APPLICATION_NAME = "SpriteViewer"

    # Recent files
    MAX_RECENT_FILES = 10

    # Auto-save settings
    AUTOSAVE_DELAY_MS = 1000  # Debounce delay before saving

    # Default values for settings that don't exist
    DEFAULTS = {
        # Window geometry (will be set by application)
        'window/geometry': None,
        'window/state': None,
        'window/splitter_state': None,

        # Frame extraction defaults
        'extraction/last_width': 32,
        'extraction/last_height': 32,
        'extraction/last_offset_x': 0,
        'extraction/last_offset_y': 0,
        'extraction/last_spacing_x': 0,
        'extraction/last_spacing_y': 0,
        'extraction/last_mode': 'grid',

        # Display preferences
        'display/grid_visible': False,
        'display/last_zoom': 1.0,
        'display/zoom_fit_tiny': True,

        # Animation preferences
        'animation/last_fps': 10,
        'animation/loop_mode': True,

        # Recent files
        'recent/files': [],
        'recent/max_count': 10,
    }


class StylesConfig:
    """CSS stylesheet constants for UI components."""

    # Canvas styles
    CANVAS_NORMAL = """
        QLabel {
            border: 2px solid #ccc;
            border-radius: 4px;
            background-color: #f5f5f5;
        }
    """
    CANVAS_DRAG_HOVER = """
        QLabel {
            border: 4px dashed #4CAF50;
            border-radius: 8px;
            background-color: #e8f5e9;
        }
    """

    # Button styles
    PLAY_BUTTON_STOPPED = """
        QPushButton {
            font-size: 14pt;
            font-weight: bold;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
    """
    PLAY_BUTTON_PLAYING = """
        QPushButton {
            font-size: 14pt;
            font-weight: bold;
            background-color: #ff9800;
            color: white;
            border: none;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #e68900;
        }
        QPushButton:pressed {
            background-color: #cc7a00;
        }
    """
    NAVIGATION_BUTTONS = f"""
        QPushButton {{
            font-size: 12pt;
            min-width: {UIConfig.NAV_BUTTON_WIDTH_PX};
            min-height: {UIConfig.NAV_BUTTON_HEIGHT_PX};
            background-color: #e0e0e0;
            border: 1px solid #bbb;
            border-radius: 4px;
        }}
        QPushButton:hover:enabled {{
            background-color: #d0d0d0;
        }}
        QPushButton:pressed {{
            background-color: #c0c0c0;
        }}
        QPushButton:disabled {{
            color: #999;
            background-color: #f0f0f0;
        }}
    """

    # Container styles
    PLAYBACK_CONTROLS_FRAME = """
        QFrame {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 10px;
        }
    """
    FRAME_EXTRACTOR_GROUPBOX = """
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """
    MAIN_TOOLBAR = """
        QToolBar {
            background-color: #f5f5f5;
            border-bottom: 1px solid #ddd;
            padding: 5px;
            spacing: 5px;
        }
        QToolButton {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
            margin: 2px;
        }
        QToolButton:hover {
            background-color: #e8e8e8;
            border-color: #bbb;
        }
        QToolButton:pressed {
            background-color: #ddd;
        }
    """

    # Label styles
    INFO_LABEL = "color: #666; font-size: 10pt;"
    HELP_LABEL = "color: #888; font-style: italic; padding: 10px;"
    SPEED_LABEL = "font-weight: bold;"
    ZOOM_DISPLAY = """
        QLabel {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
            font-weight: bold;
        }
    """
    PRESET_LABEL = "font-weight: normal; margin-bottom: 5px;"
    CUSTOM_LABEL = "font-weight: normal; margin-top: 10px;"
    OFFSET_LABEL = "font-weight: normal; margin-top: 10px;"
    GRID_CHECKBOX = "margin-top: 10px;"


class ExportConfig:
    """Export functionality settings."""

    # Supported image formats
    IMAGE_FORMATS = ['PNG', 'JPG', 'BMP']
    DEFAULT_FORMAT = 'PNG'

    # Default naming patterns
    DEFAULT_PATTERN = "{name}_{index:03d}"
    DEFAULT_SCALE_FACTORS = [1.0, 2.0, 4.0]

    # Enhanced Sprite Sheet Layout Configuration
    # ==========================================

    # Layout calculation modes
    LAYOUT_MODES = ['auto', 'rows', 'columns', 'square', 'custom', 'segments_per_row']
    DEFAULT_LAYOUT_MODE = 'auto'

    # Spacing and padding settings
    DEFAULT_SPRITE_SPACING = 0      # Pixels between sprites
    MIN_SPRITE_SPACING = 0          # Minimum spacing allowed
    MAX_SPRITE_SPACING = 50         # Maximum spacing allowed
    SPRITE_SPACING_STEP = 1         # Increment step for UI controls

    DEFAULT_SHEET_PADDING = 0       # Padding around entire sheet
    MIN_SHEET_PADDING = 0           # Minimum padding allowed
    MAX_SHEET_PADDING = 100         # Maximum padding allowed
    SHEET_PADDING_STEP = 5          # Increment step for UI controls

    # Grid configuration constraints
    DEFAULT_MAX_COLUMNS = 10        # Default max columns for 'rows' mode
    DEFAULT_MAX_ROWS = 10           # Default max rows for 'columns' mode
    MIN_GRID_SIZE = 1               # Minimum grid dimension
    MAX_GRID_SIZE = 50              # Maximum grid dimension (reasonable limit)

    # Background fill options
    BACKGROUND_MODES = ['transparent', 'solid', 'checkerboard']
    DEFAULT_BACKGROUND_MODE = 'transparent'
    DEFAULT_BACKGROUND_COLOR = (255, 255, 255, 255)  # White with full alpha

    # Checkerboard pattern settings (for background)
    CHECKERBOARD_TILE_SIZE = 16     # Size of checkerboard tiles
    CHECKERBOARD_LIGHT_COLOR = (255, 255, 255, 255)  # Light checkerboard color
    CHECKERBOARD_DARK_COLOR = (192, 192, 192, 255)   # Dark checkerboard color

    # Layout calculation preferences
    PREFER_HORIZONTAL = False       # For auto mode: prefer horizontal vs vertical layouts
    ENABLE_ANTIALIASING = True      # Enable antialiasing for scaled sprites


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
    Font = FontConfig
    App = AppConfig
    Settings = SettingsConfig
    Export = ExportConfig
    Styles = StylesConfig


# Export for easy importing
__all__ = [
    'AnimationConfig',
    'AppConfig',
    'CanvasConfig',
    'Config',
    'DrawingConfig',
    'ExportConfig',
    'FileConfig',
    'FontConfig',
    'FrameExtractionConfig',
    'SettingsConfig',
    'SliderConfig',
    'StylesConfig',
    'UIConfig',
]
