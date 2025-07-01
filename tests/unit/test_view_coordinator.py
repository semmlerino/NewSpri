"""
Unit tests for ViewCoordinator (Phase 3 refactoring).
Tests the view coordinator that handles canvas display operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from coordinators import ViewCoordinator


class TestViewCoordinator:
    """Test ViewCoordinator functionality."""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create mock main window."""
        return Mock()
    
    @pytest.fixture
    def mock_canvas(self):
        """Create mock canvas with required methods."""
        canvas = Mock()
        canvas.zoom_in = Mock()
        canvas.zoom_out = Mock()
        canvas.fit_to_window = Mock()
        canvas.reset_view = Mock()
        canvas.toggle_grid = Mock()
        canvas.update = Mock()
        canvas.update_with_current_frame = Mock()
        canvas.set_frame_info = Mock()
        canvas.setStyleSheet = Mock()
        canvas.zoomChanged = MagicMock()  # Signal mock
        return canvas
    
    @pytest.fixture
    def mock_zoom_label(self):
        """Create mock zoom label."""
        label = Mock()
        label.setText = Mock()
        return label
    
    def test_initialization(self, mock_main_window):
        """Test ViewCoordinator initialization."""
        coordinator = ViewCoordinator(mock_main_window)
        
        assert coordinator.main_window == mock_main_window
        assert not coordinator.is_initialized
        assert coordinator.canvas is None
        assert coordinator.zoom_label is None
        assert coordinator._current_zoom == 1.0
        assert coordinator._grid_enabled is False
    
    def test_initialize_with_dependencies(self, mock_main_window, mock_canvas, mock_zoom_label):
        """Test initialization with dependencies."""
        coordinator = ViewCoordinator(mock_main_window)
        
        dependencies = {
            'canvas': mock_canvas,
            'zoom_label': mock_zoom_label
        }
        
        coordinator.initialize(dependencies)
        
        assert coordinator.canvas == mock_canvas
        assert coordinator.zoom_label == mock_zoom_label
        
        # Verify signal connection
        mock_canvas.zoomChanged.connect.assert_called_once()
    
    def test_cleanup(self, mock_main_window, mock_canvas):
        """Test cleanup method."""
        coordinator = ViewCoordinator(mock_main_window)
        coordinator.canvas = mock_canvas
        
        # Mock the signal disconnect
        mock_canvas.zoomChanged.disconnect = Mock()
        
        coordinator.cleanup()
        
        mock_canvas.zoomChanged.disconnect.assert_called_once()
    
    def test_cleanup_without_canvas(self, mock_main_window):
        """Test cleanup when canvas is None."""
        coordinator = ViewCoordinator(mock_main_window)
        
        # Should not raise any errors
        coordinator.cleanup()
    
    def test_zoom_operations(self, mock_main_window, mock_canvas):
        """Test zoom operations."""
        coordinator = ViewCoordinator(mock_main_window)
        coordinator.canvas = mock_canvas
        
        # Test zoom in
        coordinator.zoom_in()
        mock_canvas.zoom_in.assert_called_once()
        
        # Test zoom out
        coordinator.zoom_out()
        mock_canvas.zoom_out.assert_called_once()
        
        # Test zoom fit
        coordinator.zoom_fit()
        mock_canvas.fit_to_window.assert_called_once()
        
        # Test zoom reset
        coordinator.zoom_reset()
        mock_canvas.reset_view.assert_called_once()
    
    def test_toggle_grid(self, mock_main_window, mock_canvas):
        """Test grid toggle."""
        coordinator = ViewCoordinator(mock_main_window)
        coordinator.canvas = mock_canvas
        
        # Initial state
        assert coordinator._grid_enabled is False
        
        # Toggle grid
        coordinator.toggle_grid()
        mock_canvas.toggle_grid.assert_called_once()
        assert coordinator._grid_enabled is True
        
        # Toggle again
        coordinator.toggle_grid()
        assert mock_canvas.toggle_grid.call_count == 2
        assert coordinator._grid_enabled is False
    
    def test_view_operations(self, mock_main_window, mock_canvas):
        """Test view update operations."""
        coordinator = ViewCoordinator(mock_main_window)
        coordinator.canvas = mock_canvas
        
        # Test reset view
        coordinator.reset_view()
        mock_canvas.reset_view.assert_called_once()
        mock_canvas.update.assert_called_once()
        
        # Test update canvas
        coordinator.update_canvas()
        assert mock_canvas.update.call_count == 2
        
        # Test update with current frame
        coordinator.update_with_current_frame()
        mock_canvas.update_with_current_frame.assert_called_once()
    
    def test_set_frame_info(self, mock_main_window, mock_canvas):
        """Test setting frame info."""
        coordinator = ViewCoordinator(mock_main_window)
        coordinator.canvas = mock_canvas
        
        coordinator.set_frame_info(5, 10)
        mock_canvas.set_frame_info.assert_called_once_with(5, 10)
    
    def test_zoom_changed_handler(self, mock_main_window, mock_canvas, mock_zoom_label):
        """Test zoom change signal handler."""
        coordinator = ViewCoordinator(mock_main_window)
        coordinator.canvas = mock_canvas
        coordinator.zoom_label = mock_zoom_label
        
        # Simulate zoom change
        coordinator._on_zoom_changed(1.5)
        
        assert coordinator._current_zoom == 1.5
        mock_zoom_label.setText.assert_called_once_with("150%")
    
    def test_zoom_changed_without_label(self, mock_main_window, mock_canvas):
        """Test zoom change when zoom label is None."""
        coordinator = ViewCoordinator(mock_main_window)
        coordinator.canvas = mock_canvas
        
        # Should not raise error
        coordinator._on_zoom_changed(2.0)
        assert coordinator._current_zoom == 2.0
    
    def test_drag_drop_styles(self, mock_main_window, mock_canvas):
        """Test drag and drop style methods."""
        coordinator = ViewCoordinator(mock_main_window)
        coordinator.canvas = mock_canvas
        
        # Test drag hover style
        coordinator.set_drag_hover_style("hover-style")
        mock_canvas.setStyleSheet.assert_called_once_with("hover-style")
        
        # Test reset canvas style
        coordinator.reset_canvas_style("normal-style")
        mock_canvas.setStyleSheet.assert_called_with("normal-style")
    
    def test_state_getters(self, mock_main_window):
        """Test state getter methods."""
        coordinator = ViewCoordinator(mock_main_window)
        
        # Test initial states
        assert coordinator.get_current_zoom() == 1.0
        assert coordinator.is_grid_enabled() is False
        
        # Change states
        coordinator._current_zoom = 2.5
        coordinator._grid_enabled = True
        
        assert coordinator.get_current_zoom() == 2.5
        assert coordinator.is_grid_enabled() is True
    
    def test_operations_without_canvas(self, mock_main_window):
        """Test that operations handle None canvas gracefully."""
        coordinator = ViewCoordinator(mock_main_window)
        
        # All these should not raise errors
        coordinator.zoom_in()
        coordinator.zoom_out()
        coordinator.zoom_fit()
        coordinator.zoom_reset()
        coordinator.toggle_grid()
        coordinator.reset_view()
        coordinator.update_canvas()
        coordinator.update_with_current_frame()
        coordinator.set_frame_info(0, 0)
        coordinator.set_drag_hover_style("style")
        coordinator.reset_canvas_style("style")


class TestViewCoordinatorIntegration:
    """Test ViewCoordinator integration with sprite viewer."""
    
    def test_sprite_viewer_uses_view_coordinator(self):
        """Test that SpriteViewer properly uses ViewCoordinator."""
        from sprite_viewer import SpriteViewer
        
        # Check that SpriteViewer imports ViewCoordinator
        init_code = SpriteViewer.__init__.__code__
        
        # Check for ViewCoordinator usage
        assert 'ViewCoordinator' in init_code.co_names or \
               '_view_coordinator' in init_code.co_names
    
    def test_view_coordinator_import(self):
        """Test that ViewCoordinator can be imported correctly."""
        from coordinators import ViewCoordinator as Coordinator
        from coordinators.view_coordinator import ViewCoordinator
        
        # Verify they're the same class
        assert Coordinator is ViewCoordinator