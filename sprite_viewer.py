#!/usr/bin/env python3
"""
Python Sprite Viewer - Main Application
A lightweight PySide6-based application for previewing sprite sheet animations.
Phase 5: UI Component Extraction Complete - Clean Component-Based Architecture.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QGroupBox, QColorDialog, 
    QComboBox, QStatusBar, QToolBar, QMessageBox, QScrollArea,
    QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QAction, QDragEnterEvent, QDropEvent

from config import Config
from styles import StyleManager
from sprite_model import SpriteModel
from animation_controller import AnimationController
from auto_detection_controller import AutoDetectionController

# Phase 5: Extracted UI Components
from sprite_canvas import SpriteCanvas
from playback_controls import PlaybackControls
from frame_extractor import FrameExtractor


class SpriteViewer(QMainWindow):
    """Main sprite viewer application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Config.App.WINDOW_TITLE)
        
        # Set up window geometry with optimized sizing
        self.setGeometry(
            Config.UI.DEFAULT_WINDOW_X, 
            Config.UI.DEFAULT_WINDOW_Y,
            Config.UI.DEFAULT_WINDOW_WIDTH,  # Optimized default width
            Config.UI.DEFAULT_WINDOW_HEIGHT  # Optimized default height
        )
        
        # Set minimum size from config for consistency
        self.setMinimumSize(Config.UI.MIN_WINDOW_WIDTH, Config.UI.MIN_WINDOW_HEIGHT)
        
        # Sprite data model (Phase 3: Data extraction complete)
        self._sprite_model = SpriteModel()
        
        # Animation controller (Phase 4: Animation timing extraction)
        self._animation_controller = AnimationController()
        self._animation_controller.initialize(self._sprite_model, self)
        
        # Auto-detection controller (extracted for workflow management)
        self._auto_detection_controller = AutoDetectionController()
        
        # UI setup
        self._setup_ui()
        self._setup_toolbar()
        self._setup_menu()
        self._connect_signals()
        
        # Initialize auto-detection controller after UI setup
        self._auto_detection_controller.initialize(self._sprite_model, self._frame_extractor)
        
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
        
        # Main layout with proper margins
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Use QSplitter for flexible resizing
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Canvas
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        # Canvas with proper size policy
        self._canvas = SpriteCanvas()
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._canvas.frameChanged.connect(self._on_canvas_frame_changed)
        canvas_layout.addWidget(self._canvas)
        
        main_splitter.addWidget(canvas_container)
        
        # Right side - Controls with better sizing
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        controls_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        controls_scroll.setMinimumWidth(300)
        controls_scroll.setMaximumWidth(500)
        
        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setSpacing(8)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. Sprite Sheet Info (compact)
        info_group = QGroupBox("Sprite Sheet Info")
        info_group.setMaximumHeight(100)
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(5, 5, 5, 5)
        
        self._info_label = QLabel("No sprite sheet loaded")
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet(StyleManager.get_info_label())
        info_layout.addWidget(self._info_label)
        controls_layout.addWidget(info_group)
        
        # 2. Frame Extraction (with size policy)
        self._frame_extractor = FrameExtractor()
        self._frame_extractor.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        controls_layout.addWidget(self._frame_extractor)
        
        # 3. Playback Controls (compact)
        self._playback_controls = PlaybackControls()
        self._playback_controls.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        controls_layout.addWidget(self._playback_controls)
        
        # 4. View Options (compact)
        view_group = QGroupBox("View Options")
        view_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        view_layout = QVBoxLayout(view_group)
        view_layout.setContentsMargins(5, 5, 5, 5)
        
        # Background selector
        bg_layout = QHBoxLayout()
        bg_layout.setSpacing(5)
        bg_label = QLabel("Background:")
        bg_label.setMinimumWidth(70)
        bg_layout.addWidget(bg_label)
        
        self._bg_combo = QComboBox()
        self._bg_combo.addItems(["Checkerboard", "Solid Color"])
        self._bg_combo.currentTextChanged.connect(self._change_background)
        self._bg_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bg_layout.addWidget(self._bg_combo)
        
        self._color_button = QPushButton("Color")
        self._color_button.setMaximumWidth(60)
        self._color_button.clicked.connect(self._choose_background_color)
        self._color_button.setEnabled(False)
        bg_layout.addWidget(self._color_button)
        
        view_layout.addLayout(bg_layout)
        controls_layout.addWidget(view_group)
        
        # Add stretch to push everything to top
        controls_layout.addStretch()
        
        # Help text at bottom
        help_label = QLabel("💡 Drag & drop sprite sheets or use File→Open")
        help_label.setAlignment(Qt.AlignCenter)
        help_label.setStyleSheet("QLabel { color: #666; font-size: 11px; padding: 5px; }")
        controls_layout.addWidget(help_label)
        
        # Set the controls widget
        controls_scroll.setWidget(controls_container)
        main_splitter.addWidget(controls_scroll)
        
        # Configure splitter
        main_splitter.setStretchFactor(0, 3)  # Canvas gets 3x stretch
        main_splitter.setStretchFactor(1, 1)  # Controls get 1x stretch
        main_splitter.setSizes([900, 400])    # Initial sizes
        
        # Add splitter to main layout
        main_layout.addWidget(main_splitter)
    
    def _setup_toolbar(self):
        """Set up main toolbar with common actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet(StyleManager.get_main_toolbar())
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
        self._zoom_label.setStyleSheet(StyleManager.get_zoom_display())
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
        # ============================================================================
        # MODEL SIGNAL CONNECTIONS (Phase 3.7: Event-driven architecture)
        # ============================================================================
        
        # Connect SpriteModel signals to UI update methods
        self._sprite_model.frameChanged.connect(self._on_model_frame_changed)
        self._sprite_model.dataLoaded.connect(self._on_model_data_loaded)
        self._sprite_model.extractionCompleted.connect(self._on_model_extraction_completed)
        self._sprite_model.playbackStateChanged.connect(self._on_model_playback_state_changed)
        self._sprite_model.errorOccurred.connect(self._on_model_error_occurred)
        self._sprite_model.configurationChanged.connect(self._on_model_configuration_changed)
        
        # ============================================================================
        # ANIMATION CONTROLLER SIGNAL CONNECTIONS (Phase 4.2: Timer extraction)
        # ============================================================================
        
        # Connect AnimationController signals to UI update methods
        self._animation_controller.frameAdvanced.connect(self._on_controller_frame_advanced)
        self._animation_controller.animationStarted.connect(self._on_controller_animation_started)
        self._animation_controller.animationPaused.connect(self._on_controller_animation_paused)
        self._animation_controller.animationStopped.connect(self._on_controller_animation_stopped)
        self._animation_controller.animationCompleted.connect(self._on_controller_animation_completed)
        self._animation_controller.errorOccurred.connect(self._on_controller_error_occurred)
        self._animation_controller.statusChanged.connect(self._on_controller_status_changed)
        
        # ============================================================================
        # AUTO-DETECTION CONTROLLER SIGNAL CONNECTIONS (Extracted workflow management)
        # ============================================================================
        
        # Connect AutoDetectionController signals to UI update methods
        self._auto_detection_controller.frameSettingsDetected.connect(self._on_frame_settings_detected)
        self._auto_detection_controller.marginSettingsDetected.connect(self._on_margin_settings_detected)
        self._auto_detection_controller.spacingSettingsDetected.connect(self._on_spacing_settings_detected)
        self._auto_detection_controller.buttonConfidenceUpdate.connect(self._on_button_confidence_update)
        self._auto_detection_controller.statusUpdate.connect(self._on_detection_status_update)
        self._auto_detection_controller.workflowStateChanged.connect(self._on_detection_workflow_state_changed)
        
        # ============================================================================
        # UI WIDGET SIGNAL CONNECTIONS (Phase 5: Extracted components)
        # ============================================================================
        
        # Frame extractor signals (updated to use AutoDetectionController)
        self._frame_extractor.settingsChanged.connect(self._update_frame_slicing)
        self._frame_extractor.presetSelected.connect(self._frame_extractor.set_frame_size)
        self._frame_extractor.auto_btn.clicked.connect(self._auto_detection_controller.run_frame_detection)
        self._frame_extractor.auto_margins_btn.clicked.connect(self._auto_detection_controller.run_margin_detection)
        self._frame_extractor.auto_spacing_btn.clicked.connect(self._auto_detection_controller.run_spacing_detection)
        self._frame_extractor.comprehensive_auto_btn.clicked.connect(self._auto_detection_controller.run_comprehensive_detection_with_dialog)
        self._frame_extractor.grid_checkbox.toggled.connect(self._toggle_grid)
        self._frame_extractor.modeChanged.connect(self._on_extraction_mode_changed)
        
        # Playback control signals (updated for Phase 4.2: Controller integration)
        self._playback_controls.playPauseClicked.connect(self._animation_controller.toggle_playback)
        self._playback_controls.frameChanged.connect(self._on_frame_slider_changed)
        self._playback_controls.fpsChanged.connect(self._animation_controller.set_fps)
        self._playback_controls.loopToggled.connect(self._animation_controller.set_loop_mode)
        
        self._playback_controls.prev_btn.clicked.connect(self._go_to_prev_frame)
        self._playback_controls.next_btn.clicked.connect(self._go_to_next_frame)
    
    # ============================================================================
    # MODEL SIGNAL HANDLERS (Phase 3.7: Event-driven architecture)
    # ============================================================================
    
    def _on_model_frame_changed(self, current_frame: int, total_frames: int):
        """Handle frame change from model."""
        # Update canvas display
        if self._sprite_model.sprite_frames and 0 <= current_frame < len(self._sprite_model.sprite_frames):
            self._canvas.set_pixmap(self._sprite_model.sprite_frames[current_frame])
            self._canvas.set_frame_info(current_frame, total_frames)
            self._playback_controls.set_current_frame(current_frame)
    
    def _on_model_data_loaded(self, file_path: str):
        """Handle data loaded from model."""
        self._info_label.setText(self._sprite_model.sprite_info)
        self._status_bar.showMessage(f"Loaded: {self._sprite_model.file_name}")
    
    def _on_model_extraction_completed(self, frame_count: int):
        """Handle frame extraction completion from model."""
        self._info_label.setText(self._sprite_model.sprite_info)
        if frame_count > 0:
            self._playback_controls.set_frame_range(frame_count - 1)
            self._playback_controls.update_button_states(True, True, False)
        else:
            self._playback_controls.set_frame_range(0)
            self._playback_controls.update_button_states(False, False, False)
        
        # Update CCL mode availability after extraction
        self._update_ccl_availability()
    
    def _on_model_playback_state_changed(self, is_playing: bool):
        """Handle playback state change from model."""
        # Update UI to reflect model's playback state
        # Timer control is now handled by AnimationController
        self._playback_controls.set_playing(is_playing)
    
    def _on_model_error_occurred(self, error_message: str):
        """Handle error from model."""
        QMessageBox.warning(self, "Sprite Model Error", error_message)
        self._status_bar.showMessage(f"Error: {error_message}")
    
    def _on_model_configuration_changed(self):
        """Handle configuration change from model."""
        # Trigger re-extraction of frames with new settings
        self._update_frame_slicing()
    
    # ============================================================================
    # ANIMATION CONTROLLER SIGNAL HANDLERS (Phase 4.2: Timer extraction)
    # ============================================================================
    
    def _on_controller_frame_advanced(self, frame_index: int):
        """Handle frame advancement from animation controller."""
        # Update display for new frame (controller drives this during playback)
        self._update_display()
    
    def _on_controller_animation_started(self):
        """Handle animation start from controller."""
        # Update UI state for animation start
        self._status_bar.showMessage("Animation started")
    
    def _on_controller_animation_paused(self):
        """Handle animation pause from controller."""
        # Update UI state for animation pause
        self._status_bar.showMessage("Animation paused")
    
    def _on_controller_animation_stopped(self):
        """Handle animation stop from controller."""
        # Update UI state for animation stop
        self._status_bar.showMessage("Animation stopped")
    
    def _on_controller_animation_completed(self):
        """Handle animation completion from controller."""
        # Update UI state for animation completion
        self._status_bar.showMessage("Animation completed")
    
    def _on_controller_error_occurred(self, error_message: str):
        """Handle error from animation controller."""
        # Display controller error to user
        self._status_bar.showMessage(f"Animation error: {error_message}")
    
    def _on_controller_status_changed(self, status_message: str):
        """Handle status updates from animation controller."""
        # Display controller status in status bar
        self._status_bar.showMessage(status_message)
    
    def _show_welcome_message(self):
        """Show welcome message in status bar."""
        self._status_bar.showMessage("Welcome! Drag & drop sprite sheets or click Open to get started")
        # Reset model to default state
        self._sprite_model.clear_sprite_data()
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
        zoom_percent = int(self._canvas.get_zoom_factor() * 100)
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
        """Load and slice a sprite sheet using SpriteModel."""
        # Load sprite sheet through model (Phase 3.3: File loading extraction)
        success, error_message = self._sprite_model.load_sprite_sheet(file_path)
        
        if not success:
            # Handle loading error with UI feedback
            QMessageBox.warning(self, "Error", error_message)
            self._show_welcome_message()
            return
        
        # Update UI with sprite sheet info from model
        self._info_label.setText(self._sprite_model.sprite_info)
        
        # Handle new sprite sheet workflow with proper auto-detection
        self._auto_detection_controller.handle_new_sprite_sheet_loaded()
        
        # Slice the sprite sheet and update display  
        self._slice_sprite_sheet()
        self._update_display()
        
        # Update status bar
        self._status_bar.showMessage(f"Loaded: {self._sprite_model.file_name}")
    
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
        """Slice the original sprite sheet into individual frames using SpriteModel."""
        # Get frame extraction settings from UI
        frame_width, frame_height = self._frame_extractor.get_frame_size()
        offset_x, offset_y = self._frame_extractor.get_offset()
        spacing_x, spacing_y = self._frame_extractor.get_spacing()
        
        # Extract frames through model (Phase 3.4: Frame extraction)
        success, error_message, total_frames = self._sprite_model.extract_frames(
            frame_width, frame_height, offset_x, offset_y, spacing_x, spacing_y
        )
        
        if not success:
            # Handle extraction error
            self._info_label.setText(self._sprite_model.sprite_info)
            QMessageBox.warning(self, "Frame Extraction Error", error_message)
            return
        
        # Update UI with extraction results
        self._info_label.setText(self._sprite_model.sprite_info)
        
        if total_frames > 0:
            # Update playback controls for successful extraction
            self._playback_controls.set_frame_range(total_frames - 1)
            self._playback_controls.update_button_states(True, True, False)
        else:
            # No frames extracted - reset playback controls
            self._playback_controls.set_frame_range(0)
            self._playback_controls.update_button_states(False, False, False)
    
    def _update_frame_slicing(self):
        """Update frame slicing based on current settings."""
        if not self._sprite_model.original_sprite_sheet:
            return
        
        # Re-slice with new dimensions
        self._slice_sprite_sheet()
        
        # Reset to first frame if current is out of bounds
        if self._sprite_model.current_frame >= len(self._sprite_model.sprite_frames):
            self._sprite_model.set_current_frame(0)
        
        # Update display
        self._update_display()
        
        # Update grid
        if self._frame_extractor.grid_checkbox.isChecked():
            frame_width, frame_height = self._frame_extractor.get_frame_size()
            self._canvas.set_grid_overlay(True, max(frame_width, frame_height))
    
    def _on_extraction_mode_changed(self, mode: str):
        """Handle extraction mode change between grid and CCL."""
        try:
            # Set the extraction mode in the sprite model
            success = self._sprite_model.set_extraction_mode(mode)
            
            if success:
                # Update display with new extraction
                self._update_display()
                # Update playback controls
                self._playback_controls.set_total_frames(self._sprite_model.total_frames)
                if self._sprite_model.total_frames > 0:
                    self._sprite_model.set_current_frame(0)  # Reset to first frame
                
                # Show status message
                if mode == "ccl":
                    self.statusBar().showMessage(f"Switched to CCL mode: {self._sprite_model.total_frames} individual sprites", 3000)
                else:
                    self.statusBar().showMessage(f"Switched to Grid mode: {self._sprite_model.total_frames} frames", 3000)
            else:
                # Revert UI if mode change failed
                current_mode = self._sprite_model.get_extraction_mode()
                self._frame_extractor.set_extraction_mode(current_mode)
                self.statusBar().showMessage(f"Failed to switch to {mode} mode", 3000)
        
        except Exception as e:
            self.statusBar().showMessage(f"Error switching extraction mode: {str(e)}", 5000)
    
    def _update_ccl_availability(self):
        """Update CCL mode availability based on model state."""
        available = self._sprite_model.is_ccl_available()
        sprite_count = len(self._sprite_model.get_ccl_sprite_bounds()) if available else 0
        self._frame_extractor.set_ccl_available(available, sprite_count)
    
    def _update_display(self):
        """Update the canvas display."""
        if self._sprite_model.sprite_frames and 0 <= self._sprite_model.current_frame < len(self._sprite_model.sprite_frames):
            self._canvas.set_pixmap(self._sprite_model.sprite_frames[self._sprite_model.current_frame])
            self._canvas.set_frame_info(self._sprite_model.current_frame, len(self._sprite_model.sprite_frames))
            self._playback_controls.set_current_frame(self._sprite_model.current_frame)
            self._update_navigation_buttons()
            # Update zoom label in case auto-fit occurred
            self._update_zoom_label()
        else:
            self._canvas.set_pixmap(QPixmap())
            self._canvas.set_frame_info(0, 0)
            self._playback_controls.set_current_frame(0)
            self._update_navigation_buttons()
            # Update zoom label for empty state
            self._update_zoom_label()
            # If no sprite sheet is loaded, show welcome message
            if not self._sprite_model.original_sprite_sheet:
                self._show_welcome_message()
    
    def _update_navigation_buttons(self):
        """Update navigation button states."""
        has_frames = bool(self._sprite_model.sprite_frames)
        at_start = self._sprite_model.current_frame == 0
        at_end = self._sprite_model.current_frame == len(self._sprite_model.sprite_frames) - 1 if has_frames else True
        
        self._playback_controls.update_button_states(has_frames, at_start, at_end)
    
    def _toggle_grid(self, checked: bool = None):
        """Toggle grid overlay."""
        if checked is None:
            checked = self._frame_extractor.grid_checkbox.isChecked()
            self._frame_extractor.grid_checkbox.setChecked(not checked)
        else:
            frame_width, frame_height = self._frame_extractor.get_frame_size()
            self._canvas.set_grid_overlay(checked, max(frame_width, frame_height))
    
    def _on_frame_slider_changed(self, value: int):
        """Handle frame slider change using SpriteModel."""
        if self._sprite_model.sprite_frames and 0 <= value < len(self._sprite_model.sprite_frames):
            if self._sprite_model.is_playing:
                self._animation_controller.pause_animation()
            self._sprite_model.set_current_frame(value)
            self._update_display()
    
    
    def _go_to_prev_frame(self):
        """Go to previous frame using SpriteModel."""
        if self._sprite_model.sprite_frames and self._sprite_model.current_frame > 0:
            if self._sprite_model.is_playing:
                self._animation_controller.pause_animation()
            self._sprite_model.previous_frame()
            self._update_display()
    
    def _go_to_next_frame(self):
        """Go to next frame using SpriteModel."""
        if self._sprite_model.sprite_frames and self._sprite_model.current_frame < len(self._sprite_model.sprite_frames) - 1:
            if self._sprite_model.is_playing:
                self._animation_controller.pause_animation()
            self._sprite_model.next_frame()
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
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    event.acceptProposedAction()
                    self._canvas.setStyleSheet(StyleManager.get_canvas_drag_hover())
                    self._status_bar.showMessage("Drop sprite sheet to load...")
                    return
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop event."""
        # Reset canvas style
        self._canvas.setStyleSheet(StyleManager.get_canvas_normal())
        
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self._load_sprite_sheet(file_path)
                event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self._canvas.setStyleSheet(StyleManager.get_canvas_normal())
        self._show_welcome_message()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()
        
        if key == Qt.Key_Space:
            self._animation_controller.toggle_playback()
        elif key == Qt.Key_G:
            self._toggle_grid()
        elif key == Qt.Key_Left and self._sprite_model.sprite_frames:
            self._go_to_prev_frame()
        elif key == Qt.Key_Right and self._sprite_model.sprite_frames:
            self._go_to_next_frame()
        elif key == Qt.Key_Home and self._sprite_model.sprite_frames:
            self._go_to_first_frame()
        elif key == Qt.Key_End and self._sprite_model.sprite_frames:
            self._go_to_last_frame()
        else:
            super().keyPressEvent(event)
    
    # ============================================================================
    # AUTO-DETECTION CONTROLLER SIGNAL HANDLERS
    # ============================================================================
    
    def _on_frame_settings_detected(self, width: int, height: int):
        """Handle frame settings detected by AutoDetectionController."""
        self._frame_extractor.set_frame_size(width, height)
        self._slice_sprite_sheet()  # Re-slice with new settings
    
    def _on_margin_settings_detected(self, offset_x: int, offset_y: int):
        """Handle margin settings detected by AutoDetectionController."""
        self._frame_extractor.offset_x.setValue(offset_x)
        self._frame_extractor.offset_y.setValue(offset_y)
        self._slice_sprite_sheet()  # Re-slice with new settings
    
    def _on_spacing_settings_detected(self, spacing_x: int, spacing_y: int):
        """Handle spacing settings detected by AutoDetectionController."""
        self._frame_extractor.spacing_x.setValue(spacing_x)
        self._frame_extractor.spacing_y.setValue(spacing_y)
        self._slice_sprite_sheet()  # Re-slice with new settings
    
    def _on_button_confidence_update(self, button_type: str, confidence: str, message: str):
        """Handle button confidence updates from AutoDetectionController."""
        if button_type == 'comprehensive':
            self._update_comprehensive_button_style(confidence)
        else:
            # Handle individual button confidence updates
            if confidence == 'reset':
                self._frame_extractor.reset_auto_button_style(button_type)
            else:
                self._frame_extractor.update_auto_button_confidence(button_type, confidence, message)
    
    def _on_detection_status_update(self, message: str, timeout_ms: int):
        """Handle status updates from AutoDetectionController."""
        self._status_bar.showMessage(message, timeout_ms)
    
    def _on_detection_workflow_state_changed(self, state: str):
        """Handle workflow state changes from AutoDetectionController."""
        if state == "working":
            self._frame_extractor.comprehensive_auto_btn.setText("🔄 Working...")
            self._frame_extractor.comprehensive_auto_btn.setEnabled(False)
        else:
            self._frame_extractor.comprehensive_auto_btn.setEnabled(True)
    
    def _update_comprehensive_button_style(self, confidence: str):
        """Update comprehensive button style based on confidence level."""
        if confidence == 'success':
            self._frame_extractor.comprehensive_auto_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2e7d32;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            self._frame_extractor.comprehensive_auto_btn.setText("✓ Auto-Detected")
        elif confidence == 'reset':
            self._frame_extractor.comprehensive_auto_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1976d2;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
            self._frame_extractor.comprehensive_auto_btn.setText("🔍 Auto-Detect All")
    
    def _update_playback_ui(self, is_playing: bool):
        """Update UI based on playback state."""
        # This method is for toolbar updates if we add play/pause to toolbar
        pass
    
    def _update_controls_width(self):
        """Update controls panel width based on current window size with optimized ratios."""
        if hasattr(self, '_controls_container'):
            window_width = self.width()
            
            # Calculate responsive width with optimized breakpoints
            if window_width < 800:
                # Small screens: need more controls space for usability
                ratio = 0.35
            elif window_width < 1000:
                # Medium screens: use optimized ratio
                ratio = Config.UI.CONTROLS_WIDTH_RATIO  # 0.22
            else:
                # Large screens: minimize controls dominance
                ratio = 0.20
            
            calculated_width = int(window_width * ratio)
            responsive_width = max(
                Config.UI.CONTROLS_MIN_WIDTH,
                min(calculated_width, Config.UI.CONTROLS_MAX_WIDTH)
            )
            
            # Apply width to the scroll area (which contains the controls)
            self._controls_container.setMinimumWidth(responsive_width)
            self._controls_container.setMaximumWidth(responsive_width)
    
    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)


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