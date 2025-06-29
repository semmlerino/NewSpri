"""
Global pytest configuration and fixtures for Python Sprite Viewer tests.
Provides reusable fixtures, test utilities, and setup/teardown for all test modules.
Configured for proper PySide6 integration with error suppression.
"""

import os
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Generator, Optional
from unittest.mock import Mock, MagicMock

import pytest

# Configure Qt environment BEFORE importing PySide6
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_LOGGING_RULES"] = "*.debug=false;*.warning=false;*.critical=false"
os.environ["QT_ASSUME_STDERR_HAS_CONSOLE"] = "1"
os.environ["QT_FORCE_STDERR_LOGGING"] = "0"
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

# Suppress warnings before PySide6 import
warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*qt.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*pyside.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, module=".*qt.*")

# Now safely import PySide6
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap, QImage
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QSignalSpy
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    # Create mock classes for when PySide6 is not available
    class QApplication:
        def __init__(self, args=None): pass
        @staticmethod
        def instance(): return None
        def setAttribute(self, attr, value): pass
        def setQuitOnLastWindowClosed(self, value): pass
        def processEvents(self): pass
        def quit(self): pass
    
    class QPixmap:
        def __init__(self, width=100, height=100): 
            self._width, self._height = width, height
        def width(self): return self._width
        def height(self): return self._height
        def isNull(self): return False
        def fill(self, color=None): pass
    
    class Qt:
        AA_DontShowIconsInMenus = 1
        AA_DontUseNativeMenuBar = 2
        AA_DontUseNativeDialogs = 3
        red = 4
        green = 5
        blue = 6
        yellow = 7
        white = 8
        OpenHandCursor = 9
    
    class QSignalSpy:
        def __init__(self, signal): 
            self.signal = signal
            self._calls = []
        def __len__(self): return len(self._calls)
        def __getitem__(self, index): return self._calls[index]

# Add project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import project modules for testing
try:
    from config import Config
    from sprite_model import SpriteModel
    from animation_controller import AnimationController
    from auto_detection_controller import AutoDetectionController
except ImportError as e:
    # Create mock versions if imports fail
    class Config:
        class Canvas:
            MIN_WIDTH = 600
            MIN_HEIGHT = 400
        class Animation:
            DEFAULT_FPS = 10
    
    class SpriteModel:
        def __init__(self): pass
    
    class AnimationController:
        def __init__(self): pass
    
    class AutoDetectionController:
        def __init__(self): pass


