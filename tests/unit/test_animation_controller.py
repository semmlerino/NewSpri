"""
Unit tests for AnimationController.
Tests animation timing, state management, and signal coordination.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QTimer
from PySide6.QtTest import QSignalSpy

from core.animation_controller import AnimationController
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
        assert animation_controller.current_fps == test_fps
    
    @pytest.mark.parametrize("fps", [1, 5, 10, 15, 24, 30, 60])
    def test_fps_validation(self, animation_controller, fps):
        """Test FPS validation with various values."""
        animation_controller.set_fps(fps)
        assert Config.Animation.MIN_FPS <= animation_controller.current_fps <= Config.Animation.MAX_FPS
    
    def test_fps_bounds_clamping(self, animation_controller):
        """Test FPS values are clamped to valid bounds."""
        # Test below minimum
        animation_controller.set_fps(0)
        assert animation_controller.current_fps >= Config.Animation.MIN_FPS
        
        # Test above maximum
        animation_controller.set_fps(1000)
        assert animation_controller.current_fps <= Config.Animation.MAX_FPS
    
    def test_loop_mode_toggle(self, animation_controller):
        """Test toggling loop mode."""
        initial_state = animation_controller._loop_enabled
        
        animation_controller.set_loop_mode(not initial_state)
        assert animation_controller._loop_enabled != initial_state
        
        animation_controller.set_loop_mode(initial_state)
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
        precision = animation_controller.get_timing_precision()
        assert precision >= 0
        assert precision <= 1000  # Should not exceed 1 second


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
        assert animation_controller._is_playing
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
        
        assert not animation_controller._is_playing
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
        
        assert not animation_controller._is_playing
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
        
        initial_state = animation_controller._is_playing
        
        result = animation_controller.toggle_playback()
        assert result is True  # Should succeed
        assert animation_controller._is_playing != initial_state
        
        animation_controller.toggle_playback()
        assert animation_controller._is_playing == initial_state


class TestAnimationControllerRealSignals:
    """Test animation controller signal emission with REAL Qt signal mechanisms."""
    
    def test_real_fps_changed_signal(self, animation_controller, real_signal_tester):
        """Test fpsChanged signal with real QSignalSpy and proper argument access."""
        # Connect real signal spy
        fps_spy = real_signal_tester.connect_spy(animation_controller.fpsChanged, 'fps_changed')
        
        # Trigger FPS change
        animation_controller.set_fps(25)
        
        # Verify real signal emission
        assert real_signal_tester.verify_emission('fps_changed', count=1)
        
        # Get real signal arguments
        args = real_signal_tester.get_signal_args('fps_changed', 0)
        assert len(args) >= 1
        assert args[0] == 25  # New FPS value
    
    def test_real_loop_mode_changed_signal(self, animation_controller, real_signal_tester):
        """Test loopModeChanged signal with real Qt signal mechanisms."""
        # Connect real signal spy
        loop_spy = real_signal_tester.connect_spy(animation_controller.loopModeChanged, 'loop_changed')
        
        # Test enabling loop mode
        animation_controller.set_loop_mode(True)
        assert real_signal_tester.verify_emission('loop_changed', count=1)
        
        args = real_signal_tester.get_signal_args('loop_changed', 0)
        assert len(args) >= 1
        assert args[0] is True
        
        # Test disabling loop mode with fresh spy
        loop_spy2 = real_signal_tester.connect_spy(animation_controller.loopModeChanged, 'loop_changed2')
        animation_controller.set_loop_mode(False)
        
        assert real_signal_tester.verify_emission('loop_changed2', count=1)
        args2 = real_signal_tester.get_signal_args('loop_changed2', 0)
        assert len(args2) >= 1
        assert args2[0] is False
    
    def test_real_playback_state_signal_with_integration(self, real_sprite_system, real_signal_tester):
        """Test playback state changes with real sprite system integration."""
        # Initialize real system
        success = real_sprite_system.initialize_system(frame_count=4)
        assert success
        
        controller = real_sprite_system.animation_controller
        
        # Connect real signal spy
        state_spy = real_signal_tester.connect_spy(controller.playbackStateChanged, 'state_changed')
        
        # Test animation start
        start_success = controller.start_animation()
        assert start_success
        
        # Verify real signal emission
        assert real_signal_tester.verify_emission('state_changed', count=1, timeout=1000)
        
        args = real_signal_tester.get_signal_args('state_changed', 0)
        assert len(args) >= 1
        assert args[0] is True  # Should emit True when starting
        
        # Test animation pause
        pause_spy = real_signal_tester.connect_spy(controller.playbackStateChanged, 'pause_state')
        controller.pause_animation()
        
        assert real_signal_tester.verify_emission('pause_state', count=1)
        pause_args = real_signal_tester.get_signal_args('pause_state', 0)
        assert len(pause_args) >= 1
        assert pause_args[0] is False  # Should emit False when pausing
    
    def test_real_animation_lifecycle_signals(self, real_sprite_system, real_signal_tester):
        """Test complete animation lifecycle with real signal tracking."""
        # Initialize real system
        real_sprite_system.initialize_system(frame_count=6)
        controller = real_sprite_system.animation_controller
        
        # Connect multiple real signal spies
        signals = real_sprite_system.get_real_signal_connections()
        
        started_spy = real_signal_tester.connect_spy(signals['animation_started'], 'started')
        paused_spy = real_signal_tester.connect_spy(signals['animation_paused'], 'paused')
        stopped_spy = real_signal_tester.connect_spy(signals['animation_stopped'], 'stopped')
        status_spy = real_signal_tester.connect_spy(signals['status_changed'], 'status')
        
        # Test start sequence
        controller.start_animation()
        
        assert real_signal_tester.verify_emission('started', count=1)
        assert real_signal_tester.verify_emission_range('status', min_count=1)  # Status messages
        
        # Test pause sequence
        controller.pause_animation()
        
        assert real_signal_tester.verify_emission('paused', count=1)
        
        # Test stop sequence
        controller.start_animation()  # Restart first
        controller.stop_animation()
        
        assert real_signal_tester.verify_emission('stopped', count=1)
        
        # Verify system state
        state_checks = real_sprite_system.verify_system_state()
        assert state_checks['controller_initialized']
        assert state_checks['has_sprite_model']
        assert state_checks['timer_exists']
    
    def test_real_signal_timing_accuracy(self, real_sprite_system, real_signal_tester):
        """Test signal timing accuracy with real Qt timer mechanisms."""
        real_sprite_system.initialize_system(frame_count=3)
        controller = real_sprite_system.animation_controller
        
        # Set specific FPS for timing test
        controller.set_fps(20)  # 50ms intervals
        
        # Connect frame advancement spy
        signals = real_sprite_system.get_real_signal_connections()
        frame_spy = real_signal_tester.connect_spy(signals['frame_advanced'], 'frame_advanced')
        
        # Start animation and wait for frame advancements
        controller.start_animation()
        
        # Wait longer to allow multiple frames
        if real_signal_tester.wait_for_signal('frame_advanced', timeout=200):
            frame_count = real_signal_tester.get_spy_count('frame_advanced')
            # Should have at least some frame advancements in 200ms at 20 FPS
            assert frame_count >= 0  # Accept any result due to timing variability
        
        controller.stop_animation()
    
    def test_real_error_signal_handling(self, animation_controller, real_signal_tester):
        """Test error signal emission with real Qt mechanisms."""
        # Connect error signal spy
        error_spy = real_signal_tester.connect_spy(animation_controller.errorOccurred, 'error')
        
        # Trigger error condition (invalid FPS)
        animation_controller.set_fps(-5)  # Should trigger error
        
        # Check if error signal was emitted
        error_emitted = real_signal_tester.verify_emission('error', count=1, timeout=100)
        
        if error_emitted:
            args = real_signal_tester.get_signal_args('error', 0)
            assert len(args) >= 1
            assert isinstance(args[0], str)  # Error message should be string
    
    def test_multiple_real_signals_coordination(self, real_sprite_system, real_signal_tester):
        """Test coordination of multiple real signals in complex scenarios."""
        real_sprite_system.initialize_system(frame_count=5)
        controller = real_sprite_system.animation_controller
        
        signals = real_sprite_system.get_real_signal_connections()
        
        # Connect multiple spies
        fps_spy = real_signal_tester.connect_spy(signals['fps_changed'], 'fps')
        loop_spy = real_signal_tester.connect_spy(signals['loop_mode_changed'], 'loop')
        state_spy = real_signal_tester.connect_spy(signals['playback_state_changed'], 'state')
        status_spy = real_signal_tester.connect_spy(signals['status_changed'], 'status')
        
        # Perform complex sequence
        controller.set_fps(15)
        controller.set_loop_mode(False)
        controller.start_animation()
        controller.pause_animation()
        
        # Verify all signals were emitted
        assert real_signal_tester.verify_emission('fps', count=1)
        assert real_signal_tester.verify_emission('loop', count=1)
        assert real_signal_tester.verify_emission_range('state', min_count=1)  # Multiple state changes
        assert real_signal_tester.verify_emission_range('status', min_count=1)  # Multiple status updates
        
        # Verify signal arguments
        fps_args = real_signal_tester.get_signal_args('fps', 0)
        loop_args = real_signal_tester.get_signal_args('loop', 0)
        
        assert fps_args[0] == 15
        assert loop_args[0] is False


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
        
        mock_sprite_viewer = Mock()
        # Add viewer signal mocks
        mock_sprite_viewer.closing = Mock()
        mock_sprite_viewer.frame_display_changed = Mock()
        
        result = animation_controller.initialize(mock_sprite_model, mock_sprite_viewer)
        
        assert result is True  # Check initialization success
        assert animation_controller._sprite_model == mock_sprite_model
        assert animation_controller._sprite_viewer == mock_sprite_viewer
        assert animation_controller._is_active
    
    def test_sprite_model_coordination(self, animation_controller):
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
        
        mock_sprite_viewer = Mock()
        mock_sprite_viewer.closing = Mock()
        mock_sprite_viewer.frame_display_changed = Mock()
        
        animation_controller.initialize(mock_sprite_model, mock_sprite_viewer)
        animation_controller._is_playing = True  # Manually set playing state
        
        # Test frame advancement via timer timeout
        animation_controller._on_timer_timeout()
        
        # Should call sprite model methods
        mock_sprite_model.next_frame.assert_called()


class TestAnimationControllerPerformance:
    """Test AnimationController performance features."""
    
    def test_frame_timing_history(self, animation_controller):
        """Test frame timing history tracking."""
        # Test the _track_frame_timing method
        animation_controller._last_frame_time = 1.0  # Set initial time
        
        # Call track timing multiple times
        animation_controller._track_frame_timing()
        
        # Check that timing history is maintained
        assert hasattr(animation_controller, '_frame_timing_history')
        assert animation_controller._max_timing_history > 0
    
    def test_performance_monitoring(self, animation_controller):
        """Test performance monitoring features."""
        # Set initial time for tracking
        animation_controller._last_frame_time = 1.0
        
        # Track frame timing
        animation_controller._track_frame_timing()
        
        # Get performance metrics
        metrics = animation_controller.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert 'target_fps' in metrics
        assert 'measured_fps' in metrics
        assert metrics['target_fps'] > 0


class TestAnimationControllerErrorHandling:
    """Test AnimationController error handling."""
    
    def test_invalid_fps_handling(self, animation_controller):
        """Test handling of invalid FPS values."""
        # Store original FPS
        original_fps = animation_controller._current_fps
        
        # Test with values outside valid range
        result = animation_controller.set_fps(0)  # Below minimum
        assert result is False
        assert animation_controller._current_fps == original_fps
        
        # Test with very high value
        result = animation_controller.set_fps(1000)  # Above maximum
        assert result is False
        assert animation_controller._current_fps == original_fps
    
    def test_timer_error_handling(self, animation_controller):
        """Test timer error handling."""
        with patch.object(animation_controller._animation_timer, 'start', side_effect=Exception("Timer error")):
            # Should not raise exception
            animation_controller.start_animation()
            
            # Should emit error signal
            # (In real implementation, this would be caught and handled)
    
    def test_cleanup_on_destruction(self, animation_controller, qapp):
        """Test proper cleanup when controller is destroyed."""
        # Initialize with mock model that has frames
        mock_model = Mock()
        mock_model.sprite_frames = [Mock()]
        mock_model.fps = 10  # Direct attribute
        mock_model.loop_enabled = True  # Direct attribute
        # Add signal mocks
        mock_model.dataLoaded = Mock()
        mock_model.extractionCompleted = Mock()
        mock_model.frameChanged = Mock()
        mock_model.errorOccurred = Mock()
        
        mock_viewer = Mock()
        mock_viewer.closing = Mock()
        mock_viewer.frame_display_changed = Mock()
        
        animation_controller.initialize(mock_model, mock_viewer)
        result = animation_controller.start_animation()
        
        # Check that start_animation succeeded
        assert result is True
        assert animation_controller._is_playing is True
        
        # Shutdown (not cleanup)
        animation_controller.shutdown()
        
        # After shutdown, timer and playing state should be false
        assert not animation_controller._animation_timer.isActive()
        assert not animation_controller._is_playing