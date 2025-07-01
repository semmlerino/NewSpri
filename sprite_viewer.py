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
    QSplitter, QLabel, QSizePolicy, QMessageBox, QTabWidget, QPushButton, QDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent

from config import Config
from utils import StyleManager

# Core MVC Components
from sprite_model import SpriteModel
from core import AnimationController, AutoDetectionController

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
from export import ExportDialog, get_frame_exporter


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
        
        self._auto_detection_controller = AutoDetectionController()
        
        # Animation splitting components
        self._segment_manager = AnimationSegmentManager()
        self._grid_view = None  # Will be initialized in UI setup
        
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
        """Set up main content area with tabbed interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main vertical layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create tab widget for different views
        self._tab_widget = QTabWidget()
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self._tab_widget)
        
        # Canvas view tab
        canvas_tab = self._create_canvas_tab()
        self._tab_widget.addTab(canvas_tab, "Frame View")
        
        # Grid view tab for animation splitting
        grid_tab = self._create_grid_tab()
        self._tab_widget.addTab(grid_tab, "Animation Splitting")
        
        # Info label at bottom
        self._info_label = QLabel("Ready - Drag and drop a sprite sheet or use File > Open")
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet(StyleManager.get_info_label())
        main_layout.addWidget(self._info_label)
    
    def _create_canvas_tab(self) -> QWidget:
        """Create the canvas tab with traditional frame view."""
        tab_widget = QWidget()
        
        # Main horizontal layout for the tab
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(5)
        
        # Create splitter for responsive layout
        splitter = QSplitter(Qt.Horizontal)
        tab_layout.addWidget(splitter)
        
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
        
        return tab_widget
    
    def _create_grid_tab(self) -> QWidget:
        """Create the grid tab for animation splitting."""
        # Initialize grid view
        self._grid_view = AnimationGridView()
        
        # Connect grid view signals
        self._grid_view.frameSelected.connect(self._on_grid_frame_selected)
        self._grid_view.framePreviewRequested.connect(self._on_grid_frame_preview)
        self._grid_view.segmentCreated.connect(self._on_segment_created)
        self._grid_view.segmentDeleted.connect(self._on_segment_deleted)
        self._grid_view.segmentSelected.connect(self._on_segment_selected)
        self._grid_view.segmentPreviewRequested.connect(self._on_segment_preview_requested)
        self._grid_view.exportRequested.connect(self._export_animation_segment)
        
        # Synchronize grid view with existing segments
        self._grid_view.sync_segments_with_manager(self._segment_manager)
        
        # Add refresh button for debugging
        from PySide6.QtWidgets import QVBoxLayout, QWidget, QPushButton
        container = QWidget()
        layout = QVBoxLayout(container)
        
        refresh_btn = QPushButton("🔄 Refresh Grid View")
        refresh_btn.clicked.connect(self._force_refresh_grid_view)
        layout.addWidget(refresh_btn)
        
        layout.addWidget(self._grid_view)
        
        return container
    
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
        """Show enhanced export dialog for exporting frames and animation segments."""
        if not self._sprite_model.sprite_frames:
            QMessageBox.warning(self, "No Frames", "No frames to export.")
            return
        
        dialog = ExportDialog(
            self,
            frame_count=len(self._sprite_model.sprite_frames),
            current_frame=self._sprite_model.current_frame,
            segment_manager=self._segment_manager
        )
        
        # Set sprites for visual preview (Phase 4 enhancement)
        dialog.set_sprites(self._sprite_model.sprite_frames)
        
        dialog.exportRequested.connect(self._handle_unified_export_request)
        dialog.exec()
    
    def _export_current_frame(self):
        """Export only the current frame."""
        if not self._sprite_model.sprite_frames:
            QMessageBox.warning(self, "No Frames", "No frames to export.")
            return
        
        dialog = ExportDialog(
            self,
            frame_count=len(self._sprite_model.sprite_frames),
            current_frame=self._sprite_model.current_frame,
            segment_manager=self._segment_manager
        )
        
        # Set sprites for visual preview (Phase 4 enhancement)
        dialog.set_sprites(self._sprite_model.sprite_frames)
        
        # The new dialog will automatically handle single frame export via presets
        dialog.exportRequested.connect(self._handle_unified_export_request)
        dialog.exec()
    
    def _handle_unified_export_request(self, settings: dict):
        """Handle unified export request from new dialog (handles both frames and segments)."""
        # Check if this is a segment export
        if settings.get('mode') == 'segments' and 'selected_segments' in settings:
            self._handle_segment_export_request(settings)
        else:
            self._handle_export_request(settings)
    
    def _handle_export_request(self, settings: dict):
        """Handle export request from dialog."""
        try:
            exporter = get_frame_exporter()
            
            # Validate required settings
            required_keys = ['output_dir', 'base_name', 'format', 'mode', 'scale_factor']
            for key in required_keys:
                if key not in settings:
                    QMessageBox.critical(self, "Export Error", f"Missing required setting: {key}")
                    return
            
            # Get the appropriate frames based on export mode
            all_frames = self._sprite_model.sprite_frames
            if not all_frames:
                QMessageBox.warning(self, "Export Error", "No frames available to export.")
                return
            
            frames_to_export = all_frames
            export_mode = settings['mode']
            selected_indices = None
            
            # For frame selection, filter frames to only the selected ones
            selected_indices = settings.get('selected_indices', [])
            if selected_indices:
                if not selected_indices:
                    QMessageBox.warning(self, "Export Error", "No frames selected for export.")
                    return
                
                # Validate selected indices
                valid_indices = [i for i in selected_indices if 0 <= i < len(all_frames)]
                if not valid_indices:
                    QMessageBox.warning(self, "Export Error", "No valid frames selected for export.")
                    return
                
                frames_to_export = [all_frames[i] for i in valid_indices]
                # Ensure we use individual mode since we're pre-filtering frames
                export_mode = 'individual'
                
                if len(valid_indices) != len(selected_indices):
                    # Some indices were invalid, warn user
                    invalid_count = len(selected_indices) - len(valid_indices)
                    QMessageBox.information(
                        self, "Selection Adjusted", 
                        f"Exported {len(valid_indices)} frames. "
                        f"{invalid_count} invalid frame selection(s) were skipped."
                    )
            
            success = exporter.export_frames(
                frames=frames_to_export,
                output_dir=settings['output_dir'],
                base_name=settings['base_name'],
                format=settings['format'],
                mode=export_mode,
                scale_factor=settings['scale_factor'],
                pattern=settings.get('pattern', Config.Export.DEFAULT_PATTERN),
                selected_indices=selected_indices,
                sprite_sheet_layout=settings.get('sprite_sheet_layout')
            )
            
            if not success:
                QMessageBox.critical(self, "Export Failed", "Failed to start export.")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Unexpected error during export: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _handle_segment_specific_export_request(self, settings: dict, segment_frames: list, segment_name: str):
        """Handle export request for a specific animation segment."""
        try:
            exporter = get_frame_exporter()
            
            # Validate required settings
            required_keys = ['output_dir', 'base_name', 'format', 'mode', 'scale_factor']
            for key in required_keys:
                if key not in settings:
                    QMessageBox.critical(self, "Export Error", f"Missing required setting: {key}")
                    return
            
            if not segment_frames:
                QMessageBox.warning(self, "Export Error", f"No frames available for segment '{segment_name}'.")
                return
            
            frames_to_export = segment_frames
            export_mode = settings['mode']
            selected_indices = None
            
            # For frame selection, filter segment frames to only the selected ones
            selected_indices = settings.get('selected_indices', [])
            if selected_indices:
                if not selected_indices:
                    QMessageBox.warning(self, "Export Error", "No frames selected for export.")
                    return
                
                # Validate selected indices against segment frame count
                valid_indices = [i for i in selected_indices if 0 <= i < len(segment_frames)]
                if not valid_indices:
                    QMessageBox.warning(self, "Export Error", "No valid frames selected for export.")
                    return
                
                frames_to_export = [segment_frames[i] for i in valid_indices]
                # Ensure we use individual mode since we're pre-filtering frames
                export_mode = 'individual'
                
                if len(valid_indices) != len(selected_indices):
                    # Some indices were invalid, warn user
                    invalid_count = len(selected_indices) - len(valid_indices)
                    QMessageBox.information(
                        self, "Selection Adjusted", 
                        f"Exported {len(valid_indices)} frames from segment '{segment_name}'. "
                        f"{invalid_count} invalid frame selection(s) were skipped."
                    )
            
            # Update base name to include segment name
            base_name = f"{settings['base_name']}_{segment_name}"
            
            success = exporter.export_frames(
                frames=frames_to_export,
                output_dir=settings['output_dir'],
                base_name=base_name,
                format=settings['format'],
                mode=export_mode,
                scale_factor=settings['scale_factor'],
                pattern=settings.get('pattern', Config.Export.DEFAULT_PATTERN),
                selected_indices=selected_indices,
                sprite_sheet_layout=settings.get('sprite_sheet_layout')
            )
            
            if not success:
                QMessageBox.critical(self, "Export Failed", f"Failed to start export for segment '{segment_name}'.")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Unexpected error during segment export: {str(e)}")
            import traceback
            traceback.print_exc()

    def _handle_segment_export_request(self, settings: dict):
        """Handle animation segment export request from enhanced dialog."""
        selected_segments = settings.get('selected_segments', [])
        
        if not selected_segments:
            QMessageBox.warning(self, "No Segments", "No animation segments selected for export.")
            return
        
        exporter = get_frame_exporter()
        all_frames = self._sprite_model.sprite_frames
        
        for segment_name in selected_segments:
            segment = self._segment_manager.get_segment(segment_name)
            if not segment:
                continue
            
            # Extract frames for this segment
            segment_frames = self._segment_manager.extract_frames_for_segment(
                segment_name, all_frames
            )
            
            if not segment_frames:
                continue
            
            # Determine output directory and naming
            base_output_dir = settings['output_dir']
            segment_output_dir = os.path.join(base_output_dir, segment_name)
            os.makedirs(segment_output_dir, exist_ok=True)
            
            # Export based on mode
            mode_index = settings.get('mode_index', 0)
            
            if mode_index == 0:  # Individual segments (separate folders)
                success = exporter.export_frames(
                    frames=segment_frames,
                    output_dir=segment_output_dir,
                    base_name=settings.get('base_name', segment_name),
                    format=settings['format'],
                    mode='individual',
                    scale_factor=settings['scale_factor']
                )
            elif mode_index == 1:  # Combined sprite sheet
                success = exporter.export_frames(
                    frames=segment_frames,
                    output_dir=segment_output_dir,
                    base_name=f"{segment_name}_sheet",
                    format=settings['format'],
                    mode='sheet',
                    scale_factor=settings['scale_factor']
                )
            elif mode_index == 2:  # Animated GIF per segment
                success = exporter.export_frames(
                    frames=segment_frames,
                    output_dir=segment_output_dir,
                    base_name=segment_name,
                    format='GIF',
                    mode='gif',
                    scale_factor=settings['scale_factor'],
                    fps=settings.get('fps', 10),
                    loop=settings.get('loop', True)
                )
            else:  # Individual frames (all segments)
                success = exporter.export_frames(
                    frames=segment_frames,
                    output_dir=base_output_dir,
                    base_name=f"{segment_name}_{settings.get('base_name', 'frame')}",
                    format=settings['format'],
                    mode='individual',
                    scale_factor=settings['scale_factor']
                )
            
            if not success:
                QMessageBox.warning(
                    self, "Export Warning", 
                    f"Failed to export segment '{segment_name}'"
                )
        
        # Save metadata if requested
        if settings.get('include_metadata', False):
            metadata_file = os.path.join(base_output_dir, 'animation_segments.json')
            success, error = self._segment_manager.save_segments_to_file(metadata_file)
            if not success:
                QMessageBox.warning(self, "Metadata Export", f"Failed to save metadata: {error}")
        
        QMessageBox.information(
            self, "Export Complete", 
            f"Successfully exported {len(selected_segments)} animation segment(s)"
        )
    
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
        
        # Check if frames are available immediately after loading
        if hasattr(self._sprite_model, 'sprite_frames'):
            frame_count = len(self._sprite_model.sprite_frames)
            if frame_count > 0:
                self._update_grid_view_frames()
        
        self._status_manager.show_message(f"Loaded sprite sheet: {file_path}")
    
    def _on_extraction_completed(self, frame_count: int):
        """Handle extraction completion."""
        if frame_count > 0:
            self._playback_controls.set_frame_range(frame_count - 1)
            self._playback_controls.update_button_states(True, True, False)
            
            # Update canvas with frame info
            current_frame = self._sprite_model.current_frame
            self._canvas.set_frame_info(current_frame, frame_count)
            
            # Update grid view with new frames
            self._update_grid_view_frames()
        else:
            self._playback_controls.set_frame_range(0)
            self._playback_controls.update_button_states(False, False, False)
            self._canvas.set_frame_info(0, 0)
            
            # Clear grid view if no frames
            if self._grid_view:
                self._grid_view.set_frames([])
        
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
    
    # Animation Grid View Signal Handlers
    def _on_grid_frame_selected(self, frame_index: int):
        """Handle frame selection from grid view - just update status, don't switch tabs."""
        # Update status to show selected frame but don't switch tabs
        self._status_manager.show_message(f"Selected frame {frame_index}")
    
    def _on_grid_frame_preview(self, frame_index: int):
        """Handle frame preview request (double-click) - switch to main view."""
        # Switch to canvas view and show selected frame
        self._tab_widget.setCurrentIndex(0)  # Switch to Frame View tab
        self._sprite_model.set_current_frame(frame_index)
        self._status_manager.show_message(f"Previewing frame {frame_index}")
    
    def _on_segment_created(self, segment):
        """Handle creation of new animation segment."""
        original_name = segment.name
        
        # Try to add segment to manager
        success, error = self._segment_manager.add_segment(
            segment.name, segment.start_frame, segment.end_frame, 
            segment.color, getattr(segment, 'description', '')
        )
        
        if not success and "already exists" in error:
            # Try to auto-resolve name conflict
            base_name = original_name.split('_')[0] if '_' in original_name else original_name
            retry_count = 0
            max_retries = 10
            
            while not success and retry_count < max_retries:
                retry_count += 1
                # Generate new unique name
                import time
                timestamp = int(time.time() * 1000) % 10000
                new_name = f"{base_name}_{timestamp}"
                
                success, error = self._segment_manager.add_segment(
                    new_name, segment.start_frame, segment.end_frame, 
                    segment.color, getattr(segment, 'description', '')
                )
                
                if success:
                    # Update the segment name in grid view
                    if hasattr(self, '_grid_view') and hasattr(self._grid_view, '_segments'):
                        if original_name in self._grid_view._segments:
                            # Remove old entry and add new one
                            segment_data = self._grid_view._segments.pop(original_name)
                            segment_data.name = new_name
                            self._grid_view._segments[new_name] = segment_data
                            
                            # Update the segment list widget
                            self._grid_view._segment_list.remove_segment(original_name)
                            self._grid_view._segment_list.add_segment(segment_data)
                    
                    self._status_manager.show_message(
                        f"Created animation segment '{new_name}' with {segment.frame_count} frames "
                        f"(renamed from '{original_name}' to resolve conflict)"
                    )
                    return
        
        if not success:
            # Remove from grid view if it was added there but failed in manager
            if hasattr(self, '_grid_view') and hasattr(self._grid_view, '_segments'):
                if original_name in self._grid_view._segments:
                    del self._grid_view._segments[original_name]
                    self._grid_view._segment_list.remove_segment(original_name)
            
            QMessageBox.warning(self, "Segment Creation Error", f"{error}\n\nPlease try a different name.")
        else:
            self._status_manager.show_message(
                f"Created animation segment '{segment.name}' with {segment.frame_count} frames"
            )
    
    def _on_segment_deleted(self, segment_name: str):
        """Handle deletion of animation segment."""
        if self._segment_manager.remove_segment(segment_name):
            self._status_manager.show_message(f"Deleted animation segment '{segment_name}'")
    
    def _on_segment_selected(self, segment):
        """Handle selection of animation segment."""
        # Just show the segment is selected - DON'T switch tabs automatically
        # User can use "Export Selected" button or double-click to preview
        self._status_manager.show_message(
            f"Selected segment '{segment.name}' (frames {segment.start_frame}-{segment.end_frame}) - Use 'Export Selected' to export"
        )
    
    def _on_segment_preview_requested(self, segment):
        """Handle segment preview request (double-click)."""
        # Stay in current view and show the segment start frame
        self._sprite_model.set_current_frame(segment.start_frame)
        self._status_manager.show_message(
            f"Segment '{segment.name}' selected (frames {segment.start_frame}-{segment.end_frame})"
        )
    
    def _export_animation_segment(self, segment):
        """Export a specific animation segment."""
        # Get frames for the segment
        all_frames = self._sprite_model.get_all_frames()
        segment_frames = self._segment_manager.extract_frames_for_segment(
            segment.name, all_frames
        )
        
        if not segment_frames:
            QMessageBox.warning(
                self, "Export Error", 
                f"No frames available for segment '{segment.name}'"
            )
            return
        
        # Open export dialog
        dialog = ExportDialog(
            self, 
            frame_count=len(segment_frames),
            current_frame=0,
            segment_manager=self._segment_manager
        )
        
        # Set sprites for visual preview (Phase 4 enhancement)
        dialog.set_sprites(segment_frames)
        
        # Create custom export handler for this segment
        def handle_segment_export(settings):
            self._handle_segment_specific_export_request(settings, segment_frames, segment.name)
        
        dialog.exportRequested.connect(handle_segment_export)
        if dialog.exec() == QDialog.Accepted:
            self._status_manager.show_message(f"Exported segment '{segment.name}'")
    
    def _update_grid_view_frames(self):
        """Update grid view with current frames."""
        if self._grid_view:
            # Try multiple ways to get frames for backward compatibility
            frames = []
            
            # Method 1: Try get_all_frames if available
            if hasattr(self._sprite_model, 'get_all_frames'):
                frames = self._sprite_model.get_all_frames()
            
            # Method 2: Try sprite_frames property as fallback
            if not frames and hasattr(self._sprite_model, 'sprite_frames'):
                frames = self._sprite_model.sprite_frames
            
            # Method 3: Try _sprite_frames attribute as last resort
            if not frames and hasattr(self._sprite_model, '_sprite_frames'):
                frames = self._sprite_model._sprite_frames
            
            print(f"DEBUG: Found {len(frames)} frames for grid view")
            
            if frames:
                self._grid_view.set_frames(frames)
                print(f"DEBUG: Grid view updated with {len(frames)} frames")
                
                # Update segment manager context
                sprite_path = ""
                if hasattr(self._sprite_model, '_file_path'):
                    sprite_path = self._sprite_model._file_path
                elif hasattr(self._sprite_model, '_sprite_sheet_path'):
                    sprite_path = self._sprite_model._sprite_sheet_path
                
                if sprite_path:
                    self._segment_manager.set_sprite_context(sprite_path, len(frames))
                    print(f"DEBUG: Segment manager updated for {sprite_path}")
            else:
                print("DEBUG: No frames available for grid view")
                self._grid_view.set_frames([])  # Clear grid view
    
    def _force_refresh_grid_view(self):
        """Force refresh the grid view (for debugging)."""
        print("DEBUG: Force refreshing grid view...")
        self._update_grid_view_frames()
    
    def _on_tab_changed(self, index: int):
        """Handle tab change - refresh grid view when switching to animation splitting."""
        if index == 1 and self._grid_view:  # Animation Splitting tab
            print("DEBUG: Switched to Animation Splitting tab, refreshing grid view...")
            self._update_grid_view_frames()

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