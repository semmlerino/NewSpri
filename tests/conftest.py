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
    from core.animation_controller import AnimationController
    from core.auto_detection_controller import AutoDetectionController
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


# Import common fixtures from fixture modules
try:
    from tests.fixtures.common_fixtures import *
except ImportError:
    pass  # Fixtures may not be available in all environments


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
# REAL QT EVENT HELPERS (Phase 1: Mock-to-Real Conversion)
# ============================================================================

@pytest.fixture
def real_event_helpers(qapp):
    """
    Utilities for creating REAL Qt events instead of mocks.
    Provides authentic Qt event simulation for accurate UI testing.
    """
    if not PYSIDE6_AVAILABLE:
        return MagicMock()
    
    from PySide6.QtGui import QMouseEvent, QKeyEvent, QWheelEvent
    from PySide6.QtCore import QPointF, QPoint, Qt
    from PySide6.QtTest import QTest
    
    class RealEventHelpers:
        """Factory for creating real Qt events for testing."""
        
        @staticmethod
        def create_mouse_press(x=10, y=10, button=Qt.LeftButton, modifiers=Qt.NoModifier):
            """Create real QMouseEvent for mouse press."""
            pos = QPointF(x, y)
            return QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                pos, pos, pos, button, button, modifiers
            )
        
        @staticmethod
        def create_mouse_move(x=15, y=15, buttons=Qt.LeftButton, modifiers=Qt.NoModifier):
            """Create real QMouseEvent for mouse move."""
            pos = QPointF(x, y)
            return QMouseEvent(
                QMouseEvent.Type.MouseMove,
                pos, pos, pos, Qt.NoButton, buttons, modifiers
            )
        
        @staticmethod
        def create_mouse_release(x=15, y=15, button=Qt.LeftButton, modifiers=Qt.NoModifier):
            """Create real QMouseEvent for mouse release."""
            pos = QPointF(x, y)
            return QMouseEvent(
                QMouseEvent.Type.MouseButtonRelease,
                pos, pos, pos, button, Qt.NoButton, modifiers
            )
        
        @staticmethod
        def create_key_press(key, modifiers=Qt.NoModifier, text=""):
            """Create real QKeyEvent for key press."""
            return QKeyEvent(QKeyEvent.Type.KeyPress, key, modifiers, text)
        
        @staticmethod
        def create_key_release(key, modifiers=Qt.NoModifier, text=""):
            """Create real QKeyEvent for key release."""
            return QKeyEvent(QKeyEvent.Type.KeyRelease, key, modifiers, text)
        
        @staticmethod
        def create_wheel_event(x=10, y=10, delta_x=0, delta_y=120, modifiers=Qt.NoModifier):
            """Create real QWheelEvent for wheel scrolling."""
            pos = QPointF(x, y)
            global_pos = QPointF(x, y)
            pixel_delta = QPoint(0, 0)
            angle_delta = QPoint(delta_x, delta_y)
            return QWheelEvent(
                pos, global_pos, pixel_delta, angle_delta,
                Qt.NoButton, modifiers, Qt.ScrollPhase.NoScrollPhase, False
            )
        
        @staticmethod
        def simulate_real_drag(widget, start_pos, end_pos, qtbot, button=Qt.LeftButton):
            """
            Simulate a REAL drag operation using QTest.
            This creates authentic Qt drag behavior vs mocked events.
            """
            qtbot.mousePress(widget, button, Qt.NoModifier, start_pos)
            qtbot.mouseMove(widget, end_pos)
            qtbot.mouseRelease(widget, button, Qt.NoModifier, end_pos)
            qapp.processEvents()  # Process real Qt events
        
        @staticmethod
        def simulate_real_click(widget, pos, qtbot, button=Qt.LeftButton, modifiers=Qt.NoModifier):
            """Simulate a real mouse click using QTest."""
            qtbot.mouseClick(widget, button, modifiers, pos)
            qapp.processEvents()
        
        @staticmethod
        def simulate_real_double_click(widget, pos, qtbot, button=Qt.LeftButton):
            """Simulate a real double-click using QTest."""
            qtbot.mouseDClick(widget, button, Qt.NoModifier, pos)
            qapp.processEvents()
        
        @staticmethod 
        def simulate_real_key_sequence(widget, qtbot, key, modifiers=Qt.NoModifier):
            """Simulate real key press and release sequence."""
            qtbot.keyPress(widget, key, modifiers)
            qtbot.keyRelease(widget, key, modifiers)
            qapp.processEvents()
        
        @staticmethod
        def calculate_manhattan_distance(start_pos, end_pos):
            """Calculate Manhattan distance between two points (useful for drag thresholds)."""
            if hasattr(start_pos, 'manhattanLength'):
                return (end_pos - start_pos).manhattanLength()
            else:
                # Fallback for QPoint/QPointF
                dx = abs(end_pos.x() - start_pos.x())
                dy = abs(end_pos.y() - start_pos.y())
                return dx + dy
        
        def create_modifier_combinations(self):
            """Get common modifier combinations for testing."""
            return {
                'none': Qt.NoModifier,
                'ctrl': Qt.ControlModifier,
                'shift': Qt.ShiftModifier,
                'alt': Qt.AltModifier,
                'ctrl_shift': Qt.ControlModifier | Qt.ShiftModifier,
                'ctrl_alt': Qt.ControlModifier | Qt.AltModifier,
                'shift_alt': Qt.ShiftModifier | Qt.AltModifier
            }
    
    return RealEventHelpers()


