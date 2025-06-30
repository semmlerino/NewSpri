"""
Sprite Viewer - Main application window (REFACTORED)
Modern sprite sheet animation viewer with improved usability.
Refactored to use centralized managers for better maintainability.
"""

import sys
import os
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget,
    QSplitter, QLabel, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent

from config import Config
from styles import StyleManager

# Core MVC Components
from sprite_model import SpriteModel
from animation_controller import AnimationController
from auto_detection_controller import AutoDetectionController

# Managers (Phase 5 refactoring)
from shortcut_manager import get_shortcut_manager
from action_manager import get_action_manager
from menu_manager import get_menu_manager

# UI Managers
from settings_manager import get_settings_manager
from recent_files_manager import get_recent_files_manager
from enhanced_status_bar import EnhancedStatusBar, StatusBarManager

# Export System
from export_dialog import ExportDialog
from frame_exporter import get_frame_exporter

# Phase 5: Extracted UI Components
from sprite_canvas import SpriteCanvas
from playback_controls import PlaybackControls
from frame_extractor import FrameExtractor


class SpriteViewer(QMainWindow):
    """
    Main sprite viewer application window.
    Refactored to use centralized managers for better maintainability.
    
    Responsibilities (after refactoring):
    - Component coordination and integration
    - High-level event handling
    - Window state management
    - Signal routing between components
    """

    def __init__(self):
        """Initialize sprite viewer with manager-based architecture."""
        super().__init__()
        
        # Initialize managers first
        self._init_managers()
        
        # Initialize core MVC components
        self._init_core_components()
        
        # Set up UI using managers
        self._setup_ui()
        self._setup_managers()
        
        # Connect all signals
        self._connect_signals()
        
        # Initialize auto-detection controller after UI setup
        self._auto_detection_controller.initialize(self._sprite_model, self._frame_extractor)
        
        # Apply settings and show welcome
        self._apply_settings()
        self._show_welcome_message()
    
    def _init_managers(self):
        """Initialize all centralized managers."""
        # Get manager instances (singletons)
        self._shortcut_manager = get_shortcut_manager(self)
        self._action_manager = get_action_manager(self)
        self._menu_manager = get_menu_manager(self)
        self._settings_manager = get_settings_manager()
        self._recent_files = get_recent_files_manager()
    
    def _init_core_components(self):
        """Initialize core MVC components."""
        # Model layer
        self._sprite_model = SpriteModel()
        
        # Controller layer
        self._animation_controller = AnimationController()
        self._animation_controller.initialize(self._sprite_model, self)
        
        self._auto_detection_controller = AutoDetectionController()
        
        # Status management will be initialized after status bar is created
        self._status_manager = None
    
    def _setup_ui(self):
        """Set up user interface using manager-based architecture."""
        self.setWindowTitle("Python Sprite Viewer")
        self.setMinimumSize(Config.UI.MIN_WINDOW_WIDTH, Config.UI.MIN_WINDOW_HEIGHT)
        
        # Enable drag & drop
        self.setAcceptDrops(True)
        
        # Set up managers
        self._setup_menu_bar()
        self._setup_toolbar() 
        self._setup_status_bar()
        
        # Set up main content area
        self._setup_main_content()
    
    def _setup_managers(self):
        """Configure managers with application-specific settings."""
        # Configure action manager with callbacks
        self._setup_action_callbacks()
        
        # Configure shortcut manager context
        self._update_manager_context()
        
        # Configure menu manager with recent files
        self._menu_manager.set_recent_files_handler(
            lambda menu: self._recent_files.create_recent_files_menu(menu)
        )
    
    def _setup_action_callbacks(self):
        """Set up action callbacks using ActionManager."""
        # File actions
        self._action_manager.set_action_callback('file_open', self._load_sprites)
        self._action_manager.set_action_callback('file_quit', self.close)
        self._action_manager.set_action_callback('file_export_frames', self._export_frames)
        self._action_manager.set_action_callback('file_export_current', self._export_current_frame)
        
        # View actions
        self._action_manager.set_action_callback('view_zoom_in', self._zoom_in)
        self._action_manager.set_action_callback('view_zoom_out', self._zoom_out)
        self._action_manager.set_action_callback('view_zoom_fit', self._zoom_fit)
        self._action_manager.set_action_callback('view_zoom_reset', self._zoom_reset)
        self._action_manager.set_action_callback('view_toggle_grid', self._toggle_grid)
        
        # Animation actions
        self._action_manager.set_action_callback('animation_toggle', 
                                               lambda: self._animation_controller.toggle_playback())
        self._action_manager.set_action_callback('animation_prev_frame', self._go_to_prev_frame)
        self._action_manager.set_action_callback('animation_next_frame', self._go_to_next_frame)
        self._action_manager.set_action_callback('animation_first_frame', self._go_to_first_frame)
        self._action_manager.set_action_callback('animation_last_frame', self._go_to_last_frame)
        
        # Toolbar actions (reuse same callbacks)
        self._action_manager.set_action_callback('toolbar_export', self._export_frames)
        
        # Help actions  
        self._action_manager.set_action_callback('help_shortcuts', self._show_shortcuts)
        self._action_manager.set_action_callback('help_about', self._show_about)
    
    def _setup_menu_bar(self):
        """Set up menu bar using MenuManager."""
        menubar = self.menuBar()
        self._menus = self._menu_manager.create_menu_bar(menubar)
    
    def _setup_toolbar(self):
        """Set up toolbar using MenuManager."""
        # Create main toolbar
        self._main_toolbar = self._menu_manager.create_toolbar('main')
        
        # Apply styling
        if self._main_toolbar:
            self._main_toolbar.setStyleSheet(StyleManager.get_main_toolbar())
            
            # Add zoom display widget
            self._main_toolbar.addSeparator()
            self._zoom_label = QLabel("100%")
            self._zoom_label.setMinimumWidth(Config.UI.ZOOM_LABEL_MIN_WIDTH)
            self._zoom_label.setAlignment(Qt.AlignCenter)
            self._zoom_label.setStyleSheet(StyleManager.get_zoom_display())
            self._main_toolbar.addWidget(self._zoom_label)
    
    def _setup_status_bar(self):
        """Set up status bar."""
        status_bar = EnhancedStatusBar(self)
        self.setStatusBar(status_bar)
        self._status_manager = StatusBarManager(status_bar)
    
    def _setup_main_content(self):
        """Set up main content area."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create splitter for responsive layout
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side - Canvas
        self._canvas = self._create_canvas_section()
        splitter.addWidget(self._canvas)
        
        # Right side - Controls
        controls_widget = self._create_controls_section()
        splitter.addWidget(controls_widget)
        
        # Set splitter proportions
        splitter.setSizes([700, 300])  # Canvas gets more space
        splitter.setCollapsible(0, False)  # Canvas not collapsible
        splitter.setCollapsible(1, False)  # Controls not collapsible
        
        # Info label at bottom
        self._info_label = QLabel("Ready - Drag and drop a sprite sheet or use File > Open")
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet(StyleManager.get_info_label())
        main_layout.addWidget(self._info_label)
    
    def _create_canvas_section(self) -> QWidget:
        """Create canvas section."""
        self._canvas = SpriteCanvas()
        # Set sprite model reference for canvas to get current frame
        self._canvas.set_sprite_model(self._sprite_model)
        return self._canvas
    
    def _create_controls_section(self) -> QWidget:
        """Create controls section."""
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)
        
        # Playback controls
        self._playback_controls = PlaybackControls()
        controls_layout.addWidget(self._playback_controls)
        
        # Frame extractor
        self._frame_extractor = FrameExtractor()
        controls_layout.addWidget(self._frame_extractor)
        
        # Stretch to push everything to top
        controls_layout.addStretch()
        
        return controls_widget
    
    def _connect_signals(self):
        """Connect signals between components."""
        # Sprite model signals
        self._sprite_model.frameChanged.connect(self._on_frame_changed)
        self._sprite_model.dataLoaded.connect(self._on_sprite_loaded)
        self._sprite_model.extractionCompleted.connect(self._on_extraction_completed)
        
        # Animation controller signals
        self._animation_controller.animationStarted.connect(self._on_playback_started)
        self._animation_controller.animationPaused.connect(self._on_playback_paused)
        self._animation_controller.animationStopped.connect(self._on_playback_stopped)
        self._animation_controller.animationCompleted.connect(self._on_playback_completed)
        self._animation_controller.frameAdvanced.connect(self._on_frame_advanced)
        self._animation_controller.errorOccurred.connect(self._on_animation_error)
        self._animation_controller.statusChanged.connect(self._status_manager.show_message)
        
        # Auto-detection controller signals
        self._auto_detection_controller.frameSettingsDetected.connect(self._on_frame_settings_detected)
        self._auto_detection_controller.statusUpdate.connect(self._on_detection_status_update)
        
        # Canvas signals
        self._canvas.zoomChanged.connect(self._on_zoom_changed)
        self._canvas.mouseMoved.connect(self._status_manager.update_mouse_position)
        
        # Frame extractor signals
        self._frame_extractor.settingsChanged.connect(self._update_frame_slicing)
        self._frame_extractor.modeChanged.connect(self._on_extraction_mode_changed)
        
        # Playback controls signals
        self._playback_controls.playPauseClicked.connect(self._animation_controller.toggle_playback)
        self._playback_controls.frameChanged.connect(self._sprite_model.set_current_frame)
        self._playback_controls.fpsChanged.connect(self._animation_controller.set_fps)
        self._playback_controls.loopToggled.connect(self._animation_controller.set_loop_mode)
        
        # Navigation button signals (need to connect the actual buttons)
        self._playback_controls.prev_btn.clicked.connect(self._go_to_prev_frame)
        self._playback_controls.next_btn.clicked.connect(self._go_to_next_frame)
    
    def _apply_settings(self):
        """Apply saved settings."""
        # Restore window geometry
        self._settings_manager.restore_window_geometry(self)
    
    def _update_manager_context(self):
        """Update manager context based on current state."""
        has_frames = bool(self._sprite_model.sprite_frames)
        is_playing = self._animation_controller.is_playing
        
        # Update both managers
        self._shortcut_manager.update_context(
            has_frames=has_frames,
            is_playing=is_playing
        )
        self._action_manager.update_context(
            has_frames=has_frames,
            is_playing=is_playing
        )
    
    
    # ============================================================================
    # FILE OPERATIONS
    # ============================================================================
    
    def _load_sprites(self):
        """Load sprite files or sprite sheet."""
        from PySide6.QtWidgets import QFileDialog
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Load Sprite Sheet", "", 
            f"Images ({Config.File.IMAGE_FILTER})"
        )
        
        if file_path:
            self._load_sprite_file(file_path)
    
    def _load_sprite_file(self, file_path: str):
        """Load a sprite file."""
        success, error_message = self._sprite_model.load_sprite_sheet(file_path)
        
        if success:
            # Add to recent files
            self._recent_files.add_file_to_recent(file_path)
            
            # Update context for managers
            self._update_manager_context()
            
            # Update display first (fast)
            self._canvas.update()
            self._info_label.setText(self._sprite_model.sprite_info)
            
            # Trigger appropriate detection based on current extraction mode
            current_mode = self._frame_extractor.get_extraction_mode()
            if current_mode == "ccl":
                # For CCL mode, try direct CCL extraction without grid auto-detection
                self._status_manager.show_message("Running CCL extraction...")
                self._update_frame_slicing()  # This will trigger CCL extraction
            else:
                # For grid mode, run comprehensive grid auto-detection
                self._auto_detection_controller.run_comprehensive_detection_with_dialog()
        else:
            QMessageBox.critical(self, "Load Error", error_message)
    
    # ============================================================================
    # EXPORT OPERATIONS
    # ============================================================================
    
    def _export_frames(self):
        """Show export dialog for exporting frames."""
        if not self._sprite_model.sprite_frames:
            QMessageBox.warning(self, "No Frames", "No frames to export.")
            return
        
        dialog = ExportDialog(
            self,
            frame_count=len(self._sprite_model.sprite_frames),
            current_frame=self._sprite_model.current_frame
        )
        dialog.exportRequested.connect(self._handle_export_request)
        dialog.exec()
    
    def _export_current_frame(self):
        """Export only the current frame."""
        if not self._sprite_model.sprite_frames:
            QMessageBox.warning(self, "No Frames", "No frames to export.")
            return
        
        dialog = ExportDialog(
            self,
            frame_count=len(self._sprite_model.sprite_frames),
            current_frame=self._sprite_model.current_frame
        )
        
        # Pre-configure for single frame export
        dialog.selected_radio.setChecked(True)
        dialog._update_ui_state()
        
        dialog.exportRequested.connect(self._handle_export_request)
        dialog.exec()
    
    def _handle_export_request(self, settings: dict):
        """Handle export request from dialog."""
        exporter = get_frame_exporter()
        
        success = exporter.export_frames(
            frames=self._sprite_model.sprite_frames,
            output_dir=settings['output_dir'],
            base_name=settings['base_name'],
            format=settings['format'],
            mode=settings['mode'],
            scale_factor=settings['scale_factor'],
            pattern=settings.get('pattern', Config.Export.DEFAULT_PATTERN),
            selected_indices=settings.get('selected_indices', None)
        )
        
        if not success:
            QMessageBox.critical(self, "Export Failed", "Failed to start export.")
    
    # ============================================================================
    # VIEW OPERATIONS
    # ============================================================================
    
    def _zoom_in(self):
        """Zoom in on canvas."""
        self._canvas.zoom_in()
    
    def _zoom_out(self):
        """Zoom out on canvas."""
        self._canvas.zoom_out()
    
    def _zoom_fit(self):
        """Fit canvas to window."""
        self._canvas.fit_to_window()
    
    def _zoom_reset(self):
        """Reset canvas zoom to 100%."""
        self._canvas.reset_view()
    
    def _toggle_grid(self):
        """Toggle grid overlay."""
        self._canvas.toggle_grid()
    
    def _on_zoom_changed(self, zoom_factor: float):
        """Handle zoom change."""
        percentage = int(zoom_factor * 100)
        self._zoom_label.setText(f"{percentage}%")
    
    # ============================================================================
    # ANIMATION OPERATIONS
    # ============================================================================
    
    def _go_to_prev_frame(self):
        """Go to previous frame."""
        self._sprite_model.previous_frame()
    
    def _go_to_next_frame(self):
        """Go to next frame."""
        self._sprite_model.next_frame()
    
    def _go_to_first_frame(self):
        """Go to first frame."""
        self._sprite_model.first_frame()
    
    def _go_to_last_frame(self):
        """Go to last frame."""
        self._sprite_model.last_frame()
    
    # ============================================================================
    # SIGNAL HANDLERS
    # ============================================================================
    
    def _on_frame_changed(self, frame_index: int, total_frames: int):
        """Handle frame change."""
        # Update canvas frame info and trigger repaint with new frame
        self._canvas.set_frame_info(frame_index, total_frames)
        self._canvas.update_with_current_frame()
        
        # Update playback controls
        self._playback_controls.set_current_frame(frame_index)
    
    def _on_sprite_loaded(self, file_path: str):
        """Handle sprite loaded."""
        self._canvas.reset_view()
        self._canvas.update()
        
        # Update managers context
        self._update_manager_context()
        
        # Enable CCL mode - always available when sprite is loaded
        self._frame_extractor.set_ccl_available(True, 0)
    
    def _on_extraction_completed(self, frame_count: int):
        """Handle extraction completion."""
        if frame_count > 0:
            self._playback_controls.set_frame_range(frame_count - 1)
            self._playback_controls.update_button_states(True, True, False)
            
            # Update canvas with frame info
            current_frame = self._sprite_model.current_frame
            self._canvas.set_frame_info(current_frame, frame_count)
        else:
            self._playback_controls.set_frame_range(0)
            self._playback_controls.update_button_states(False, False, False)
            self._canvas.set_frame_info(0, 0)
        
        # Update managers context
        self._update_manager_context()
        
        # Update display with current frame
        self._canvas.update_with_current_frame()
    
    def _on_playback_started(self):
        """Handle playback start."""
        self._playback_controls.update_button_states(False, True, True)
        self._update_manager_context()
    
    def _on_playback_paused(self):
        """Handle playback pause."""
        self._playback_controls.update_button_states(True, True, True)
        self._update_manager_context()
    
    def _on_playback_stopped(self):
        """Handle playback stop."""
        self._playback_controls.update_button_states(True, True, False)
        self._update_manager_context()
    
    def _on_playback_completed(self):
        """Handle playback completion."""
        self._playback_controls.update_button_states(True, True, False)
        self._update_manager_context()
    
    def _on_frame_advanced(self, frame_index: int):
        """Handle frame advancement from animation controller."""
        # Frame advancement is handled by the animation controller
        # UI updates happen through sprite model frameChanged signal
        pass
    
    def _on_animation_error(self, error_message: str):
        """Handle animation controller error."""
        QMessageBox.warning(self, "Animation Error", error_message)
    
    def _on_frame_settings_detected(self, width: int, height: int):
        """Handle frame settings detected."""
        self._frame_extractor.set_frame_size(width, height)
        self._update_frame_slicing()
    
    def _on_detection_status_update(self, message: str):
        """Handle detection status update."""
        self._status_manager.show_message(message)
    
    def _on_extraction_mode_changed(self, mode: str):
        """Handle extraction mode change (grid vs CCL)."""
        if not self._sprite_model.original_sprite_sheet:
            return
        
        # Update sprite model extraction mode
        self._sprite_model.set_extraction_mode(mode)
        
        # Update info label immediately to reflect mode change
        self._info_label.setText(self._sprite_model.sprite_info)
        
        # Re-extract frames with new mode
        self._update_frame_slicing()
        
        # Update status
        mode_name = "CCL" if mode == "ccl" else "Grid"
        self._status_manager.show_message(f"Switched to {mode_name} extraction mode")
    
    def _update_frame_slicing(self):
        """Update frame slicing based on current settings."""
        if not self._sprite_model.original_sprite_sheet:
            return
        
        # Get current extraction mode
        mode = self._frame_extractor.get_extraction_mode()
        
        if mode == "ccl":
            # Use CCL extraction
            success, error_message, total_frames = self._sprite_model.extract_ccl_frames()
        else:
            # Get frame extraction settings for grid mode
            frame_width, frame_height = self._frame_extractor.get_frame_size()
            offset_x, offset_y = self._frame_extractor.get_offset()
            spacing_x, spacing_y = self._frame_extractor.get_spacing()
            
            # Extract frames using grid mode
            success, error_message, total_frames = self._sprite_model.extract_frames(
                frame_width, frame_height, offset_x, offset_y, spacing_x, spacing_y
            )
        
        if not success:
            QMessageBox.warning(self, "Frame Extraction Error", error_message)
            return
        
        # Update info
        self._info_label.setText(self._sprite_model.sprite_info)
        
        # Update managers context
        self._update_manager_context()
        
        # Ensure first frame is displayed after extraction
        if total_frames > 0:
            self._sprite_model.set_current_frame(0)
            self._canvas.update_with_current_frame()
    
    # ============================================================================
    # HELP DIALOGS
    # ============================================================================
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog using ShortcutManager."""
        help_html = self._shortcut_manager.generate_help_html()
        QMessageBox.information(self, "Keyboard Shortcuts", help_html)
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """
<h3>Python Sprite Viewer</h3>
<p>Version 2.0 (Refactored)</p>
<p>A modern sprite sheet animation viewer with improved usability and architecture.</p>
<p>Features:</p>
<ul>
<li>Automatic frame extraction</li>
<li>Smooth animation playback</li>
<li>Intuitive controls</li>
<li>Smart size detection</li>
<li>Frame export (PNG, JPG, BMP, GIF)</li>
<li>Sprite sheet generation</li>
<li>Centralized manager architecture</li>
</ul>
        """
        QMessageBox.about(self, "About Sprite Viewer", about_text)
    
    def _show_welcome_message(self):
        """Show welcome message."""
        self._info_label.setText("Ready - Drag and drop a sprite sheet or use File > Open")
    
    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._canvas.setStyleSheet(StyleManager.get_canvas_drag_hover())
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self._canvas.setStyleSheet(StyleManager.get_canvas_normal())
        self._show_welcome_message()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        self._canvas.setStyleSheet(StyleManager.get_canvas_normal())
        
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            self._load_sprite_file(file_path)
            event.acceptProposedAction()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts using ShortcutManager."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Create key sequence string
        key_sequence = ""
        if modifiers & Qt.ControlModifier:
            key_sequence += "Ctrl+"
        if modifiers & Qt.ShiftModifier:
            key_sequence += "Shift+"
        if modifiers & Qt.AltModifier:
            key_sequence += "Alt+"
        
        # Add key name
        if key == Qt.Key_Space:
            key_sequence += "Space"
        elif key == Qt.Key_Left:
            key_sequence += "Left"
        elif key == Qt.Key_Right:
            key_sequence += "Right"
        elif key == Qt.Key_Home:
            key_sequence += "Home"
        elif key == Qt.Key_End:
            key_sequence += "End"
        elif key == Qt.Key_G:
            key_sequence += "G"
        elif key == Qt.Key_Plus:
            key_sequence += "+"
        elif key == Qt.Key_Minus:
            key_sequence += "-"
        elif key == Qt.Key_0:
            key_sequence += "0"
        elif key == Qt.Key_1:
            key_sequence += "1"
        elif key == Qt.Key_O:
            key_sequence += "O"
        elif key == Qt.Key_Q:
            key_sequence += "Q"
        elif key == Qt.Key_E:
            key_sequence += "E"
        else:
            # Let parent handle other keys
            super().keyPressEvent(event)
            return
        
        # Try to handle with shortcut manager
        if self._shortcut_manager.handle_key_press(key_sequence):
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle close event."""
        # Save settings
        self._settings_manager.save_window_geometry(self)
        
        # Accept close
        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Python Sprite Viewer")
    app.setApplicationVersion("2.0 (Refactored)")
    
    # Set application style
    app.setStyle("Fusion")
    
    viewer = SpriteViewer()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()