#!/usr/bin/env python3
"""
Sprite Canvas Widget
Custom canvas widget for displaying sprites with zoom and pan capabilities.
Part of Python Sprite Viewer - Phase 5: UI Component Extraction.
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QFont

from config import Config
from styles import StyleManager


class SpriteCanvas(QLabel):
    """Custom canvas widget for displaying sprites with zoom and pan capabilities."""
    
    frameChanged = Signal(int, int)  # current_frame, total_frames
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(Config.Canvas.MIN_WIDTH, Config.Canvas.MIN_HEIGHT)
        self.setStyleSheet(StyleManager.get_canvas_normal())
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.OpenHandCursor)
        
        # Canvas properties
        self._pixmap = None
        self._zoom_factor = 1.0
        self._pan_offset = [0, 0]
        self._last_pan_point = None
        
        # Background settings
        self._show_checkerboard = True
        self._bg_color = Config.Canvas.DEFAULT_BG_COLOR
        self._show_grid = False
        self._grid_size = Config.Canvas.DEFAULT_GRID_SIZE
        
        # Frame info
        self._current_frame = 0
        self._total_frames = 0
        
        # Enable mouse tracking for pan
        self.setMouseTracking(True)
    
    def set_pixmap(self, pixmap: QPixmap, auto_fit=None):
        """Set the sprite pixmap to display."""
        self._pixmap = pixmap
        
        # Auto-fit if enabled in config (can be overridden by parameter)
        if auto_fit is None:
            auto_fit = Config.Canvas.AUTO_FIT_ON_LOAD
            
        if auto_fit and pixmap and not pixmap.isNull():
            self.auto_fit_sprite()
        else:
            self.update()
    
    def set_frame_info(self, current: int, total: int):
        """Update frame information."""
        self._current_frame = current
        self._total_frames = total
        self.frameChanged.emit(current, total)
    
    def set_zoom(self, factor: float):
        """Set zoom factor."""
        self._zoom_factor = max(Config.Canvas.ZOOM_MIN, min(Config.Canvas.ZOOM_MAX, factor))
        self.update()
    
    def reset_view(self):
        """Reset zoom and pan to default."""
        self._zoom_factor = 1.0
        self._pan_offset = Config.Canvas.DEFAULT_PAN_OFFSET.copy()
        self.update()
    
    def fit_to_window(self):
        """Zoom to fit the sprite in the window."""
        if not self._pixmap or self._pixmap.isNull():
            return
            
        self._zoom_factor = self._calculate_fit_zoom()
        self._pan_offset = Config.Canvas.DEFAULT_PAN_OFFSET.copy()
        self.update()
    
    def auto_fit_sprite(self):
        """Auto-fit sprite with smart minimum zoom for tiny sprites."""
        if not self._pixmap or self._pixmap.isNull():
            return
        
        pixmap_size = self._pixmap.size()
        
        # Apply minimum zoom for tiny sprites
        if (pixmap_size.width() < Config.Canvas.TINY_SPRITE_THRESHOLD or 
            pixmap_size.height() < Config.Canvas.TINY_SPRITE_THRESHOLD):
            min_zoom = Config.Canvas.MIN_DISPLAY_ZOOM
        else:
            min_zoom = Config.Canvas.ZOOM_MIN
        
        # Calculate fit-to-window zoom with tighter margin
        fit_zoom = self._calculate_fit_zoom(Config.Canvas.INITIAL_FIT_MARGIN)
        
        # Use the larger of minimum zoom or fit zoom
        self._zoom_factor = max(min_zoom, fit_zoom)
        self._pan_offset = Config.Canvas.DEFAULT_PAN_OFFSET.copy()
        self.update()
    
    def _calculate_fit_zoom(self, margin=None):
        """Calculate zoom factor to fit sprite in window."""
        if not self._pixmap or self._pixmap.isNull():
            return 1.0
            
        if margin is None:
            margin = Config.Canvas.ZOOM_FIT_MARGIN
            
        canvas_rect = self.rect()
        pixmap_size = self._pixmap.size()
        
        # Calculate scale to fit
        scale_x = canvas_rect.width() / pixmap_size.width()
        scale_y = canvas_rect.height() / pixmap_size.height()
        return min(scale_x, scale_y) * margin
    
    def get_zoom_factor(self):
        """Get current zoom factor."""
        return self._zoom_factor
    
    def set_background_mode(self, checkerboard: bool, color: QColor = None):
        """Set background display mode."""
        self._show_checkerboard = checkerboard
        if color:
            self._bg_color = color
        self.update()
    
    def set_grid_overlay(self, show: bool, size: int = Config.Canvas.DEFAULT_GRID_SIZE):
        """Toggle grid overlay."""
        self._show_grid = show
        self._grid_size = size
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event for rendering sprite with background and overlays."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)  # Pixel-perfect scaling
        
        rect = self.rect()
        
        # Draw background
        if self._show_checkerboard:
            self._draw_checkerboard(painter, rect)
        else:
            painter.fillRect(rect, self._bg_color)
        
        # Draw sprite if available
        if self._pixmap and not self._pixmap.isNull():
            scaled_size = self._pixmap.size() * self._zoom_factor
            
            # Center the sprite
            x = (rect.width() - scaled_size.width()) // 2 + self._pan_offset[0]
            y = (rect.height() - scaled_size.height()) // 2 + self._pan_offset[1]
            
            target_rect = QRect(x, y, scaled_size.width(), scaled_size.height())
            painter.drawPixmap(target_rect, self._pixmap)
            
            # Draw grid overlay if enabled
            if self._show_grid:
                self._draw_grid(painter, target_rect)
            
            # Draw frame info overlay
            self._draw_frame_info(painter, rect)
    
    def _draw_frame_info(self, painter: QPainter, rect: QRect):
        """Draw frame information overlay."""
        if self._total_frames <= 0:
            return
            
        # Create semi-transparent background
        info_rect = QRect(
            rect.width() - Config.Drawing.FRAME_INFO_MARGIN_RIGHT, 
            Config.Drawing.FRAME_INFO_MARGIN_TOP,
            Config.Drawing.FRAME_INFO_WIDTH, 
            Config.Drawing.FRAME_INFO_HEIGHT
        )
        painter.fillRect(info_rect, QColor(0, 0, 0, Config.Drawing.FRAME_INFO_BG_ALPHA))
        
        # Draw text
        painter.setPen(Config.Drawing.FRAME_INFO_TEXT_COLOR)
        font = QFont()
        font.setPointSize(Config.Font.FRAME_INFO_FONT_SIZE)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(info_rect, Qt.AlignCenter, f"Frame {self._current_frame + 1}/{self._total_frames}")
    
    def _draw_checkerboard(self, painter: QPainter, rect: QRect):
        """Draw checkerboard background pattern."""
        tile_size = Config.Drawing.CHECKERBOARD_TILE_SIZE
        light_color = Config.Drawing.CHECKERBOARD_LIGHT_COLOR
        dark_color = Config.Drawing.CHECKERBOARD_DARK_COLOR
        
        for y in range(0, rect.height(), tile_size):
            for x in range(0, rect.width(), tile_size):
                color = light_color if (x // tile_size + y // tile_size) % 2 == 0 else dark_color
                painter.fillRect(x, y, tile_size, tile_size, color)
    
    def _draw_grid(self, painter: QPainter, sprite_rect: QRect):
        """Draw grid overlay on sprite."""
        pen = QPen(Config.Drawing.GRID_COLOR)
        pen.setWidth(Config.Drawing.GRID_PEN_WIDTH)
        painter.setPen(pen)
        
        grid_size = self._grid_size * self._zoom_factor
        
        # Vertical lines
        x = sprite_rect.left()
        while x <= sprite_rect.right():
            painter.drawLine(x, sprite_rect.top(), x, sprite_rect.bottom())
            x += grid_size
        
        # Horizontal lines
        y = sprite_rect.top()
        while y <= sprite_rect.bottom():
            painter.drawLine(sprite_rect.left(), y, sprite_rect.right(), y)
            y += grid_size
    
    def mousePressEvent(self, event):
        """Handle mouse press for panning."""
        if event.button() == Qt.LeftButton:
            self._last_pan_point = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning."""
        if self._last_pan_point and (event.buttons() & Qt.LeftButton):
            delta = event.position().toPoint() - self._last_pan_point
            self._pan_offset[0] += delta.x()
            self._pan_offset[1] += delta.y()
            self._last_pan_point = event.position().toPoint()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            self._last_pan_point = None
            self.setCursor(Qt.OpenHandCursor)
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        zoom_in = delta > 0
        
        if zoom_in:
            self._zoom_factor *= Config.Canvas.ZOOM_FACTOR
        else:
            self._zoom_factor /= Config.Canvas.ZOOM_FACTOR
        
        self._zoom_factor = max(Config.Canvas.ZOOM_MIN, min(Config.Canvas.ZOOM_MAX, self._zoom_factor))
        self.update()


# Export for easy importing
__all__ = ['SpriteCanvas']