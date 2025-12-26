"""
Unit tests for AnimationCoordinator (Phase 5 refactoring).
Tests the animation coordinator that handles animation control and navigation.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from coordinators import AnimationCoordinator


class TestAnimationCoordinator:
    """Test AnimationCoordinator functionality."""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create mock main window."""
        window = Mock()
        window._shortcut_manager = Mock()
        return window
    
    @pytest.fixture
    def mock_sprite_model(self):
        """Create mock sprite model."""
        model = Mock()
        model.sprite_frames = [Mock() for _ in range(5)]  # 5 mock frames
        model.current_frame = 2
        model.previous_frame = Mock()
        model.next_frame = Mock()
        model.first_frame = Mock()
        model.last_frame = Mock()
        model.set_current_frame = Mock()
        return model
    
    @pytest.fixture
    def mock_animation_controller(self):
        """Create mock animation controller."""
        controller = Mock()
        controller.is_playing = False
        controller.toggle_playback = Mock()
        controller.start_playback = Mock()
        controller.pause_playback = Mock()
        controller.stop_playback = Mock()
        controller.set_fps = Mock()
        controller.set_loop_mode = Mock()
        return controller
    
    @pytest.fixture
    def mock_playback_controls(self):
        """Create mock playback controls."""
        controls = Mock()
        controls.update_button_states = Mock()
        controls.set_frame_range = Mock()
        return controls
    
    @pytest.fixture
    def mock_action_manager(self):
        """Create mock action manager."""
        manager = Mock()
        manager.update_context = Mock()
        return manager
    
    @pytest.fixture
    def mock_status_manager(self):
        """Create mock status manager."""
        return Mock()
    
    def test_initialization(self, mock_main_window):
        """Test AnimationCoordinator initialization."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        assert coordinator.main_window == mock_main_window
        assert not coordinator.is_initialized
        assert coordinator.sprite_model is None
        assert coordinator.animation_controller is None
        assert coordinator.playback_controls is None
        assert coordinator.action_manager is None
        assert coordinator.status_manager is None
    
    def test_initialize_with_dependencies(self, mock_main_window, mock_sprite_model, 
                                          mock_animation_controller, mock_playback_controls,
                                          mock_action_manager, mock_status_manager):
        """Test initialization with dependencies."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        dependencies = {
            'sprite_model': mock_sprite_model,
            'animation_controller': mock_animation_controller,
            'playback_controls': mock_playback_controls,
            'action_manager': mock_action_manager,
            'status_manager': mock_status_manager
        }
        
        coordinator.initialize(dependencies)
        
        assert coordinator.sprite_model == mock_sprite_model
        assert coordinator.animation_controller == mock_animation_controller
        assert coordinator.playback_controls == mock_playback_controls
        assert coordinator.action_manager == mock_action_manager
        assert coordinator.status_manager == mock_status_manager
        assert coordinator.is_initialized
    
    def test_cleanup(self, mock_main_window):
        """Test cleanup method."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        # Should not raise any errors
        coordinator.cleanup()
    
    def test_frame_navigation(self, mock_main_window, mock_sprite_model):
        """Test frame navigation methods."""
        coordinator = AnimationCoordinator(mock_main_window)
        coordinator.sprite_model = mock_sprite_model
        
        # Test previous frame
        coordinator.go_to_prev_frame()
        mock_sprite_model.previous_frame.assert_called_once()
        
        # Test next frame
        coordinator.go_to_next_frame()
        mock_sprite_model.next_frame.assert_called_once()
        
        # Test first frame
        coordinator.go_to_first_frame()
        mock_sprite_model.first_frame.assert_called_once()
        
        # Test last frame
        coordinator.go_to_last_frame()
        mock_sprite_model.last_frame.assert_called_once()
        
        # Test go to specific frame
        coordinator.go_to_frame(3)
        mock_sprite_model.set_current_frame.assert_called_once_with(3)
    
    def test_frame_navigation_without_model(self, mock_main_window):
        """Test frame navigation without sprite model."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        # Should not raise errors
        coordinator.go_to_prev_frame()
        coordinator.go_to_next_frame()
        coordinator.go_to_first_frame()
        coordinator.go_to_last_frame()
        coordinator.go_to_frame(0)
    
    def test_playback_control(self, mock_main_window, mock_animation_controller):
        """Test playback control methods."""
        coordinator = AnimationCoordinator(mock_main_window)
        coordinator.animation_controller = mock_animation_controller
        
        # Test toggle playback
        coordinator.toggle_playback()
        mock_animation_controller.toggle_playback.assert_called_once()
        
        # Test start playback
        coordinator.start_playback()
        mock_animation_controller.start_playback.assert_called_once()
        
        # Test pause playback
        coordinator.pause_playback()
        mock_animation_controller.pause_playback.assert_called_once()
        
        # Test stop playback
        coordinator.stop_playback()
        mock_animation_controller.stop_playback.assert_called_once()
    
    def test_playback_control_without_controller(self, mock_main_window):
        """Test playback control without animation controller."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        # Should not raise errors
        coordinator.toggle_playback()
        coordinator.start_playback()
        coordinator.pause_playback()
        coordinator.stop_playback()
    
    def test_playback_state_handlers(self, mock_main_window, mock_playback_controls,
                                     mock_action_manager, mock_sprite_model):
        """Test playback state handler methods."""
        coordinator = AnimationCoordinator(mock_main_window)
        coordinator.playback_controls = mock_playback_controls
        coordinator.action_manager = mock_action_manager
        coordinator.sprite_model = mock_sprite_model
        
        # Test playback started
        coordinator.on_playback_started()
        mock_playback_controls.update_button_states.assert_called_with(False, True, True)
        
        # Test playback paused
        coordinator.on_playback_paused()
        mock_playback_controls.update_button_states.assert_called_with(True, True, True)
        
        # Test playback stopped
        coordinator.on_playback_stopped()
        mock_playback_controls.update_button_states.assert_called_with(True, True, False)
        
        # Test playback completed
        coordinator.on_playback_completed()
        mock_playback_controls.update_button_states.assert_called_with(True, True, False)
        
        # Verify context updates
        assert mock_action_manager.update_context.call_count == 4
    
    def test_frame_advanced_handler(self, mock_main_window):
        """Test frame advanced handler."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        # Should not raise error
        coordinator.on_frame_advanced(3)
    
    @patch('coordinators.animation_coordinator.QMessageBox')
    def test_animation_error_handler(self, mock_messagebox, mock_main_window):
        """Test animation error handler."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        coordinator.on_animation_error("Test error")
        
        mock_messagebox.warning.assert_called_once_with(
            mock_main_window,
            "Animation Error",
            "Test error"
        )
    
    def test_extraction_completed_handler(self, mock_main_window, mock_playback_controls):
        """Test extraction completed handler."""
        coordinator = AnimationCoordinator(mock_main_window)
        coordinator.playback_controls = mock_playback_controls
        
        # Test with frames
        coordinator.on_extraction_completed(10)
        mock_playback_controls.set_frame_range.assert_called_with(9)
        mock_playback_controls.update_button_states.assert_called_with(True, True, False)
        
        # Test without frames
        coordinator.on_extraction_completed(0)
        mock_playback_controls.set_frame_range.assert_called_with(0)
        mock_playback_controls.update_button_states.assert_called_with(False, False, False)
    
    def test_extraction_completed_without_controls(self, mock_main_window):
        """Test extraction completed without playback controls."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        # Should not raise error
        coordinator.on_extraction_completed(10)
        coordinator.on_extraction_completed(0)
    
    def test_playback_settings(self, mock_main_window, mock_animation_controller):
        """Test playback settings methods."""
        coordinator = AnimationCoordinator(mock_main_window)
        coordinator.animation_controller = mock_animation_controller
        
        # Test set FPS
        coordinator.set_fps(30.0)
        mock_animation_controller.set_fps.assert_called_once_with(30.0)
        
        # Test set loop mode
        coordinator.set_loop_mode(True)
        mock_animation_controller.set_loop_mode.assert_called_once_with(True)
    
    def test_playback_settings_without_controller(self, mock_main_window):
        """Test playback settings without animation controller."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        # Should not raise errors
        coordinator.set_fps(30.0)
        coordinator.set_loop_mode(True)
    
    def test_state_queries(self, mock_main_window, mock_sprite_model, mock_animation_controller):
        """Test state query methods."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        # Test is_playing
        assert coordinator.is_playing() is False
        
        coordinator.animation_controller = mock_animation_controller
        mock_animation_controller.is_playing = True
        assert coordinator.is_playing() is True
        
        # Test get_current_frame
        assert coordinator.get_current_frame() == 0
        
        coordinator.sprite_model = mock_sprite_model
        assert coordinator.get_current_frame() == 2
        
        # Test get_frame_count
        assert coordinator.get_frame_count() == 5
        
        # Test with no frames
        mock_sprite_model.sprite_frames = []
        assert coordinator.get_frame_count() == 0
    
    def test_update_context(self, mock_main_window, mock_sprite_model,
                           mock_action_manager, mock_animation_controller):
        """Test _update_context method."""
        coordinator = AnimationCoordinator(mock_main_window)
        coordinator.sprite_model = mock_sprite_model
        coordinator.action_manager = mock_action_manager
        coordinator.animation_controller = mock_animation_controller
        coordinator.shortcut_manager = mock_main_window._shortcut_manager

        # Test context update
        coordinator._update_context()

        # Verify managers were updated
        mock_main_window._shortcut_manager.update_context.assert_called_once_with(
            has_frames=True,
            is_playing=False
        )
        mock_action_manager.update_context.assert_called_once_with(
            has_frames=True,
            is_playing=False
        )
    
    def test_update_context_without_managers(self, mock_main_window):
        """Test _update_context without managers."""
        coordinator = AnimationCoordinator(mock_main_window)
        
        # Should not raise error
        coordinator._update_context()


