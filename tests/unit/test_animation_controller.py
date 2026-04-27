"""
Unit tests for AnimationController.
Tests animation timing, state management, and signal coordination.
"""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtTest import QSignalSpy

from config import Config
from core.animation_controller import AnimationController


class TestAnimationControllerInitialization:
    """Test AnimationController initialization."""

    def test_initial_state(self, animation_controller):
        """Test controller starts in proper initial state after construction."""
        # After single-step init, controller is active but not playing
        assert animation_controller._is_active
        assert not animation_controller.is_playing
        assert animation_controller.current_fps == Config.Animation.DEFAULT_FPS

    def test_timer_initialization(self, animation_controller):
        """Test animation timer is properly initialized."""
        assert isinstance(animation_controller._animation_timer, QTimer)
        assert not animation_controller._animation_timer.isSingleShot()

    def test_signals_exist(self, animation_controller):
        """Test all required signals are defined."""
        signals = [
            "animationStarted",
            "animationPaused",
            "animationStopped",
            "animationCompleted",
            "errorOccurred",
            "statusChanged",
        ]

        for signal_name in signals:
            assert hasattr(animation_controller, signal_name)


class TestAnimationControllerState:
    """Test animation state management."""

    def test_set_fps(self, animation_controller):
        """Test setting FPS value."""
        test_fps = 30
        result = animation_controller.set_fps(test_fps)

        assert result is True
        assert animation_controller.current_fps == test_fps

    @pytest.mark.parametrize("fps", [1, 5, 10, 15, 24, 30, 60])
    def test_fps_validation(self, animation_controller, fps):
        """Test FPS validation with various values."""
        result = animation_controller.set_fps(fps)

        assert result is True
        assert animation_controller.current_fps == fps

    def test_fps_bounds_clamping(self, animation_controller):
        """Test FPS values outside the valid range are rejected."""
        original_fps = animation_controller.current_fps

        # Test below minimum
        result = animation_controller.set_fps(0)
        assert result is False
        assert animation_controller.current_fps == original_fps

        # Test above maximum
        result = animation_controller.set_fps(1000)
        assert result is False
        assert animation_controller.current_fps == original_fps

    def test_loop_mode_toggle(self, animation_controller):
        """Test toggling loop mode."""
        animation_controller.set_loop_mode(False)
        assert animation_controller._loop_enabled is False

        animation_controller.set_loop_mode(True)
        assert animation_controller._loop_enabled is True


class TestAnimationControllerTiming:
    """Test animation timing calculations."""

    @pytest.mark.parametrize(
        "fps,expected_interval",
        [
            (10, 100),  # 1000ms / 10fps = 100ms
            (30, 33),  # 1000ms / 30fps ≈ 33ms
            (60, 17),  # 1000ms / 60fps ≈ 17ms
            (1, 1000),  # 1000ms / 1fps = 1000ms
        ],
    )
    def test_timer_interval_calculation(self, animation_controller, fps, expected_interval):
        """Test timer interval calculation for various FPS values."""
        animation_controller.set_fps(fps)
        calculated_interval = animation_controller._calculate_timer_interval()

        # Allow small rounding differences
        assert abs(calculated_interval - expected_interval) <= 1


