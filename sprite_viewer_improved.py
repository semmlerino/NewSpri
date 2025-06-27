#!/usr/bin/env python3
"""
Python Sprite Viewer - Improved UI
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
    QScrollArea, QGroupBox, QColorDialog, QComboBox, QStatusBar,
    QToolButton, QFrame, QGridLayout, QButtonGroup, QRadioButton,
    QToolBar, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QRect, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QAction, QDragEnterEvent, QDropEvent, QIcon, QFont

from config import Config


class SpriteCanvas(QLabel):
    """Custom canvas widget for displaying sprites with zoom and pan capabilities."""
    
    frameChanged = Signal(int, int)  # current_frame, total_frames
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(Config.Canvas.MIN_WIDTH, Config.Canvas.MIN_HEIGHT)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """)
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
    
    def set_pixmap(self, pixmap: QPixmap):
        """Set the sprite pixmap to display."""
        self._pixmap = pixmap
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
            
        canvas_rect = self.rect()
        pixmap_size = self._pixmap.size()
        
        # Calculate scale to fit
        scale_x = canvas_rect.width() / pixmap_size.width()
        scale_y = canvas_rect.height() / pixmap_size.height()
        self._zoom_factor = min(scale_x, scale_y) * Config.Canvas.ZOOM_FIT_MARGIN
        self._pan_offset = Config.Canvas.DEFAULT_PAN_OFFSET.copy()
        self.update()
    
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


class PlaybackControls(QFrame):
    """Unified playback control widget."""
    
    playPauseClicked = Signal()
    frameChanged = Signal(int)
    fpsChanged = Signal(int)
    loopToggled = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(Config.UI.MAIN_LAYOUT_SPACING)
        
        # Large play/pause button
        self.play_button = QPushButton("▶ Play")
        self.play_button.setMinimumHeight(Config.UI.PLAYBACK_BUTTON_MIN_HEIGHT)
        self.play_button.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.play_button.clicked.connect(self.playPauseClicked)
        layout.addWidget(self.play_button)
        
        # Frame navigation
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(Config.UI.NAV_BUTTON_SPACING)
        
        # Navigation buttons with better styling
        button_style = f"""
            QPushButton {{
                font-size: 12pt;
                min-width: {Config.UI.NAV_BUTTON_WIDTH_PX};
                min-height: {Config.UI.NAV_BUTTON_HEIGHT_PX};
                background-color: #e0e0e0;
                border: 1px solid #bbb;
                border-radius: 4px;
            }}
            QPushButton:hover:enabled {{
                background-color: #d0d0d0;
            }}
            QPushButton:pressed {{
                background-color: #c0c0c0;
            }}
            QPushButton:disabled {{
                color: #999;
                background-color: #f0f0f0;
            }}
        """
        
        self.first_btn = QPushButton("⏮")
        self.first_btn.setStyleSheet(button_style)
        self.first_btn.setToolTip("First frame (Home)")
        nav_layout.addWidget(self.first_btn)
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setStyleSheet(button_style)
        self.prev_btn.setToolTip("Previous frame (←)")
        nav_layout.addWidget(self.prev_btn)
        
        # Frame slider in the middle
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(Config.Slider.FRAME_SLIDER_MIN)
        self.frame_slider.setMaximum(0)
        self.frame_slider.valueChanged.connect(self.frameChanged)
        nav_layout.addWidget(self.frame_slider, 1)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setStyleSheet(button_style)
        self.next_btn.setToolTip("Next frame (→)")
        nav_layout.addWidget(self.next_btn)
        
        self.last_btn = QPushButton("⏭")
        self.last_btn.setStyleSheet(button_style)
        self.last_btn.setToolTip("Last frame (End)")
        nav_layout.addWidget(self.last_btn)
        
        layout.addLayout(nav_layout)
        
        # FPS control with better layout
        fps_layout = QHBoxLayout()
        fps_label = QLabel("Speed:")
        fps_label.setStyleSheet("font-weight: bold;")
        fps_layout.addWidget(fps_label)
        
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setRange(Config.Animation.MIN_FPS, Config.Animation.MAX_FPS)
        self.fps_slider.setValue(Config.Animation.DEFAULT_FPS)
        self.fps_slider.setTickPosition(QSlider.TicksBelow)
        self.fps_slider.setTickInterval(Config.Slider.FPS_SLIDER_TICK_INTERVAL)
        self.fps_slider.valueChanged.connect(self._on_fps_changed)
        fps_layout.addWidget(self.fps_slider, 1)
        
        self.fps_value = QLabel(f"{Config.Animation.DEFAULT_FPS} fps")
        self.fps_value.setMinimumWidth(Config.Slider.FPS_VALUE_MIN_WIDTH)
        self.fps_value.setAlignment(Qt.AlignRight)
        fps_layout.addWidget(self.fps_value)
        
        layout.addLayout(fps_layout)
        
        # Loop checkbox
        self.loop_checkbox = QCheckBox("Loop animation")
        self.loop_checkbox.setChecked(True)
        self.loop_checkbox.toggled.connect(self.loopToggled)
        layout.addWidget(self.loop_checkbox)
    
    def _on_fps_changed(self, value):
        self.fps_value.setText(f"{value} fps")
        self.fpsChanged.emit(value)
    
    def set_playing(self, playing: bool):
        """Update play button state."""
        if playing:
            self.play_button.setText("⏸ Pause")
            self.play_button.setStyleSheet("""
                QPushButton {
                    font-size: 14pt;
                    font-weight: bold;
                    background-color: #ff9800;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e68900;
                }
                QPushButton:pressed {
                    background-color: #cc7a00;
                }
            """)
        else:
            self.play_button.setText("▶ Play")
            self.play_button.setStyleSheet("""
                QPushButton {
                    font-size: 14pt;
                    font-weight: bold;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """)
    
    def set_frame_range(self, max_frame: int):
        """Set the frame slider range."""
        self.frame_slider.setMaximum(max_frame)
    
    def set_current_frame(self, frame: int):
        """Set current frame without triggering signal."""
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(frame)
        self.frame_slider.blockSignals(False)
    
    def update_button_states(self, has_frames: bool, at_start: bool, at_end: bool):
        """Update navigation button states."""
        self.play_button.setEnabled(has_frames)
        self.first_btn.setEnabled(has_frames and not at_start)
        self.prev_btn.setEnabled(has_frames and not at_start)
        self.next_btn.setEnabled(has_frames and not at_end)
        self.last_btn.setEnabled(has_frames and not at_end)


