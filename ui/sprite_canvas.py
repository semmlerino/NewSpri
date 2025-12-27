#!/usr/bin/env python3
"""
Sprite Canvas Widget
Custom canvas widget for displaying sprites with zoom and pan capabilities.
Part of Python Sprite Viewer - Phase 5: UI Component Extraction.
"""

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel

from config import Config


class SpriteCanvas(QLabel):
    """Custom canvas widget for displaying sprites with zoom and pan capabilities."""

    frameChanged = Signal(int, int)  # current_frame, total_frames
    mouseMoved = Signal(int, int)  # mouse x, y coordinates in sprite space
    zoomChanged = Signal(float)  # zoom factor

    def __init__(self):
        super().__init__()
        self.setMinimumSize(Config.Canvas.MIN_WIDTH, Config.Canvas.MIN_HEIGHT)
        self.setStyleSheet(Config.Styles.CANVAS_NORMAL)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setContentsMargins(0, 0, 0, 0)

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

        # Cached checkerboard pattern (regenerated on resize)
        self._checkerboard_cache: QPixmap | None = None
        self._checkerboard_cache_size: tuple[int, int] = (0, 0)

        # Enable mouse tracking for pan and coordinate tracking
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

    def update(self, *args, **kwargs):
        """Standard update - just trigger repaint without fetching frame."""
        super().update(*args, **kwargs)

    def set_frame_info(self, current: int, total: int):
        """Update frame information."""
        self._current_frame = current
        self._total_frames = total
        self.frameChanged.emit(current, total)

    def set_zoom(self, factor: float):
        """Set zoom factor."""
        self._zoom_factor = max(Config.Canvas.ZOOM_MIN, min(Config.Canvas.ZOOM_MAX, factor))
        self.update()
        self.zoomChanged.emit(self._zoom_factor)

    def reset_view(self):
        """Reset zoom and pan to default."""
        self._zoom_factor = 1.0
        self._pan_offset = Config.Canvas.DEFAULT_PAN_OFFSET.copy()
        self.update()
        self.zoomChanged.emit(self._zoom_factor)

    def fit_to_window(self):
        """Zoom to fit the sprite in the window."""
        if not self._pixmap or self._pixmap.isNull():
            return

        self._zoom_factor = self._calculate_fit_zoom()
        self._pan_offset = Config.Canvas.DEFAULT_PAN_OFFSET.copy()
        self.update()
        self.zoomChanged.emit(self._zoom_factor)

    def auto_fit_sprite(self):
        """Auto-fit sprite with smart minimum zoom for tiny sprites."""
        if not self._pixmap or self._pixmap.isNull():
            return

        pixmap_size = self._pixmap.size()

        # Apply minimum zoom for tiny sprites
        if (
            pixmap_size.width() < Config.Canvas.TINY_SPRITE_THRESHOLD
            or pixmap_size.height() < Config.Canvas.TINY_SPRITE_THRESHOLD
        ):
            min_zoom = Config.Canvas.MIN_DISPLAY_ZOOM
        else:
            min_zoom = Config.Canvas.ZOOM_MIN

        # Calculate fit-to-window zoom with tighter margin
        fit_zoom = self._calculate_fit_zoom(Config.Canvas.INITIAL_FIT_MARGIN)

        # Use the larger of minimum zoom or fit zoom
        self._zoom_factor = max(min_zoom, fit_zoom)
        self._pan_offset = Config.Canvas.DEFAULT_PAN_OFFSET.copy()
        self.update()
        self.zoomChanged.emit(self._zoom_factor)

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

    def set_background_mode(self, checkerboard: bool, color: QColor | None = None):
        """Set background display mode."""
        self._show_checkerboard = checkerboard
        if color is not None:
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
        # Use antialiasing to prevent edge cutoff
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform, False
        )  # Keep pixel-perfect for sprites

        # Get the full widget rect
        rect = self.rect()

        # Ensure we're using the full widget area
        painter.setViewport(rect)
        painter.setWindow(rect)

        # Draw background
        if self._show_checkerboard:
            self._draw_checkerboard(painter, rect)
        else:
            painter.fillRect(rect, self._bg_color)

        # Draw sprite if available
        if self._pixmap and not self._pixmap.isNull():
            # Create a temporary pixmap with 1px border to prevent edge cutoff
            temp_pixmap = QPixmap(self._pixmap.width() + 2, self._pixmap.height() + 2)
            temp_pixmap.fill(Qt.GlobalColor.transparent)

            temp_painter = QPainter(temp_pixmap)
            temp_painter.drawPixmap(1, 1, self._pixmap)
            temp_painter.end()

            # Scale the temporary pixmap
            scaled_size = temp_pixmap.size() * self._zoom_factor

            # Center the sprite - use floating point for accuracy
            x = (rect.width() - scaled_size.width()) / 2.0 + self._pan_offset[0]
            y = (rect.height() - scaled_size.height()) / 2.0 + self._pan_offset[1]

            # Round to nearest pixel to avoid subpixel rendering issues
            x = round(x)
            y = round(y)

            # Draw the temporary pixmap (which includes padding)
            target_rect = QRect(x, y, scaled_size.width(), scaled_size.height())
            painter.drawPixmap(target_rect, temp_pixmap)

            # Draw grid overlay if enabled (adjust for padding)
            if self._show_grid:
                # Adjust grid rect to account for the 1px padding
                grid_rect = QRect(
                    target_rect.x() + int(self._zoom_factor),
                    target_rect.y() + int(self._zoom_factor),
                    int(self._pixmap.width() * self._zoom_factor),
                    int(self._pixmap.height() * self._zoom_factor),
                )
                self._draw_grid(painter, grid_rect)

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
            Config.Drawing.FRAME_INFO_HEIGHT,
        )
        painter.fillRect(info_rect, QColor(0, 0, 0, Config.Drawing.FRAME_INFO_BG_ALPHA))

        # Draw text
        painter.setPen(Config.Drawing.FRAME_INFO_TEXT_COLOR)
        font = QFont()
        font.setPointSize(Config.Font.FRAME_INFO_FONT_SIZE)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            info_rect,
            Qt.AlignmentFlag.AlignCenter,
            f"Frame {self._current_frame + 1}/{self._total_frames}",
        )

    def _draw_checkerboard(self, painter: QPainter, rect: QRect):
        """Draw checkerboard background pattern using cached pixmap."""
        current_size = (rect.width(), rect.height())

        # Regenerate cache if size changed
        if self._checkerboard_cache is None or self._checkerboard_cache_size != current_size:
            self._checkerboard_cache = self._generate_checkerboard(rect.width(), rect.height())
            self._checkerboard_cache_size = current_size

        # Draw cached checkerboard
        painter.drawPixmap(0, 0, self._checkerboard_cache)

    def _generate_checkerboard(self, width: int, height: int) -> QPixmap:
        """Generate checkerboard pattern pixmap."""
        tile_size = Config.Drawing.CHECKERBOARD_TILE_SIZE
        light_color = Config.Drawing.CHECKERBOARD_LIGHT_COLOR
        dark_color = Config.Drawing.CHECKERBOARD_DARK_COLOR

        pixmap = QPixmap(width, height)
        cache_painter = QPainter(pixmap)

        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                color = light_color if (x // tile_size + y // tile_size) % 2 == 0 else dark_color
                cache_painter.fillRect(x, y, tile_size, tile_size, color)

        cache_painter.end()
        return pixmap

    def _draw_grid(self, painter: QPainter, sprite_rect: QRect):
        """Draw grid overlay on sprite."""
        pen = QPen(Config.Drawing.GRID_COLOR)
        pen.setWidth(Config.Drawing.GRID_PEN_WIDTH)
        painter.setPen(pen)

        grid_size = self._grid_size * self._zoom_factor

        # Vertical lines
        x = sprite_rect.left()
        while x <= sprite_rect.right():
            painter.drawLine(int(x), sprite_rect.top(), int(x), sprite_rect.bottom())
            x += grid_size

        # Horizontal lines
        y = sprite_rect.top()
        while y <= sprite_rect.bottom():
            painter.drawLine(sprite_rect.left(), int(y), sprite_rect.right(), int(y))
            y += grid_size

    def mousePressEvent(self, event):
        """Handle mouse press for panning."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_pan_point = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """Handle mouse move for panning and coordinate tracking."""
        mouse_pos = event.position().toPoint()

        # Handle panning if left button is pressed
        if self._last_pan_point and (event.buttons() & Qt.MouseButton.LeftButton):
            delta = mouse_pos - self._last_pan_point
            self._pan_offset[0] += delta.x()
            self._pan_offset[1] += delta.y()
            self._last_pan_point = mouse_pos
            self.update()

        # Emit mouse coordinates in sprite space
        sprite_coords = self._screen_to_sprite_coords(mouse_pos)
        if sprite_coords:
            self.mouseMoved.emit(sprite_coords[0], sprite_coords[1])

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_pan_point = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        zoom_in = delta > 0

        if zoom_in:
            self._zoom_factor *= Config.Canvas.ZOOM_FACTOR
        else:
            self._zoom_factor /= Config.Canvas.ZOOM_FACTOR

        self._zoom_factor = max(
            Config.Canvas.ZOOM_MIN, min(Config.Canvas.ZOOM_MAX, self._zoom_factor)
        )
        self.update()

        # Emit zoom change signal
        self.zoomChanged.emit(self._zoom_factor)

    def _screen_to_sprite_coords(self, screen_pos):
        """
        Convert screen coordinates to sprite coordinates.

        Args:
            screen_pos: QPoint with screen coordinates

        Returns:
            Tuple of (x, y) sprite coordinates, or None if outside sprite
        """
        if not self._pixmap:
            return None

        # Get widget dimensions
        widget_rect = self.rect()

        # Calculate sprite rectangle on screen
        pixmap_size = self._pixmap.size()
        scaled_width = pixmap_size.width() * self._zoom_factor
        scaled_height = pixmap_size.height() * self._zoom_factor

        # Calculate sprite position with pan offset
        sprite_x = (widget_rect.width() - scaled_width) // 2 + self._pan_offset[0]
        sprite_y = (widget_rect.height() - scaled_height) // 2 + self._pan_offset[1]

        # Check if mouse is within sprite bounds
        sprite_rect = QRect(int(sprite_x), int(sprite_y), int(scaled_width), int(scaled_height))
        if not sprite_rect.contains(screen_pos):
            return None

        # Convert to sprite coordinates
        relative_x = screen_pos.x() - sprite_x
        relative_y = screen_pos.y() - sprite_y

        # Scale back to original sprite coordinates
        sprite_coord_x = int(relative_x / self._zoom_factor)
        sprite_coord_y = int(relative_y / self._zoom_factor)

        # Ensure coordinates are within sprite bounds
        if 0 <= sprite_coord_x < pixmap_size.width() and 0 <= sprite_coord_y < pixmap_size.height():
            return (sprite_coord_x, sprite_coord_y)

        return None


# Export for easy importing
__all__ = ["SpriteCanvas"]