# ============================================================================
# APPLICATION FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """
    Session-scoped QApplication fixture for Qt-based tests.
    Ensures single QApplication instance across all tests with proper Qt configuration.
    """
    if not PYSIDE6_AVAILABLE:
        yield QApplication()
        return
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(["pytest"])
        
        # Configure application for testing
        app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
        app.setAttribute(Qt.AA_DontUseNativeMenuBar, True)
        app.setAttribute(Qt.AA_DontUseNativeDialogs, True)
        app.setQuitOnLastWindowClosed(False)
    
    # Suppress Qt debug output
    app.processEvents()
    
    yield app
    
    # Cleanup - process any remaining events
    if app:
        app.processEvents()
        # Note: Don't call app.quit() in session fixture as it affects other tests


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_sprite_paths() -> dict:
    """Paths to sample sprite sheets for testing."""
    sprite_dir = PROJECT_ROOT / "spritetests"
    return {
        "archer_idle": sprite_dir / "Archer" / "Archer_Idle.png",
        "archer_run": sprite_dir / "Archer_Run.png", 
        "lancer_idle": sprite_dir / "Lancer_Idle.png",
        "test_sheet": sprite_dir / "test_sprite_sheet.png",
        "test_rect_32x48": sprite_dir / "test_rect_32x48.png",
        "debug_final": sprite_dir / "debug_final.png"
    }


# ============================================================================
# SPRITE AND IMAGE FIXTURES
# ============================================================================

@pytest.fixture
def mock_pixmap() -> QPixmap:
    """Mock QPixmap for testing."""
    if PYSIDE6_AVAILABLE:
        pixmap = QPixmap(256, 256)
        pixmap.fill(Qt.red)
        return pixmap
    else:
        return QPixmap(256, 256)


@pytest.fixture
def test_sprite_sheet(sample_sprite_paths) -> Optional[QPixmap]:
    """Load a real test sprite sheet if available."""
    if not PYSIDE6_AVAILABLE:
        return QPixmap(512, 512)
    
    test_path = sample_sprite_paths["test_sheet"]
    if test_path.exists():
        return QPixmap(str(test_path))
    return None


@pytest.fixture
def mock_sprite_frames() -> list[QPixmap]:
    """Generate mock sprite frames for testing."""
    frames = []
    if PYSIDE6_AVAILABLE:
        colors = [Qt.red, Qt.green, Qt.blue, Qt.yellow]
        for i, color in enumerate(colors):
            pixmap = QPixmap(64, 64)
            pixmap.fill(color)
            frames.append(pixmap)
    else:
        frames = [QPixmap(64, 64) for _ in range(4)]
    
    return frames


# ============================================================================
# MODEL AND CONTROLLER FIXTURES
# ============================================================================

@pytest.fixture
def sprite_model() -> SpriteModel:
    """Fresh SpriteModel instance for testing."""
    return SpriteModel()


@pytest.fixture
def animation_controller() -> AnimationController:
    """Fresh AnimationController instance for testing."""
    return AnimationController()


@pytest.fixture
def auto_detection_controller() -> AutoDetectionController:
    """Fresh AutoDetectionController instance for testing."""
    return AutoDetectionController()


@pytest.fixture
def configured_sprite_model(sprite_model, mock_sprite_frames) -> SpriteModel:
    """SpriteModel pre-configured with test data."""
    # Mock the sprite frames
    sprite_model._sprite_frames = mock_sprite_frames
    sprite_model._frame_width = 64
    sprite_model._frame_height = 64
    sprite_model._offset_x = 0
    sprite_model._offset_y = 0
    sprite_model._spacing_x = 0
    sprite_model._spacing_y = 0
    
    return sprite_model


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def test_config() -> Config:
    """Access to test configuration."""
    return Config


@pytest.fixture
def mock_config():
    """Mock configuration for testing without affecting real config."""
    config_mock = Mock()
    
    # Mock Canvas config
    config_mock.Canvas = Mock()
    config_mock.Canvas.MIN_WIDTH = 600
    config_mock.Canvas.MIN_HEIGHT = 400
    config_mock.Canvas.ZOOM_MIN = 0.1
    config_mock.Canvas.ZOOM_MAX = 10.0
    
    # Mock Animation config
    config_mock.Animation = Mock()
    config_mock.Animation.DEFAULT_FPS = 10
    config_mock.Animation.MIN_FPS = 1
    config_mock.Animation.MAX_FPS = 60
    
    # Mock FrameExtraction config
    config_mock.FrameExtraction = Mock()
    config_mock.FrameExtraction.DEFAULT_FRAME_WIDTH = 192
    config_mock.FrameExtraction.DEFAULT_FRAME_HEIGHT = 192
    
    return config_mock


# ============================================================================
# UI FIXTURES
# ============================================================================

@pytest.fixture
def mock_qt_signals():
    """Mock Qt signals for testing signal/slot interactions."""
    signals = Mock()
    signals.frameChanged = Mock()
    signals.dataLoaded = Mock()
    signals.extractionCompleted = Mock()
    signals.playbackStateChanged = Mock()
    signals.errorOccurred = Mock()
    
    # Add emit method to each signal
    for signal_name in dir(signals):
        if not signal_name.startswith('_'):
            signal = getattr(signals, signal_name)
            signal.emit = Mock()
            signal.connect = Mock()
    
    return signals


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

@pytest.fixture
def detection_test_cases() -> list[dict]:
    """Test cases for detection algorithms."""
    return [
        {
            "name": "square_32x32",
            "frame_size": (32, 32),
            "expected_frames": 16,
            "margin": (0, 0),
            "spacing": (0, 0)
        },
        {
            "name": "rect_32x48", 
            "frame_size": (32, 48),
            "expected_frames": 12,
            "margin": (4, 4),
            "spacing": (2, 2)
        },
        {
            "name": "large_64x64",
            "frame_size": (64, 64),
            "expected_frames": 9,
            "margin": (8, 8), 
            "spacing": (4, 4)
        }
    ]


@pytest.fixture
def animation_test_cases() -> list[dict]:
    """Test cases for animation functionality."""
    return [
        {
            "name": "default_fps",
            "fps": 10,
            "frame_count": 4,
            "expected_interval": 100  # milliseconds
        },
        {
            "name": "fast_animation",
            "fps": 30,
            "frame_count": 8,
            "expected_interval": 33  # milliseconds (rounded)
        },
        {
            "name": "slow_animation", 
            "fps": 2,
            "frame_count": 6,
            "expected_interval": 500  # milliseconds
        }
    ]


# ============================================================================
# PARAMETRIZED TEST DATA
# ============================================================================

@pytest.fixture(params=[
    {"width": 32, "height": 32},
    {"width": 48, "height": 32},
    {"width": 64, "height": 48},
    {"width": 128, "height": 128}
])
def frame_sizes(request):
    """Parametrized frame sizes for testing."""
    return request.param


@pytest.fixture(params=[1, 5, 10, 20, 30, 60])
def fps_values(request):
    """Parametrized FPS values for testing."""
    return request.param


# ============================================================================
# CLEANUP AND UTILITIES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_globals():
    """Auto-cleanup for any global state changes."""
    yield
    # Add any global cleanup here if needed


def pytest_configure(config):
    """Pytest configuration hook for Qt environment setup."""
    import logging
    
    # Configure logging to reduce Qt noise
    logging.getLogger('Qt').setLevel(logging.CRITICAL)
    logging.getLogger('PySide6').setLevel(logging.CRITICAL)
    logging.getLogger('shiboken6').setLevel(logging.CRITICAL)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test file paths
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "ui" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
            if PYSIDE6_AVAILABLE:
                item.add_marker(pytest.mark.requires_display)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        # Skip UI tests if PySide6 not available
        if not PYSIDE6_AVAILABLE and "ui" in str(item.fspath):
            item.add_marker(pytest.mark.skip(reason="PySide6 not available"))


def pytest_runtest_setup(item):
    """Setup hook for individual test items."""
    # Skip tests requiring PySide6 if not available
    if item.get_closest_marker("requires_display") and not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 not available for UI tests")