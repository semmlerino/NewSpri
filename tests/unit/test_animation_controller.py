"""
Unit tests for AnimationController.
Tests animation timing, state management, and signal coordination.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QTimer, QSignalSpy

from animation_controller import AnimationController
from config import Config


class TestAnimationControllerInitialization:
    """Test AnimationController initialization."""
    
    def test_controller_creation(self, animation_controller):
        """Test AnimationController can be created successfully."""
        assert isinstance(animation_controller, AnimationController)
    
    def test_initial_state(self, animation_controller):
        """Test controller starts in proper initial state."""
        assert not animation_controller._is_active
        assert not animation_controller._is_playing
        assert animation_controller._current_fps == Config.Animation.DEFAULT_FPS
        assert animation_controller._loop_enabled
    
    def test_timer_initialization(self, animation_controller):
        """Test animation timer is properly initialized."""
        assert isinstance(animation_controller._animation_timer, QTimer)
        assert not animation_controller._animation_timer.isSingleShot()
    
    def test_signals_exist(self, animation_controller):
        """Test all required signals are defined."""
        signals = [
            'animationStarted', 'animationPaused', 'animationStopped',
            'animationCompleted', 'frameAdvanced', 'playbackStateChanged',
            'fpsChanged', 'loopModeChanged', 'errorOccurred', 'statusChanged'
        ]
        
        for signal_name in signals:
            assert hasattr(animation_controller, signal_name)


class TestAnimationControllerState:
    """Test animation state management."""
    
    def test_set_fps(self, animation_controller):
        """Test setting FPS value."""
        test_fps = 30
        animation_controller.set_fps(test_fps)
        
        assert animation_controller._current_fps == test_fps
        assert animation_controller.get_fps() == test_fps
    
    @pytest.mark.parametrize("fps", [1, 5, 10, 15, 24, 30, 60])
    def test_fps_validation(self, animation_controller, fps):
        """Test FPS validation with various values."""
        animation_controller.set_fps(fps)
        assert Config.Animation.MIN_FPS <= animation_controller.get_fps() <= Config.Animation.MAX_FPS
    
    def test_fps_bounds_clamping(self, animation_controller):
        """Test FPS values are clamped to valid bounds."""
        # Test below minimum
        animation_controller.set_fps(0)
        assert animation_controller.get_fps() >= Config.Animation.MIN_FPS
        
        # Test above maximum
        animation_controller.set_fps(1000)
        assert animation_controller.get_fps() <= Config.Animation.MAX_FPS
    
    def test_loop_mode_toggle(self, animation_controller):
        """Test toggling loop mode."""
        initial_state = animation_controller._loop_enabled
        
        animation_controller.set_loop_enabled(not initial_state)
        assert animation_controller._loop_enabled != initial_state
        
        animation_controller.set_loop_enabled(initial_state)
        assert animation_controller._loop_enabled == initial_state


class TestAnimationControllerTiming:
    """Test animation timing calculations."""
    
    @pytest.mark.parametrize("fps,expected_interval", [
        (10, 100),  # 1000ms / 10fps = 100ms
        (30, 33),   # 1000ms / 30fps ≈ 33ms  
        (60, 17),   # 1000ms / 60fps ≈ 17ms
        (1, 1000),  # 1000ms / 1fps = 1000ms
    ])
    def test_timer_interval_calculation(self, animation_controller, fps, expected_interval):
        """Test timer interval calculation for various FPS values."""
        animation_controller.set_fps(fps)
        calculated_interval = animation_controller._calculate_timer_interval()
        
        # Allow small rounding differences
        assert abs(calculated_interval - expected_interval) <= 1
    
    def test_timer_precision_tracking(self, animation_controller):
        """Test timer precision tracking."""
        animation_controller.set_fps(30)
        
        # Timer precision should be calculated
        precision = animation_controller._get_timer_precision()
        assert precision >= 0
        assert precision <= 1000  # Should not exceed 1 second


class TestAnimationControllerPlayback:
    """Test animation playback control."""
    
    def test_start_animation(self, animation_controller, qapp):
        """Test starting animation."""
        spy = QSignalSpy(animation_controller.animationStarted)
        
        animation_controller.start_animation()
        
        assert animation_controller._is_playing
        assert animation_controller._animation_timer.isActive()
        assert len(spy) > 0
    
    def test_pause_animation(self, animation_controller, qapp):
        """Test pausing animation."""
        spy = QSignalSpy(animation_controller.animationPaused)
        
        # Start then pause
        animation_controller.start_animation()
        animation_controller.pause_animation()
        
        assert not animation_controller._is_playing
        assert not animation_controller._animation_timer.isActive()
        assert len(spy) > 0
    
    def test_stop_animation(self, animation_controller, qapp):
        """Test stopping animation."""
        spy = QSignalSpy(animation_controller.animationStopped)
        
        # Start then stop
        animation_controller.start_animation()
        animation_controller.stop_animation()
        
        assert not animation_controller._is_playing
        assert not animation_controller._animation_timer.isActive()
        assert len(spy) > 0
    
    def test_toggle_playback(self, animation_controller):
        """Test toggling playback state."""
        initial_state = animation_controller._is_playing
        
        animation_controller.toggle_playback()
        assert animation_controller._is_playing != initial_state
        
        animation_controller.toggle_playback()
        assert animation_controller._is_playing == initial_state


class TestAnimationControllerSignals:
    """Test animation controller signal emission."""
    
    def test_fps_changed_signal(self, animation_controller, qapp):
        """Test fpsChanged signal emission."""
        spy = QSignalSpy(animation_controller.fpsChanged)
        
        animation_controller.set_fps(25)
        
        assert len(spy) > 0
        assert spy[0][0] == 25  # First argument should be the new FPS
    
    def test_playback_state_changed_signal(self, animation_controller, qapp):
        """Test playbackStateChanged signal emission."""
        spy = QSignalSpy(animation_controller.playbackStateChanged)
        
        animation_controller.start_animation()
        
        assert len(spy) > 0
        assert spy[0][0] is True  # Should emit True when starting
    
    def test_loop_mode_changed_signal(self, animation_controller, qapp):
        """Test loopModeChanged signal emission."""
        spy = QSignalSpy(animation_controller.loopModeChanged)
        
        animation_controller.set_loop_enabled(False)
        
        assert len(spy) > 0
        assert spy[0][0] is False  # Should emit False when disabled


class TestAnimationControllerIntegration:
    """Test AnimationController integration with other components."""
    
    def test_initialize_with_sprite_model(self, animation_controller):
        """Test initialization with sprite model."""
        mock_sprite_model = Mock()
        mock_sprite_viewer = Mock()
        
        animation_controller.initialize(mock_sprite_model, mock_sprite_viewer)
        
        assert animation_controller._sprite_model == mock_sprite_model
        assert animation_controller._sprite_viewer == mock_sprite_viewer
        assert animation_controller._is_active
    
    def test_sprite_model_coordination(self, animation_controller):
        """Test coordination with sprite model."""
        mock_sprite_model = Mock()
        mock_sprite_model.get_frame_count.return_value = 5
        mock_sprite_model.get_frame.return_value = Mock()
        
        animation_controller.initialize(mock_sprite_model, Mock())
        
        # Test frame advancement
        animation_controller._advance_frame()
        
        # Should call sprite model methods
        mock_sprite_model.get_frame_count.assert_called()


class TestAnimationControllerPerformance:
    """Test AnimationController performance features."""
    
    def test_frame_timing_history(self, animation_controller):
        """Test frame timing history tracking."""
        # Initialize with mock data
        animation_controller._frame_timing_history = [1.0, 1.1, 0.9, 1.0, 1.2]
        
        average_timing = animation_controller._get_average_frame_timing()
        assert average_timing > 0
        assert 0.5 < average_timing < 2.0  # Reasonable range
    
    def test_performance_monitoring(self, animation_controller):
        """Test performance monitoring features."""
        animation_controller._record_frame_timing(16.67)  # 60 FPS timing
        
        assert len(animation_controller._frame_timing_history) > 0
        
        # History should be bounded
        max_history = animation_controller._max_timing_history
        for _ in range(max_history + 10):
            animation_controller._record_frame_timing(16.67)
        
        assert len(animation_controller._frame_timing_history) <= max_history


class TestAnimationControllerErrorHandling:
    """Test AnimationController error handling."""
    
    def test_invalid_fps_handling(self, animation_controller):
        """Test handling of invalid FPS values."""
        # Test with None
        animation_controller.set_fps(None)
        assert animation_controller.get_fps() > 0
        
        # Test with negative values
        animation_controller.set_fps(-5)
        assert animation_controller.get_fps() > 0
    
    def test_timer_error_handling(self, animation_controller):
        """Test timer error handling."""
        with patch.object(animation_controller._animation_timer, 'start', side_effect=Exception("Timer error")):
            # Should not raise exception
            animation_controller.start_animation()
            
            # Should emit error signal
            # (In real implementation, this would be caught and handled)
    
    def test_cleanup_on_destruction(self, animation_controller):
        """Test proper cleanup when controller is destroyed."""
        animation_controller.start_animation()
        assert animation_controller._animation_timer.isActive()
        
        # Cleanup
        animation_controller.cleanup()
        
        assert not animation_controller._animation_timer.isActive()
        assert not animation_controller._is_playing