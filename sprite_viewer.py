#!/usr/bin/env python3
"""
Python Sprite Viewer
A lightweight PySide6-based application for previewing sprite sheet animations.
"""

import sys
import os
import math
from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QPushButton, QSpinBox, QCheckBox, QFileDialog,
    QScrollArea, QGroupBox, QColorDialog, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QAction, QDragEnterEvent, QDropEvent


class SpriteCanvas(QLabel):
    """Custom canvas widget for displaying sprites with zoom and pan capabilities."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setStyleSheet("border: 1px solid gray;")
        self.setAlignment(Qt.AlignCenter)
        
        # Canvas properties
        self._pixmap = None
        self._zoom_factor = 1.0
        self._pan_offset = [0, 0]
        self._last_pan_point = None
        
        # Background settings
        self._show_checkerboard = True
        self._bg_color = QColor(128, 128, 128)
        self._show_grid = False
        self._grid_size = 32
        
        # Enable mouse tracking for pan
        self.setMouseTracking(True)
    
    def set_pixmap(self, pixmap: QPixmap):
        """Set the sprite pixmap to display."""
        self._pixmap = pixmap
        self.update()
    
    def set_zoom(self, factor: float):
        """Set zoom factor."""
        self._zoom_factor = max(0.1, min(10.0, factor))
        self.update()
    
    def set_background_mode(self, checkerboard: bool, color: QColor = None):
        """Set background display mode."""
        self._show_checkerboard = checkerboard
        if color:
            self._bg_color = color
        self.update()
    
    def set_grid_overlay(self, show: bool, size: int = 32):
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
    
    def _draw_checkerboard(self, painter: QPainter, rect: QRect):
        """Draw checkerboard background pattern."""
        tile_size = 16
        light_color = QColor(255, 255, 255)
        dark_color = QColor(192, 192, 192)
        
        for y in range(0, rect.height(), tile_size):
            for x in range(0, rect.width(), tile_size):
                color = light_color if (x // tile_size + y // tile_size) % 2 == 0 else dark_color
                painter.fillRect(x, y, tile_size, tile_size, color)
    
    def _draw_grid(self, painter: QPainter, sprite_rect: QRect):
        """Draw grid overlay on sprite."""
        pen = QPen(QColor(255, 0, 0, 128))
        pen.setWidth(1)
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
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        zoom_in = delta > 0
        
        if zoom_in:
            self._zoom_factor *= 1.2
        else:
            self._zoom_factor /= 1.2
        
        self._zoom_factor = max(0.1, min(10.0, self._zoom_factor))
        self.update()


class SpriteViewer(QMainWindow):
    """Main sprite viewer application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Sprite Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        # Sprite data
        self._sprite_frames: List[QPixmap] = []
        self._current_frame = 0
        self._is_playing = False
        self._loop_enabled = True
        self._original_sprite_sheet: Optional[QPixmap] = None
        
        # Animation timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._next_frame)
        self._fps = 10
        
        # UI setup
        self._setup_ui()
        self._setup_menu()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Load test sprites if available
        self._load_test_sprites()
    
    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Canvas
        canvas_layout = QVBoxLayout()
        
        # Canvas
        self._canvas = SpriteCanvas()
        canvas_layout.addWidget(self._canvas)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        
        self._zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_slider.setRange(10, 1000)  # 0.1x to 10x
        self._zoom_slider.setValue(100)  # 1x
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)
        zoom_layout.addWidget(self._zoom_slider)
        
        self._zoom_label = QLabel("100%")
        zoom_layout.addWidget(self._zoom_label)
        
        canvas_layout.addLayout(zoom_layout)
        main_layout.addLayout(canvas_layout, 3)
        
        # Right panel - Controls
        controls_layout = QVBoxLayout()
        
        # File controls
        file_group = QGroupBox("File")
        file_layout = QVBoxLayout(file_group)
        
        self._load_button = QPushButton("Load Sprites...")
        self._load_button.clicked.connect(self._load_sprites)
        file_layout.addWidget(self._load_button)
        
        controls_layout.addWidget(file_group)
        
        # Frame slicing controls
        slice_group = QGroupBox("Frame Slicing")
        slice_layout = QVBoxLayout(slice_group)
        
        # Frame dimensions
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(QLabel("Frame Size:"))
        
        self._frame_width = QSpinBox()
        self._frame_width.setRange(1, 1024)
        self._frame_width.setValue(192)  # 3×64 tiles
        self._frame_width.valueChanged.connect(self._update_frame_slicing)
        dim_layout.addWidget(self._frame_width)
        
        dim_layout.addWidget(QLabel("x"))
        
        self._frame_height = QSpinBox()
        self._frame_height.setRange(1, 1024)
        self._frame_height.setValue(192)  # 3×64 tiles
        self._frame_height.valueChanged.connect(self._update_frame_slicing)
        dim_layout.addWidget(self._frame_height)
        
        slice_layout.addLayout(dim_layout)
        
        # Margins/Offset
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Offset:"))
        
        self._margin_x = QSpinBox()
        self._margin_x.setRange(0, 500)
        self._margin_x.setValue(0)  # Better default for complete sprites
        self._margin_x.valueChanged.connect(self._update_frame_slicing)
        margin_layout.addWidget(self._margin_x)
        
        margin_layout.addWidget(QLabel(","))
        
        self._margin_y = QSpinBox()
        self._margin_y.setRange(0, 500)
        self._margin_y.setValue(0)  # Better default for complete sprites
        self._margin_y.valueChanged.connect(self._update_frame_slicing)
        margin_layout.addWidget(self._margin_y)
        
        slice_layout.addLayout(margin_layout)
        
        # Grid settings
        self._grid_checkbox = QCheckBox("Show Grid")
        self._grid_checkbox.toggled.connect(self._toggle_grid)
        slice_layout.addWidget(self._grid_checkbox)
        
        controls_layout.addWidget(slice_group)
        
        # Playback controls
        playback_group = QGroupBox("Playback")
        playback_layout = QVBoxLayout(playback_group)
        
        # Play/Pause button
        self._play_button = QPushButton("Play")
        self._play_button.clicked.connect(self._toggle_playback)
        playback_layout.addWidget(self._play_button)
        
        # FPS control
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        
        self._fps_slider = QSlider(Qt.Horizontal)
        self._fps_slider.setRange(1, 60)
        self._fps_slider.setValue(10)
        self._fps_slider.valueChanged.connect(self._on_fps_changed)
        fps_layout.addWidget(self._fps_slider)
        
        self._fps_label = QLabel("10")
        fps_layout.addWidget(self._fps_label)
        
        playback_layout.addLayout(fps_layout)
        
        # Loop toggle
        self._loop_checkbox = QCheckBox("Loop")
        self._loop_checkbox.setChecked(True)
        self._loop_checkbox.toggled.connect(self._toggle_loop)
        playback_layout.addWidget(self._loop_checkbox)
        
        # Frame counter
        self._frame_label = QLabel("Frame: 0/0")
        playback_layout.addWidget(self._frame_label)
        
        controls_layout.addWidget(playback_group)
        
        # Background controls
        bg_group = QGroupBox("Background")
        bg_layout = QVBoxLayout(bg_group)
        
        self._bg_combo = QComboBox()
        self._bg_combo.addItems(["Checkerboard", "Solid Color"])
        self._bg_combo.currentTextChanged.connect(self._change_background)
        bg_layout.addWidget(self._bg_combo)
        
        self._color_button = QPushButton("Choose Color")
        self._color_button.clicked.connect(self._choose_background_color)
        self._color_button.setEnabled(False)
        bg_layout.addWidget(self._color_button)
        
        controls_layout.addWidget(bg_group)
        
        # Preset frame sizes
        preset_group = QGroupBox("Quick Presets")
        preset_layout = QHBoxLayout(preset_group)
        
        preset_2x2_btn = QPushButton("128×128")
        preset_2x2_btn.clicked.connect(lambda: self._set_frame_size(128, 128))
        preset_layout.addWidget(preset_2x2_btn)
        
        preset_single_btn = QPushButton("64×64")
        preset_single_btn.clicked.connect(lambda: self._set_frame_size(64, 64))
        preset_layout.addWidget(preset_single_btn)
        
        preset_192_btn = QPushButton("192×192")
        preset_192_btn.clicked.connect(lambda: self._set_frame_size(192, 192))
        preset_layout.addWidget(preset_192_btn)
        
        controls_layout.addWidget(preset_group)
        
        # Auto-detect margins button
        auto_detect_button = QPushButton("Auto-Detect Margins")
        auto_detect_button.clicked.connect(self._auto_detect_margins)
        controls_layout.addWidget(auto_detect_button)
        
        # Add stretch to push controls to top
        controls_layout.addStretch()
        
        main_layout.addLayout(controls_layout, 1)
    
    def _setup_menu(self):
        """Set up menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._load_sprites)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        grid_action = QAction("Toggle Grid", self)
        grid_action.setShortcut("G")
        grid_action.triggered.connect(self._toggle_grid)
        view_menu.addAction(grid_action)
        
        # Playback menu
        playback_menu = menubar.addMenu("Playback")
        
        play_action = QAction("Play/Pause", self)
        play_action.setShortcut("Space")
        play_action.triggered.connect(self._toggle_playback)
        playback_menu.addAction(play_action)
    
    def _load_sprites(self):
        """Load sprite files or sprite sheet."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Load Sprites", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        
        if file_path:
            self._load_sprite_sheet(file_path)
    
    def _load_sprite_sheet(self, file_path: str):
        """Load and slice a sprite sheet."""
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return
        
        # Store original sprite sheet for re-slicing
        self._original_sprite_sheet = pixmap
        
        # Slice the sprite sheet into individual frames
        self._slice_sprite_sheet()
        
        # Reset to first frame
        self._current_frame = 0
        self._update_display()
    
    def _load_test_sprites(self):
        """Load test sprites from Archer folder if available."""
        archer_dir = Path("Archer")
        if archer_dir.exists():
            sprite_files = list(archer_dir.glob("*.png"))
            if sprite_files:
                # Load first sprite as test
                self._load_sprite_sheet(str(sprite_files[0]))
    
    def _slice_sprite_sheet(self):
        """Slice the original sprite sheet into individual frames."""
        if not self._original_sprite_sheet:
            return
        
        frame_width = self._frame_width.value()
        frame_height = self._frame_height.value()
        margin_x = self._margin_x.value()
        margin_y = self._margin_y.value()
        
        sheet_width = self._original_sprite_sheet.width()
        sheet_height = self._original_sprite_sheet.height()
        
        # Calculate available area after margins
        available_width = sheet_width - margin_x
        available_height = sheet_height - margin_y
        
        # Calculate how many frames fit in the available area
        frames_per_row = available_width // frame_width
        frames_per_col = available_height // frame_height
        
        # Extract individual frames starting from margin offset
        self._sprite_frames = []
        for row in range(frames_per_col):
            for col in range(frames_per_row):
                x = margin_x + (col * frame_width)
                y = margin_y + (row * frame_height)
                
                # Extract frame from sprite sheet
                frame_rect = QRect(x, y, frame_width, frame_height)
                frame = self._original_sprite_sheet.copy(frame_rect)
                
                if not frame.isNull():
                    self._sprite_frames.append(frame)
    
    def _update_frame_slicing(self):
        """Update frame slicing based on current settings."""
        if not self._original_sprite_sheet:
            return
        
        # Re-slice the sprite sheet with new dimensions
        self._slice_sprite_sheet()
        
        # Reset to first frame if current frame is out of bounds
        if self._current_frame >= len(self._sprite_frames):
            self._current_frame = 0
        
        # Update display and grid
        self._update_display()
        frame_width = self._frame_width.value()
        frame_height = self._frame_height.value()
        grid_size = max(frame_width, frame_height)
        self._canvas.set_grid_overlay(self._grid_checkbox.isChecked(), grid_size)
    
    def _update_display(self):
        """Update the canvas display."""
        if self._sprite_frames and 0 <= self._current_frame < len(self._sprite_frames):
            self._canvas.set_pixmap(self._sprite_frames[self._current_frame])
            self._frame_label.setText(f"Frame: {self._current_frame + 1}/{len(self._sprite_frames)}")
        else:
            self._canvas.set_pixmap(QPixmap())
            self._frame_label.setText("Frame: 0/0")
    
    def _toggle_playback(self):
        """Toggle animation playback."""
        if self._is_playing:
            self._timer.stop()
            self._play_button.setText("Play")
            self._is_playing = False
        else:
            if self._sprite_frames:
                self._timer.start(1000 // self._fps)
                self._play_button.setText("Pause")
                self._is_playing = True
    
    def _next_frame(self):
        """Advance to next frame."""
        if not self._sprite_frames:
            return
        
        self._current_frame += 1
        
        if self._current_frame >= len(self._sprite_frames):
            if self._loop_enabled:
                self._current_frame = 0
            else:
                self._current_frame = len(self._sprite_frames) - 1
                self._toggle_playback()  # Stop playback
        
        self._update_display()
    
    def _toggle_loop(self, enabled: bool):
        """Toggle loop mode."""
        self._loop_enabled = enabled
    
    def _toggle_grid(self):
        """Toggle grid overlay."""
        checked = self._grid_checkbox.isChecked()
        self._canvas.set_grid_overlay(checked, max(self._frame_width.value(), self._frame_height.value()))
    
    def _on_zoom_changed(self, value: int):
        """Handle zoom slider change."""
        zoom_factor = value / 100.0
        self._canvas.set_zoom(zoom_factor)
        self._zoom_label.setText(f"{value}%")
    
    def _on_fps_changed(self, value: int):
        """Handle FPS slider change."""
        self._fps = value
        self._fps_label.setText(str(value))
        
        if self._is_playing:
            self._timer.setInterval(1000 // self._fps)
    
    def _change_background(self, bg_type: str):
        """Change background type."""
        if bg_type == "Checkerboard":
            self._canvas.set_background_mode(True)
            self._color_button.setEnabled(False)
        else:
            self._canvas.set_background_mode(False)
            self._color_button.setEnabled(True)
    
    def _choose_background_color(self):
        """Choose background color."""
        color = QColorDialog.getColor(Qt.gray, self)
        if color.isValid():
            self._canvas.set_background_mode(False, color)
    
    def _auto_detect_margins(self):
        """Auto-detect margins by analyzing sprite sheet content."""
        if not self._original_sprite_sheet:
            return
        
        # Convert to QImage for pixel analysis
        image = self._original_sprite_sheet.toImage()
        width = image.width()
        height = image.height()
        
        # Detect left margin
        left_margin = 0
        for x in range(width):
            has_content = False
            for y in range(height):
                pixel = image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                if alpha > 10:  # Non-transparent pixel (with small threshold)
                    has_content = True
                    break
            if has_content:
                break
            left_margin += 1
        
        # Detect top margin
        top_margin = 0
        for y in range(height):
            has_content = False
            for x in range(width):
                pixel = image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                if alpha > 10:  # Non-transparent pixel (with small threshold)
                    has_content = True
                    break
            if has_content:
                break
            top_margin += 1
        
        # Update margin controls
        self._margin_x.setValue(left_margin)
        self._margin_y.setValue(top_margin)
        
        # Trigger re-slicing
        self._update_frame_slicing()
    
    def _set_frame_size(self, width: int, height: int):
        """Set frame size using preset values."""
        self._frame_width.setValue(width)
        self._frame_height.setValue(height)
        # _update_frame_slicing will be called automatically via valueChanged signals
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop event."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self._load_sprite_sheet(file_path)
                event.acceptProposedAction()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()
        
        if key == Qt.Key_Space:
            self._toggle_playback()
        elif key == Qt.Key_G:
            self._grid_checkbox.setChecked(not self._grid_checkbox.isChecked())
        elif key == Qt.Key_Left and self._sprite_frames:
            if self._is_playing:
                self._toggle_playback()
            self._current_frame = max(0, self._current_frame - 1)
            self._update_display()
        elif key == Qt.Key_Right and self._sprite_frames:
            if self._is_playing:
                self._toggle_playback()
            self._current_frame = min(len(self._sprite_frames) - 1, self._current_frame + 1)
            self._update_display()
        else:
            super().keyPressEvent(event)


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Python Sprite Viewer")
    app.setApplicationVersion("1.0")
    
    viewer = SpriteViewer()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()