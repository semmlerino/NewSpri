"""
Integrated real sprite system for authentic component testing.
Combines SpriteModel and AnimationController with real image data.
"""

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPainter, QPixmap

    from sprite_model.sprite_extraction import GridConfig

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


class RealSpriteSystem:
    """Integrated real sprite system for authentic component testing."""

    def __init__(self):
        from sprite_model import SpriteModel

        self.sprite_model = SpriteModel()
        self.animation_controller = None  # Created during initialize_system
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
        width, height = frame_size

        # Configure sprite model with real data
        self.sprite_model.set_frames(self.test_frames)
        self.sprite_model._apply_grid_config(GridConfig(width=width, height=height))
        self.sprite_model.set_current_frame(0)

        # Use real setter methods
        self.sprite_model.set_fps(10)
        self.sprite_model.set_loop_enabled(True)

        return self.sprite_model

    def initialize_system(self, frame_count=6, frame_size=(64, 64)):
        """Initialize complete real system with sprite model and animation controller."""
        from core.animation_controller import AnimationController

        # Setup sprite model with real data
        self.setup_sprite_model(frame_count, frame_size)

        # Create minimal mock viewer (heavy UI component)

        # Create real controller with real sprite model (single-step init)
        self.animation_controller = AnimationController(
            sprite_model=self.sprite_model,
        )

        self._initialized = True
        return True

    def get_real_signal_connections(self):
        """Get dictionary of real signals for testing."""
        if not self._initialized:
            return {}

        return {
            "animation_started": self.animation_controller.animationStarted,
            "animation_paused": self.animation_controller.animationPaused,
            "animation_stopped": self.animation_controller.animationStopped,
            "status_changed": self.animation_controller.statusChanged,
            "error_occurred": self.animation_controller.errorOccurred,
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
            "controller_initialized": self._initialized,
            "has_sprite_model": self.sprite_model is not None,
            "has_test_frames": len(self.test_frames) > 0,
            "controller_active": self.animation_controller._is_active
            if self._initialized
            else False,
            "valid_fps": self.animation_controller._current_fps > 0,
            "timer_exists": self.animation_controller._animation_timer is not None,
        }
        return checks

    def cleanup(self):
        """Clean up system resources."""
        if self.animation_controller is None:
            self.test_frames.clear()
            return

        if self.animation_controller._is_playing:
            self.animation_controller.stop_animation()
        self.animation_controller.shutdown()
        self.test_frames.clear()
