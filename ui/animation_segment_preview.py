"""
Animation Segment Preview Widget - Visual preview panel for animation segments
Displays each animation segment with individual playback controls.
Part of Animation Segment System Enhancement.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QLabel, QPushButton, QFrame, QToolButton, QSpinBox,
    QCheckBox, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon

from config import Config
from core.animation_controller import AnimationController
from sprite_model.core import SpriteModel


class SegmentPreviewItem(QFrame):
    """Individual animation segment preview with playback controls.
    
    Features:
    - Play/pause animation control
    - Bounce mode (ping-pong) animation
    - Frame holds: Pause on specific frames for a set duration
    - Hold management: Add, edit, clear individual holds or apply to all frames
    - Visual preview of current frame
    - Export options via context menu
    """
    
    # Signals
    playToggled = Signal(str, bool)  # segment_name, is_playing
    removeRequested = Signal(str)    # segment_name
    exportRequested = Signal(str)    # segment_name
    bounceChanged = Signal(str, bool)  # segment_name, bounce_mode
    frameHoldsChanged = Signal(str, dict)  # segment_name, frame_holds
    
    def __init__(self, segment_name: str, color: QColor, frames: List[QPixmap], 
                 bounce_mode: bool = False, frame_holds: Dict[int, int] = None,
                 zoom_factor: float = 1.0):
        super().__init__()
        self.segment_name = segment_name
        self.segment_color = color
        self._frames = frames
        self._current_frame = 0
        self._is_playing = False
        self._fps = 10  # Default FPS
        self._zoom_factor = zoom_factor
        
        # Animation mode properties
        self._bounce_mode = bounce_mode
        self._frame_holds = frame_holds or {}
        self._playback_direction = 1  # 1 for forward, -1 for backward
        self._hold_counter = 0  # Counter for frame holds
        
        # Create mini animation controller
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_frame)
        self._update_timer_interval()
        
        self._setup_ui()
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def _setup_ui(self):
        """Set up the preview item UI."""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {self.segment_color.name()};
                border-radius: 8px;
                background-color: #FAFAFA;
                margin: 4px;
                padding: 8px;
            }}
            QFrame:hover {{
                background-color: #F0F0F0;
            }}
        """)
        
        layout = QHBoxLayout(self)
        
        # Left side: Info and controls
        info_layout = QVBoxLayout()
        
        # Segment name with color indicator
        name_layout = QHBoxLayout()
        color_indicator = QLabel()
        color_indicator.setFixedSize(16, 16)
        color_indicator.setStyleSheet(f"""
            QLabel {{
                background-color: {self.segment_color.name()};
                border: 1px solid #666;
                border-radius: 3px;
            }}
        """)
        name_layout.addWidget(color_indicator)
        
        name_label = QLabel(self.segment_name)
        name_label.setStyleSheet("font-weight: bold;")
        name_layout.addWidget(name_label)
        name_layout.addStretch()
        
        info_layout.addLayout(name_layout)
        
        # Frame info
        frame_info = QLabel(f"{len(self._frames)} frames")
        frame_info.setStyleSheet("color: #666; font-size: 10px;")
        info_layout.addWidget(frame_info)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Play/Pause button
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(32, 32)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.play_button.clicked.connect(self._toggle_playback)
        controls_layout.addWidget(self.play_button)
        
        # Frame counter
        self.frame_counter = QLabel("1 / " + str(len(self._frames)))
        self.frame_counter.setStyleSheet("color: #666; font-size: 10px;")
        controls_layout.addWidget(self.frame_counter)
        
        # FPS control
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet("color: #666; font-size: 10px;")
        controls_layout.addWidget(fps_label)
        
        self.fps_spinner = QSpinBox()
        self.fps_spinner.setMinimum(1)
        self.fps_spinner.setMaximum(60)
        self.fps_spinner.setValue(self._fps)
        self.fps_spinner.setFixedWidth(50)
        self.fps_spinner.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #DDD;
                border-radius: 4px;
                padding: 2px;
                font-size: 10px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 12px;
            }
        """)
        self.fps_spinner.valueChanged.connect(self._on_fps_changed)
        controls_layout.addWidget(self.fps_spinner)
        
        controls_layout.addStretch()
        
        # Animation mode controls (2nd row)
        mode_layout = QHBoxLayout()
        
        # Bounce mode checkbox
        self.bounce_checkbox = QCheckBox("Bounce")
        self.bounce_checkbox.setChecked(self._bounce_mode)
        self.bounce_checkbox.setToolTip("Play animation forward then backward")
        self.bounce_checkbox.setStyleSheet("font-size: 10px; color: #666;")
        self.bounce_checkbox.toggled.connect(self._on_bounce_toggled)
        mode_layout.addWidget(self.bounce_checkbox)
        
        # Frame hold button
        self.hold_button = QPushButton("Holds")
        self.hold_button.setFixedSize(40, 20)
        self.hold_button.setToolTip("Set frame hold durations")
        self.hold_button.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                padding: 2px;
                background-color: #E0E0E0;
                border: 1px solid #999;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
        """)
        self.hold_button.clicked.connect(self._show_hold_menu)
        mode_layout.addWidget(self.hold_button)
        
        mode_layout.addStretch()
        info_layout.addLayout(mode_layout)
        
        # Remove button
        remove_button = QToolButton()
        remove_button.setText("×")
        remove_button.setFixedSize(20, 20)
        remove_button.setStyleSheet("""
            QToolButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #da190b;
            }
        """)
        remove_button.clicked.connect(lambda: self.removeRequested.emit(self.segment_name))
        controls_layout.addWidget(remove_button)
        
        info_layout.addLayout(controls_layout)
        layout.addLayout(info_layout)
        
        # Right side: Animation preview
        self.preview_label = QLabel()
        base_size = int(120 * self._zoom_factor)
        self.preview_label.setFixedSize(base_size, base_size)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 1px solid #DDD;
                background-color: white;
                border-radius: 4px;
            }
        """)
        
        # Display first frame
        if self._frames:
            self._display_frame(0)
        
        layout.addWidget(self.preview_label)
        
    def _display_frame(self, index: int):
        """Display a specific frame in the preview."""
        if 0 <= index < len(self._frames):
            pixmap = self._frames[index]
            scaled_size = int(110 * self._zoom_factor)
            scaled = pixmap.scaled(
                scaled_size, scaled_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
            self.frame_counter.setText(f"{index + 1} / {len(self._frames)}")
            
    def _update_frame(self):
        """Update to next frame in animation."""
        # Check if we're holding the current frame
        if self._current_frame in self._frame_holds:
            if self._hold_counter < self._frame_holds[self._current_frame]:
                self._hold_counter += 1
                return  # Keep displaying the same frame
            else:
                self._hold_counter = 0  # Reset counter for next time
        
        # Update frame based on playback mode
        if self._bounce_mode:
            # Bounce mode: reverse direction at ends
            next_frame = self._current_frame + self._playback_direction
            
            if next_frame >= len(self._frames):
                # Hit the end, reverse direction
                self._playback_direction = -1
                next_frame = len(self._frames) - 2  # Go back one frame
            elif next_frame < 0:
                # Hit the start, reverse direction
                self._playback_direction = 1
                next_frame = 1  # Go forward one frame
                
            self._current_frame = max(0, min(next_frame, len(self._frames) - 1))
        else:
            # Normal loop mode
            self._current_frame = (self._current_frame + 1) % len(self._frames)
            
        self._display_frame(self._current_frame)
        
    def _toggle_playback(self):
        """Toggle animation playback."""
        self._is_playing = not self._is_playing
        
        if self._is_playing:
            self.play_button.setText("⏸")
            self.play_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            self._timer.start()
        else:
            self.play_button.setText("▶")
            self.play_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self._timer.stop()
            
        self.playToggled.emit(self.segment_name, self._is_playing)
        
    def _update_timer_interval(self):
        """Update timer interval based on current FPS."""
        if self._fps > 0:
            interval = 1000 // self._fps
            self._timer.setInterval(interval)
            
    def _on_fps_changed(self, value: int):
        """Handle FPS change from spinner."""
        self._fps = value
        self._update_timer_interval()
        
    def set_playing(self, playing: bool):
        """Set playback state externally."""
        if playing != self._is_playing:
            self._toggle_playback()
            
    def stop_playback(self):
        """Stop playback and reset to first frame."""
        if self._is_playing:
            self._toggle_playback()
        self._current_frame = 0
        self._display_frame(0)
    
    def _show_context_menu(self, pos):
        """Show context menu for segment actions."""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        # Export actions
        export_menu = menu.addMenu("Export Segment")
        
        export_frames_action = export_menu.addAction("Export as Individual Frames...")
        export_frames_action.triggered.connect(
            lambda: self.exportRequested.emit(self.segment_name)
        )
        
        export_sheet_action = export_menu.addAction("Export as Sprite Sheet...")
        export_sheet_action.triggered.connect(
            lambda: self.exportRequested.emit(self.segment_name)
        )
        
        menu.addSeparator()
        
        # Remove action
        remove_action = menu.addAction("Remove Segment")
        remove_action.triggered.connect(
            lambda: self.removeRequested.emit(self.segment_name)
        )
        
        menu.exec_(self.mapToGlobal(pos))
    
    def _on_bounce_toggled(self, checked: bool):
        """Handle bounce mode toggle."""
        self._bounce_mode = checked
        # Reset playback direction when toggling mode
        self._playback_direction = 1
        # Emit signal for persistence
        self.bounceChanged.emit(self.segment_name, checked)
        
    def _show_hold_menu(self):
        """Show menu for setting frame holds."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
            }
        """)
        
        # Show current frame holds
        if self._frame_holds:
            menu.addSection("Current Frame Holds")
            for frame_idx, duration in sorted(self._frame_holds.items()):
                action = menu.addAction(f"Frame {frame_idx + 1}: Hold for {duration} frames")
                action.triggered.connect(lambda checked, idx=frame_idx: self._edit_frame_hold(idx))
            menu.addSeparator()
        
        # Add new frame hold
        add_action = menu.addAction("Add Frame Hold...")
        add_action.triggered.connect(self._add_frame_hold)
        
        # Add hold to all frames
        add_all_action = menu.addAction("Add Hold to All Frames...")
        add_all_action.triggered.connect(self._add_hold_to_all_frames)
        
        # Clear all holds
        if self._frame_holds:
            clear_action = menu.addAction("Clear All Holds")
            clear_action.triggered.connect(self._clear_frame_holds)
        
        menu.exec_(self.hold_button.mapToGlobal(self.hold_button.rect().bottomLeft()))
    
    def _add_frame_hold(self):
        """Add a new frame hold."""
        if not self._frames:
            return
            
        # Get frame index
        frame_idx, ok = QInputDialog.getInt(
            self, "Add Frame Hold", 
            f"Frame number (1-{len(self._frames)}):",
            value=self._current_frame + 1,
            minValue=1, maxValue=len(self._frames)
        )
        
        if ok:
            frame_idx -= 1  # Convert to 0-based index
            
            # Get hold duration
            duration, ok = QInputDialog.getInt(
                self, "Add Frame Hold",
                f"Hold duration for frame {frame_idx + 1} (in frames):",
                value=self._frame_holds.get(frame_idx, 5),
                minValue=1, maxValue=60
            )
            
            if ok:
                self._frame_holds[frame_idx] = duration
                self._update_hold_button_text()
                # Emit signal for persistence
                self.frameHoldsChanged.emit(self.segment_name, self._frame_holds)
    
    def _edit_frame_hold(self, frame_idx: int):
        """Edit an existing frame hold."""
        current_duration = self._frame_holds.get(frame_idx, 5)
        
        duration, ok = QInputDialog.getInt(
            self, "Edit Frame Hold",
            f"Hold duration for frame {frame_idx + 1} (in frames):",
            value=current_duration,
            minValue=0, maxValue=60
        )
        
        if ok:
            if duration > 0:
                self._frame_holds[frame_idx] = duration
            else:
                # Remove hold if duration is 0
                self._frame_holds.pop(frame_idx, None)
            self._update_hold_button_text()
            # Emit signal for persistence
            self.frameHoldsChanged.emit(self.segment_name, self._frame_holds)
    
    def _clear_frame_holds(self):
        """Clear all frame holds."""
        self._frame_holds.clear()
        self._hold_counter = 0
        self._update_hold_button_text()
        # Emit signal for persistence
        self.frameHoldsChanged.emit(self.segment_name, self._frame_holds)
    
    def _add_hold_to_all_frames(self):
        """Add the same hold duration to all frames."""
        if not self._frames:
            return
            
        # Get hold duration
        duration, ok = QInputDialog.getInt(
            self, "Add Hold to All Frames",
            "Hold duration for all frames (in frames):",
            value=5,
            minValue=1, maxValue=60
        )
        
        if ok:
            # Apply to all frames
            for i in range(len(self._frames)):
                self._frame_holds[i] = duration
            
            self._update_hold_button_text()
            # Emit signal for persistence
            self.frameHoldsChanged.emit(self.segment_name, self._frame_holds)
    
    def _update_hold_button_text(self):
        """Update hold button text to show count."""
        if self._frame_holds:
            self.hold_button.setText(f"Holds ({len(self._frame_holds)})")
        else:
            self.hold_button.setText("Holds")
    
    def set_zoom_factor(self, zoom_factor: float):
        """Update the zoom factor and resize the preview."""
        self._zoom_factor = zoom_factor
        base_size = int(120 * self._zoom_factor)
        self.preview_label.setFixedSize(base_size, base_size)
        # Redraw current frame with new size
        self._display_frame(self._current_frame)


class AnimationSegmentPreview(QWidget):
    """Main widget for previewing all animation segments."""
    
    # Signals
    segmentRemoved = Signal(str)  # segment_name
    playbackStateChanged = Signal(str, bool)  # segment_name, is_playing
    segmentBounceChanged = Signal(str, bool)  # segment_name, bounce_mode
    segmentFrameHoldsChanged = Signal(str, dict)  # segment_name, frame_holds
    
    def __init__(self):
        super().__init__()
        self._preview_items: Dict[str, SegmentPreviewItem] = {}
        self._all_frames: List[QPixmap] = []
        self._zoom_factor = 1.0  # Default zoom level
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the main UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title bar
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #E3F2FD;
                border-bottom: 2px solid #2196F3;
                padding: 8px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        
        title = QLabel("Animation Segments")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2;")
        title_layout.addWidget(title)
        
        # Global controls
        self.play_all_button = QPushButton("Play All")
        self.play_all_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.play_all_button.clicked.connect(self._toggle_all_playback)
        title_layout.addWidget(self.play_all_button)
        
        self.stop_all_button = QPushButton("Stop All")
        self.stop_all_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        self.stop_all_button.clicked.connect(self._stop_all_playback)
        title_layout.addWidget(self.stop_all_button)
        
        title_layout.addStretch()
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(4)
        
        # Zoom out button
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.setFixedSize(24, 24)
        self.zoom_out_button.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.zoom_out_button.clicked.connect(self._zoom_out)
        zoom_layout.addWidget(self.zoom_out_button)
        
        # Zoom level label
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #666; font-size: 12px; min-width: 40px; text-align: center;")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        zoom_layout.addWidget(self.zoom_label)
        
        # Zoom in button
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setFixedSize(24, 24)
        self.zoom_in_button.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.zoom_in_button.clicked.connect(self._zoom_in)
        zoom_layout.addWidget(self.zoom_in_button)
        
        title_layout.addLayout(zoom_layout)
        layout.addWidget(title_bar)
        
        # Add keyboard shortcuts for zoom
        from PySide6.QtGui import QKeySequence, QShortcut
        zoom_in_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        zoom_in_shortcut.activated.connect(self._zoom_in)
        zoom_in_shortcut2 = QShortcut(QKeySequence("Ctrl+="), self)  # For keyboards without numpad
        zoom_in_shortcut2.activated.connect(self._zoom_in)
        
        zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        zoom_out_shortcut.activated.connect(self._zoom_out)
        
        # Scroll area for segment previews
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container for preview items
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignTop)
        self.container_layout.setSpacing(4)
        
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)
        
        # Empty state
        self.empty_label = QLabel("No animation segments yet.\nSelect frames and right-click to create.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-style: italic;
                padding: 40px;
            }
        """)
        self.container_layout.addWidget(self.empty_label)
        
    def set_frames(self, frames: List[QPixmap]):
        """Set the available frames for segment extraction."""
        self._all_frames = frames
        
    def add_segment(self, name: str, start_frame: int, end_frame: int, color: QColor,
                   bounce_mode: bool = False, frame_holds: Dict[int, int] = None):
        """Add a new segment preview."""
        if not self._all_frames:
            return
            
        # Extract frames for this segment
        segment_frames = self._all_frames[start_frame:end_frame + 1]
        if not segment_frames:
            return
            
        # Hide empty state
        self.empty_label.hide()
        
        # Create preview item with animation settings and current zoom
        preview_item = SegmentPreviewItem(name, color, segment_frames, bounce_mode, frame_holds, self._zoom_factor)
        preview_item.removeRequested.connect(self._on_remove_requested)
        preview_item.playToggled.connect(self._on_play_toggled)
        preview_item.bounceChanged.connect(self._on_bounce_changed)
        preview_item.frameHoldsChanged.connect(self._on_frame_holds_changed)
        
        # Add to container
        self.container_layout.insertWidget(self.container_layout.count() - 1, preview_item)
        self._preview_items[name] = preview_item
        
    def remove_segment(self, name: str):
        """Remove a segment preview."""
        if name in self._preview_items:
            preview_item = self._preview_items[name]
            preview_item.stop_playback()
            self.container_layout.removeWidget(preview_item)
            preview_item.deleteLater()
            del self._preview_items[name]
            
            # Show empty state if no segments left
            if not self._preview_items:
                self.empty_label.show()
                
    def update_segment(self, name: str, new_name: str = None, color: QColor = None):
        """Update an existing segment."""
        if name in self._preview_items and new_name and new_name != name:
            # Handle rename by recreating (simpler than updating internals)
            preview_item = self._preview_items[name]
            # Store current state
            was_playing = preview_item._is_playing
            frames = preview_item._frames
            
            # Remove old
            self.remove_segment(name)
            
            # Add new
            if color is None:
                color = preview_item.segment_color
            self.add_segment(new_name, 0, len(frames) - 1, color)
            
            # Restore playback state
            if was_playing and new_name in self._preview_items:
                self._preview_items[new_name].set_playing(True)
                
    def clear_segments(self):
        """Clear all segment previews."""
        for name in list(self._preview_items.keys()):
            self.remove_segment(name)
            
    def _on_remove_requested(self, name: str):
        """Handle remove request from preview item."""
        self.segmentRemoved.emit(name)
        
    def _on_play_toggled(self, name: str, is_playing: bool):
        """Handle playback state change."""
        self.playbackStateChanged.emit(name, is_playing)
        
    def _on_bounce_changed(self, name: str, bounce_mode: bool):
        """Handle bounce mode change."""
        self.segmentBounceChanged.emit(name, bounce_mode)
        
    def _on_frame_holds_changed(self, name: str, frame_holds: dict):
        """Handle frame holds change."""
        self.segmentFrameHoldsChanged.emit(name, frame_holds)
        
    def _toggle_all_playback(self):
        """Toggle playback for all segments."""
        # Check if any are playing
        any_playing = any(item._is_playing for item in self._preview_items.values())
        
        # If any playing, stop all. Otherwise, start all.
        target_state = not any_playing
        
        for item in self._preview_items.values():
            item.set_playing(target_state)
            
        # Update button text
        self.play_all_button.setText("Pause All" if target_state else "Play All")
        
    def _stop_all_playback(self):
        """Stop playback for all segments."""
        for item in self._preview_items.values():
            item.stop_playback()
            
        self.play_all_button.setText("Play All")
    
    def _zoom_in(self):
        """Increase zoom level."""
        if self._zoom_factor < 2.0:  # Max zoom 200%
            self._zoom_factor = min(2.0, self._zoom_factor + 0.25)
            self._update_zoom()
    
    def _zoom_out(self):
        """Decrease zoom level."""
        if self._zoom_factor > 0.5:  # Min zoom 50%
            self._zoom_factor = max(0.5, self._zoom_factor - 0.25)
            self._update_zoom()
    
    def _update_zoom(self):
        """Update zoom for all preview items."""
        # Update zoom label
        self.zoom_label.setText(f"{int(self._zoom_factor * 100)}%")
        
        # Update button states
        self.zoom_in_button.setEnabled(self._zoom_factor < 2.0)
        self.zoom_out_button.setEnabled(self._zoom_factor > 0.5)
        
        # Update all preview items
        for item in self._preview_items.values():
            item.set_zoom_factor(self._zoom_factor)