class TestAnimationControllerPlayback:
    """Test animation playback control."""

    def test_start_animation(self, animation_controller, qapp):
        """Test starting animation."""
        from unittest.mock import Mock

        # Set up mock sprite model with frames
        mock_sprite_model = Mock()
        mock_sprite_model.sprite_frames = [Mock(), Mock(), Mock()]  # Mock frames
        mock_sprite_model.first_frame = Mock()

        # Initialize controller properly
        animation_controller._sprite_model = mock_sprite_model
        animation_controller._is_active = True

        spy = QSignalSpy(animation_controller.animationStarted)

        result = animation_controller.start_animation()

        assert result is True
        assert animation_controller.is_playing
        assert animation_controller._animation_timer.isActive()
        assert spy.count() > 0

    def test_pause_animation(self, animation_controller, qapp):
        """Test pausing animation."""
        from unittest.mock import Mock

        # Set up mock sprite model with frames
        mock_sprite_model = Mock()
        mock_sprite_model.sprite_frames = [Mock(), Mock(), Mock()]
        animation_controller._sprite_model = mock_sprite_model
        animation_controller._is_active = True

        spy = QSignalSpy(animation_controller.animationPaused)

        # Start then pause
        animation_controller.start_animation()
        animation_controller.pause_animation()

        assert not animation_controller.is_playing
        assert not animation_controller._animation_timer.isActive()
        assert spy.count() > 0

    def test_stop_animation(self, animation_controller, qapp):
        """Test stopping animation."""
        from unittest.mock import Mock

        # Set up mock sprite model with frames
        mock_sprite_model = Mock()
        mock_sprite_model.sprite_frames = [Mock(), Mock(), Mock()]
        mock_sprite_model.first_frame = Mock()
        animation_controller._sprite_model = mock_sprite_model
        animation_controller._is_active = True

        spy = QSignalSpy(animation_controller.animationStopped)

        # Start then stop
        animation_controller.start_animation()
        animation_controller.stop_animation()

        assert not animation_controller.is_playing
        assert not animation_controller._animation_timer.isActive()
        assert spy.count() > 0

    def test_toggle_playback(self, animation_controller):
        """Test toggling playback state."""
        from unittest.mock import Mock

        # Set up mock sprite model with frames
        mock_sprite_model = Mock()
        mock_sprite_model.sprite_frames = [Mock(), Mock(), Mock()]
        mock_sprite_model.first_frame = Mock()
        animation_controller._sprite_model = mock_sprite_model
        animation_controller._is_active = True

        initial_state = animation_controller.is_playing

        result = animation_controller.toggle_playback()
        assert result is True  # Should succeed
        assert animation_controller.is_playing != initial_state

        animation_controller.toggle_playback()
        assert animation_controller.is_playing == initial_state


class TestAnimationControllerRealSignals:
    """Test animation controller signal emission with REAL Qt signal mechanisms."""

    def test_real_animation_lifecycle_signals(self, real_sprite_system, real_signal_tester):
        """Test complete animation lifecycle with real signal tracking."""
        # Initialize real system
        real_sprite_system.initialize_system(frame_count=6)
        controller = real_sprite_system.animation_controller

        # Connect multiple real signal spies
        signals = real_sprite_system.get_real_signal_connections()

        started_spy = real_signal_tester.connect_spy(signals["animation_started"], "started")
        paused_spy = real_signal_tester.connect_spy(signals["animation_paused"], "paused")
        stopped_spy = real_signal_tester.connect_spy(signals["animation_stopped"], "stopped")
        status_spy = real_signal_tester.connect_spy(signals["status_changed"], "status")

        # Test start sequence
        controller.start_animation()

        assert real_signal_tester.verify_emission("started", count=1)
        assert real_signal_tester.verify_emission_range("status", min_count=1)  # Status messages

        # Test pause sequence
        controller.pause_animation()

        assert real_signal_tester.verify_emission("paused", count=1)

        # Test stop sequence
        controller.start_animation()  # Restart first
        controller.stop_animation()

        assert real_signal_tester.verify_emission("stopped", count=1)

        # Verify system state
        state_checks = real_sprite_system.verify_system_state()
        assert state_checks["controller_initialized"]
        assert state_checks["has_sprite_model"]
        assert state_checks["timer_exists"]

    def test_real_error_signal_handling(self, animation_controller, real_signal_tester):
        """Test error signal emission with real Qt mechanisms."""
        # Connect error signal spy
        error_spy = real_signal_tester.connect_spy(animation_controller.errorOccurred, "error")

        # Trigger error condition (invalid FPS)
        animation_controller.set_fps(-5)  # Should trigger error

        # Check if error signal was emitted
        error_emitted = real_signal_tester.verify_emission("error", count=1, timeout=100)

        # Error signal should be emitted for invalid FPS
        assert error_emitted, "errorOccurred signal should be emitted for negative FPS"
        args = real_signal_tester.get_signal_args("error", 0)
        assert len(args) >= 1, "Error signal should have at least one argument"
        assert isinstance(args[0], str), "Error message should be a string"


