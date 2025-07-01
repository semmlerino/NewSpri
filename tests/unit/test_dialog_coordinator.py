"""
Unit tests for DialogCoordinator (Phase 7 refactoring).
Tests the dialog coordinator that handles help and information dialogs.
"""

import pytest
from unittest.mock import Mock, patch
from coordinators import DialogCoordinator


class TestDialogCoordinator:
    """Test DialogCoordinator functionality."""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create mock main window."""
        return Mock()
    
    @pytest.fixture
    def mock_shortcut_manager(self):
        """Create mock shortcut manager."""
        manager = Mock()
        manager.generate_help_html = Mock(return_value="<html>Help content</html>")
        return manager
    
    def test_initialization(self, mock_main_window):
        """Test DialogCoordinator initialization."""
        coordinator = DialogCoordinator(mock_main_window)
        
        assert coordinator.main_window == mock_main_window
        assert not coordinator.is_initialized
        assert coordinator.shortcut_manager is None
    
    def test_initialize_with_dependencies(self, mock_main_window, mock_shortcut_manager):
        """Test initialization with dependencies."""
        coordinator = DialogCoordinator(mock_main_window)
        
        dependencies = {
            'shortcut_manager': mock_shortcut_manager
        }
        
        coordinator.initialize(dependencies)
        
        assert coordinator.shortcut_manager == mock_shortcut_manager
        assert coordinator.is_initialized
    
    def test_cleanup(self, mock_main_window):
        """Test cleanup method."""
        coordinator = DialogCoordinator(mock_main_window)
        
        # Should not raise any errors
        coordinator.cleanup()
    
    @patch('coordinators.dialog_coordinator.QMessageBox')
    def test_show_shortcuts(self, mock_msgbox, mock_main_window, mock_shortcut_manager):
        """Test showing shortcuts dialog."""
        coordinator = DialogCoordinator(mock_main_window)
        coordinator.shortcut_manager = mock_shortcut_manager
        
        coordinator.show_shortcuts()
        
        mock_shortcut_manager.generate_help_html.assert_called_once()
        mock_msgbox.information.assert_called_once_with(
            mock_main_window, 
            "Keyboard Shortcuts", 
            "<html>Help content</html>"
        )
    
    @patch('coordinators.dialog_coordinator.QMessageBox')
    def test_show_shortcuts_without_manager(self, mock_msgbox, mock_main_window):
        """Test showing shortcuts without shortcut manager."""
        coordinator = DialogCoordinator(mock_main_window)
        
        coordinator.show_shortcuts()
        
        mock_msgbox.warning.assert_called_once_with(
            mock_main_window,
            "Error",
            "Shortcut manager not available"
        )
    
    @patch('coordinators.dialog_coordinator.QMessageBox')
    def test_show_about(self, mock_msgbox, mock_main_window):
        """Test showing about dialog."""
        coordinator = DialogCoordinator(mock_main_window)
        
        coordinator.show_about()
        
        mock_msgbox.about.assert_called_once()
        call_args = mock_msgbox.about.call_args
        assert call_args[0][0] == mock_main_window
        assert call_args[0][1] == "About Sprite Viewer"
        assert "Python Sprite Viewer" in call_args[0][2]
        assert "Version 2.0 (Refactored)" in call_args[0][2]
    
    @patch('coordinators.dialog_coordinator.QMessageBox')
    def test_show_error(self, mock_msgbox, mock_main_window):
        """Test showing error dialog."""
        coordinator = DialogCoordinator(mock_main_window)
        
        coordinator.show_error("Test Error", "This is an error message")
        
        mock_msgbox.critical.assert_called_once_with(
            mock_main_window,
            "Test Error",
            "This is an error message"
        )
    
    @patch('coordinators.dialog_coordinator.QMessageBox')
    def test_show_warning(self, mock_msgbox, mock_main_window):
        """Test showing warning dialog."""
        coordinator = DialogCoordinator(mock_main_window)
        
        coordinator.show_warning("Test Warning", "This is a warning message")
        
        mock_msgbox.warning.assert_called_once_with(
            mock_main_window,
            "Test Warning",
            "This is a warning message"
        )
    
    @patch('coordinators.dialog_coordinator.QMessageBox')
    def test_show_info(self, mock_msgbox, mock_main_window):
        """Test showing info dialog."""
        coordinator = DialogCoordinator(mock_main_window)
        
        coordinator.show_info("Test Info", "This is an info message")
        
        mock_msgbox.information.assert_called_once_with(
            mock_main_window,
            "Test Info",
            "This is an info message"
        )


class TestDialogCoordinatorIntegration:
    """Test DialogCoordinator integration with sprite viewer."""
    
    def test_sprite_viewer_uses_dialog_coordinator(self):
        """Test that SpriteViewer properly uses DialogCoordinator."""
        from sprite_viewer import SpriteViewer
        
        # Check that SpriteViewer imports DialogCoordinator
        init_code = SpriteViewer.__init__.__code__
        
        # Check for DialogCoordinator usage
        assert 'DialogCoordinator' in init_code.co_names or \
               '_dialog_coordinator' in init_code.co_names
    
    def test_dialog_coordinator_import(self):
        """Test that DialogCoordinator can be imported correctly."""
        from coordinators import DialogCoordinator as Coordinator
        from coordinators.dialog_coordinator import DialogCoordinator
        
        # Verify they're the same class
        assert Coordinator is DialogCoordinator
    
    def test_dialog_methods_removed_from_sprite_viewer(self):
        """Test that dialog methods are removed from SpriteViewer."""
        from sprite_viewer import SpriteViewer
        
        # These methods should not exist anymore
        assert not hasattr(SpriteViewer, '_show_shortcuts')
        assert not hasattr(SpriteViewer, '_show_about')