class FrameExtractor(QGroupBox):
    """Frame extraction settings widget."""
    
    settingsChanged = Signal()
    presetSelected = Signal(int, int)
    
    def __init__(self):
        super().__init__("Frame Extraction")
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Quick presets as radio buttons
        preset_label = QLabel("Quick Presets:")
        preset_label.setStyleSheet("font-weight: normal; margin-bottom: 5px;")
        layout.addWidget(preset_label)
        
        presets_layout = QGridLayout()
        presets_layout.setSpacing(Config.UI.PRESET_GRID_SPACING)
        
        self.preset_group = QButtonGroup()
        preset_data = Config.FrameExtraction.FRAME_PRESETS
        
        for i, (label, width, height, tooltip) in enumerate(preset_data):
            btn = QRadioButton(label)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, w=width, h=height: self.presetSelected.emit(w, h))
            self.preset_group.addButton(btn, i)
            presets_layout.addWidget(btn, i // 3, i % 3)
        
        # Default to 192×192
        self.preset_group.button(Config.FrameExtraction.DEFAULT_PRESET_INDEX).setChecked(True)
        
        layout.addLayout(presets_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        layout.addWidget(separator)
        
        # Custom size controls
        custom_label = QLabel("Custom Size:")
        custom_label.setStyleSheet("font-weight: normal; margin-top: 10px;")
        layout.addWidget(custom_label)
        
        size_layout = QHBoxLayout()
        size_layout.setSpacing(Config.UI.SIZE_LAYOUT_SPACING)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(Config.FrameExtraction.MIN_FRAME_SIZE, Config.FrameExtraction.MAX_FRAME_SIZE)
        self.width_spin.setValue(Config.FrameExtraction.DEFAULT_FRAME_WIDTH)
        self.width_spin.setSuffix(" px")
        self.width_spin.valueChanged.connect(self._on_custom_size_changed)
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel("×"))
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(Config.FrameExtraction.MIN_FRAME_SIZE, Config.FrameExtraction.MAX_FRAME_SIZE)
        self.height_spin.setValue(Config.FrameExtraction.DEFAULT_FRAME_HEIGHT)
        self.height_spin.setSuffix(" px")
        self.height_spin.valueChanged.connect(self._on_custom_size_changed)
        size_layout.addWidget(self.height_spin)
        
        # Auto-detect button
        self.auto_btn = QPushButton("Auto")
        self.auto_btn.setMaximumWidth(Config.UI.AUTO_BUTTON_MAX_WIDTH)
        self.auto_btn.setToolTip("Auto-detect frame size")
        size_layout.addWidget(self.auto_btn)
        
        layout.addLayout(size_layout)
        
        # Offset controls
        offset_label = QLabel("Offset (if needed):")
        offset_label.setStyleSheet("font-weight: normal; margin-top: 10px;")
        layout.addWidget(offset_label)
        
        offset_layout = QHBoxLayout()
        offset_layout.setSpacing(Config.UI.SIZE_LAYOUT_SPACING)
        
        offset_layout.addWidget(QLabel("X:"))
        self.offset_x = QSpinBox()
        self.offset_x.setRange(Config.FrameExtraction.DEFAULT_OFFSET, Config.FrameExtraction.MAX_OFFSET)
        self.offset_x.setValue(Config.FrameExtraction.DEFAULT_OFFSET)
        self.offset_x.setSuffix(" px")
        self.offset_x.valueChanged.connect(self.settingsChanged)
        offset_layout.addWidget(self.offset_x)
        
        offset_layout.addWidget(QLabel("Y:"))
        self.offset_y = QSpinBox()
        self.offset_y.setRange(Config.FrameExtraction.DEFAULT_OFFSET, Config.FrameExtraction.MAX_OFFSET)
        self.offset_y.setValue(Config.FrameExtraction.DEFAULT_OFFSET)
        self.offset_y.setSuffix(" px")
        self.offset_y.valueChanged.connect(self.settingsChanged)
        offset_layout.addWidget(self.offset_y)
        
        # Auto-detect margins button
        self.auto_margins_btn = QPushButton("Auto")
        self.auto_margins_btn.setMaximumWidth(Config.UI.AUTO_BUTTON_MAX_WIDTH)
        self.auto_margins_btn.setToolTip("Auto-detect margins")
        offset_layout.addWidget(self.auto_margins_btn)
        
        layout.addLayout(offset_layout)
        
        # Grid overlay checkbox
        self.grid_checkbox = QCheckBox("Show grid overlay")
        self.grid_checkbox.setStyleSheet("margin-top: 10px;")
        layout.addWidget(self.grid_checkbox)
    
    def _on_custom_size_changed(self):
        """Handle custom size change."""
        # Uncheck all preset buttons when custom size is used
        for button in self.preset_group.buttons():
            button.setChecked(False)
        self.settingsChanged.emit()
    
    def get_frame_size(self) -> Tuple[int, int]:
        """Get current frame size."""
        return self.width_spin.value(), self.height_spin.value()
    
    def get_offset(self) -> Tuple[int, int]:
        """Get current offset."""
        return self.offset_x.value(), self.offset_y.value()
    
    def set_frame_size(self, width: int, height: int):
        """Set frame size programmatically."""
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        
        # Check corresponding preset if it matches
        for i, btn in enumerate(self.preset_group.buttons()):
            preset_text = btn.text()
            if preset_text == f"{width}×{height}":
                btn.setChecked(True)
                break


class SpriteViewer(QMainWindow):
    """Main sprite viewer application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Config.App.WINDOW_TITLE)
        self.setGeometry(
            Config.UI.DEFAULT_WINDOW_X, 
            Config.UI.DEFAULT_WINDOW_Y,
            Config.UI.DEFAULT_WINDOW_WIDTH, 
            Config.UI.DEFAULT_WINDOW_HEIGHT
        )
        
        # Sprite data
        self._sprite_frames: List[QPixmap] = []
        self._current_frame = 0
        self._is_playing = False
        self._loop_enabled = True
        self._original_sprite_sheet: Optional[QPixmap] = None
        self._sprite_sheet_info = ""  # Store basic info separately
        
        # Animation timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._next_frame)
        self._fps = Config.Animation.DEFAULT_FPS
        
        # UI setup
        self._setup_ui()
        self._setup_toolbar()
        self._setup_menu()
        self._connect_signals()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._show_welcome_message()
        
        # Load test sprites if available
        self._load_test_sprites()
    
    def _setup_ui(self):
        """Set up the user interface with improved layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(Config.UI.MAIN_LAYOUT_SPACING)
        
        # Left side - Canvas
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        # Canvas
        self._canvas = SpriteCanvas()
        self._canvas.frameChanged.connect(self._on_canvas_frame_changed)
        canvas_layout.addWidget(self._canvas)
        
        main_layout.addWidget(canvas_container, 2)
        
        # Right side - Controls
        controls_container = QWidget()
        controls_container.setMaximumWidth(Config.UI.CONTROLS_MAX_WIDTH)
        controls_container.setMinimumWidth(Config.UI.CONTROLS_MIN_WIDTH)
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setSpacing(Config.UI.CONTROLS_LAYOUT_SPACING)
        
        # 1. Sprite Sheet Info (collapsible)
        info_group = QGroupBox("Sprite Sheet Info")
        info_group.setMaximumHeight(Config.UI.INFO_GROUP_MAX_HEIGHT)  # Prevent growing
        info_layout = QVBoxLayout(info_group)
        self._info_label = QLabel("No sprite sheet loaded")
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet("color: #666; font-size: 10pt;")
        self._info_label.setAlignment(Qt.AlignTop)
        info_layout.addWidget(self._info_label)
        controls_layout.addWidget(info_group)
        
        # 2. Frame Extraction
        self._frame_extractor = FrameExtractor()
        controls_layout.addWidget(self._frame_extractor)
        
        # 3. Playback Controls
        self._playback_controls = PlaybackControls()
        controls_layout.addWidget(self._playback_controls)
        
        # 4. View Options (compact)
        view_group = QGroupBox("View Options")
        view_layout = QVBoxLayout(view_group)
        
        # Background selector
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background:"))
        self._bg_combo = QComboBox()
        self._bg_combo.addItems(["Checkerboard", "Solid Color"])
        self._bg_combo.currentTextChanged.connect(self._change_background)
        bg_layout.addWidget(self._bg_combo, 1)
        
        self._color_button = QPushButton("Color")
        self._color_button.setMaximumWidth(Config.UI.COLOR_BUTTON_MAX_WIDTH)
        self._color_button.clicked.connect(self._choose_background_color)
        self._color_button.setEnabled(False)
        bg_layout.addWidget(self._color_button)
        
        view_layout.addLayout(bg_layout)
        controls_layout.addWidget(view_group)
        
        # Add stretch to push everything to top
        controls_layout.addStretch()
        
        # Help text at bottom
        help_label = QLabel("Drag & drop sprite sheets or use toolbar buttons")
        help_label.setAlignment(Qt.AlignCenter)
        help_label.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
        controls_layout.addWidget(help_label)
        
        main_layout.addWidget(controls_container)
    
    def _setup_toolbar(self):
        """Set up main toolbar with common actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f5f5f5;
                border-bottom: 1px solid #ddd;
                padding: 5px;
                spacing: 5px;
            }
            QToolButton {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                margin: 2px;
            }
            QToolButton:hover {
                background-color: #e8e8e8;
                border-color: #bbb;
            }
            QToolButton:pressed {
                background-color: #ddd;
            }
        """)
        self.addToolBar(toolbar)
        
        # File actions
        open_action = QAction("📁 Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setToolTip("Open sprite sheet (Ctrl+O)")
        open_action.triggered.connect(self._load_sprites)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # View actions
        self._zoom_in_action = QAction("🔍+", self)
        self._zoom_in_action.setShortcut("Ctrl++")
        self._zoom_in_action.setToolTip("Zoom in (Ctrl++)")
        self._zoom_in_action.triggered.connect(self._zoom_in)
        toolbar.addAction(self._zoom_in_action)
        
        self._zoom_out_action = QAction("🔍-", self)
        self._zoom_out_action.setShortcut("Ctrl+-")
        self._zoom_out_action.setToolTip("Zoom out (Ctrl+-)")
        self._zoom_out_action.triggered.connect(self._zoom_out)
        toolbar.addAction(self._zoom_out_action)
        
        self._zoom_fit_action = QAction("🔍⇄", self)
        self._zoom_fit_action.setShortcut("Ctrl+0")
        self._zoom_fit_action.setToolTip("Fit to window (Ctrl+0)")
        self._zoom_fit_action.triggered.connect(self._zoom_fit)
        toolbar.addAction(self._zoom_fit_action)
        
        self._zoom_reset_action = QAction("🔍1:1", self)
        self._zoom_reset_action.setShortcut("Ctrl+1")
        self._zoom_reset_action.setToolTip("Reset zoom (Ctrl+1)")
        self._zoom_reset_action.triggered.connect(self._zoom_reset)
        toolbar.addAction(self._zoom_reset_action)
        
        toolbar.addSeparator()
        
        # Add current zoom display
        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(Config.UI.ZOOM_LABEL_MIN_WIDTH)
        self._zoom_label.setAlignment(Qt.AlignCenter)
        self._zoom_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
        """)
        toolbar.addWidget(self._zoom_label)
    
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
        
        view_menu.addAction(self._zoom_in_action)
        view_menu.addAction(self._zoom_out_action)
        view_menu.addAction(self._zoom_fit_action)
        view_menu.addAction(self._zoom_reset_action)
        view_menu.addSeparator()
        
        grid_action = QAction("Toggle Grid", self)
        grid_action.setShortcut("G")
        grid_action.setCheckable(True)
        grid_action.triggered.connect(self._toggle_grid)
        view_menu.addAction(grid_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        shortcuts_action = QAction("Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _connect_signals(self):
        """Connect all widget signals."""
        # Frame extractor signals
        self._frame_extractor.settingsChanged.connect(self._update_frame_slicing)
        self._frame_extractor.presetSelected.connect(self._frame_extractor.set_frame_size)
        self._frame_extractor.auto_btn.clicked.connect(self._auto_detect_frame_size)
        self._frame_extractor.auto_margins_btn.clicked.connect(self._auto_detect_margins)
        self._frame_extractor.grid_checkbox.toggled.connect(self._toggle_grid)
        
        # Playback control signals
        self._playback_controls.playPauseClicked.connect(self._toggle_playback)
        self._playback_controls.frameChanged.connect(self._on_frame_slider_changed)
        self._playback_controls.fpsChanged.connect(self._on_fps_changed)
        self._playback_controls.loopToggled.connect(self._toggle_loop)
        
        self._playback_controls.first_btn.clicked.connect(self._go_to_first_frame)
        self._playback_controls.prev_btn.clicked.connect(self._go_to_prev_frame)
        self._playback_controls.next_btn.clicked.connect(self._go_to_next_frame)
        self._playback_controls.last_btn.clicked.connect(self._go_to_last_frame)
    
    def _show_welcome_message(self):
        """Show welcome message in status bar."""
        self._status_bar.showMessage("Welcome! Drag & drop sprite sheets or click Open to get started")
        # Reset info label to default state
        self._sprite_sheet_info = ""
        self._info_label.setText("No sprite sheet loaded")
    
    def _on_canvas_frame_changed(self, current: int, total: int):
        """Handle frame info change from canvas."""
        if total > 0:
            self._status_bar.showMessage(f"Frame {current + 1} of {total}")
    
    def _zoom_in(self):
        """Zoom in by 20%."""
        self._canvas.set_zoom(self._canvas._zoom_factor * Config.Canvas.ZOOM_FACTOR)
        self._update_zoom_label()
    
    def _zoom_out(self):
        """Zoom out by 20%."""
        self._canvas.set_zoom(self._canvas._zoom_factor / Config.Canvas.ZOOM_FACTOR)
        self._update_zoom_label()
    
    def _zoom_fit(self):
        """Fit sprite to window."""
        self._canvas.fit_to_window()
        self._update_zoom_label()
    
    def _zoom_reset(self):
        """Reset zoom to 100%."""
        self._canvas.set_zoom(1.0)
        self._update_zoom_label()
    
    def _update_zoom_label(self):
        """Update zoom percentage display."""
        zoom_percent = int(self._canvas._zoom_factor * 100)
        self._zoom_label.setText(f"{zoom_percent}%")
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts = """
<h3>Keyboard Shortcuts</h3>
<table>
<tr><td><b>Space</b></td><td>Play/Pause animation</td></tr>
<tr><td><b>← / →</b></td><td>Previous/Next frame</td></tr>
<tr><td><b>Home/End</b></td><td>First/Last frame</td></tr>
<tr><td><b>Ctrl+O</b></td><td>Open sprite sheet</td></tr>
<tr><td><b>Ctrl++/-</b></td><td>Zoom in/out</td></tr>
<tr><td><b>Ctrl+0</b></td><td>Fit to window</td></tr>
<tr><td><b>Ctrl+1</b></td><td>Reset zoom (100%)</td></tr>
<tr><td><b>G</b></td><td>Toggle grid overlay</td></tr>
<tr><td><b>Mouse wheel</b></td><td>Zoom in/out</td></tr>
<tr><td><b>Click+drag</b></td><td>Pan view</td></tr>
</table>
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts)
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """
<h3>Python Sprite Viewer</h3>
<p>Version 2.0</p>
<p>A modern sprite sheet animation viewer with improved usability.</p>
<p>Features:</p>
<ul>
<li>Automatic frame extraction</li>
<li>Smooth animation playback</li>
<li>Intuitive controls</li>
<li>Smart size detection</li>
</ul>
        """
        QMessageBox.about(self, "About Sprite Viewer", about_text)
    
    def _load_sprites(self):
        """Load sprite files or sprite sheet."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Load Sprite Sheet", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        
        if file_path:
            self._load_sprite_sheet(file_path)
    
    def _load_sprite_sheet(self, file_path: str):
        """Load and slice a sprite sheet."""
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", "Failed to load image file")
            # Reset to welcome state on error
            self._show_welcome_message()
            return
        
        # Store original sprite sheet for re-slicing
        self._original_sprite_sheet = pixmap
        
        # Update info
        file_name = Path(file_path).name
        self._sprite_sheet_info = (
            f"<b>File:</b> {file_name}<br>"
            f"<b>Size:</b> {pixmap.width()} × {pixmap.height()} px<br>"
            f"<b>Format:</b> {Path(file_path).suffix.upper()[1:]}"
        )
        self._info_label.setText(self._sprite_sheet_info)
        
        # Try to auto-detect frame size if it's a new sheet
        if self._should_auto_detect_size(pixmap):
            self._auto_detect_frame_size()
        
        # Slice the sprite sheet into individual frames
        self._slice_sprite_sheet()
        
        # Reset to first frame
        self._current_frame = 0
        self._update_display()
        
        # Update status
        self._status_bar.showMessage(f"Loaded: {file_name}")
    
    def _should_auto_detect_size(self, pixmap: QPixmap) -> bool:
        """Check if we should auto-detect frame size."""
        # Simple heuristic: if dimensions are multiples of common sizes
        width = pixmap.width()
        height = pixmap.height()
        
        common_sizes = Config.File.COMMON_FRAME_SIZES
        for size in common_sizes:
            if width % size == 0 and height % size == 0:
                return True
        return False
    
    def _auto_detect_frame_size(self):
        """Auto-detect frame size based on sprite sheet analysis."""
        if not self._original_sprite_sheet:
            return
        
        width = self._original_sprite_sheet.width()
        height = self._original_sprite_sheet.height()
        
        # Try common sprite sizes
        common_sizes = Config.FrameExtraction.AUTO_DETECT_SIZES
        
        for size in common_sizes:
            if width % size == 0 and height % size == 0:
                # Check if this produces a reasonable number of frames
                frames_x = width // size
                frames_y = height // size
                total_frames = frames_x * frames_y
                
                if Config.Animation.MIN_REASONABLE_FRAMES <= total_frames <= Config.Animation.MAX_REASONABLE_FRAMES:  # Reasonable frame count
                    self._frame_extractor.set_frame_size(size, size)
                    self._status_bar.showMessage(f"Auto-detected frame size: {size}×{size}")
                    return
        
        # If no common size fits, try to find the GCD
        from math import gcd
        frame_size = gcd(width, height)
        if frame_size >= Config.FrameExtraction.MIN_SPRITE_SIZE:  # Minimum reasonable sprite size
            self._frame_extractor.set_frame_size(frame_size, frame_size)
            self._status_bar.showMessage(f"Auto-detected frame size: {frame_size}×{frame_size}")
    
    def _load_test_sprites(self):
        """Load test sprites from various common locations."""
        test_paths = [
            Path("test_sprite_sheet.png"),
            Path("Archer") / "*.png",
            Path("sprites") / "*.png",
            Path("assets") / "*.png"
        ]
        
        for path_pattern in test_paths:
            if path_pattern.parent.exists():
                sprite_files = list(path_pattern.parent.glob(path_pattern.name))
                if sprite_files:
                    self._load_sprite_sheet(str(sprite_files[0]))
                    break
            elif path_pattern.exists():
                self._load_sprite_sheet(str(path_pattern))
                break
    
    def _slice_sprite_sheet(self):
        """Slice the original sprite sheet into individual frames."""
        if not self._original_sprite_sheet:
            return
        
        frame_width, frame_height = self._frame_extractor.get_frame_size()
        offset_x, offset_y = self._frame_extractor.get_offset()
        
        sheet_width = self._original_sprite_sheet.width()
        sheet_height = self._original_sprite_sheet.height()
        
        # Calculate available area after margins
        available_width = sheet_width - offset_x
        available_height = sheet_height - offset_y
        
        # Calculate how many frames fit
        frames_per_row = available_width // frame_width if frame_width > 0 else 0
        frames_per_col = available_height // frame_height if frame_height > 0 else 0
        
        # Extract individual frames
        self._sprite_frames = []
        for row in range(frames_per_col):
            for col in range(frames_per_row):
                x = offset_x + (col * frame_width)
                y = offset_y + (row * frame_height)
                
                # Extract frame from sprite sheet
                frame_rect = QRect(x, y, frame_width, frame_height)
                frame = self._original_sprite_sheet.copy(frame_rect)
                
                if not frame.isNull():
                    self._sprite_frames.append(frame)
        
        # Update UI
        total_frames = len(self._sprite_frames)
        if total_frames > 0:
            # Update info label with complete information
            frame_info = (
                f"<br><b>Frames:</b> {total_frames} "
                f"({frames_per_row}×{frames_per_col})<br>"
                f"<b>Frame size:</b> {frame_width}×{frame_height} px"
            )
            self._info_label.setText(self._sprite_sheet_info + frame_info)
            
            # Update playback controls
            self._playback_controls.set_frame_range(total_frames - 1)
            self._playback_controls.update_button_states(True, True, False)
        else:
            # No frames extracted
            self._info_label.setText(self._sprite_sheet_info + "<br><b>Frames:</b> 0")
    
    def _update_frame_slicing(self):
        """Update frame slicing based on current settings."""
        if not self._original_sprite_sheet:
            return
        
        # Re-slice with new dimensions
        self._slice_sprite_sheet()
        
        # Reset to first frame if current is out of bounds
        if self._current_frame >= len(self._sprite_frames):
            self._current_frame = 0
        
        # Update display
        self._update_display()
        
        # Update grid
        if self._frame_extractor.grid_checkbox.isChecked():
            frame_width, frame_height = self._frame_extractor.get_frame_size()
            self._canvas.set_grid_overlay(True, max(frame_width, frame_height))
    
    def _update_display(self):
        """Update the canvas display."""
        if self._sprite_frames and 0 <= self._current_frame < len(self._sprite_frames):
            self._canvas.set_pixmap(self._sprite_frames[self._current_frame])
            self._canvas.set_frame_info(self._current_frame, len(self._sprite_frames))
            self._playback_controls.set_current_frame(self._current_frame)
            self._update_navigation_buttons()
        else:
            self._canvas.set_pixmap(QPixmap())
            self._canvas.set_frame_info(0, 0)
            self._playback_controls.set_current_frame(0)
            self._update_navigation_buttons()
            # If no sprite sheet is loaded, show welcome message
            if not self._original_sprite_sheet:
                self._show_welcome_message()
    
    def _update_navigation_buttons(self):
        """Update navigation button states."""
        has_frames = bool(self._sprite_frames)
        at_start = self._current_frame == 0
        at_end = self._current_frame == len(self._sprite_frames) - 1 if has_frames else True
        
        self._playback_controls.update_button_states(has_frames, at_start, at_end)
    
    def _toggle_playback(self):
        """Toggle animation playback."""
        if self._is_playing:
            self._timer.stop()
            self._is_playing = False
            self._playback_controls.set_playing(False)
        else:
            if self._sprite_frames:
                self._timer.start(Config.Animation.TIMER_BASE // self._fps)
                self._is_playing = True
                self._playback_controls.set_playing(True)
    
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
    
    def _toggle_grid(self, checked: bool = None):
        """Toggle grid overlay."""
        if checked is None:
            checked = self._frame_extractor.grid_checkbox.isChecked()
            self._frame_extractor.grid_checkbox.setChecked(not checked)
        else:
            frame_width, frame_height = self._frame_extractor.get_frame_size()
            self._canvas.set_grid_overlay(checked, max(frame_width, frame_height))
    
    def _on_fps_changed(self, value: int):
        """Handle FPS change."""
        self._fps = value
        if self._is_playing:
            self._timer.setInterval(Config.Animation.TIMER_BASE // self._fps)
    
    def _on_frame_slider_changed(self, value: int):
        """Handle frame slider change."""
        if self._sprite_frames and 0 <= value < len(self._sprite_frames):
            if self._is_playing:
                self._toggle_playback()
            self._current_frame = value
            self._update_display()
    
    def _go_to_first_frame(self):
        """Go to first frame."""
        if self._sprite_frames:
            if self._is_playing:
                self._toggle_playback()
            self._current_frame = 0
            self._update_display()
    
    def _go_to_last_frame(self):
        """Go to last frame."""
        if self._sprite_frames:
            if self._is_playing:
                self._toggle_playback()
            self._current_frame = len(self._sprite_frames) - 1
            self._update_display()
    
    def _go_to_prev_frame(self):
        """Go to previous frame."""
        if self._sprite_frames and self._current_frame > 0:
            if self._is_playing:
                self._toggle_playback()
            self._current_frame -= 1
            self._update_display()
    
    def _go_to_next_frame(self):
        """Go to next frame."""
        if self._sprite_frames and self._current_frame < len(self._sprite_frames) - 1:
            if self._is_playing:
                self._toggle_playback()
            self._current_frame += 1
            self._update_display()
    
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
                if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:  # Non-transparent pixel
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
                if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:  # Non-transparent pixel
                    has_content = True
                    break
            if has_content:
                break
            top_margin += 1
        
        # Update controls
        self._frame_extractor.offset_x.setValue(left_margin)
        self._frame_extractor.offset_y.setValue(top_margin)
        
        self._status_bar.showMessage(f"Auto-detected margins: X={left_margin}, Y={top_margin}")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    event.acceptProposedAction()
                    self._canvas.setStyleSheet("""
                        QLabel {
                            border: 4px dashed #4CAF50;
                            border-radius: 8px;
                            background-color: #e8f5e9;
                        }
                    """)
                    self._status_bar.showMessage("Drop sprite sheet to load...")
                    return
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop event."""
        # Reset canvas style
        self._canvas.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """)
        
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self._load_sprite_sheet(file_path)
                event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self._canvas.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """)
        self._show_welcome_message()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()
        
        if key == Qt.Key_Space:
            self._toggle_playback()
        elif key == Qt.Key_G:
            self._toggle_grid()
        elif key == Qt.Key_Left and self._sprite_frames:
            self._go_to_prev_frame()
        elif key == Qt.Key_Right and self._sprite_frames:
            self._go_to_next_frame()
        elif key == Qt.Key_Home and self._sprite_frames:
            self._go_to_first_frame()
        elif key == Qt.Key_End and self._sprite_frames:
            self._go_to_last_frame()
        else:
            super().keyPressEvent(event)


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Python Sprite Viewer")
    app.setApplicationVersion("2.0")
    
    # Set application style
    app.setStyle("Fusion")
    
    viewer = SpriteViewer()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()