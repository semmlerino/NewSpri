"""
Tests for AnimationController timer state machine behavior.

Covers:
- Timer timeout behavior and frame advancement
- Animation completion handling
- Exception handling during timeout
- Signal emission ordering
- FPS changes during playback
- State consistency
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from core.animation_controller import AnimationController

if TYPE_CHECKING:
    from sprite_model import SpriteModel


# Mark all tests in this module as requiring Qt
pytestmark = pytest.mark.requires_qt


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_sprite_model() -> MagicMock:
    """Create a mock SpriteModel with basic functionality."""
    model = MagicMock(spec=['sprite_frames', 'next_frame', 'first_frame',
                           'current_frame_index', 'fps', 'loop_enabled',
                           'set_fps', 'set_loop_enabled',
                           'frameChanged', 'dataLoaded',
                           'extractionCompleted', 'errorOccurred'])
    model.sprite_frames = [MagicMock() for _ in range(8)]  # 8 mock frames
    model.current_frame_index = 0
    model.next_frame = MagicMock(return_value=(1, True))  # Next frame, should continue
    model.first_frame = MagicMock(return_value=0)
    model.fps = 12  # Default FPS
    model.loop_enabled = True  # Default loop mode
    model.set_fps = MagicMock()
    model.set_loop_enabled = MagicMock()

    # Mock signals - need connect method
    model.frameChanged = MagicMock()
    model.frameChanged.connect = MagicMock()
    model.dataLoaded = MagicMock()
    model.dataLoaded.connect = MagicMock()
    model.extractionCompleted = MagicMock()
    model.extractionCompleted.connect = MagicMock()
    model.errorOccurred = MagicMock()
    model.errorOccurred.connect = MagicMock()

    return model


@pytest.fixture
def mock_sprite_viewer() -> MagicMock:
    """Create a mock SpriteViewer with basic functionality."""
    viewer = MagicMock()
    # Mock the closing signal
    viewer.closing = MagicMock()
    viewer.closing.connect = MagicMock()
    return viewer


@pytest.fixture
def animation_controller(qapp, mock_sprite_model: MagicMock, mock_sprite_viewer: MagicMock) -> AnimationController:
    """Create an AnimationController with mock model and viewer."""
    return AnimationController(
        sprite_model=mock_sprite_model,
        sprite_viewer=mock_sprite_viewer,
    )


# ============================================================================
# Timer Timeout Tests
# ============================================================================


class TestTimerTimeout:
    """Tests for _on_timer_timeout behavior."""

    def test_timer_timeout_advances_frame(
        self, animation_controller: AnimationController, mock_sprite_model: MagicMock
    ) -> None:
        """Timer timeout should advance to next frame."""
        # Start animation
        animation_controller.start_animation()

        # Capture signal emission
        frame_advanced_spy = []
        animation_controller.frameAdvanced.connect(lambda idx: frame_advanced_spy.append(idx))

        # Simulate timer timeout
        animation_controller._on_timer_timeout()

        # Verify next_frame was called
        mock_sprite_model.next_frame.assert_called_once()

        # Verify frameAdvanced signal was emitted
        assert len(frame_advanced_spy) == 1
        assert frame_advanced_spy[0] == 1  # next_frame returns (1, True)

    def test_timer_timeout_animation_completion(
        self, animation_controller: AnimationController, mock_sprite_model: MagicMock
    ) -> None:
        """Timer timeout with should_continue=False should complete animation."""
        # Configure mock to signal completion
        mock_sprite_model.next_frame.return_value = (7, False)  # Last frame, don't continue

        # Start animation
        animation_controller.start_animation()

        # Capture signals
        completed_spy = []
        paused_spy = []
        animation_controller.animationCompleted.connect(lambda: completed_spy.append(True))
        animation_controller.animationPaused.connect(lambda: paused_spy.append(True))

        # Simulate timer timeout
        animation_controller._on_timer_timeout()

        # Verify animation was paused and completed
        assert len(completed_spy) == 1
        assert len(paused_spy) == 1
        assert not animation_controller.is_playing

    def test_timer_timeout_exception_handling(
        self, animation_controller: AnimationController, mock_sprite_model: MagicMock
    ) -> None:
        """Timer timeout should catch exceptions and emit error signal."""
        # Configure mock to raise exception
        mock_sprite_model.next_frame.side_effect = ValueError("Invalid frame state")

        # Start animation
        animation_controller.start_animation()

        # Capture error signal
        error_spy = []
        animation_controller.errorOccurred.connect(lambda msg: error_spy.append(msg))

        # Simulate timer timeout
        animation_controller._on_timer_timeout()

        # Verify error was emitted and animation stopped
        assert len(error_spy) == 1
        assert "Invalid frame state" in error_spy[0]
        assert not animation_controller.is_playing

    def test_timer_timeout_no_action_when_not_playing(
        self, animation_controller: AnimationController, mock_sprite_model: MagicMock
    ) -> None:
        """Timer timeout should do nothing if not playing."""
        # Don't start animation

        # Simulate timer timeout
        animation_controller._on_timer_timeout()

        # Verify next_frame was NOT called
        mock_sprite_model.next_frame.assert_not_called()


# ============================================================================
# Signal Ordering Tests
# ============================================================================


class TestSignalOrdering:
    """Tests for correct signal emission ordering."""

    def test_start_animation_signal_order(
        self, animation_controller: AnimationController
    ) -> None:
        """Start animation should emit signals in correct order."""
        signal_order = []

        animation_controller.animationStarted.connect(
            lambda: signal_order.append("animationStarted")
        )
        animation_controller.playbackStateChanged.connect(
            lambda state: signal_order.append(f"playbackStateChanged({state})")
        )
        animation_controller.statusChanged.connect(
            lambda msg: signal_order.append("statusChanged")
        )

        animation_controller.start_animation()

        # Verify signal order
        assert signal_order == [
            "animationStarted",
            "playbackStateChanged(True)",
            "statusChanged"
        ]

    def test_pause_animation_signal_order(
        self, animation_controller: AnimationController
    ) -> None:
        """Pause animation should emit signals in correct order."""
        # Start first
        animation_controller.start_animation()

        signal_order = []

        animation_controller.animationPaused.connect(
            lambda: signal_order.append("animationPaused")
        )
        animation_controller.playbackStateChanged.connect(
            lambda state: signal_order.append(f"playbackStateChanged({state})")
        )
        animation_controller.statusChanged.connect(
            lambda msg: signal_order.append("statusChanged")
        )

        animation_controller.pause_animation()

        # Verify signal order
        assert signal_order == [
            "animationPaused",
            "playbackStateChanged(False)",
            "statusChanged"
        ]


# ============================================================================
# FPS Change Tests
# ============================================================================


class TestFPSChanges:
    """Tests for FPS changes during playback."""

    def test_fps_change_during_playback(
        self, animation_controller: AnimationController
    ) -> None:
        """FPS change during playback should update timer interval immediately."""
        # Start at default FPS
        animation_controller.start_animation()
        initial_interval = animation_controller._animation_timer.interval()

        # Change FPS
        animation_controller.set_fps(30)
        new_interval = animation_controller._animation_timer.interval()

        # Verify interval changed
        assert new_interval != initial_interval
        # 30 FPS = ~33ms interval
        assert new_interval == pytest.approx(1000 / 30, abs=2)

    def test_fps_change_when_not_playing(
        self, animation_controller: AnimationController
    ) -> None:
        """FPS change when not playing should update stored FPS."""
        animation_controller.set_fps(24)

        # Verify FPS is stored
        assert animation_controller.current_fps == 24

        # Start and verify interval uses new FPS
        animation_controller.start_animation()
        interval = animation_controller._animation_timer.interval()
        # 24 FPS = ~42ms interval
        assert interval == pytest.approx(1000 / 24, abs=2)

    def test_rapid_fps_changes(
        self, animation_controller: AnimationController
    ) -> None:
        """Multiple rapid FPS changes should result in correct final value."""
        animation_controller.start_animation()

        # Rapid FPS changes
        animation_controller.set_fps(10)
        animation_controller.set_fps(20)
        animation_controller.set_fps(30)
        animation_controller.set_fps(60)

        # Verify final FPS
        assert animation_controller.current_fps == 60
        # 60 FPS = ~17ms interval
        assert animation_controller._animation_timer.interval() == pytest.approx(1000 / 60, abs=2)


# ============================================================================
# State Consistency Tests
# ============================================================================


class TestStateConsistency:
    """Tests for state consistency."""

    def test_is_playing_state_after_start(
        self, animation_controller: AnimationController
    ) -> None:
        """After start: is_playing should be True and timer active."""
        animation_controller.start_animation()

        assert animation_controller.is_playing is True
        assert animation_controller._animation_timer.isActive() is True

    def test_is_playing_state_after_pause(
        self, animation_controller: AnimationController
    ) -> None:
        """After pause: is_playing should be False and timer inactive."""
        animation_controller.start_animation()
        animation_controller.pause_animation()

        assert animation_controller.is_playing is False
        assert animation_controller._animation_timer.isActive() is False

    def test_is_playing_state_after_error(
        self, animation_controller: AnimationController, mock_sprite_model: MagicMock
    ) -> None:
        """After error: is_playing should be False and timer inactive."""
        # Configure mock to raise exception
        mock_sprite_model.next_frame.side_effect = RuntimeError("Test error")

        animation_controller.start_animation()

        # Trigger error via timer timeout
        animation_controller._on_timer_timeout()

        assert animation_controller.is_playing is False
        assert animation_controller._animation_timer.isActive() is False

    def test_pause_when_not_playing_is_safe(
        self, animation_controller: AnimationController
    ) -> None:
        """Pausing when not playing should be a no-op."""
        # Capture signals
        paused_spy = []
        animation_controller.animationPaused.connect(lambda: paused_spy.append(True))

        # Pause without starting
        animation_controller.pause_animation()

        # No signal should be emitted
        assert len(paused_spy) == 0
        assert animation_controller.is_playing is False

    def test_stop_animation_resets_to_first_frame(
        self, animation_controller: AnimationController, mock_sprite_model: MagicMock
    ) -> None:
        """Stop animation should reset to first frame."""
        animation_controller.start_animation()
        animation_controller.stop_animation()

        mock_sprite_model.first_frame.assert_called()
        assert animation_controller.is_playing is False

    def test_toggle_playback_starts_when_paused(
        self, animation_controller: AnimationController
    ) -> None:
        """Toggle playback should start when paused."""
        assert not animation_controller.is_playing

        animation_controller.toggle_playback()

        assert animation_controller.is_playing is True

    def test_toggle_playback_pauses_when_playing(
        self, animation_controller: AnimationController
    ) -> None:
        """Toggle playback should pause when playing."""
        animation_controller.start_animation()
        assert animation_controller.is_playing

        animation_controller.toggle_playback()

        assert animation_controller.is_playing is False


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_start_without_frames_fails(self, qapp) -> None:
        """Starting animation without frames should fail and emit error."""
        mock_model = MagicMock()
        mock_model.sprite_frames = []  # No frames
        mock_model.fps = 12
        mock_model.loop_enabled = True
        mock_model.dataLoaded = MagicMock()
        mock_model.extractionCompleted = MagicMock()
        mock_model.frameChanged = MagicMock()
        mock_model.errorOccurred = MagicMock()
        mock_viewer = MagicMock()

        controller = AnimationController(
            sprite_model=mock_model,
            sprite_viewer=mock_viewer,
        )

        error_spy = []
        controller.errorOccurred.connect(lambda msg: error_spy.append(msg))

        result = controller.start_animation()

        assert result is False
        assert len(error_spy) == 1
        assert "No sprite frames" in error_spy[0]

    def test_start_with_empty_frames_fails(self, qapp) -> None:
        """Starting animation with empty frames list should fail gracefully."""
        mock_model = MagicMock()
        mock_model.sprite_frames = []  # Empty frames
        mock_model.fps = 12
        mock_model.loop_enabled = True
        mock_model.dataLoaded = MagicMock()
        mock_model.extractionCompleted = MagicMock()
        mock_model.frameChanged = MagicMock()
        mock_model.errorOccurred = MagicMock()
        mock_viewer = MagicMock()

        controller = AnimationController(
            sprite_model=mock_model,
            sprite_viewer=mock_viewer,
        )

        result = controller.start_animation()

        assert result is False
        assert not controller.is_playing

    def test_multiple_start_calls(
        self, animation_controller: AnimationController
    ) -> None:
        """Multiple start calls should be safe."""
        result1 = animation_controller.start_animation()
        result2 = animation_controller.start_animation()

        assert result1 is True
        # Second start may return True (already playing) or restart
        assert animation_controller.is_playing is True

    def test_fps_bounds(
        self, animation_controller: AnimationController
    ) -> None:
        """FPS should accept valid values and reject out-of-range values."""
        from config import Config

        # Very low FPS (within valid range)
        result = animation_controller.set_fps(Config.Animation.MIN_FPS)
        assert result is True
        assert animation_controller.current_fps == Config.Animation.MIN_FPS

        # Max FPS (within valid range)
        result = animation_controller.set_fps(Config.Animation.MAX_FPS)
        assert result is True
        assert animation_controller.current_fps == Config.Animation.MAX_FPS

        # Out of range FPS should be rejected
        result = animation_controller.set_fps(120)
        assert result is False
        # Should remain at last valid value
        assert animation_controller.current_fps == Config.Animation.MAX_FPS

    def test_loop_mode_affects_completion(
        self, animation_controller: AnimationController, mock_sprite_model: MagicMock
    ) -> None:
        """Loop mode should be passed to sprite model."""
        animation_controller.set_loop_mode(False)
        animation_controller.start_animation()

        # The model handles loop logic, controller just passes it through
        assert animation_controller.loop_enabled is False

