"""
Unit tests for EventCoordinator (Phase 6 refactoring).
Tests the event coordinator that handles keyboard shortcuts and drag/drop events.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from coordinators import EventCoordinator


class TestEventCoordinator:
    """Test EventCoordinator functionality."""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create mock main window."""
        return Mock()
    
    @pytest.fixture
    def mock_shortcut_manager(self):
        """Create mock shortcut manager."""
        manager = Mock()
        manager.handle_key_press = Mock(return_value=True)
        manager.is_shortcut_enabled = Mock(return_value=True)
        return manager
    
    @pytest.fixture
    def mock_file_controller(self):
        """Create mock file controller."""
        controller = Mock()
        controller.is_valid_drop = Mock(return_value=True)
        controller.extract_file_from_drop = Mock(return_value="/test/file.png")
        controller.load_file = Mock()
        return controller
    
    @pytest.fixture
    def mock_canvas(self):
        """Create mock canvas."""
        canvas = Mock()
        canvas.setStyleSheet = Mock()
        return canvas
    
    @pytest.fixture
    def mock_status_manager(self):
        """Create mock status manager."""
        manager = Mock()
        manager.show_message = Mock()
        return manager

    def test_initialize_with_dependencies(self, mock_main_window, mock_shortcut_manager,
                                          mock_file_controller, mock_canvas,
                                          mock_status_manager):
        """Test initialization with dependencies."""
        coordinator = EventCoordinator(mock_main_window)

        welcome_callback = Mock()
        dependencies = {
            'shortcut_manager': mock_shortcut_manager,
            'file_controller': mock_file_controller,
            'canvas': mock_canvas,
            'status_manager': mock_status_manager,
            'show_welcome_message': welcome_callback
        }

        coordinator.initialize(dependencies)

        assert coordinator.shortcut_manager == mock_shortcut_manager
        assert coordinator.file_controller == mock_file_controller
        assert coordinator.canvas == mock_canvas
        assert coordinator.status_manager == mock_status_manager
        assert coordinator._show_welcome_message == welcome_callback
        assert coordinator.is_initialized
    
    def test_cleanup(self, mock_main_window):
        """Test cleanup method."""
        coordinator = EventCoordinator(mock_main_window)
        
        # Should not raise any errors
        coordinator.cleanup()
    
    def test_key_mapping_constants(self):
        """Test KEY_MAPPING constants."""
        assert EventCoordinator.KEY_MAPPING[Qt.Key_Space] == "Space"
        assert EventCoordinator.KEY_MAPPING[Qt.Key_Left] == "Left"
        assert EventCoordinator.KEY_MAPPING[Qt.Key_Right] == "Right"
        assert EventCoordinator.KEY_MAPPING[Qt.Key_Home] == "Home"
        assert EventCoordinator.KEY_MAPPING[Qt.Key_End] == "End"
        assert EventCoordinator.KEY_MAPPING[Qt.Key_Plus] == "+"
        assert EventCoordinator.KEY_MAPPING[Qt.Key_Minus] == "-"
    
    def test_handle_key_press_regular_key(self, mock_main_window, mock_shortcut_manager):
        """Test handling regular key presses."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.shortcut_manager = mock_shortcut_manager
        
        # Test regular key (A)
        result = coordinator.handle_key_press(Qt.Key_A, Qt.ControlModifier)
        
        assert result is True
        mock_shortcut_manager.handle_key_press.assert_called_once()
        call_args = mock_shortcut_manager.handle_key_press.call_args[0][0]
        # Should be something like "Ctrl+A"
        assert "A" in call_args
    
    def test_handle_key_press_special_key(self, mock_main_window, mock_shortcut_manager):
        """Test handling special key presses."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.shortcut_manager = mock_shortcut_manager
        
        # Test special key (Space)
        result = coordinator.handle_key_press(Qt.Key_Space, Qt.NoModifier)
        
        assert result is True
        mock_shortcut_manager.handle_key_press.assert_called_once_with("Space")
    
    def test_handle_key_press_with_modifiers(self, mock_main_window, mock_shortcut_manager):
        """Test handling key presses with modifiers."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.shortcut_manager = mock_shortcut_manager
        
        # Test special key with modifiers
        result = coordinator.handle_key_press(Qt.Key_Left, Qt.ControlModifier | Qt.ShiftModifier)
        
        assert result is True
        mock_shortcut_manager.handle_key_press.assert_called_once_with("Ctrl+Shift+Left")
    
    def test_handle_key_press_unknown_key(self, mock_main_window, mock_shortcut_manager):
        """Test handling unknown key presses."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.shortcut_manager = mock_shortcut_manager
        
        # Test unknown key
        result = coordinator.handle_key_press(Qt.Key_F13, Qt.NoModifier)
        
        assert result is False
        mock_shortcut_manager.handle_key_press.assert_not_called()
    
    def test_handle_key_press_without_manager(self, mock_main_window):
        """Test handling key press without shortcut manager."""
        coordinator = EventCoordinator(mock_main_window)
        
        result = coordinator.handle_key_press(Qt.Key_A, Qt.ControlModifier)
        
        assert result is False
    
    @patch('coordinators.event_coordinator.StyleManager')
    def test_handle_drag_enter(self, mock_style_manager, mock_main_window,
                               mock_file_controller, mock_canvas):
        """Test handling drag enter event."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.file_controller = mock_file_controller
        coordinator.canvas = mock_canvas

        # Mock event
        event = Mock()
        event.mimeData = Mock(return_value=Mock())
        event.acceptProposedAction = Mock()

        # Mock style manager
        mock_style_manager.get_canvas_drag_hover.return_value = "drag-hover-style"

        # Handle event
        coordinator.handle_drag_enter(event)

        # Verify
        mock_file_controller.is_valid_drop.assert_called_once()
        event.acceptProposedAction.assert_called_once()
        mock_canvas.setStyleSheet.assert_called_once_with("drag-hover-style")
    
    def test_handle_drag_enter_invalid_drop(self, mock_main_window, mock_file_controller):
        """Test handling drag enter with invalid drop."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.file_controller = mock_file_controller
        mock_file_controller.is_valid_drop.return_value = False
        
        # Mock event
        event = Mock()
        event.mimeData = Mock(return_value=Mock())
        event.acceptProposedAction = Mock()
        
        # Handle event
        coordinator.handle_drag_enter(event)
        
        # Verify
        event.acceptProposedAction.assert_not_called()
    
    @patch('coordinators.event_coordinator.StyleManager')
    def test_handle_drag_leave(self, mock_style_manager, mock_main_window,
                              mock_canvas):
        """Test handling drag leave event."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.canvas = mock_canvas
        welcome_callback = Mock()
        coordinator._show_welcome_message = welcome_callback

        # Mock style manager
        mock_style_manager.get_canvas_normal.return_value = "normal-style"

        # Handle event
        event = Mock()
        coordinator.handle_drag_leave(event)

        # Verify
        mock_canvas.setStyleSheet.assert_called_once_with("normal-style")
        welcome_callback.assert_called_once()
    
    @patch('coordinators.event_coordinator.StyleManager')
    def test_handle_drop(self, mock_style_manager, mock_main_window,
                        mock_file_controller, mock_canvas):
        """Test handling drop event."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.file_controller = mock_file_controller
        coordinator.canvas = mock_canvas

        # Mock event
        event = Mock()
        event.acceptProposedAction = Mock()

        # Mock style manager
        mock_style_manager.get_canvas_normal.return_value = "normal-style"

        # Handle event
        coordinator.handle_drop(event)

        # Verify
        mock_canvas.setStyleSheet.assert_called_once_with("normal-style")
        mock_file_controller.extract_file_from_drop.assert_called_once_with(event)
        mock_file_controller.load_file.assert_called_once_with("/test/file.png")
        event.acceptProposedAction.assert_called_once()
    
    def test_handle_drop_no_file(self, mock_main_window, mock_file_controller):
        """Test handling drop event with no file."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.file_controller = mock_file_controller
        mock_file_controller.extract_file_from_drop.return_value = None
        
        # Mock event
        event = Mock()
        event.acceptProposedAction = Mock()
        
        # Handle event
        coordinator.handle_drop(event)
        
        # Verify
        mock_file_controller.load_file.assert_not_called()
        event.acceptProposedAction.assert_not_called()
    
    def test_handle_grid_frame_selected(self, mock_main_window, mock_status_manager):
        """Test handling grid frame selection."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.status_manager = mock_status_manager
        
        coordinator.handle_grid_frame_selected(5)
        
        mock_status_manager.show_message.assert_called_once_with("Selected frame 5")
    
    def test_handle_grid_frame_preview(self, mock_main_window, mock_status_manager):
        """Test handling grid frame preview."""
        coordinator = EventCoordinator(mock_main_window)
        coordinator.status_manager = mock_status_manager
        
        coordinator.handle_grid_frame_preview(3)
        
        mock_status_manager.show_message.assert_called_once_with("Previewing frame 3")
    
    def test_is_shortcut_enabled(self, mock_main_window, mock_shortcut_manager):
        """Test checking if shortcut is enabled."""
        coordinator = EventCoordinator(mock_main_window)
        
        # Without manager
        assert coordinator.is_shortcut_enabled("Ctrl+S") is False
        
        # With manager
        coordinator.shortcut_manager = mock_shortcut_manager
        assert coordinator.is_shortcut_enabled("Ctrl+S") is True
        mock_shortcut_manager.is_shortcut_enabled.assert_called_once_with("Ctrl+S")


