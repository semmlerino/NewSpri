#!/usr/bin/env python3
"""
Playback Controls Widget
Unified playback control widget for sprite animation.
Part of Python Sprite Viewer - Phase 5: UI Component Extraction.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, 
    QLabel, QCheckBox
)
from PySide6.QtCore import Qt, Signal

from config import Config
from styles import StyleManager


class PlaybackControls(QFrame):
    """Unified playback control widget."""
    
    playPauseClicked = Signal()
    frameChanged = Signal(int)
    fpsChanged = Signal(int)
    loopToggled = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet(StyleManager.get_playback_controls_frame())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(Config.UI.MAIN_LAYOUT_SPACING)
        
        # Large play/pause button
        self.play_button = QPushButton("▶ Play")
        self.play_button.setMinimumHeight(Config.UI.PLAYBACK_BUTTON_MIN_HEIGHT)
        self.play_button.setStyleSheet(StyleManager.get_play_button_stopped())
        self.play_button.clicked.connect(self.playPauseClicked)
        layout.addWidget(self.play_button)
        
        # Frame navigation
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(Config.UI.NAV_BUTTON_SPACING)
        
        # Navigation buttons with better styling
        button_style = StyleManager.get_navigation_buttons()
        
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
        fps_label.setStyleSheet(StyleManager.get_speed_label())
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
            self.play_button.setStyleSheet(StyleManager.get_play_button_playing())
        else:
            self.play_button.setText("▶ Play")
            self.play_button.setStyleSheet(StyleManager.get_play_button_stopped())
    
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


# Export for easy importing
__all__ = ['PlaybackControls']