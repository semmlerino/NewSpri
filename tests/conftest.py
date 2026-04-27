"""
Global pytest configuration and fixtures for Python Sprite Viewer tests.
Provides reusable fixtures, test utilities, and setup/teardown for all test modules.
Configured for proper PySide6 integration with error suppression.
"""

# ruff: noqa: I001

import os
import sys
import tempfile
import warnings
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

pytest_plugins = (
    "tests.fixtures.common_fixtures",
    "tests.fixtures.qt_mocks",
)

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

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication


# Add project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from core.animation_controller import AnimationController
from core.auto_detection_controller import AutoDetectionController
from sprite_model import SpriteModel


# ============================================================================
# APPLICATION FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """
    Session-scoped QApplication fixture for Qt-based tests.
    Ensures single QApplication instance across all tests with proper Qt configuration.
    """
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
        "debug_final": sprite_dir / "debug_final.png",
    }


# ============================================================================
# SPRITE AND IMAGE FIXTURES
# ============================================================================


@pytest.fixture
def mock_pixmap() -> QPixmap:
    """Mock QPixmap for testing."""
    pixmap = QPixmap(256, 256)
    pixmap.fill(Qt.red)
    return pixmap


@pytest.fixture
def test_sprite_sheet(sample_sprite_paths) -> QPixmap | None:
    """Load a real test sprite sheet if available."""
    test_path = sample_sprite_paths["test_sheet"]
    if test_path.exists():
        return QPixmap(str(test_path))
    return None


@pytest.fixture
def mock_sprite_frames(qapp) -> list[QPixmap]:
    """Generate mock sprite frames for testing."""
    frames = []
    colors = [Qt.red, Qt.green, Qt.blue, Qt.yellow]
    for _i, color in enumerate(colors):
        pixmap = QPixmap(64, 64)
        pixmap.fill(color)
        frames.append(pixmap)

    return frames


# ============================================================================
# MODEL AND CONTROLLER FIXTURES
# ============================================================================


@pytest.fixture
def sprite_model(qapp) -> SpriteModel:
    """Fresh SpriteModel instance for testing."""
    return SpriteModel()


@pytest.fixture
def animation_controller(sprite_model) -> AnimationController:
    """Fresh AnimationController instance for testing."""
    return AnimationController(sprite_model=sprite_model)


@pytest.fixture
def auto_detection_controller(sprite_model) -> AutoDetectionController:
    """Fresh AutoDetectionController instance for testing."""
    return AutoDetectionController(sprite_model=sprite_model)


@pytest.fixture
def configured_sprite_model(sprite_model, mock_sprite_frames) -> SpriteModel:
    """SpriteModel pre-configured with test data."""
    # Modify frames in-place to preserve AnimationStateManager reference
    sprite_model._sprite_frames.clear()
    sprite_model._sprite_frames.extend(mock_sprite_frames)
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
        if not signal_name.startswith("_"):
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
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
    from PySide6.QtTest import QTest

    class RealEventHelpers:
        """Factory for creating real Qt events for testing."""

        @staticmethod
        def create_mouse_press(x=10, y=10, button=Qt.LeftButton, modifiers=Qt.NoModifier):
            """Create real QMouseEvent for mouse press."""
            pos = QPointF(x, y)
            return QMouseEvent(
                QMouseEvent.Type.MouseButtonPress, pos, pos, pos, button, button, modifiers
            )

        @staticmethod
        def create_mouse_move(x=15, y=15, buttons=Qt.LeftButton, modifiers=Qt.NoModifier):
            """Create real QMouseEvent for mouse move."""
            pos = QPointF(x, y)
            return QMouseEvent(
                QMouseEvent.Type.MouseMove, pos, pos, pos, Qt.NoButton, buttons, modifiers
            )

        @staticmethod
        def create_mouse_release(x=15, y=15, button=Qt.LeftButton, modifiers=Qt.NoModifier):
            """Create real QMouseEvent for mouse release."""
            pos = QPointF(x, y)
            return QMouseEvent(
                QMouseEvent.Type.MouseButtonRelease, pos, pos, pos, button, Qt.NoButton, modifiers
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
                pos,
                global_pos,
                pixel_delta,
                angle_delta,
                Qt.NoButton,
                modifiers,
                Qt.ScrollPhase.NoScrollPhase,
                False,
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
            if hasattr(start_pos, "manhattanLength"):
                return (end_pos - start_pos).manhattanLength()
            else:
                # Fallback for QPoint/QPointF
                dx = abs(end_pos.x() - start_pos.x())
                dy = abs(end_pos.y() - start_pos.y())
                return dx + dy

        def create_modifier_combinations(self):
            """Get common modifier combinations for testing."""
            return {
                "none": Qt.NoModifier,
                "ctrl": Qt.ControlModifier,
                "shift": Qt.ShiftModifier,
                "alt": Qt.AltModifier,
                "ctrl_shift": Qt.ControlModifier | Qt.ShiftModifier,
                "ctrl_alt": Qt.ControlModifier | Qt.AltModifier,
                "shift_alt": Qt.ShiftModifier | Qt.AltModifier,
            }

    return RealEventHelpers()


@pytest.fixture
def real_signal_tester(qapp):
    """
    Enhanced signal testing with REAL Qt signal mechanisms.
    Replaces mock signal testing with authentic QSignalSpy usage.
    """
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
                    if hasattr(emission, "__len__") and not isinstance(emission, str):
                        return list(emission)
                    else:
                        return [emission]
                except (AttributeError, IndexError, TypeError) as e:
                    # All methods failed - this indicates a real problem
                    import warnings

                    warnings.warn(
                        f"QSignalSpy argument access failed for '{name}' at index {emission_index}: {e}. "
                        f"This may indicate a PySide6 version incompatibility.",
                        stacklevel=2,
                    )
                    return []

        def get_all_emissions(self, name):
            """Get all emissions for a signal as list of argument lists."""
            spy = self.spies.get(name)
            if not spy:
                return []

            return [self.get_signal_args(name, i) for i in range(spy.count())]

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
        PROJECT_ROOT / "assets" / "Ark.png",
    ]

    for path in ark_paths:
        if path.exists():
            return {
                "path": str(path),
                "filename": "Ark.png",
                "exists": True,
                "absolute_path": str(path.absolute()),
            }

    return {"path": None, "filename": "Ark.png", "exists": False, "absolute_path": None}


@pytest.fixture
def real_image_factory(qapp):
    """
    Factory for creating REAL test images instead of mocks.
    Generates authentic QPixmap objects with various patterns for testing.
    """
    from tests.fixtures.real_image_factory import RealImageFactory

    return RealImageFactory()


@pytest.fixture
def real_sprite_system(qapp):
    """
    Real component integration fixture for Phase 2/3 conversions.
    Creates authentic SpriteModel + AnimationController integration instead of mocks.
    """
    from tests.fixtures.real_sprite_system import RealSpriteSystem

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
            "spacing": (0, 0),
        },
        {
            "name": "rect_32x48",
            "frame_size": (32, 48),
            "expected_frames": 12,
            "margin": (4, 4),
            "spacing": (2, 2),
        },
        {
            "name": "large_64x64",
            "frame_size": (64, 64),
            "expected_frames": 9,
            "margin": (8, 8),
            "spacing": (4, 4),
        },
    ]


@pytest.fixture
def animation_test_cases() -> list[dict]:
    """Test cases for animation functionality."""
    return [
        {
            "name": "default_fps",
            "fps": 10,
            "frame_count": 4,
            "expected_interval": 100,  # milliseconds
        },
        {
            "name": "fast_animation",
            "fps": 30,
            "frame_count": 8,
            "expected_interval": 33,  # milliseconds (rounded)
        },
        {
            "name": "slow_animation",
            "fps": 2,
            "frame_count": 6,
            "expected_interval": 500,  # milliseconds
        },
    ]


# ============================================================================
# PARAMETRIZED TEST DATA
# ============================================================================


@pytest.fixture(
    params=[
        {"width": 32, "height": 32},
        {"width": 48, "height": 32},
        {"width": 64, "height": 48},
        {"width": 128, "height": 128},
    ]
)
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


def pytest_configure(config):
    """Pytest configuration hook for Qt environment setup."""
    import logging

    # Configure logging to reduce Qt noise
    logging.getLogger("Qt").setLevel(logging.CRITICAL)
    logging.getLogger("PySide6").setLevel(logging.CRITICAL)
    logging.getLogger("shiboken6").setLevel(logging.CRITICAL)


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
            item.add_marker(pytest.mark.requires_display)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


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
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent

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
                    "End": Qt.Key_End,
                }
                if key_sequence in key_map:
                    self.simulate_key_press(widget, key_map[key_sequence])

    return KeyboardTestHelper(qapp)


@pytest.fixture
def menu_test_helper(qapp):
    """Helper for testing menu actions and structure."""

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
                    structure[menu_action.text()] = [
                        {
                            "text": action.text(),
                            "shortcut": action.shortcut().toString()
                            if hasattr(action, "shortcut")
                            else "",
                            "checkable": action.isCheckable(),
                            "has_submenu": action.menu() is not None,
                        }
                        for action in menu.actions()
                        if not action.isSeparator()
                    ]
            return structure

    return MenuTestHelper(qapp)


@pytest.fixture
def settings_test_helper(temp_dir):
    """Helper for testing settings persistence."""
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
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtTest import QSignalSpy

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
            assert spy.count() == expected_count, (
                f"Expected {expected_count} emissions, got {spy.count()}"
            )

        def assert_signal_not_emitted(self, spy):
            """Assert that a signal was not emitted."""
            assert spy.count() == 0, f"Expected no emissions, got {spy.count()}"

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
            self.operations_log.append({"operation": operation, "path": str(path), **kwargs})

        def get_operations(self, operation_type=None):
            """Get logged operations, optionally filtered by type."""
            if operation_type:
                return [op for op in self.operations_log if op["operation"] == operation_type]
            return self.operations_log.copy()

        def clear_log(self):
            """Clear the operations log."""
            self.operations_log.clear()

    return MockFileOperations()