class TestEventCoordinatorIntegration:
    """Test EventCoordinator integration with sprite viewer."""
    
    def test_sprite_viewer_uses_event_coordinator(self):
        """Test that SpriteViewer properly uses EventCoordinator."""
        from sprite_viewer import SpriteViewer
        
        # Check that SpriteViewer imports EventCoordinator
        init_code = SpriteViewer.__init__.__code__
        
        # Check for EventCoordinator usage
        assert 'EventCoordinator' in init_code.co_names or \
               '_event_coordinator' in init_code.co_names
    
    def test_event_coordinator_import(self):
        """Test that EventCoordinator can be imported correctly."""
        from coordinators import EventCoordinator as Coordinator
        from coordinators.event_coordinator import EventCoordinator
        
        # Verify they're the same class
        assert Coordinator is EventCoordinator
    
    def test_event_methods_updated_in_sprite_viewer(self):
        """Test that event methods use EventCoordinator in SpriteViewer."""
        from sprite_viewer import SpriteViewer
        
        # These methods should still exist but use coordinator
        assert hasattr(SpriteViewer, 'dragEnterEvent')
        assert hasattr(SpriteViewer, 'dragLeaveEvent')
        assert hasattr(SpriteViewer, 'dropEvent')
        assert hasattr(SpriteViewer, 'keyPressEvent')
        
        # Key mapping should not exist anymore
        assert not hasattr(SpriteViewer, '_KEY_MAPPING')