class TestAnimationControllerIntegration:
    """Test AnimationController integration with other components."""

    def test_initialize_with_sprite_model(self, animation_controller):
        """Test initialization with sprite model."""
        mock_sprite_model = Mock()
        mock_sprite_model.sprite_frames = [Mock()]  # Add sprite frames
        mock_sprite_model.fps = 10  # Direct attribute access
        mock_sprite_model.loop_enabled = True  # Direct attribute access
        # Add signal mocks
        mock_sprite_model.dataLoaded = Mock()
        mock_sprite_model.extractionCompleted = Mock()
        mock_sprite_model.frameChanged = Mock()
        mock_sprite_model.errorOccurred = Mock()

        # Create controller with dependencies (single-step init)
        controller = AnimationController(
            sprite_model=mock_sprite_model,
        )

        assert controller._sprite_model == mock_sprite_model
        assert controller._is_active

    def test_sprite_model_coordination(self):
        """Test coordination with sprite model."""
        mock_sprite_model = Mock()
        mock_sprite_model.sprite_frames = [Mock()]  # Add sprite frames
        mock_sprite_model.fps = 10  # Direct attribute
        mock_sprite_model.loop_enabled = True  # Direct attribute
        mock_sprite_model.next_frame.return_value = (1, True)  # frame_index, should_continue
        # Add signal mocks
        mock_sprite_model.dataLoaded = Mock()
        mock_sprite_model.extractionCompleted = Mock()
        mock_sprite_model.frameChanged = Mock()
        mock_sprite_model.errorOccurred = Mock()

        controller = AnimationController(
            sprite_model=mock_sprite_model,
        )
        assert controller.start_animation() is True
        controller._animation_timer.stop()

        # Test frame advancement via timer timeout
        controller._on_timer_timeout()

        # Should call sprite model methods
        mock_sprite_model.next_frame.assert_called()


class TestAnimationControllerErrorHandling:
    """Test AnimationController error handling."""

    def test_invalid_fps_handling(self, animation_controller):
        """Test handling of invalid FPS values."""
        # Store original FPS
        original_fps = animation_controller.current_fps

        # Test with values outside valid range
        result = animation_controller.set_fps(0)  # Below minimum
        assert result is False
        assert animation_controller.current_fps == original_fps

        # Test with very high value
        result = animation_controller.set_fps(1000)  # Above maximum
        assert result is False
        assert animation_controller.current_fps == original_fps

    def test_timer_error_handling(self, animation_controller):
        """Test timer error handling."""
        with patch.object(
            animation_controller._animation_timer, "start", side_effect=Exception("Timer error")
        ):
            # Should not raise exception
            animation_controller.start_animation()

            # Should emit error signal
            # (In real implementation, this would be caught and handled)

    def test_cleanup_on_destruction(self, qapp):
        """Test proper cleanup when controller is destroyed."""
        # Create controller with mock model that has frames
        mock_model = Mock()
        mock_model.sprite_frames = [Mock()]
        mock_model.fps = 10  # Direct attribute
        mock_model.loop_enabled = True  # Direct attribute
        # Add signal mocks
        mock_model.dataLoaded = Mock()
        mock_model.extractionCompleted = Mock()
        mock_model.frameChanged = Mock()
        mock_model.errorOccurred = Mock()

        controller = AnimationController(
            sprite_model=mock_model,
        )
        result = controller.start_animation()

        # Check that start_animation succeeded
        assert result is True
        assert controller.is_playing is True

        # Shutdown (not cleanup)
        controller.shutdown()

        # After shutdown, timer and playing state should be false
        assert not controller._animation_timer.isActive()
        assert not controller.is_playing