class TestAnimationCoordinatorIntegration:
    """Test AnimationCoordinator integration with sprite viewer."""
    
    def test_sprite_viewer_uses_animation_coordinator(self):
        """Test that SpriteViewer properly uses AnimationCoordinator."""
        from sprite_viewer import SpriteViewer
        
        # Check that SpriteViewer imports AnimationCoordinator
        init_code = SpriteViewer.__init__.__code__
        
        # Check for AnimationCoordinator usage
        assert 'AnimationCoordinator' in init_code.co_names or \
               '_animation_coordinator' in init_code.co_names
    
    def test_animation_coordinator_import(self):
        """Test that AnimationCoordinator can be imported correctly."""
        from coordinators import AnimationCoordinator as Coordinator
        from coordinators.animation_coordinator import AnimationCoordinator
        
        # Verify they're the same class
        assert Coordinator is AnimationCoordinator
    
    def test_animation_methods_removed_from_sprite_viewer(self):
        """Test that animation methods have been removed from SpriteViewer."""
        from sprite_viewer import SpriteViewer
        
        # These methods should no longer exist in SpriteViewer
        assert not hasattr(SpriteViewer, '_go_to_prev_frame')
        assert not hasattr(SpriteViewer, '_go_to_next_frame')
        assert not hasattr(SpriteViewer, '_go_to_first_frame')
        assert not hasattr(SpriteViewer, '_go_to_last_frame')
        assert not hasattr(SpriteViewer, '_on_playback_started')
        assert not hasattr(SpriteViewer, '_on_playback_paused')
        assert not hasattr(SpriteViewer, '_on_playback_stopped')
        assert not hasattr(SpriteViewer, '_on_playback_completed')
        assert not hasattr(SpriteViewer, '_on_frame_advanced')
        assert not hasattr(SpriteViewer, '_on_animation_error')