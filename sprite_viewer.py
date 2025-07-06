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
    QSplitter, QLabel, QSizePolicy, QTabWidget, QPushButton, QDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QKeySequence

from config import Config
from utils import StyleManager

# Coordinator system (Phase 1 refactoring)
from coordinators import CoordinatorRegistry, UISetupHelper, ViewCoordinator, ExportCoordinator, AnimationCoordinator, EventCoordinator, DialogCoordinator

# Core MVC Components
from sprite_model import SpriteModel
from core import AnimationController, AutoDetectionController, FileController, AnimationSegmentController

# Managers (Phase 5 refactoring)
from managers import (
    get_shortcut_manager, get_actionmanager, get_menu_manager,
    get_settings_manager, get_recent_files_manager, AnimationSegmentManager
)

# UI Components
from ui import (
    SpriteCanvas, PlaybackControls, FrameExtractor,
    AnimationGridView, EnhancedStatusBar, StatusBarManager
)

# Export System
from export import get_frame_exporter, ExportHandler


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
        
        # Initialize coordinator registry (Phase 1 refactoring)
        self._coordinator_registry = CoordinatorRegistry()
        
        # Initialize managers first
        self._init_managers()
        
        # Initialize core MVC components
        self._init_core_components()
        
        # Set up recent files handler BEFORE creating menus
        self._menu_manager.set_recent_files_handler(
            lambda menu: self._recent_files.populate_recent_files_directly(menu)
        )
        
        # Initialize UI Setup Helper (Phase 2 refactoring)
        self._ui_helper = UISetupHelper(self)
        self._coordinator_registry.register('ui_setup', self._ui_helper)
        
        # Initialize UI helper with dependencies
        ui_dependencies = {
            'menu_manager': self._menu_manager,
            'action_manager': self._action_manager,
            'shortcut_manager': self._shortcut_manager,
            'segment_manager': self._segment_manager,
            'sprite_model': self._sprite_model,
            'segment_controller': self._segment_controller
        }
        self._ui_helper.initialize(ui_dependencies)
        
        # Set up UI using UI helper
        ui_components = self._ui_helper.setup_ui()
        
        # Extract UI components from helper
        self._tab_widget = ui_components['tab_widget']
        self._canvas = ui_components['canvas']
        self._playback_controls = ui_components['playback_controls']
        self._frame_extractor = ui_components['frame_extractor']
        self._grid_view = ui_components['grid_view']
        self._segment_preview = ui_components['segment_preview']
        self._info_label = ui_components['info_label']
        self._zoom_label = ui_components['zoom_label']
        self._main_toolbar = ui_components['main_toolbar']
        self._status_manager = ui_components['status_manager']
        self._menus = ui_components['menus']
        
        # Initialize View Coordinator (Phase 3 refactoring)
        self._view_coordinator = ViewCoordinator(self)
        self._coordinator_registry.register('view', self._view_coordinator)
        
        # Initialize view coordinator with dependencies
        view_dependencies = {
            'canvas': self._canvas,
            'zoom_label': self._zoom_label
        }
        self._view_coordinator.initialize(view_dependencies)
        
        # Initialize Export Coordinator (Phase 4 refactoring)
        self._export_coordinator = ExportCoordinator(self)
        self._coordinator_registry.register('export', self._export_coordinator)
        
        # Initialize export coordinator with dependencies
        export_dependencies = {
            'sprite_model': self._sprite_model,
            'segment_manager': self._segment_manager,
            'export_handler': self._export_handler
        }
        self._export_coordinator.initialize(export_dependencies)
        
        # Initialize Animation Coordinator (Phase 5 refactoring)
        self._animation_coordinator = AnimationCoordinator(self)
        self._coordinator_registry.register('animation', self._animation_coordinator)
        
        # Initialize animation coordinator with dependencies
        animation_dependencies = {
            'sprite_model': self._sprite_model,
            'animation_controller': self._animation_controller,
            'playback_controls': self._playback_controls,
            'action_manager': self._action_manager,
            'status_manager': self._status_manager
        }
        self._animation_coordinator.initialize(animation_dependencies)
        
        # Initialize Event Coordinator (Phase 6 refactoring)
        self._event_coordinator = EventCoordinator(self)
        self._coordinator_registry.register('event', self._event_coordinator)
        
        # Initialize event coordinator with dependencies
        event_dependencies = {
            'shortcut_manager': self._shortcut_manager,
            'file_controller': self._file_controller,
            'view_coordinator': self._view_coordinator,
            'status_manager': self._status_manager,
            'show_welcome_message': self._show_welcome_message
        }
        self._event_coordinator.initialize(event_dependencies)
        
        # Initialize Dialog Coordinator (Phase 7 refactoring)
        self._dialog_coordinator = DialogCoordinator(self)
        self._coordinator_registry.register('dialog', self._dialog_coordinator)
        
        # Initialize dialog coordinator with dependencies
        dialog_dependencies = {
            'shortcut_manager': self._shortcut_manager
        }
        self._dialog_coordinator.initialize(dialog_dependencies)
        
        # Set up managers with UI components
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
        self._action_manager = get_actionmanager(self)
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
        
        # File operations controller
        self._file_controller = FileController()
        self._file_controller.file_loaded.connect(self._on_file_loaded)
        self._file_controller.file_load_failed.connect(self._on_file_load_failed)
        
        self._auto_detection_controller = AutoDetectionController()
        
        # Animation segment controller
        self._segment_controller = AnimationSegmentController(self)
        
        # Animation splitting components
        self._segment_manager = AnimationSegmentManager()
        self._grid_view = None  # Will be initialized in UI setup
        
        # Status management will be initialized after status bar is created
        self._status_manager = None
        
        # Export handler for centralized export logic
        self._export_handler = ExportHandler(self)
    
    
    def _setup_managers(self):
        """Configure managers with application-specific settings."""
        # Configure action manager with callbacks
        self._setup_action_callbacks()
        
        # Configure segment controller dependencies
        self._segment_controller.set_segment_manager(self._segment_manager)
        self._segment_controller.set_export_handler(self._export_handler)
        self._segment_controller.set_grid_view(self._grid_view)
        self._segment_controller.set_sprite_model(self._sprite_model)
        self._segment_controller.set_tab_widget(self._tab_widget)
        self._segment_controller.set_segment_preview(self._segment_preview)
        
        # Connect segment controller status messages
        self._segment_controller.statusMessage.connect(self._status_manager.show_message)
        
        # Configure shortcut manager context
        self._update_manager_context()
    
    def _setup_action_callbacks(self):
        """Set up action callbacks using ActionManager."""
        # File actions
        self._action_manager.set_action_callback('file_open', self._load_sprites)
        self._action_manager.set_action_callback('file_quit', self.close)
        self._action_manager.set_action_callback('file_export_frames', self._export_coordinator.export_frames)
        self._action_manager.set_action_callback('file_export_current', self._export_coordinator.export_current_frame)
        
        # View actions (Phase 3 refactoring - use ViewCoordinator)
        self._action_manager.set_action_callback('view_zoom_in', self._view_coordinator.zoom_in)
        self._action_manager.set_action_callback('view_zoom_out', self._view_coordinator.zoom_out)
        self._action_manager.set_action_callback('view_zoom_fit', self._view_coordinator.zoom_fit)
        self._action_manager.set_action_callback('view_zoom_reset', self._view_coordinator.zoom_reset)
        self._action_manager.set_action_callback('view_toggle_grid', self._view_coordinator.toggle_grid)
        
        # Animation actions (Phase 5 refactoring - use AnimationCoordinator)
        self._action_manager.set_action_callback('animation_toggle', self._animation_coordinator.toggle_playback)
        self._action_manager.set_action_callback('animation_prev_frame', self._animation_coordinator.go_to_prev_frame)
        self._action_manager.set_action_callback('animation_next_frame', self._animation_coordinator.go_to_next_frame)
        self._action_manager.set_action_callback('animation_first_frame', self._animation_coordinator.go_to_first_frame)
        self._action_manager.set_action_callback('animation_last_frame', self._animation_coordinator.go_to_last_frame)
        self._action_manager.set_action_callback('animation_restart', self._animation_coordinator.restart_animation)
        self._action_manager.set_action_callback('animation_speed_decrease', self._animation_coordinator.decrease_animation_speed)
        self._action_manager.set_action_callback('animation_speed_increase', self._animation_coordinator.increase_animation_speed)
        
        # Toolbar actions (reuse same callbacks)
        self._action_manager.set_action_callback('toolbar_export', self._export_coordinator.export_frames)
        
        # Help actions (Phase 7 refactoring - use DialogCoordinator)
        self._action_manager.set_action_callback('help_shortcuts', self._dialog_coordinator.show_shortcuts)
        self._action_manager.set_action_callback('help_about', self._dialog_coordinator.show_about)
    
    
    
    
    
    
    
    
    
    def _connect_signals(self):
        """Connect signals between components."""
        # Sprite model signals
        self._sprite_model.frameChanged.connect(self._on_frame_changed)
        self._sprite_model.dataLoaded.connect(self._on_sprite_loaded)
        self._sprite_model.extractionCompleted.connect(self._on_extraction_completed)
        
        # Animation controller signals (Phase 5 refactoring - use AnimationCoordinator)
        self._animation_controller.animationStarted.connect(self._animation_coordinator.on_playback_started)
        self._animation_controller.animationPaused.connect(self._animation_coordinator.on_playback_paused)
        self._animation_controller.animationStopped.connect(self._animation_coordinator.on_playback_stopped)
        self._animation_controller.animationCompleted.connect(self._animation_coordinator.on_playback_completed)
        self._animation_controller.frameAdvanced.connect(self._animation_coordinator.on_frame_advanced)
        self._animation_controller.errorOccurred.connect(self._animation_coordinator.on_animation_error)
        self._animation_controller.statusChanged.connect(self._status_manager.show_message)
        
        # Auto-detection controller signals
        self._auto_detection_controller.frameSettingsDetected.connect(self._on_frame_settings_detected)
        self._auto_detection_controller.statusUpdate.connect(self._status_manager.show_message)
        
        # Canvas signals (Phase 3 refactoring - zoom handled by ViewCoordinator)
        # self._canvas.zoomChanged is now connected in ViewCoordinator
        self._canvas.mouseMoved.connect(self._status_manager.update_mouse_position)
        
        # Frame extractor signals
        self._frame_extractor.settingsChanged.connect(self._update_frame_slicing)
        self._frame_extractor.modeChanged.connect(self._on_extraction_mode_changed)
        
        # Playback controls signals (Phase 5 refactoring - use AnimationCoordinator)
        self._playback_controls.playPauseClicked.connect(self._animation_coordinator.toggle_playback)
        self._playback_controls.frameChanged.connect(self._animation_coordinator.go_to_frame)
        self._playback_controls.fpsChanged.connect(self._animation_coordinator.set_fps)
        self._playback_controls.loopToggled.connect(self._animation_coordinator.set_loop_mode)
        
        # Navigation button signals (Phase 5 refactoring - use AnimationCoordinator)
        self._playback_controls.prevFrameClicked.connect(self._animation_coordinator.go_to_prev_frame)
        self._playback_controls.nextFrameClicked.connect(self._animation_coordinator.go_to_next_frame)
        
        # Grid view signals (Phase 6 refactoring - use EventCoordinator)
        if self._grid_view:
            self._grid_view.frameSelected.connect(self._event_coordinator.handle_grid_frame_selected)
            self._grid_view.framePreviewRequested.connect(self._on_grid_frame_preview)
            self._grid_view.segmentCreated.connect(self._segment_controller.create_segment)
            self._grid_view.segmentDeleted.connect(self._segment_controller.delete_segment)
            self._grid_view.segmentRenamed.connect(self._segment_controller.rename_segment)
            self._grid_view.segmentSelected.connect(self._segment_controller.select_segment)
            self._grid_view.segmentPreviewRequested.connect(self._segment_controller.preview_segment)
            self._grid_view.exportRequested.connect(
                lambda segment: self._segment_controller.export_segment(segment, self)
            )
    
    def _apply_settings(self):
        """Apply saved settings."""
        # Restore window geometry
        self._settings_manager.restore_window_geometry(self)
    
    def _update_manager_context(self):
        """Update manager context based on current state."""
        has_frames = bool(self._sprite_model.sprite_frames)
        is_playing = self._animation_coordinator.is_playing()  # Phase 5 refactoring
        
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
        file_path = self._file_controller.open_file_dialog(self)
        if file_path:
            self._file_controller.load_file(file_path)
    
    def _on_file_loaded(self, file_path: str):
        """Handle successful file load from FileController."""
        success, error_message = self._sprite_model.load_sprite_sheet(file_path)
        
        if success:
            # Update context for managers
            self._update_manager_context()
            
            # Update display first (fast) - Phase 3 refactoring
            self._view_coordinator.update_canvas()
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
            self._dialog_coordinator.show_error("Load Error", error_message)
    
    def _on_file_load_failed(self, error_message: str):
        """Handle file load failure from FileController."""
        QMessageBox.critical(self, "Load Error", error_message)
    
    # ============================================================================
    # SIGNAL HANDLERS
    # ============================================================================
    
    def _on_frame_changed(self, frame_index: int, total_frames: int):
        """Handle frame change."""
        # Update canvas frame info and trigger repaint with new frame (Phase 3 refactoring)
        self._view_coordinator.set_frame_info(frame_index, total_frames)
        self._view_coordinator.update_with_current_frame()
        
        # Update playback controls
        self._playback_controls.set_current_frame(frame_index)
        
        # Update button states based on current position
        has_frames = total_frames > 0
        at_start = frame_index == 0
        at_end = frame_index >= total_frames - 1 if total_frames > 0 else True
        self._playback_controls.update_button_states(has_frames, at_start, at_end)
    
    def _on_sprite_loaded(self, file_path: str):
        """Handle sprite loaded."""
        # Reset and update canvas view (Phase 3 refactoring)
        self._view_coordinator.reset_view()
        
        # Update managers context
        self._update_manager_context()
        
        # Enable CCL mode - always available when sprite is loaded
        self._frame_extractor.set_ccl_available(True, 0)
        
        # Check if frames are available immediately after loading
        if hasattr(self._sprite_model, 'sprite_frames'):
            frame_count = len(self._sprite_model.sprite_frames)
            if frame_count > 0:
                self._segment_controller.update_grid_view_frames()
        
        self._status_manager.show_message(f"Loaded sprite sheet: {file_path}")
    
    def _on_extraction_completed(self, frame_count: int):
        """Handle extraction completion."""
        # Update playback controls (Phase 5 refactoring - use AnimationCoordinator)
        self._animation_coordinator.on_extraction_completed(frame_count)
        
        if frame_count > 0:
            # Update canvas with frame info (Phase 3 refactoring)
            current_frame = self._sprite_model.current_frame
            self._view_coordinator.set_frame_info(current_frame, frame_count)
            
            # Update grid view with new frames
            self._segment_controller.update_grid_view_frames()
            
            # Update segment manager with sprite context to load saved segments
            if self._sprite_model.file_path:
                self._segment_manager.set_sprite_context(self._sprite_model.file_path, frame_count)
                
                # Sync loaded segments to grid view
                if self._grid_view:
                    self._grid_view.sync_segments_with_manager(self._segment_manager)
        else:
            self._view_coordinator.set_frame_info(0, 0)
            
            # Clear grid view if no frames
            if self._grid_view:
                self._grid_view.set_frames([])
        
        # Update managers context
        self._update_manager_context()
        
        # Update display with current frame (Phase 3 refactoring)
        self._view_coordinator.update_with_current_frame()
    
    
    def _on_frame_settings_detected(self, width: int, height: int):
        """Handle frame settings detected."""
        self._frame_extractor.set_frame_size(width, height)
        self._update_frame_slicing()
    
    
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
            self._dialog_coordinator.show_warning("Frame Extraction Error", error_message)
            return
        
        # Update info
        self._info_label.setText(self._sprite_model.sprite_info)
        
        # Update managers context
        self._update_manager_context()
        
        # Ensure first frame is displayed after extraction (Phase 3 refactoring)
        if total_frames > 0:
            self._sprite_model.set_current_frame(0)
            self._view_coordinator.update_with_current_frame()
    
    # ============================================================================
    # HELP DIALOGS
    # ============================================================================
    
    
    def _show_welcome_message(self):
        """Show welcome message."""
        self._info_label.setText("Ready - Drag and drop a sprite sheet or use File > Open")
    
    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        # Phase 6 refactoring - use EventCoordinator
        self._event_coordinator.handle_drag_enter(event)
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        # Phase 6 refactoring - use EventCoordinator
        self._event_coordinator.handle_drag_leave(event)
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        # Phase 6 refactoring - use EventCoordinator
        self._event_coordinator.handle_drop(event)
    
    # Animation Grid View Signal Handlers
    def _on_grid_frame_preview(self, frame_index: int):
        """Handle frame preview request (double-click) - switch to main view."""
        # Switch to canvas view and show selected frame
        self._tab_widget.setCurrentIndex(0)  # Switch to Frame View tab
        self._sprite_model.set_current_frame(frame_index)
        self._status_manager.show_message(f"Previewing frame {frame_index}")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts using EventCoordinator."""
        # Phase 6 refactoring - use EventCoordinator
        if self._event_coordinator.handle_key_press(event.key(), event.modifiers()):
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle close event."""
        # Save settings
        self._settings_manager.save_window_geometry(self)
        
        # Clean up coordinators (Phase 1 refactoring)
        self._coordinator_registry.cleanup_all()
        
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