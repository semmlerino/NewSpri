"""
Sprite Sheet Preview Widget - Visual Layout Preview System
Real-time visual preview of sprite sheet layouts with spacing and alignment.
Part of Phase 4: Enhanced Live Preview System implementation.
"""

import math
from typing import List, Optional, Tuple
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QCheckBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QFont, 
    QWheelEvent, QMouseEvent, QPaintEvent
)

from config import Config
from ..core.frame_exporter import SpriteSheetLayout


@dataclass
class PreviewSettings:
    """Configuration for preview rendering."""
    show_grid: bool = True
    show_measurements: bool = True
    show_sprite_borders: bool = True
    preview_quality: str = "balanced"  # "fast", "balanced", "high"
    max_preview_size: int = 400  # Maximum preview dimensions
    grid_color: Tuple[int, int, int, int] = (100, 100, 100, 128)
    spacing_color: Tuple[int, int, int, int] = (255, 0, 0, 80)
    padding_color: Tuple[int, int, int, int] = (0, 255, 0, 80)


class SpriteSheetPreviewCanvas(QWidget):
    """Core canvas widget that renders the sprite sheet preview."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sprites: List[QPixmap] = []
        self.layout: Optional[SpriteSheetLayout] = None
        self.preview_settings = PreviewSettings()
        
        # View state
        self._zoom_factor = 1.0
        self._pan_offset = [0, 0]
        self._last_mouse_pos = None
        self._dragging = False
        
        # Cached preview data
        self._preview_pixmap: Optional[QPixmap] = None
        self._preview_valid = False
        self._grid_dimensions = (0, 0)
        self._frame_size = (32, 32)  # Default frame size
        
        # Performance optimization
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._generate_preview)
        
        self.setMinimumSize(200, 150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        # Enable focus for keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
    
    def set_sprites(self, sprites: List[QPixmap]):
        """Set the sprites to preview."""
        self.sprites = sprites
        if sprites:
            self._frame_size = (sprites[0].width(), sprites[0].height())
        self._invalidate_preview()
    
    def set_layout(self, layout: SpriteSheetLayout):
        """Set the layout configuration."""
        self.layout = layout
        self._invalidate_preview()
    
    def set_preview_settings(self, settings: PreviewSettings):
        """Update preview settings."""
        self.preview_settings = settings
        self._invalidate_preview()
    
    def _invalidate_preview(self):
        """Mark preview as invalid and schedule update."""
        self._preview_valid = False
        self._update_timer.start(50)  # Debounce updates
    
    def _generate_preview(self):
        """Generate the preview pixmap with current settings."""
        if not self.sprites or not self.layout:
            self._preview_pixmap = None
            self.update()
            return
        
        try:
            # Calculate layout dimensions
            cols, rows = self._calculate_grid_layout()
            self._grid_dimensions = (cols, rows)
            
            # Calculate preview size
            frame_width, frame_height = self._frame_size
            spacing = self.layout.spacing
            padding = self.layout.padding
            
            # Calculate actual sprite sheet dimensions
            sheet_width = (cols * frame_width) + ((cols - 1) * spacing) + (2 * padding)
            sheet_height = (rows * frame_height) + ((rows - 1) * spacing) + (2 * padding)
            
            # Scale for preview if too large
            scale_factor = min(
                self.preview_settings.max_preview_size / max(sheet_width, 1),
                self.preview_settings.max_preview_size / max(sheet_height, 1),
                1.0  # Don't scale up
            )
            
            preview_width = int(sheet_width * scale_factor)
            preview_height = int(sheet_height * scale_factor)
            
            # Create preview pixmap
            self._preview_pixmap = QPixmap(preview_width, preview_height)
            self._preview_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(self._preview_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing,
                                self.preview_settings.preview_quality != "fast")
            
            # Draw background
            self._draw_background(painter, preview_width, preview_height, scale_factor)
            
            # Draw sprites
            self._draw_sprites(painter, cols, rows, scale_factor)
            
            # Draw overlays
            if self.preview_settings.show_grid:
                self._draw_grid(painter, cols, rows, scale_factor)
            
            if self.preview_settings.show_measurements:
                self._draw_measurements(painter, cols, rows, scale_factor)
            
            painter.end()
            self._preview_valid = True
            
        except Exception as e:
            print(f"Preview generation error: {e}")
            self._preview_pixmap = None
        
        self.update()
    
    def _calculate_grid_layout(self) -> Tuple[int, int]:
        """Calculate grid dimensions using layout configuration."""
        if not self.layout or not self.sprites:
            return (1, 1)
        
        frame_count = len(self.sprites)
        
        if self.layout.mode == 'custom':
            return (self.layout.custom_columns or 1, self.layout.custom_rows or 1)
        elif self.layout.mode == 'rows':
            max_cols = self.layout.max_columns or Config.Export.DEFAULT_MAX_COLUMNS
            cols = min(max_cols, frame_count)
            rows = math.ceil(frame_count / cols)
            return (cols, rows)
        elif self.layout.mode == 'columns':
            max_rows = self.layout.max_rows or Config.Export.DEFAULT_MAX_ROWS
            rows = min(max_rows, frame_count)
            cols = math.ceil(frame_count / rows)
            return (cols, rows)
        elif self.layout.mode == 'square':
            cols = math.ceil(math.sqrt(frame_count))
            rows = math.ceil(frame_count / cols)
            return (cols, rows)
        else:  # auto mode
            cols = math.ceil(math.sqrt(frame_count))
            rows = math.ceil(frame_count / cols)
            return (cols, rows)
    
    def _draw_background(self, painter: QPainter, width: int, height: int, scale: float):
        """Draw the background based on layout settings."""
        if not self.layout:
            return
        
        if self.layout.background_mode == 'transparent':
            # Draw checkerboard pattern for transparency visualization
            self._draw_transparency_checkerboard(painter, width, height)
            
        elif self.layout.background_mode == 'solid':
            r, g, b, a = self.layout.background_color
            painter.fillRect(0, 0, width, height, QColor(r, g, b, a))
            
        elif self.layout.background_mode == 'checkerboard':
            self._draw_checkerboard_background(painter, width, height, scale)
    
    def _draw_transparency_checkerboard(self, painter: QPainter, width: int, height: int):
        """Draw light checkerboard pattern for transparency visualization."""
        tile_size = 8
        light_color = QColor(240, 240, 240)
        dark_color = QColor(220, 220, 220)
        
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                tile_x = x // tile_size
                tile_y = y // tile_size
                is_light = (tile_x + tile_y) % 2 == 0
                color = light_color if is_light else dark_color
                painter.fillRect(x, y, tile_size, tile_size, color)
    
    def _draw_checkerboard_background(self, painter: QPainter, width: int, height: int, scale: float):
        """Draw checkerboard background pattern."""
        tile_size = max(1, int(Config.Export.CHECKERBOARD_TILE_SIZE * scale))
        light_color = QColor(*Config.Export.CHECKERBOARD_LIGHT_COLOR)
        dark_color = QColor(*Config.Export.CHECKERBOARD_DARK_COLOR)
        
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                tile_x = x // tile_size
                tile_y = y // tile_size
                is_light = (tile_x + tile_y) % 2 == 0
                color = light_color if is_light else dark_color
                painter.fillRect(x, y, tile_size, tile_size, color)
    
    def _draw_sprites(self, painter: QPainter, cols: int, rows: int, scale: float):
        """Draw sprites in their layout positions."""
        if not self.sprites or not self.layout:
            return
        
        frame_width, frame_height = self._frame_size
        scaled_frame_width = int(frame_width * scale)
        scaled_frame_height = int(frame_height * scale)
        scaled_spacing = int(self.layout.spacing * scale)
        scaled_padding = int(self.layout.padding * scale)
        
        for i, sprite in enumerate(self.sprites[:cols * rows]):
            row = i // cols
            col = i % cols
            
            # Calculate position
            x = scaled_padding + (col * (scaled_frame_width + scaled_spacing))
            y = scaled_padding + (row * (scaled_frame_height + scaled_spacing))
            
            # Scale sprite for preview
            if scale != 1.0:
                scaled_sprite = sprite.scaled(
                    scaled_frame_width, scaled_frame_height,
                    Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            else:
                scaled_sprite = sprite

            painter.drawPixmap(x, y, scaled_sprite)

            # Draw sprite border if enabled
            if self.preview_settings.show_sprite_borders:
                pen = QPen(QColor(100, 100, 100, 100))
                pen.setWidth(1)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(x, y, scaled_frame_width, scaled_frame_height)
    
    def _draw_grid(self, painter: QPainter, cols: int, rows: int, scale: float):
        """Draw grid lines and spacing visualization."""
        if not self.layout:
            return
        
        frame_width, frame_height = self._frame_size
        scaled_frame_width = int(frame_width * scale)
        scaled_frame_height = int(frame_height * scale)
        scaled_spacing = int(self.layout.spacing * scale)
        scaled_padding = int(self.layout.padding * scale)
        
        # Grid color
        grid_color = QColor(*self.preview_settings.grid_color)
        spacing_color = QColor(*self.preview_settings.spacing_color)
        padding_color = QColor(*self.preview_settings.padding_color)
        
        # Draw padding area
        if scaled_padding > 0:
            painter.setBrush(padding_color)
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Top padding
            painter.drawRect(0, 0, self._preview_pixmap.width(), scaled_padding)
            # Bottom padding  
            painter.drawRect(0, self._preview_pixmap.height() - scaled_padding,
                           self._preview_pixmap.width(), scaled_padding)
            # Left padding
            painter.drawRect(0, 0, scaled_padding, self._preview_pixmap.height())
            # Right padding
            painter.drawRect(self._preview_pixmap.width() - scaled_padding, 0,
                           scaled_padding, self._preview_pixmap.height())
        
        # Draw spacing areas
        if scaled_spacing > 0:
            painter.setBrush(spacing_color)
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Horizontal spacing
            for col in range(cols - 1):
                x = scaled_padding + (col + 1) * scaled_frame_width + col * scaled_spacing
                painter.drawRect(x, scaled_padding, scaled_spacing,
                               rows * scaled_frame_height + (rows - 1) * scaled_spacing)
            
            # Vertical spacing
            for row in range(rows - 1):
                y = scaled_padding + (row + 1) * scaled_frame_height + row * scaled_spacing
                painter.drawRect(scaled_padding, y,
                               cols * scaled_frame_width + (cols - 1) * scaled_spacing,
                               scaled_spacing)
        
        # Draw grid lines
        painter.setPen(QPen(grid_color, 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Vertical grid lines
        for col in range(cols + 1):
            x = scaled_padding + col * (scaled_frame_width + scaled_spacing)
            painter.drawLine(x, scaled_padding, x,
                           scaled_padding + rows * scaled_frame_height + (rows - 1) * scaled_spacing)
        
        # Horizontal grid lines
        for row in range(rows + 1):
            y = scaled_padding + row * (scaled_frame_height + scaled_spacing)
            painter.drawLine(scaled_padding, y,
                           scaled_padding + cols * scaled_frame_width + (cols - 1) * scaled_spacing, y)
    
    def _draw_measurements(self, painter: QPainter, cols: int, rows: int, scale: float):
        """Draw measurement indicators."""
        if not self.layout or scale < 0.3:  # Skip measurements if too small
            return
        
        font = QFont()
        font.setPointSize(max(8, int(10 * scale)))
        painter.setFont(font)
        painter.setPen(QPen(QColor(50, 50, 50, 200)))

        _frame_width, _frame_height = self._frame_size
        scaled_spacing = int(self.layout.spacing * scale)
        scaled_padding = int(self.layout.padding * scale)
        
        # Draw spacing measurements
        if self.layout.spacing > 0 and scaled_spacing > 15:
            spacing_text = f"{self.layout.spacing}px"
            painter.drawText(scaled_padding + scaled_spacing // 4, 
                           scaled_padding - 5, spacing_text)
        
        # Draw padding measurements
        if self.layout.padding > 0 and scaled_padding > 15:
            padding_text = f"{self.layout.padding}px"
            painter.drawText(5, scaled_padding // 2, padding_text)
    
    def paintEvent(self, event: QPaintEvent):
        """Paint the preview canvas."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        
        if not self._preview_valid:
            # Show loading state
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Generating preview...")
            return

        if not self._preview_pixmap:
            # Show empty state
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No sprites to preview")
            return
        
        # Calculate centered position with zoom and pan
        widget_center_x = self.width() // 2
        widget_center_y = self.height() // 2
        
        preview_width = int(self._preview_pixmap.width() * self._zoom_factor)
        preview_height = int(self._preview_pixmap.height() * self._zoom_factor)
        
        draw_x = widget_center_x - preview_width // 2 + self._pan_offset[0]
        draw_y = widget_center_y - preview_height // 2 + self._pan_offset[1]
        
        # Draw preview with zoom
        if self._zoom_factor == 1.0:
            painter.drawPixmap(draw_x, draw_y, self._preview_pixmap)
        else:
            scaled_preview = self._preview_pixmap.scaled(
                preview_width, preview_height,
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(draw_x, draw_y, scaled_preview)
        
        # Draw zoom indicator
        if self._zoom_factor != 1.0:
            zoom_text = f"Zoom: {self._zoom_factor:.1f}x"
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(10, 20, zoom_text)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom with mouse wheel."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom
            zoom_in = event.angleDelta().y() > 0
            zoom_factor = 1.1 if zoom_in else 0.9
            self._zoom_factor = max(0.1, min(5.0, self._zoom_factor * zoom_factor))
            self.update()
        else:
            # Pan
            delta_x = event.angleDelta().x() // 8
            delta_y = event.angleDelta().y() // 8
            self._pan_offset[0] += delta_x
            self._pan_offset[1] += delta_y
            self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for panning."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._last_mouse_pos = event.position().toPoint()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for panning."""
        if self._dragging and self._last_mouse_pos:
            current_pos = event.position().toPoint()
            delta_x = current_pos.x() - self._last_mouse_pos.x()
            delta_y = current_pos.y() - self._last_mouse_pos.y()
            
            self._pan_offset[0] += delta_x
            self._pan_offset[1] += delta_y
            self._last_mouse_pos = current_pos
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._last_mouse_pos = None
    
    def reset_view(self):
        """Reset zoom and pan to default."""
        self._zoom_factor = 1.0
        self._pan_offset = [0, 0]
        self.update()


class SpriteSheetPreviewWidget(QWidget):
    """Complete preview widget with canvas and controls."""
    
    previewUpdated = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = SpriteSheetPreviewCanvas()
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the preview widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Preview controls
        controls_layout = QHBoxLayout()
        
        # Grid toggle
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(True)
        controls_layout.addWidget(self.grid_checkbox)
        
        # Measurements toggle
        self.measurements_checkbox = QCheckBox("Show Measurements")
        self.measurements_checkbox.setChecked(True)
        controls_layout.addWidget(self.measurements_checkbox)
        
        controls_layout.addStretch()
        
        # Reset view button
        reset_button = QPushButton("Reset View")
        reset_button.setMaximumWidth(80)
        reset_button.clicked.connect(self.canvas.reset_view)
        controls_layout.addWidget(reset_button)
        
        layout.addLayout(controls_layout)
        
        # Preview canvas in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.canvas)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(scroll_area)
        
        # Info label
        self.info_label = QLabel("Select sprite sheet preset to see preview")
        self.info_label.setStyleSheet("color: #666; font-size: 11px; padding: 4px;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
    
    def _connect_signals(self):
        """Connect control signals."""
        self.grid_checkbox.toggled.connect(self._update_preview_settings)
        self.measurements_checkbox.toggled.connect(self._update_preview_settings)
    
    def _update_preview_settings(self):
        """Update preview settings based on controls."""
        settings = PreviewSettings(
            show_grid=self.grid_checkbox.isChecked(),
            show_measurements=self.measurements_checkbox.isChecked()
        )
        self.canvas.set_preview_settings(settings)
    
    def update_preview(self, sprites: List[QPixmap], layout: SpriteSheetLayout):
        """Update the preview with new sprites and layout."""
        if not sprites or not layout:
            self.info_label.setText("No sprites available for preview")
            return
        
        self.canvas.set_sprites(sprites)
        self.canvas.set_layout(layout)
        
        # Update info label
        cols, rows = self.canvas._calculate_grid_layout()
        spacing_text = f", {layout.spacing}px spacing" if layout.spacing > 0 else ""
        padding_text = f", {layout.padding}px padding" if layout.padding > 0 else ""
        
        info_text = f"Grid: {cols}×{rows} ({len(sprites)} sprites){spacing_text}{padding_text}"
        self.info_label.setText(info_text)
        
        self.previewUpdated.emit()
    
    def clear_preview(self):
        """Clear the preview."""
        self.canvas.set_sprites([])
        self.info_label.setText("Select sprite sheet preset to see preview")