@pytest.fixture  
def real_signal_tester(qapp):
    """
    Enhanced signal testing with REAL Qt signal mechanisms.
    Replaces mock signal testing with authentic QSignalSpy usage.
    """
    if not PYSIDE6_AVAILABLE:
        return MagicMock()
    
    from PySide6.QtTest import QSignalSpy
    
    class RealSignalTester:
        """Utilities for testing real Qt signal connections and emissions."""
        
        def __init__(self):
            self.spies = {}
            self._cleanup_list = []
        
        def connect_spy(self, signal, name):
            """Connect QSignalSpy to real signal and store with name."""
            spy = QSignalSpy(signal)
            self.spies[name] = spy
            self._cleanup_list.append(spy)
            return spy
        
        def verify_emission(self, name, count=1, timeout=1000):
            """Verify signal was emitted specified number of times."""
            spy = self.spies.get(name)
            if not spy:
                return False
            
            # Wait for emissions if needed
            if spy.count() < count and timeout > 0:
                spy.wait(timeout)
            
            return spy.count() == count
        
        def verify_emission_range(self, name, min_count=1, max_count=None, timeout=1000):
            """Verify signal emission count is within range."""
            spy = self.spies.get(name)
            if not spy:
                return False
            
            if spy.count() < min_count and timeout > 0:
                spy.wait(timeout)
            
            actual_count = spy.count()
            if max_count is None:
                return actual_count >= min_count
            return min_count <= actual_count <= max_count
        
        def get_signal_args(self, name, emission_index=0):
            """
            Get real signal arguments from QSignalSpy.
            Handles PySide6 QSignalSpy argument access properly.
            """
            spy = self.spies.get(name)
            if not spy or spy.count() <= emission_index:
                return []
            
            # PySide6 QSignalSpy argument access varies by version
            try:
                # Method 1: Direct indexing (newer PySide6)
                emission = spy[emission_index]
                if isinstance(emission, (list, tuple)):
                    return list(emission)
                else:
                    return [emission]
            except (IndexError, TypeError):
                try:
                    # Method 2: Using at() method
                    emission = spy.at(emission_index)
                    if hasattr(emission, '__len__') and not isinstance(emission, str):
                        return list(emission)
                    else:
                        return [emission]
                except (AttributeError, IndexError, TypeError):
                    # Method 3: Fallback - return empty list
                    return []
        
        def get_all_emissions(self, name):
            """Get all emissions for a signal as list of argument lists."""
            spy = self.spies.get(name)
            if not spy:
                return []
            
            emissions = []
            for i in range(spy.count()):
                emissions.append(self.get_signal_args(name, i))
            return emissions
        
        def wait_for_signal(self, name, timeout=1000):
            """Wait for signal emission and return success."""
            spy = self.spies.get(name)
            if not spy:
                return False
            return spy.wait(timeout)
        
        def reset_spy(self, name):
            """Reset signal spy to clear previous emissions."""
            spy = self.spies.get(name)
            if spy:
                # Remove the old spy and return None to indicate it needs reconnection
                del self.spies[name]
                return None
            return None
        
        def get_spy_count(self, name):
            """Get current emission count for named spy."""
            spy = self.spies.get(name)
            return spy.count() if spy else 0
        
        def assert_signal_emitted(self, name, expected_count=1, timeout=1000):
            """Assert signal was emitted expected number of times."""
            if not self.verify_emission(name, expected_count, timeout):
                actual_count = self.get_spy_count(name)
                raise AssertionError(
                    f"Signal '{name}' emitted {actual_count} times, expected {expected_count}"
                )
        
        def assert_signal_not_emitted(self, name):
            """Assert signal was not emitted."""
            count = self.get_spy_count(name)
            if count > 0:
                raise AssertionError(f"Signal '{name}' unexpectedly emitted {count} times")
        
        def cleanup(self):
            """Cleanup all signal spies."""
            self.spies.clear()
            self._cleanup_list.clear()
    
    tester = RealSignalTester()
    yield tester
    tester.cleanup()


