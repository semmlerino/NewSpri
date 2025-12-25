#!/usr/bin/env python3
"""
Enhanced Status Bar Module
==========================

Enhanced status bar with detailed application state information.
Shows frame info, extraction mode, zoom level, FPS, and mouse coordinates.
"""

from typing import Optional
from PySide6.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout
from PySide6.QtCore import QObject, QTimer

from config import Config


class EnhancedStatusBar(QStatusBar):
    """
    Enhanced status bar with multiple information panels.
    
    Layout: [Status Message] | Frame: 3/16 | Size: 32×32 px | Mode: Grid | Zoom: 150% | FPS: 12 | Mouse: (128, 64)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Status message timer for temporary messages
        self._message_timer = QTimer()
        self._message_timer.setSingleShot(True)
        self._message_timer.timeout.connect(self._clear_temporary_message)
        
        # Create permanent status widgets
        self._setup_permanent_widgets()
        
        # Initialize with default values
        self._reset_to_defaults()
    
    def _setup_permanent_widgets(self) -> None:
        """Set up the permanent status bar widgets."""
        # Create a container widget for permanent status
        permanent_widget = QWidget()
        permanent_layout = QHBoxLayout(permanent_widget)
        permanent_layout.setContentsMargins(5, 0, 5, 0)
        permanent_layout.setSpacing(15)
        
        # Frame information
        self._frame_label = QLabel("Frame: -")
        self._frame_label.setToolTip("Current frame / Total frames")
        self._frame_label.setMinimumWidth(80)
        
        # Sprite size information
        self._size_label = QLabel("Size: -")
        self._size_label.setToolTip("Individual sprite dimensions")
        self._size_label.setMinimumWidth(90)
        
        # Extraction mode indicator
        self._mode_label = QLabel("Mode: Grid")
        self._mode_label.setToolTip("Current extraction mode (Grid or CCL)")
        self._mode_label.setMinimumWidth(70)
        self._mode_label.setStyleSheet(self._get_mode_style("grid"))
        
        # Zoom level indicator
        self._zoom_label = QLabel("Zoom: 100%")
        self._zoom_label.setToolTip("Current zoom level")
        self._zoom_label.setMinimumWidth(80)
        
        # FPS indicator
        self._fps_label = QLabel("FPS: 10")
        self._fps_label.setToolTip("Animation frames per second")
        self._fps_label.setMinimumWidth(50)
        
        # Mouse coordinates
        self._mouse_label = QLabel("Mouse: -")
        self._mouse_label.setToolTip("Mouse position in sprite coordinates")
        self._mouse_label.setMinimumWidth(100)
        
        # Add all widgets to layout
        permanent_layout.addWidget(self._frame_label)
        permanent_layout.addWidget(self._create_separator())
        permanent_layout.addWidget(self._size_label)
        permanent_layout.addWidget(self._create_separator())
        permanent_layout.addWidget(self._mode_label)
        permanent_layout.addWidget(self._create_separator())
        permanent_layout.addWidget(self._zoom_label)
        permanent_layout.addWidget(self._create_separator())
        permanent_layout.addWidget(self._fps_label)
        permanent_layout.addWidget(self._create_separator())
        permanent_layout.addWidget(self._mouse_label)
        
        # Add permanent widget to status bar
        self.addPermanentWidget(permanent_widget)
    
    def _create_separator(self) -> QLabel:
        """Create a separator line for the status bar."""
        separator = QLabel("|")
        separator.setStyleSheet("color: #888888;")
        return separator
    
    def _get_mode_style(self, mode: str) -> str:
        """Get stylesheet for extraction mode indicator."""
        if mode.lower() == "grid":
            return """
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-weight: bold;
                }
            """
        elif mode.lower() == "ccl":
            return """
                QLabel {
                    background-color: #2196F3;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-weight: bold;
                }
            """
        else:
            return """
                QLabel {
                    background-color: #888888;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-weight: bold;
                }
            """
    
    def _reset_to_defaults(self) -> None:
        """Reset all status indicators to default values."""
        self.update_frame_info(0, 0)
        self.update_sprite_size(0, 0)
        self.update_extraction_mode("Grid")
        self.update_zoom_level(100.0)
        self.update_fps(Config.Animation.DEFAULT_FPS)
        self.update_mouse_position(None, None)
    
    # Status message methods
    def show_message(self, message: str, timeout: int = 5000) -> None:
        """
        Show a temporary status message.
        
        Args:
            message: Message to display
            timeout: Time in milliseconds before clearing (0 = permanent)
        """
        super().showMessage(message)
        
        if timeout > 0:
            self._message_timer.start(timeout)
    
    def show_permanent_message(self, message: str) -> None:
        """Show a permanent status message."""
        self.show_message(message, 0)
    
    def _clear_temporary_message(self) -> None:
        """Clear temporary status message."""
        self.clearMessage()
    
    # Information update methods
    def update_frame_info(self, current_frame: int, total_frames: int) -> None:
        """
        Update frame information display.
        
        Args:
            current_frame: Current frame number (1-based)
            total_frames: Total number of frames
        """
        if total_frames > 0:
            self._frame_label.setText(f"Frame: {current_frame}/{total_frames}")
        else:
            self._frame_label.setText("Frame: -")
    
    def update_sprite_size(self, width: int, height: int) -> None:
        """
        Update sprite size information.
        
        Args:
            width: Sprite width in pixels
            height: Sprite height in pixels
        """
        if width > 0 and height > 0:
            self._size_label.setText(f"Size: {width}×{height} px")
        else:
            self._size_label.setText("Size: -")
    
    def update_extraction_mode(self, mode: str) -> None:
        """
        Update extraction mode indicator.
        
        Args:
            mode: Current extraction mode ("Grid", "CCL", etc.)
        """
        self._mode_label.setText(f"Mode: {mode}")
        self._mode_label.setStyleSheet(self._get_mode_style(mode))
        self._mode_label.setToolTip(f"Current extraction mode: {mode}")
    
    def update_zoom_level(self, zoom_percent: float) -> None:
        """
        Update zoom level indicator.
        
        Args:
            zoom_percent: Zoom level as percentage (100.0 = 100%)
        """
        self._zoom_label.setText(f"Zoom: {zoom_percent:.0f}%")
        self._zoom_label.setToolTip(f"Current zoom level: {zoom_percent:.1f}%")
    
    def update_fps(self, fps: int) -> None:
        """
        Update FPS indicator.
        
        Args:
            fps: Frames per second
        """
        self._fps_label.setText(f"FPS: {fps}")
        self._fps_label.setToolTip(f"Animation speed: {fps} frames per second")
    
    def update_mouse_position(self, x: Optional[int], y: Optional[int]) -> None:
        """
        Update mouse position indicator.
        
        Args:
            x: Mouse X coordinate in sprite space (None if not available)
            y: Mouse Y coordinate in sprite space (None if not available)
        """
        if x is not None and y is not None:
            self._mouse_label.setText(f"Mouse: ({x}, {y})")
            self._mouse_label.setToolTip(f"Mouse position in sprite coordinates: ({x}, {y})")
        else:
            self._mouse_label.setText("Mouse: -")
            self._mouse_label.setToolTip("Mouse position not available")
    
    # Convenience methods for common status updates
    def show_loading_message(self, filename: str) -> None:
        """Show loading message for a file."""
        self.show_message(f"Loading: {filename}...", 0)
    
    def show_loaded_message(self, filename: str) -> None:
        """Show successful load message."""
        self.show_message(f"Loaded: {filename}", 3000)
    
    def show_error_message(self, error: str) -> None:
        """Show error message."""
        self.show_message(f"Error: {error}", 5000)
    
    def show_export_message(self, export_type: str, count: int = 1) -> None:
        """Show export completion message."""
        if count == 1:
            self.show_message(f"Exported {export_type}", 3000)
        else:
            self.show_message(f"Exported {count} {export_type}", 3000)
    
    def show_auto_detection_message(self, result: str) -> None:
        """Show auto-detection result message."""
        self.show_message(f"Auto-detect: {result}", 4000)
    
    def show_welcome_message(self) -> None:
        """Show welcome message."""
        self.show_permanent_message(Config.App.WELCOME_MESSAGE)
    
    def show_ready_message(self) -> None:
        """Show ready message."""
        self.show_permanent_message(Config.App.READY_MESSAGE)
    
    # State management methods
    def update_sprite_loaded_state(self, width: int, height: int, frame_count: int, mode: str) -> None:
        """
        Update status bar for loaded sprite state.
        
        Args:
            width: Sprite width
            height: Sprite height
            frame_count: Number of frames
            mode: Extraction mode
        """
        self.update_sprite_size(width, height)
        self.update_frame_info(1, frame_count)
        self.update_extraction_mode(mode)
    
    def update_animation_state(self, current_frame: int, total_frames: int, fps: int) -> None:
        """
        Update status bar for animation state.
        
        Args:
            current_frame: Current frame (1-based)
            total_frames: Total frames
            fps: Current FPS
        """
        self.update_frame_info(current_frame, total_frames)
        self.update_fps(fps)
    
    def reset_for_no_sprite(self) -> None:
        """Reset status bar when no sprite is loaded."""
        self._reset_to_defaults()
        self.show_welcome_message()


class StatusBarManager(QObject):
    """
    Manager class for coordinating status bar updates with application state.
    """
    
    def __init__(self, status_bar: EnhancedStatusBar):
        super().__init__()
        self._status_bar = status_bar
        
        # Track current state
        self._current_frame = 0
        self._total_frames = 0
        self._sprite_width = 0
        self._sprite_height = 0
        self._extraction_mode = "Grid"
        self._zoom_level = 100.0
        self._fps = Config.Animation.DEFAULT_FPS
    
    def connect_to_sprite_model(self, sprite_model) -> None:
        """Connect to sprite model signals for automatic updates."""
        if hasattr(sprite_model, 'frameChanged'):
            sprite_model.frameChanged.connect(self._on_frame_changed)
        if hasattr(sprite_model, 'dataLoaded'):
            sprite_model.dataLoaded.connect(self._on_sprite_loaded)
    
    def connect_to_animation_controller(self, animation_controller) -> None:
        """Connect to animation controller signals."""
        if hasattr(animation_controller, 'frameChanged'):
            animation_controller.frameChanged.connect(self._on_frame_changed)
        if hasattr(animation_controller, 'fpsChanged'):
            animation_controller.fpsChanged.connect(self._on_fps_changed)
    
    def connect_to_canvas(self, canvas) -> None:
        """Connect to canvas signals for zoom and mouse tracking."""
        if hasattr(canvas, 'zoomChanged'):
            canvas.zoomChanged.connect(self._on_zoom_changed)
        if hasattr(canvas, 'mouseMoved'):
            canvas.mouseMoved.connect(self._on_mouse_moved)
    
    def _on_frame_changed(self, current_frame: int, total_frames: int = None) -> None:
        """Handle frame change signal."""
        self._current_frame = current_frame
        if total_frames is not None:
            self._total_frames = total_frames
        self._status_bar.update_frame_info(self._current_frame, self._total_frames)
    
    def _on_sprite_loaded(self, filepath: str) -> None:
        """Handle sprite loaded signal."""
        # This would need to be connected to get sprite dimensions and frame count
        # Implementation depends on sprite model interface
        pass
    
    def _on_fps_changed(self, fps: int) -> None:
        """Handle FPS change signal."""
        self._fps = fps
        self._status_bar.update_fps(fps)
    
    def _on_zoom_changed(self, zoom_factor: float) -> None:
        """Handle zoom change signal."""
        self._zoom_level = zoom_factor * 100.0
        self._status_bar.update_zoom_level(self._zoom_level)
    
    def _on_mouse_moved(self, x: int, y: int) -> None:
        """Handle mouse movement signal."""
        self._status_bar.update_mouse_position(x, y)
    
    def update_extraction_mode(self, mode: str) -> None:
        """Update extraction mode."""
        self._extraction_mode = mode
        self._status_bar.update_extraction_mode(mode)
    
    def update_sprite_info(self, width: int, height: int, frame_count: int) -> None:
        """Update sprite information."""
        self._sprite_width = width
        self._sprite_height = height
        self._total_frames = frame_count
        self._status_bar.update_sprite_size(width, height)
        self._status_bar.update_frame_info(self._current_frame, frame_count)
    
    def show_message(self, message: str, timeout: int = 5000) -> None:
        """Show a status message. Delegates to wrapped status bar."""
        self._status_bar.show_message(message, timeout)
    
    def update_mouse_position(self, x: int, y: int) -> None:
        """Update mouse position display. Delegates to wrapped status bar."""
        self._status_bar.update_mouse_position(x, y)