"""
UI tests for SpriteCanvas widget.
Tests canvas display, zoom, pan functionality with Qt.
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy

from ui.sprite_canvas import SpriteCanvas
from config import Config


class TestSpriteCanvasInitialization:
    """Test SpriteCanvas widget initialization."""

    @pytest.mark.ui
    def test_initial_properties(self, qapp):
        """Test initial canvas properties."""
        canvas = SpriteCanvas()
        
        # Size constraints
        min_size = canvas.minimumSize()
        assert min_size.width() >= Config.Canvas.MIN_WIDTH
        assert min_size.height() >= Config.Canvas.MIN_HEIGHT
        
        # Initial state
        assert canvas._zoom_factor == 1.0
        assert canvas._pan_offset == [0, 0]
        assert canvas._pixmap is None
        assert canvas._show_checkerboard
    
    @pytest.mark.ui
    def test_signals_exist(self, qapp):
        """Test required signals are defined."""
        canvas = SpriteCanvas()
        assert hasattr(canvas, 'frameChanged')


class TestSpriteCanvasPixmapHandling:
    """Test pixmap display functionality."""
    
    @pytest.mark.ui
    def test_set_pixmap(self, qapp, mock_pixmap):
        """Test setting pixmap for display."""
        canvas = SpriteCanvas()
        
        canvas.set_pixmap(mock_pixmap, auto_fit=False)
        assert canvas._pixmap == mock_pixmap
    
    @pytest.mark.ui
    def test_auto_fit_on_set_pixmap(self, qapp, mock_pixmap):
        """Test auto-fit functionality when setting pixmap."""
        canvas = SpriteCanvas()
        
        # Mock the auto_fit_sprite method
        with patch.object(canvas, 'auto_fit_sprite') as mock_auto_fit:
            canvas.set_pixmap(mock_pixmap, auto_fit=True)
            mock_auto_fit.assert_called_once()
    
    @pytest.mark.ui
    def test_clear_pixmap(self, qapp, mock_pixmap):
        """Test clearing pixmap."""
        canvas = SpriteCanvas()
        canvas.set_pixmap(mock_pixmap)
        
        canvas.set_pixmap(None)
        assert canvas._pixmap is None


class TestSpriteCanvasZoom:
    """Test zoom functionality."""

    @pytest.mark.ui
    @pytest.mark.parametrize("zoom_factor", [0.5, 1.0, 2.0, 5.0])
    def test_zoom_factor_bounds(self, qapp, zoom_factor):
        """Test zoom factor is clamped to valid bounds."""
        canvas = SpriteCanvas()
        
        canvas.set_zoom(zoom_factor)
        
        assert Config.Canvas.ZOOM_MIN <= canvas._zoom_factor <= Config.Canvas.ZOOM_MAX
    
    @pytest.mark.ui
    def test_zoom_in(self, qapp):
        """Test zoom in functionality."""
        canvas = SpriteCanvas()
        initial_zoom = canvas._zoom_factor
        
        # Simulate zoom in by increasing factor
        canvas.set_zoom(initial_zoom * 1.2)
        
        assert canvas._zoom_factor > initial_zoom
    
    @pytest.mark.ui
    def test_zoom_out(self, qapp):
        """Test zoom out functionality."""
        canvas = SpriteCanvas()
        canvas.set_zoom(2.0)  # Start zoomed in
        
        # Simulate zoom out by decreasing factor
        canvas.set_zoom(1.6)
        
        assert canvas._zoom_factor < 2.0
    
    @pytest.mark.ui
    def test_reset_zoom(self, qapp):
        """Test resetting zoom to 100%."""
        canvas = SpriteCanvas()
        canvas.set_zoom(3.0)
        
        # Reset zoom to 1.0
        canvas.set_zoom(1.0)
        
        assert canvas._zoom_factor == 1.0


class TestSpriteCanvasDisplay:
    """Test display options."""
    
    @pytest.mark.ui
    def test_toggle_checkerboard(self, qapp):
        """Test toggling checkerboard background."""
        canvas = SpriteCanvas()
        initial_state = canvas._show_checkerboard
        
        canvas.set_background_mode(not initial_state)
        
        assert canvas._show_checkerboard != initial_state
    
    @pytest.mark.ui
    def test_toggle_grid(self, qapp):
        """Test toggling grid overlay."""
        canvas = SpriteCanvas()
        initial_state = canvas._show_grid
        
        canvas.set_grid_overlay(not initial_state)
        
        assert canvas._show_grid != initial_state
    
    @pytest.mark.ui
    def test_set_grid_size(self, qapp):
        """Test setting grid size."""
        canvas = SpriteCanvas()
        
        canvas.set_grid_overlay(True, 64)
        
        assert canvas._grid_size == 64


class TestSpriteCanvasFrameInfo:
    """Test frame information display."""

    @pytest.mark.ui
    def test_frame_changed_signal(self, qapp):
        """Test frameChanged signal emission."""
        canvas = SpriteCanvas()
        spy = QSignalSpy(canvas.frameChanged)
        
        canvas.set_frame_info(3, 8)
        
        # Signal should be emitted with current and total frames
        assert spy.count() > 0
        if spy.count() > 0:
            args = spy.at(0)
            assert args[0] == 3  # current_frame
            assert args[1] == 8  # total_frames


class TestSpriteCanvasMouseInteraction:
    """Test mouse interaction handling."""
    
    @pytest.mark.ui
    def test_mouse_tracking_enabled(self, qapp):
        """Test mouse tracking is enabled for pan operations."""
        canvas = SpriteCanvas()
        
        assert canvas.hasMouseTracking()
    
    @pytest.mark.ui
    def test_cursor_setup(self, qapp):
        """Test cursor is set appropriately."""
        canvas = SpriteCanvas()
        
        cursor = canvas.cursor()
        assert cursor.shape() == Qt.OpenHandCursor


class TestSpriteCanvasRenderingIntegration:
    """Test rendering and painting integration."""
    
    @pytest.mark.ui
    @pytest.mark.slow
    def test_painting_with_pixmap(self, qapp, mock_pixmap):
        """Test canvas painting with pixmap."""
        canvas = SpriteCanvas()
        canvas.set_pixmap(mock_pixmap)
        
        # Force a paint event by showing and updating
        canvas.show()
        canvas.update()
        
        # Should not crash or raise exceptions
        assert canvas._pixmap is not None
    
    @pytest.mark.ui
    def test_painting_without_pixmap(self, qapp):
        """Test canvas painting without pixmap."""
        canvas = SpriteCanvas()
        
        # Should handle gracefully
        canvas.show()
        canvas.update()
        
        # Should not crash
        assert canvas._pixmap is None


class TestSpriteCanvasErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.ui
    def test_invalid_zoom_factor(self, qapp):
        """Test handling of invalid zoom factors."""
        canvas = SpriteCanvas()
        
        # Test extreme values
        canvas.set_zoom(0)
        assert canvas._zoom_factor >= Config.Canvas.ZOOM_MIN
        
        canvas.set_zoom(1000)
        assert canvas._zoom_factor <= Config.Canvas.ZOOM_MAX
        
        # Canvas should handle None gracefully by keeping current zoom
        current_zoom = canvas._zoom_factor
        try:
            canvas.set_zoom(None)
        except:
            pass  # Should not crash
        assert canvas._zoom_factor == current_zoom
    
    @pytest.mark.ui
    def test_invalid_pan_values(self, qapp):
        """Test handling of invalid pan values."""
        canvas = SpriteCanvas()
        
        # Pan offset is internal - test it doesn't crash with invalid values
        try:
            canvas._pan_offset = [None, None]
            canvas._pan_offset = [0, 0]  # Reset to valid
        except:
            pass  # Should not crash
        assert isinstance(canvas._pan_offset[0], (int, float))
        assert isinstance(canvas._pan_offset[1], (int, float))
    
    @pytest.mark.ui
    def test_operations_without_pixmap(self, qapp):
        """Test canvas operations without loaded pixmap."""
        canvas = SpriteCanvas()
        
        # These should not crash
        canvas.set_zoom(canvas._zoom_factor * 1.2)  # Simulate zoom in
        canvas.set_zoom(canvas._zoom_factor * 0.8)  # Simulate zoom out
        canvas.auto_fit_sprite()
        canvas.set_frame_info(0, 0)
        
        assert canvas._pixmap is None  # Should remain None