@pytest.fixture
def ark_sprite_fixture():
    """
    Real Ark.png test sprite for CCL and image processing tests.
    Provides path to Ark.png sprite sheet for authentic testing.
    """
    ark_paths = [
        PROJECT_ROOT / "spritetests" / "Ark.png",
        PROJECT_ROOT / "tests" / "fixtures" / "Ark.png", 
        PROJECT_ROOT / "assets" / "Ark.png"
    ]
    
    for path in ark_paths:
        if path.exists():
            return {
                'path': str(path),
                'filename': 'Ark.png',
                'exists': True,
                'absolute_path': str(path.absolute())
            }
    
    return {
        'path': None,
        'filename': 'Ark.png', 
        'exists': False,
        'absolute_path': None
    }


@pytest.fixture
def real_image_factory(qapp):
    """
    Factory for creating REAL test images instead of mocks.
    Generates authentic QPixmap objects with various patterns for testing.
    """
    if not PYSIDE6_AVAILABLE:
        return MagicMock()
    
    from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
    from PySide6.QtCore import Qt
    
    class RealImageFactory:
        """Factory for creating real test images and sprite sheets."""
        
        @staticmethod
        def create_solid_color_frame(width=64, height=64, color=Qt.red):
            """Create a solid color frame."""
            pixmap = QPixmap(width, height)
            pixmap.fill(color)
            return pixmap
        
        @staticmethod
        def create_numbered_frame(width=64, height=64, number=0, bg_color=Qt.red, text_color=Qt.white):
            """Create a frame with a number overlay for identification."""
            pixmap = QPixmap(width, height)
            pixmap.fill(bg_color)
            
            painter = QPainter(pixmap)
            painter.setPen(text_color)
            font = QFont()
            font.setPointSize(max(8, min(width, height) // 8))
            painter.setFont(font)
            
            # Center the text
            text = str(number)
            text_rect = painter.fontMetrics().boundingRect(text)
            x = (width - text_rect.width()) // 2
            y = (height + text_rect.height()) // 2
            
            painter.drawText(x, y, text)
            painter.end()
            
            return pixmap
        
        @staticmethod
        def create_sprite_sheet(frame_count=8, frame_size=(32, 32), layout="horizontal", 
                              colors=None, spacing=0, margin=0):
            """Create a real sprite sheet with multiple frames."""
            frame_width, frame_height = frame_size
            
            if colors is None:
                colors = [Qt.red, Qt.green, Qt.blue, Qt.yellow, Qt.cyan, Qt.magenta, 
                         Qt.darkRed, Qt.darkGreen, Qt.darkBlue, Qt.darkYellow]
            
            if layout == "horizontal":
                sheet_width = frame_count * frame_width + (frame_count - 1) * spacing + 2 * margin
                sheet_height = frame_height + 2 * margin
            elif layout == "vertical":
                sheet_width = frame_width + 2 * margin
                sheet_height = frame_count * frame_height + (frame_count - 1) * spacing + 2 * margin
            else:  # grid layout
                cols = int(frame_count ** 0.5)
                if cols * cols < frame_count:
                    cols += 1
                rows = (frame_count + cols - 1) // cols
                sheet_width = cols * frame_width + (cols - 1) * spacing + 2 * margin
                sheet_height = rows * frame_height + (rows - 1) * spacing + 2 * margin
            
            sprite_sheet = QPixmap(sheet_width, sheet_height)
            sprite_sheet.fill(Qt.white)
            
            painter = QPainter(sprite_sheet)
            
            for i in range(frame_count):
                if layout == "horizontal":
                    x = margin + i * (frame_width + spacing)
                    y = margin
                elif layout == "vertical":
                    x = margin
                    y = margin + i * (frame_height + spacing)
                else:  # grid
                    col = i % cols
                    row = i // cols
                    x = margin + col * (frame_width + spacing)
                    y = margin + row * (frame_height + spacing)
                
                # Draw colored frame background
                color = colors[i % len(colors)]
                painter.fillRect(x, y, frame_width, frame_height, color)
                
                # Add frame number
                painter.setPen(Qt.white)
                font = QFont()
                font.setPointSize(max(8, min(frame_width, frame_height) // 8))
                painter.setFont(font)
                
                text = str(i)
                text_rect = painter.fontMetrics().boundingRect(text)
                text_x = x + (frame_width - text_rect.width()) // 2
                text_y = y + (frame_height + text_rect.height()) // 2
                
                painter.drawText(text_x, text_y, text)
            
            painter.end()
            return sprite_sheet
        
        @staticmethod
        def create_ccl_test_sprite():
            """Create a sprite sheet specifically for CCL testing."""
            # Create a sheet with isolated sprites for CCL to detect
            sheet = QPixmap(200, 100)
            sheet.fill(Qt.transparent)
            
            painter = QPainter(sheet)
            
            # Create separate colored rectangles for CCL to find
            sprite_rects = [
                (10, 10, 30, 30, Qt.red),
                (50, 10, 25, 35, Qt.green), 
                (85, 15, 20, 25, Qt.blue),
                (115, 5, 35, 40, Qt.yellow),
                (160, 20, 30, 25, Qt.cyan)
            ]
            
            for x, y, w, h, color in sprite_rects:
                painter.fillRect(x, y, w, h, color)
                # Add small border to make sprites distinct
                painter.setPen(Qt.black)
                painter.drawRect(x, y, w, h)
            
            painter.end()
            return sheet
        
        @staticmethod
        def save_to_temp_file(pixmap, temp_dir, filename="test_sprite.png"):
            """Save real image to temporary file and return path."""
            file_path = temp_dir / filename
            success = pixmap.save(str(file_path))
            return str(file_path) if success else None
        
        @staticmethod
        def create_animation_frames(count=6, size=(48, 48), animation_type="rotate"):
            """Create frames for animation testing."""
            frames = []
            width, height = size
            
            for i in range(count):
                pixmap = QPixmap(width, height)
                pixmap.fill(Qt.transparent)
                
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                
                if animation_type == "rotate":
                    # Rotating square animation
                    angle = (360 / count) * i
                    painter.translate(width // 2, height // 2)
                    painter.rotate(angle)
                    painter.fillRect(-10, -10, 20, 20, Qt.red)
                elif animation_type == "scale":
                    # Scaling circle animation  
                    scale = 0.5 + 0.5 * (i / count)
                    radius = int(min(width, height) * 0.3 * scale)
                    center_x, center_y = width // 2, height // 2
                    painter.setBrush(Qt.blue)
                    painter.drawEllipse(center_x - radius, center_y - radius, 
                                      radius * 2, radius * 2)
                elif animation_type == "move":
                    # Moving dot animation
                    x = int((width - 20) * (i / (count - 1)))
                    y = height // 2 - 10
                    painter.fillRect(x, y, 20, 20, Qt.green)
                
                painter.end()
                frames.append(pixmap)
            
            return frames
    
    return RealImageFactory()


@pytest.fixture
def real_sprite_system(qapp):
    """
    Real component integration fixture for Phase 2/3 conversions.
    Creates authentic SpriteModel + AnimationController integration instead of mocks.
    """
    if not PYSIDE6_AVAILABLE:
        return MagicMock()
    
    from sprite_model import SpriteModel
    from core.animation_controller import AnimationController
    from PySide6.QtGui import QPixmap, QPainter
    from PySide6.QtCore import Qt
    
    class RealSpriteSystem:
        """Integrated real sprite system for authentic component testing."""
        
        def __init__(self):
            self.sprite_model = SpriteModel()
            self.animation_controller = AnimationController()
            self.test_frames = []
            self._initialized = False
        
        def setup_test_frames(self, frame_count=6, frame_size=(64, 64)):
            """Create real test frames with actual image data."""
            self.test_frames = []
            width, height = frame_size
            colors = [Qt.red, Qt.green, Qt.blue, Qt.yellow, Qt.cyan, Qt.magenta]
            
            for i in range(frame_count):
                pixmap = QPixmap(width, height)
                color = colors[i % len(colors)]
                pixmap.fill(color)
                
                # Add frame number for identification
                painter = QPainter(pixmap)
                painter.setPen(Qt.white)
                painter.drawText(10, height // 2, str(i))
                painter.end()
                
                self.test_frames.append(pixmap)
            
            return self.test_frames
        
        def setup_sprite_model(self, frame_count=6, frame_size=(64, 64)):
            """Setup sprite model with real frame data."""
            self.setup_test_frames(frame_count, frame_size)
            
            # Configure sprite model with real data
            self.sprite_model._sprite_frames = self.test_frames
            self.sprite_model._frame_width, self.sprite_model._frame_height = frame_size
            self.sprite_model._current_frame = 0
            self.sprite_model._offset_x = 0
            self.sprite_model._offset_y = 0
            self.sprite_model._spacing_x = 0
            self.sprite_model._spacing_y = 0
            
            # Use real setter methods
            self.sprite_model.set_fps(10)
            self.sprite_model.set_loop_enabled(True)
            
            # Mock only the methods that need simulation for testing
            self.sprite_model.next_frame = Mock(return_value=(1, True))
            self.sprite_model.first_frame = Mock()
            
            return self.sprite_model
        
        def initialize_system(self, frame_count=6, frame_size=(64, 64)):
            """Initialize complete real system with sprite model and animation controller."""
            # Setup sprite model with real data
            self.setup_sprite_model(frame_count, frame_size)
            
            # Create minimal mock viewer (heavy UI component)
            mock_viewer = Mock()
            
            # Initialize real controller with real sprite model
            success = self.animation_controller.initialize(
                self.sprite_model, 
                mock_viewer
            )
            
            self._initialized = success
            return success
        
        def get_real_signal_connections(self):
            """Get dictionary of real signals for testing."""
            if not self._initialized:
                return {}
                
            return {
                'fps_changed': self.animation_controller.fpsChanged,
                'playback_state_changed': self.animation_controller.playbackStateChanged,
                'loop_mode_changed': self.animation_controller.loopModeChanged,
                'animation_started': self.animation_controller.animationStarted,
                'animation_paused': self.animation_controller.animationPaused,
                'animation_stopped': self.animation_controller.animationStopped,
                'frame_advanced': self.animation_controller.frameAdvanced,
                'status_changed': self.animation_controller.statusChanged,
                'error_occurred': self.animation_controller.errorOccurred
            }
        
        def create_real_sprite_with_frames(self, frame_count=8):
            """Create real sprite frames for advanced testing."""
            frames = []
            for i in range(frame_count):
                pixmap = QPixmap(48, 48)
                
                # Create different visual patterns for each frame
                painter = QPainter(pixmap)
                
                if i % 3 == 0:
                    painter.fillRect(0, 0, 48, 48, Qt.red)
                elif i % 3 == 1:
                    painter.fillRect(0, 0, 48, 48, Qt.green)
                else:
                    painter.fillRect(0, 0, 48, 48, Qt.blue)
                
                # Add frame number
                painter.setPen(Qt.white)
                painter.drawText(20, 25, str(i))
                painter.end()
                
                frames.append(pixmap)
            
            return frames
        
        def verify_system_state(self):
            """Verify the system is in a valid state for testing."""
            checks = {
                'controller_initialized': self._initialized,
                'has_sprite_model': self.sprite_model is not None,
                'has_test_frames': len(self.test_frames) > 0,
                'controller_active': self.animation_controller._is_active if self._initialized else False,
                'valid_fps': self.animation_controller._current_fps > 0,
                'timer_exists': self.animation_controller._animation_timer is not None
            }
            return checks
        
        def cleanup(self):
            """Clean up system resources."""
            if self.animation_controller._is_playing:
                self.animation_controller.stop_animation()
            self.animation_controller.shutdown()
            self.test_frames.clear()
    
    system = RealSpriteSystem()
    yield system
    system.cleanup()


@pytest.fixture  
def enhanced_animation_controller(real_sprite_system):
    """
    Enhanced animation controller with real sprite model integration.
    Replaces basic animation_controller fixture for integration testing.
    """
    real_sprite_system.initialize_system(frame_count=4, frame_size=(32, 32))
    return real_sprite_system.animation_controller


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


# ============================================================================
# ENHANCED FIXTURES FOR FOUNDATION TESTS (Added for Option A)
# ============================================================================

@pytest.fixture
def export_temp_dir(temp_dir) -> Path:
    """Temporary directory specifically for export testing."""
    export_dir = temp_dir / "exports"
    export_dir.mkdir()
    return export_dir


@pytest.fixture  
def keyboard_test_helper(qapp):
    """Helper for simulating keyboard events in tests."""
    if not PYSIDE6_AVAILABLE:
        return MagicMock()
    
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtCore import Qt
    
    class KeyboardTestHelper:
        def __init__(self, app):
            self.app = app
        
        def create_key_event(self, key, modifiers=Qt.NoModifier):
            """Create a QKeyEvent for testing."""
            return QKeyEvent(QKeyEvent.KeyPress, key, modifiers)
        
        def simulate_key_press(self, widget, key, modifiers=Qt.NoModifier):
            """Simulate a key press on a widget."""
            event = self.create_key_event(key, modifiers)
            widget.keyPressEvent(event)
            self.app.processEvents()
        
        def simulate_shortcut(self, widget, key_sequence):
            """Simulate a keyboard shortcut (e.g., 'Ctrl+O')."""
            # Parse common shortcut formats
            if key_sequence == "Ctrl+O":
                self.simulate_key_press(widget, Qt.Key_O, Qt.ControlModifier)
            elif key_sequence == "Ctrl+Q":
                self.simulate_key_press(widget, Qt.Key_Q, Qt.ControlModifier)
            elif key_sequence == "Ctrl++":
                self.simulate_key_press(widget, Qt.Key_Plus, Qt.ControlModifier)
            elif key_sequence == "Ctrl+-":
                self.simulate_key_press(widget, Qt.Key_Minus, Qt.ControlModifier)
            elif key_sequence == "Ctrl+0":
                self.simulate_key_press(widget, Qt.Key_0, Qt.ControlModifier)
            elif key_sequence == "Ctrl+1":
                self.simulate_key_press(widget, Qt.Key_1, Qt.ControlModifier)
            else:
                # For simple keys without modifiers
                key_map = {
                    "Space": Qt.Key_Space,
                    "G": Qt.Key_G,
                    "Left": Qt.Key_Left,
                    "Right": Qt.Key_Right,
                    "Home": Qt.Key_Home,
                    "End": Qt.Key_End
                }
                if key_sequence in key_map:
                    self.simulate_key_press(widget, key_map[key_sequence])
    
    return KeyboardTestHelper(qapp)


@pytest.fixture
def menu_test_helper(qapp):
    """Helper for testing menu actions and structure."""
    if not PYSIDE6_AVAILABLE:
        return MagicMock()
    
    class MenuTestHelper:
        def __init__(self, app):
            self.app = app
        
        def find_menu(self, menubar, menu_name):
            """Find a menu by name in a menubar."""
            for action in menubar.actions():
                if action.text() == menu_name:
                    return action.menu()
            return None
        
        def find_action(self, menu, action_text):
            """Find an action by text in a menu."""
            for action in menu.actions():
                if action_text in action.text():
                    return action
            return None
        
        def trigger_action(self, action):
            """Trigger a menu action and process events."""
            action.trigger()
            self.app.processEvents()
        
        def get_menu_structure(self, menubar):
            """Get the complete menu structure for testing."""
            structure = {}
            for menu_action in menubar.actions():
                menu = menu_action.menu()
                if menu:
                    actions = []
                    for action in menu.actions():
                        if not action.isSeparator():
                            actions.append({
                                'text': action.text(),
                                'shortcut': action.shortcut().toString() if hasattr(action, 'shortcut') else '',
                                'checkable': action.isCheckable(),
                                'has_submenu': action.menu() is not None
                            })
                    structure[menu_action.text()] = actions
            return structure
    
    return MenuTestHelper(qapp)


@pytest.fixture
def settings_test_helper(temp_dir):
    """Helper for testing settings persistence."""
    if not PYSIDE6_AVAILABLE:
        return MagicMock()
    
    from PySide6.QtCore import QSettings
    
    class SettingsTestHelper:
        def __init__(self, temp_dir):
            self.temp_dir = temp_dir
            self.settings_file = temp_dir / "test_settings.ini"
        
        def create_test_settings(self):
            """Create a QSettings instance for testing."""
            # Use INI format for easier testing
            return QSettings(str(self.settings_file), QSettings.IniFormat)
        
        def clear_settings(self):
            """Clear all test settings."""
            if self.settings_file.exists():
                self.settings_file.unlink()
        
        def get_all_settings(self):
            """Get all settings as a dictionary."""
            settings = self.create_test_settings()
            result = {}
            for key in settings.allKeys():
                result[key] = settings.value(key)
            return result
    
    return SettingsTestHelper(temp_dir)


@pytest.fixture
def signal_test_helper():
    """Helper for testing Qt signals and slots."""
    if not PYSIDE6_AVAILABLE:
        return MagicMock()
    
    from PySide6.QtTest import QSignalSpy
    from PySide6.QtCore import QObject, Signal
    
    class SignalTestHelper:
        def __init__(self):
            self.spies = []
        
        def create_spy(self, signal):
            """Create a QSignalSpy for testing signal emissions."""
            spy = QSignalSpy(signal)
            self.spies.append(spy)
            return spy
        
        def wait_for_signal(self, spy, timeout=1000):
            """Wait for a signal to be emitted."""
            return spy.wait(timeout)
        
        def assert_signal_emitted(self, spy, expected_count=1):
            """Assert that a signal was emitted the expected number of times."""
            assert len(spy) == expected_count, f"Expected {expected_count} emissions, got {len(spy)}"
        
        def assert_signal_not_emitted(self, spy):
            """Assert that a signal was not emitted."""
            assert len(spy) == 0, f"Expected no emissions, got {len(spy)}"
        
        def cleanup(self):
            """Cleanup signal spies."""
            self.spies.clear()
    
    helper = SignalTestHelper()
    yield helper
    helper.cleanup()


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing without affecting real filesystem."""
    class MockFileOperations:
        def __init__(self):
            self.mock_files = {}
            self.operations_log = []
        
        def add_mock_file(self, path, content=None):
            """Add a mock file that can be 'opened' during tests."""
            self.mock_files[str(path)] = content
        
        def log_operation(self, operation, path, **kwargs):
            """Log file operations for verification."""
            self.operations_log.append({
                'operation': operation,
                'path': str(path),
                **kwargs
            })
        
        def get_operations(self, operation_type=None):
            """Get logged operations, optionally filtered by type."""
            if operation_type:
                return [op for op in self.operations_log if op['operation'] == operation_type]
            return self.operations_log.copy()
        
        def clear_log(self):
            """Clear the operations log."""
            self.operations_log.clear()
    
    return MockFileOperations()