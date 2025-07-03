"""
View Coordinator for SpriteViewer refactoring.
Handles canvas display operations, zoom control, and view state management.
"""

from typing import Optional
from PySide6.QtCore import QObject

from .base import CoordinatorBase
from config import Config


class ViewCoordinator(CoordinatorBase):
    """
    Coordinator responsible for view and display operations.
    
    Manages zoom levels, grid display, and canvas view state.
    Extracts view control logic from SpriteViewer.
    """
    
    def __init__(self, main_window):
        """Initialize view coordinator."""
        super().__init__(main_window)
        
        # Component references
        self.canvas = None
        self.zoom_label = None
        
        # View state
        self._current_zoom = 1.0
        self._grid_enabled = False
    
    def initialize(self, dependencies):
        """
        Initialize coordinator with required dependencies.
        
        Args:
            dependencies: Dict containing:
                - canvas: SpriteCanvas instance
                - zoom_label: QLabel for zoom display
        """
        self.canvas = dependencies['canvas']
        self.zoom_label = dependencies.get('zoom_label')
        
        # Connect canvas signals
        if self.canvas:
            self.canvas.zoomChanged.connect(self._on_zoom_changed)
    
    def cleanup(self):
        """Clean up resources and disconnect signals."""
        if self.canvas:
            try:
                self.canvas.zoomChanged.disconnect(self._on_zoom_changed)
            except RuntimeError:
                # Signal might not be connected
                pass
    
    # ============================================================================
    # VIEW OPERATIONS
    # ============================================================================
    
    def zoom_in(self):
        """Zoom in on canvas."""
        if self.canvas:
            current_zoom = self.canvas.get_zoom_factor()
            from config import Config
            new_zoom = current_zoom * Config.Canvas.ZOOM_FACTOR
            self.canvas.set_zoom(new_zoom)
    
    def zoom_out(self):
        """Zoom out on canvas."""
        if self.canvas:
            current_zoom = self.canvas.get_zoom_factor()
            from config import Config
            new_zoom = current_zoom / Config.Canvas.ZOOM_FACTOR
            self.canvas.set_zoom(new_zoom)
    
    def zoom_fit(self):
        """Fit canvas to window."""
        if self.canvas:
            self.canvas.fit_to_window()
    
    def zoom_reset(self):
        """Reset canvas zoom to 100%."""
        if self.canvas:
            self.canvas.reset_view()
    
    def toggle_grid(self):
        """Toggle grid overlay."""
        if self.canvas:
            self._grid_enabled = not self._grid_enabled
            self.canvas.set_grid_overlay(self._grid_enabled)
    
    def reset_view(self):
        """Reset view to default state."""
        if self.canvas:
            self.canvas.reset_view()
            self.canvas.update()
    
    def update_canvas(self):
        """Update canvas display."""
        if self.canvas:
            self.canvas.update()
    
    def update_with_current_frame(self):
        """Update canvas with current frame."""
        if self.canvas:
            self.canvas.update_with_current_frame()
    
    def set_frame_info(self, frame_index: int, total_frames: int):
        """
        Update canvas frame info.
        
        Args:
            frame_index: Current frame index
            total_frames: Total number of frames
        """
        if self.canvas:
            self.canvas.set_frame_info(frame_index, total_frames)
    
    # ============================================================================
    # VIEW STATE
    # ============================================================================
    
    def get_current_zoom(self) -> float:
        """Get current zoom level."""
        return self._current_zoom
    
    def is_grid_enabled(self) -> bool:
        """Check if grid is enabled."""
        return self._grid_enabled
    
    # ============================================================================
    # SIGNAL HANDLERS
    # ============================================================================
    
    def _on_zoom_changed(self, zoom_factor: float):
        """
        Handle zoom change from canvas.
        
        Args:
            zoom_factor: New zoom factor
        """
        self._current_zoom = zoom_factor
        
        # Update zoom label if available
        if self.zoom_label:
            percentage = int(zoom_factor * 100)
            self.zoom_label.setText(f"{percentage}%")
    
    # ============================================================================
    # DRAG & DROP VISUAL FEEDBACK
    # ============================================================================
    
    def set_drag_hover_style(self, style: str):
        """
        Set canvas style for drag hover.
        
        Args:
            style: Style sheet string for drag hover
        """
        if self.canvas:
            self.canvas.setStyleSheet(style)
    
    def reset_canvas_style(self, style: str):
        """
        Reset canvas to normal style.
        
        Args:
            style: Style sheet string for normal state
        """
        if self.canvas:
            self.canvas.setStyleSheet(style)