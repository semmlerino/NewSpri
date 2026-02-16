"""
Sprite Viewer - Main application window (REFACTORED)
Modern sprite sheet animation viewer with improved usability.
Refactored to use centralized managers for better maintainability.
"""

import os
import sys
from collections.abc import Callable

from PySide6.QtCore import QMimeData, Qt, QTimer
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config import Config

# Coordinators
from coordinators import SignalCoordinator

# Core controllers
from core import (
    AnimationController,
    AnimationSegmentController,
    AutoDetectionController,
    ExportCoordinator,
)

# Export dialog
from export.dialogs.export_wizard import ExportDialog

# Managers
from managers import (
    AnimationSegmentManager,
    get_recent_files_manager,
    get_settings_manager,
)

# Core MVC Components
from sprite_model import SpriteModel

# Sprite model
from sprite_model.extraction_mode import ExtractionMode

# UI Components
from ui import (
    AnimationGridView,
    EnhancedStatusBar,
    FrameExtractor,
    PlaybackControls,
    SpriteCanvas,
    StatusBarManager,
)
from ui.animation_segment_preview import AnimationSegmentPreview


def _validate_sprite_file(file_path: str) -> tuple[bool, str]:
    """
    Validate a file for loading as a sprite sheet.

    Args:
        file_path: Path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "No file path provided"

    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    if not os.path.isfile(file_path):
        return False, f"Not a file: {file_path}"

    # Check if file has a supported extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in Config.File.SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file format: {ext}"

    # Check file size (100MB max)
    file_size = os.path.getsize(file_path)
    max_size = 100 * 1024 * 1024
    if file_size > max_size:
        return (
            False,
            f"File too large: {file_size / (1024 * 1024):.1f}MB (max {max_size / (1024 * 1024)}MB)",
        )

    return True, ""


def _is_valid_sprite_drop(mime_data: QMimeData) -> bool:
    """
    Check if mime data contains a valid sprite file URL.

    Args:
        mime_data: QMimeData from drag event

    Returns:
        True if valid sprite file drop
    """
    if not mime_data.hasUrls():
        return False

    urls = mime_data.urls()
    if not urls:
        return False

    first_url = urls[0]
    if not first_url.isLocalFile():
        return False

    file_path = first_url.toLocalFile()
    is_valid, _ = _validate_sprite_file(file_path)
    return is_valid


def _extract_file_from_drop(event: QDropEvent) -> str | None:
    """
    Extract file path from drop event.

    Args:
        event: QDropEvent from drop operation

    Returns:
        File path or None if invalid
    """
    mime_data = event.mimeData()
    if not _is_valid_sprite_drop(mime_data):
        return None

    urls = mime_data.urls()
    if urls:
        return urls[0].toLocalFile()

    return None


# ============================================================================
# KEYBOARD SHORTCUTS
# ============================================================================

SHORTCUTS = {
    # File actions
    "file_open": ("Ctrl+O", "Open sprite sheet"),
    "file_quit": ("Ctrl+Q", "Quit application"),
    "file_export_frames": ("Ctrl+E", "Export frames"),
    "file_export_current": ("Ctrl+Shift+E", "Export current frame"),
    # View actions
    "view_zoom_in": ("Ctrl++", "Zoom in"),
    "view_zoom_out": ("Ctrl+-", "Zoom out"),
    "view_zoom_fit": ("Ctrl+0", "Fit to window"),
    "view_zoom_reset": ("Ctrl+1", "Reset zoom (100%)"),
    "view_toggle_grid": ("G", "Toggle grid overlay"),
    # Animation actions
    "animation_toggle": ("Space", "Play/Pause animation"),
    "animation_prev_frame": ("Left", "Previous frame"),
    "animation_next_frame": ("Right", "Next frame"),
    "animation_first_frame": ("Home", "First frame"),
    "animation_last_frame": ("End", "Last frame"),
    "animation_restart": ("R", "Restart animation"),
    "animation_speed_decrease": ("[", "Decrease animation speed"),
    "animation_speed_increase": ("]", "Increase animation speed"),
}

# Actions that require frames to be loaded
ACTIONS_REQUIRING_FRAMES = {
    "file_export_frames",
    "file_export_current",
    "animation_toggle",
    "animation_prev_frame",
    "animation_next_frame",
    "animation_first_frame",
    "animation_last_frame",
    "animation_restart",
    "animation_speed_decrease",
    "animation_speed_increase",
    "toolbar_export",
}


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

    # Key mapping for special keys
    KEY_MAPPING = {
        Qt.Key.Key_Space: "Space",
        Qt.Key.Key_Left: "Left",
        Qt.Key.Key_Right: "Right",
        Qt.Key.Key_Home: "Home",
        Qt.Key.Key_End: "End",
        Qt.Key.Key_Plus: "+",
        Qt.Key.Key_Minus: "-",
    }

    def __init__(self):
        """
        Initialize sprite viewer with manager-based architecture.

        Initialization order:
        1. Managers (singletons)
        2. Core components (model, controllers)
        3. UI setup (all widgets)
        4. Controller/coordinator initialization (with constructor DI)
        5. Signal connections
        6. Final setup (settings, welcome message)
        """
        super().__init__()

        # Initialize managers first
        self._init_managers()

        # Initialize core MVC components
        self._init_core_components()

        # Set up UI directly
        self._setup_window()
        self._setup_actions()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_main_content()

        # Set up canvas zoom label connection and grid state
        self._grid_enabled = False

        # Initialize controllers with all dependencies (single-step init)
        self._animation_controller = AnimationController(
            sprite_model=self._sprite_model,
            sprite_viewer=self,
        )

        self._auto_detection_controller = AutoDetectionController(
            sprite_model=self._sprite_model,
            frame_extractor=self._frame_extractor,
        )

        self._segment_controller = AnimationSegmentController(
            segment_manager=self._segment_manager,
            grid_view=self._grid_view,
            sprite_model=self._sprite_model,
            tab_widget=self._tab_widget,
            segment_preview=self._segment_preview,
            parent=self,
        )

        # Initialize export coordinator
        self._export_coordinator = ExportCoordinator(
            sprite_model=self._sprite_model,
            segment_manager=self._segment_manager,
            parent=self,
        )

        # Connect UI signals to segment controller (deferred from _create_grid_tab)
        self._refresh_grid_btn.clicked.connect(self._segment_controller.update_grid_view_frames)
        self._tab_widget.currentChanged.connect(self._segment_controller.on_tab_changed)

        # Set up managers with UI components
        self._setup_managers()

        # Debounce timer for frame slicing (prevents per-keystroke extraction)
        self._slicing_debounce_timer = QTimer(self)
        self._slicing_debounce_timer.setSingleShot(True)
        self._slicing_debounce_timer.setInterval(300)
        self._slicing_debounce_timer.timeout.connect(self._update_frame_slicing)

        # Create signal coordinator and connect all signals
        self._signal_coordinator = SignalCoordinator(
            sprite_model=self._sprite_model,
            animation_controller=self._animation_controller,
            auto_detection_controller=self._auto_detection_controller,
            segment_controller=self._segment_controller,
            canvas=self._canvas,
            playback_controls=self._playback_controls,
            frame_extractor=self._frame_extractor,
            grid_view=self._grid_view,
            status_manager=self._status_manager,
            segment_manager=self._segment_manager,
            actions=self._actions,
            # Handler callbacks
            on_frame_changed=self._on_frame_changed,
            on_sprite_loaded=self._on_sprite_loaded,
            on_extraction_completed=self._on_extraction_completed,
            on_playback_started=self._on_playback_started,
            on_playback_paused=self._on_playback_paused,
            on_playback_stopped=self._on_playback_stopped,
            on_playback_completed=self._on_playback_completed,
            on_animation_error=self._on_animation_error,
            on_frame_settings_detected=self._on_frame_settings_detected,
            on_extraction_mode_changed=self._on_extraction_mode_changed,
            on_update_frame_slicing=self._on_settings_changed_debounced,
            on_grid_frame_preview=self._on_grid_frame_preview,
            on_export_frames_requested=self._on_export_frames_requested,
            on_export_current_frame_requested=self._on_export_current_frame_requested,
            on_zoom_changed=self._on_zoom_changed,
        )
        self._signal_coordinator.connect_all()

        # Apply settings and show welcome
        self._apply_settings()
        self._show_welcome_message()

    def _init_managers(self):
        """Initialize all centralized managers."""
        # Utility managers (keep using factories - used by dialogs etc.)
        self._settings_manager = get_settings_manager()
        self._recent_files = get_recent_files_manager()

        # Actions storage
        self._actions: dict[str, QAction] = {}
        self._shortcut_to_action: dict[str, str] = {}  # Key sequence -> action_id

    def _init_core_components(self):
        """Initialize core MVC components (model only - controllers need UI)."""
        # Model layer (no dependencies)
        self._sprite_model = SpriteModel()

        # Animation splitting components
        self._segment_manager = AnimationSegmentManager()

        # Recent files manager setup - handle clicks on recent file menu items
        self._recent_files = get_recent_files_manager()

        def _on_recent_file(path: str) -> None:
            self._load_sprite_file(path)

        self._recent_files.set_file_open_callback(_on_recent_file)

        # Placeholders - will be initialized after UI setup
        self._grid_view = None
        self._status_manager = None
        self._animation_controller = None
        self._auto_detection_controller = None
        self._signal_coordinator = None

    def _setup_window(self):
        """Set up main window properties."""
        self.setWindowTitle("Python Sprite Viewer")
        self.setMinimumSize(Config.UI.MIN_WINDOW_WIDTH, Config.UI.MIN_WINDOW_HEIGHT)
        self.setAcceptDrops(True)

    def _setup_actions(self):
        """Create all QActions with shortcuts and callbacks."""
        # File actions
        self._create_action("file_open", "📁 Open...", self._load_sprites)
        self._create_action("file_quit", "Quit", self.close)
        self._create_action("file_export_frames", "Export Frames...", None, requires_frames=True)
        self._create_action(
            "file_export_current", "Export Current Frame...", None, requires_frames=True
        )

        # View actions (callbacks connected later after canvas is created)
        self._create_action("view_zoom_in", "🔍+ Zoom In", self._zoom_in)
        self._create_action("view_zoom_out", "🔍- Zoom Out", self._zoom_out)
        self._create_action("view_zoom_fit", "🔍⇄ Fit to Window", None)
        self._create_action("view_zoom_reset", "🔍1:1 Reset Zoom", None)
        self._create_action("view_toggle_grid", "Toggle Grid", self._toggle_grid)

        # Animation actions (some callbacks connected later)
        self._create_action("animation_toggle", "Play/Pause", None, requires_frames=True)
        self._create_action("animation_prev_frame", "Previous Frame", None, requires_frames=True)
        self._create_action("animation_next_frame", "Next Frame", None, requires_frames=True)
        self._create_action("animation_first_frame", "First Frame", None, requires_frames=True)
        self._create_action("animation_last_frame", "Last Frame", None, requires_frames=True)
        self._create_action(
            "animation_restart", "Restart Animation", self._restart_animation, requires_frames=True
        )
        self._create_action(
            "animation_speed_decrease",
            "Decrease Speed",
            self._decrease_animation_speed,
            requires_frames=True,
        )
        self._create_action(
            "animation_speed_increase",
            "Increase Speed",
            self._increase_animation_speed,
            requires_frames=True,
        )

        # Toolbar actions
        self._create_action("toolbar_export", "💾 Export", None, requires_frames=True)

        # Help actions
        self._create_action("help_shortcuts", "Keyboard Shortcuts", self._show_shortcuts)
        self._create_action("help_about", "About", self._show_about)

    def _create_action(
        self,
        action_id: str,
        text: str,
        callback: Callable[..., object] | None,
        requires_frames: bool = False,
    ):
        """
        Create a QAction with shortcut and callback.

        Args:
            action_id: Action identifier (used for shortcut lookup)
            text: Display text for action
            callback: Function to call when triggered (can be None if connected later)
            requires_frames: Whether action requires frames to be loaded
        """
        action = QAction(text, self)

        # Add shortcut and tooltip
        if action_id in SHORTCUTS:
            shortcut_key, description = SHORTCUTS[action_id]
            action.setShortcut(shortcut_key)
            action.setToolTip(f"{description} ({shortcut_key})")
            self._shortcut_to_action[shortcut_key] = action_id
        else:
            # Actions without shortcuts still get tooltips from text
            action.setToolTip(text)

        # Connect callback if provided
        if callback is not None:
            action.triggered.connect(callback)

        # Set initial enabled state
        if requires_frames:
            action.setEnabled(False)

        # Store action
        self._actions[action_id] = action

    def _setup_menu_bar(self):
        """Create menu bar with all menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self._actions["file_open"])

        # Recent files submenu
        self._recent_files_menu = file_menu.addMenu("Recent Files")
        self._recent_files_menu.setToolTip("Recently opened sprite sheets")
        self._recent_files_menu.aboutToShow.connect(self._update_recent_files_menu)
        self._update_recent_files_menu()  # Initial population

        file_menu.addSeparator()
        file_menu.addAction(self._actions["file_export_frames"])
        file_menu.addAction(self._actions["file_export_current"])
        file_menu.addSeparator()
        file_menu.addAction(self._actions["file_quit"])

        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction(self._actions["view_zoom_in"])
        view_menu.addAction(self._actions["view_zoom_out"])
        view_menu.addAction(self._actions["view_zoom_fit"])
        view_menu.addAction(self._actions["view_zoom_reset"])
        view_menu.addSeparator()
        view_menu.addAction(self._actions["view_toggle_grid"])

        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction(self._actions["help_shortcuts"])
        help_menu.addSeparator()
        help_menu.addAction(self._actions["help_about"])

    def _update_recent_files_menu(self):
        """Update recent files menu content."""
        self._recent_files_menu.clear()
        self._recent_files.populate_recent_files_directly(self._recent_files_menu)

    def _setup_toolbar(self):
        """Create main toolbar."""
        self._main_toolbar = self.addToolBar("Main Toolbar")
        self._main_toolbar.setMovable(False)
        self._main_toolbar.setStyleSheet(Config.Styles.MAIN_TOOLBAR)

        # Add toolbar actions
        self._main_toolbar.addAction(self._actions["file_open"])
        self._main_toolbar.addSeparator()
        self._main_toolbar.addAction(self._actions["toolbar_export"])

        # Add zoom display widget
        self._main_toolbar.addSeparator()
        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(Config.UI.ZOOM_LABEL_MIN_WIDTH)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setStyleSheet(Config.Styles.ZOOM_DISPLAY)
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
        self._info_label.setStyleSheet(Config.Styles.INFO_LABEL)
        main_layout.addWidget(self._info_label)

    def _create_canvas_tab(self):
        """Create the canvas tab with traditional frame view."""
        tab_widget = QWidget()

        # Main horizontal layout for the tab
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(5)

        # Create splitter for responsive layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        tab_layout.addWidget(splitter)

        # Left side - Canvas
        canvas = self._create_canvas_section()
        splitter.addWidget(canvas)

        # Right side - Controls
        controls_widget = self._create_controls_section()
        splitter.addWidget(controls_widget)

        # Set splitter proportions
        splitter.setSizes([700, 300])  # Canvas gets more space
        splitter.setCollapsible(0, False)  # Canvas not collapsible
        splitter.setCollapsible(1, False)  # Controls not collapsible

        return tab_widget

    def _create_grid_tab(self):
        """Create the grid tab for animation splitting."""
        # Main container
        container = QWidget()
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for resizable layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left side: Grid view with frames
        grid_container = QWidget()
        grid_layout = QVBoxLayout(grid_container)

        # Initialize grid view
        self._grid_view = AnimationGridView()

        # Synchronize grid view with existing segments
        self._grid_view.sync_segments_with_manager(self._segment_manager)

        # Add refresh button for debugging (signal connected after controller init)
        self._refresh_grid_btn = QPushButton("🔄 Refresh Grid View")
        grid_layout.addWidget(self._refresh_grid_btn)
        grid_layout.addWidget(self._grid_view)

        splitter.addWidget(grid_container)

        # Right side: Animation segment preview
        self._segment_preview = AnimationSegmentPreview()
        splitter.addWidget(self._segment_preview)

        # Set splitter proportions (grid gets 2/3, preview gets 1/3)
        splitter.setSizes([800, 400])

        return container

    def _create_canvas_section(self):
        """Create canvas section."""
        self._canvas = SpriteCanvas()
        return self._canvas

    def _create_controls_section(self):
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

    def _setup_managers(self):
        """Configure managers with application-specific settings."""
        # Connect segment controller status messages
        if self._status_manager is not None:
            self._segment_controller.statusMessage.connect(self._status_manager.show_message)

        # Update action states based on initial context
        self._update_has_frames_actions()

    def _apply_settings(self):
        """Apply saved settings."""
        # Restore window geometry
        self._settings_manager.restore_window_geometry(self)

    def _update_has_frames_actions(self):
        """Update action enabled state based on whether frames are loaded."""
        has_frames = bool(self._sprite_model.sprite_frames)

        # Enable/disable actions that require frames
        for action_id in ACTIONS_REQUIRING_FRAMES:
            if action_id in self._actions:
                self._actions[action_id].setEnabled(has_frames)

    # ============================================================================
    # FILE OPERATIONS
    # ============================================================================

    def _load_sprites(self):
        """Show file dialog and load selected sprite sheet."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Sprite Sheet", "", Config.File.IMAGE_FILTER
        )
        if file_path:
            self._load_sprite_file(file_path)

    def _load_sprite_file(self, file_path: str) -> bool:
        """
        Load a sprite file with validation.

        This is the main entry point for loading sprites, called from:
        - File dialog selection
        - Recent files menu
        - Drag and drop

        Args:
            file_path: Path to the sprite sheet file

        Returns:
            True if loading succeeded
        """
        # Validate file first
        is_valid, error_msg = _validate_sprite_file(file_path)
        if not is_valid:
            QMessageBox.critical(self, "Load Error", error_msg)
            return False

        # Check if loading a new sprite would clear existing segments
        current_path = self._sprite_model.file_path
        if current_path and current_path != file_path:
            existing_segments = self._segment_manager.get_all_segments()
            if existing_segments:
                reply = QMessageBox.question(
                    self,
                    "Clear Segments?",
                    f"Loading a new sprite will clear {len(existing_segments)} existing segment(s).\n\nContinue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return False

        # Try to load via sprite model
        success, error_message = self._sprite_model.load_sprite_sheet(file_path)

        if not success:
            QMessageBox.critical(self, "Load Error", error_message)
            return False

        # Add to recent files on successful load
        self._recent_files.add_file_to_recent(file_path)

        # Update action states
        self._update_has_frames_actions()

        # Update display first (fast)
        self._canvas.update()
        self._info_label.setText(self._sprite_model.sprite_info)

        # Trigger appropriate detection based on current extraction mode
        current_mode = self._frame_extractor.get_extraction_mode()
        if current_mode is ExtractionMode.CCL:
            # For CCL mode, try direct CCL extraction without grid auto-detection
            if self._status_manager is not None:
                self._status_manager.show_message("Running CCL extraction...")
            self._update_frame_slicing()  # This will trigger CCL extraction
        else:
            # For grid mode, run comprehensive grid auto-detection
            # Use wait cursor to indicate processing
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            QApplication.processEvents()
            try:
                if self._auto_detection_controller:
                    self._auto_detection_controller.run_comprehensive_detection_with_dialog()
            finally:
                QApplication.restoreOverrideCursor()

        return True

    # ============================================================================
    # VIEW OPERATIONS
    # ============================================================================

    def _zoom_in(self):
        """Zoom in on canvas."""
        current_zoom = self._canvas.get_zoom_factor()
        new_zoom = current_zoom * Config.Canvas.ZOOM_FACTOR
        self._canvas.set_zoom(new_zoom)

    def _zoom_out(self):
        """Zoom out on canvas."""
        current_zoom = self._canvas.get_zoom_factor()
        new_zoom = current_zoom / Config.Canvas.ZOOM_FACTOR
        self._canvas.set_zoom(new_zoom)

    def _toggle_grid(self):
        """Toggle grid overlay."""
        self._grid_enabled = not self._grid_enabled
        self._canvas.set_grid_overlay(self._grid_enabled)

    def _on_zoom_changed(self, zoom_factor: float):
        """Handle zoom change from canvas."""
        percentage = int(zoom_factor * 100)
        self._zoom_label.setText(f"{percentage}%")

    # ============================================================================
    # ANIMATION HELPERS
    # ============================================================================

    def _restart_animation(self):
        """Restart animation from first frame."""
        self._sprite_model.set_current_frame(0)
        if self._status_manager is not None:
            self._status_manager.show_message("Animation restarted")

    def _decrease_animation_speed(self):
        """Decrease animation speed by one step."""
        if not self._animation_controller:
            return
        current_fps = self._animation_controller.current_fps
        speed_steps = Config.Animation.SPEED_STEPS
        for i in range(len(speed_steps) - 1, -1, -1):
            if current_fps > speed_steps[i]:
                self._animation_controller.set_fps(speed_steps[i])
                return
        if current_fps > speed_steps[0]:
            self._animation_controller.set_fps(speed_steps[0])

    def _increase_animation_speed(self):
        """Increase animation speed by one step."""
        if not self._animation_controller:
            return
        current_fps = self._animation_controller.current_fps
        speed_steps = Config.Animation.SPEED_STEPS
        for i in range(len(speed_steps)):
            if current_fps < speed_steps[i]:
                self._animation_controller.set_fps(speed_steps[i])
                return
        if current_fps < speed_steps[-1]:
            self._animation_controller.set_fps(speed_steps[-1])

    # ============================================================================
    # SIGNAL HANDLERS
    # ============================================================================

    def _on_frame_changed(self, frame_index: int, total_frames: int):
        """Handle frame change."""
        # Update canvas frame info
        self._canvas.set_frame_info(frame_index, total_frames)
        # Push current frame pixmap to canvas (MVC: controller pushes to view)
        pixmap = self._sprite_model.current_frame_pixmap
        if pixmap and not pixmap.isNull():
            self._canvas.set_pixmap(pixmap, auto_fit=False)

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
        self._canvas.reset_view()
        self._canvas.update()

        # Update action states
        self._update_has_frames_actions()

        # Enable CCL mode - always available when sprite is loaded
        self._frame_extractor.set_ccl_available(True, 0)

        # Check if frames are available immediately after loading
        frame_count = len(self._sprite_model.sprite_frames)
        if frame_count > 0:
            self._segment_controller.update_grid_view_frames()

        if self._status_manager is not None:
            self._status_manager.show_message(f"Loaded sprite sheet: {file_path}")

    def _on_playback_started(self):
        """Handle playback start."""
        self._playback_controls.update_button_states(False, True, True)

    def _on_playback_paused(self):
        """Handle playback pause."""
        self._playback_controls.update_button_states(True, True, True)

    def _on_playback_stopped(self):
        """Handle playback stop."""
        self._playback_controls.update_button_states(True, True, False)

    def _on_playback_completed(self):
        """Handle playback completion."""
        self._playback_controls.update_button_states(True, True, False)

    def _on_animation_error(self, error_message: str):
        """Handle animation controller error."""
        QMessageBox.warning(self, "Animation Error", error_message)

    def _on_extraction_completed_update_playback(self, frame_count: int):
        """Update playback controls after extraction completion."""
        if frame_count > 0:
            self._playback_controls.set_frame_range(frame_count - 1)
            self._playback_controls.update_button_states(True, True, False)
        else:
            self._playback_controls.set_frame_range(0)
            self._playback_controls.update_button_states(False, False, False)

    def _on_extraction_completed(self, frame_count: int):
        """Handle extraction completion."""
        # Update playback controls
        self._on_extraction_completed_update_playback(frame_count)

        if frame_count > 0:
            # Update canvas with frame info (Phase 3 refactoring)
            current_frame = self._sprite_model.current_frame
            self._canvas.set_frame_info(current_frame, frame_count)

            # Update grid view with new frames
            self._segment_controller.update_grid_view_frames()

            # Load saved segments for this sprite sheet.
            # ORDER MATTERS: set_sprite_context() loads from disk, sync copies to grid.
            if self._sprite_model.file_path:
                self._segment_manager.set_sprite_context(self._sprite_model.file_path, frame_count)

                if self._grid_view:
                    self._grid_view.sync_segments_with_manager(self._segment_manager)
        else:
            self._canvas.set_frame_info(0, 0)

            # Clear grid view if no frames
            if self._grid_view:
                self._grid_view.set_frames([])

        # Update action states
        self._update_has_frames_actions()

        # Push current frame pixmap to canvas
        pixmap = self._sprite_model.current_frame_pixmap
        if pixmap and not pixmap.isNull():
            self._canvas.set_pixmap(pixmap, auto_fit=False)

    def _on_frame_settings_detected(self, width: int, height: int):
        """Handle frame settings detected."""
        self._frame_extractor.set_frame_size(width, height)
        self._update_frame_slicing()

    def _on_extraction_mode_changed(self, mode: str):
        """Handle extraction mode change (grid vs CCL)."""
        if not self._sprite_model.original_sprite_sheet:
            return

        # Convert string from Qt signal to enum
        mode_enum = ExtractionMode(mode)

        # Update sprite model extraction mode
        success = self._sprite_model.set_extraction_mode(mode_enum)

        if not success:
            # Revert UI radio button to current model mode without re-triggering
            current_mode = self._sprite_model.get_extraction_mode()
            self._frame_extractor.blockSignals(True)
            self._frame_extractor.set_extraction_mode(current_mode)
            self._frame_extractor.blockSignals(False)
            if self._status_manager is not None:
                self._status_manager.show_message(f"Failed to switch extraction mode to {mode}")
            return

        # Update info label immediately to reflect mode change
        self._info_label.setText(self._sprite_model.sprite_info)

        # Re-extract frames with new mode
        self._update_frame_slicing()

        # Update status
        mode_name = "CCL" if mode_enum is ExtractionMode.CCL else "Grid"
        if self._status_manager is not None:
            self._status_manager.show_message(f"Switched to {mode_name} extraction mode")

    def _on_settings_changed_debounced(self):
        """Restart debounce timer on settings change (prevents per-keystroke extraction)."""
        self._slicing_debounce_timer.start()

    def _update_frame_slicing(self):
        """Update frame slicing based on current settings."""
        if not self._sprite_model.original_sprite_sheet:
            return

        # Get current extraction mode
        mode = self._frame_extractor.get_extraction_mode()

        # Use wait cursor to indicate processing (CCL can be slow for large sheets)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        try:
            if mode is ExtractionMode.CCL:
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
        finally:
            QApplication.restoreOverrideCursor()

        if not success:
            QMessageBox.warning(self, "Frame Extraction Error", error_message)
            return

        # Update info
        self._info_label.setText(self._sprite_model.sprite_info)

        # Update action states
        self._update_has_frames_actions()

        # Ensure first frame is displayed after extraction
        if total_frames > 0:
            self._sprite_model.set_current_frame(0)
            # Push first frame pixmap to canvas
            pixmap = self._sprite_model.current_frame_pixmap
            if pixmap and not pixmap.isNull():
                self._canvas.set_pixmap(pixmap, auto_fit=False)

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
        if _is_valid_sprite_drop(event.mimeData()):
            event.acceptProposedAction()
            self._canvas.setStyleSheet(Config.Styles.CANVAS_DRAG_HOVER)

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self._canvas.setStyleSheet(Config.Styles.CANVAS_NORMAL)
        self._show_welcome_message()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        self._canvas.setStyleSheet(Config.Styles.CANVAS_NORMAL)
        file_path = _extract_file_from_drop(event)
        if file_path:
            self._load_sprite_file(file_path)
            event.acceptProposedAction()

    # Animation Grid View Signal Handlers
    def _on_grid_frame_preview(self, frame_index: int):
        """Handle frame preview request (double-click) - switch to main view."""
        # Switch to canvas view and show selected frame
        self._tab_widget.setCurrentIndex(0)  # Switch to Frame View tab
        self._sprite_model.set_current_frame(frame_index)
        if self._status_manager is not None:
            self._status_manager.show_message(f"Previewing frame {frame_index}")

    # ============================================================================
    # HELP DIALOGS
    # ============================================================================

    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        help_html = self._generate_shortcuts_help_html()
        QMessageBox.information(self, "Keyboard Shortcuts", help_html)

    def _generate_shortcuts_help_html(self) -> str:
        """Generate HTML help documentation for all shortcuts."""
        html = ["<h3>Keyboard Shortcuts</h3>"]

        # Organize shortcuts by category
        categories = {
            "File": ["file_open", "file_export_frames", "file_export_current", "file_quit"],
            "View": [
                "view_zoom_in",
                "view_zoom_out",
                "view_zoom_fit",
                "view_zoom_reset",
                "view_toggle_grid",
            ],
            "Animation": [
                "animation_toggle",
                "animation_prev_frame",
                "animation_next_frame",
                "animation_first_frame",
                "animation_last_frame",
                "animation_restart",
                "animation_speed_decrease",
                "animation_speed_increase",
            ],
        }

        for category_name, action_ids in categories.items():
            html.append(f"<h4>{category_name}</h4>")
            html.append("<table>")

            for action_id in action_ids:
                if action_id in SHORTCUTS:
                    shortcut_key, description = SHORTCUTS[action_id]
                    context_info = ""
                    if action_id in ACTIONS_REQUIRING_FRAMES:
                        context_info = " <i>(requires frames)</i>"

                    html.append(
                        f"<tr><td><b>{shortcut_key}</b></td>"
                        f"<td>{description}{context_info}</td></tr>"
                    )

            html.append("</table>")
            html.append("<br>")

        # Add mouse actions
        html.append("<h4>Mouse Actions</h4>")
        html.append("<table>")
        html.append("<tr><td><b>Mouse wheel</b></td><td>Zoom in/out</td></tr>")
        html.append("<tr><td><b>Click+drag</b></td><td>Pan view</td></tr>")
        html.append("</table>")

        return "\n".join(html)

    def _show_about(self):
        """Show about dialog."""
        about_text = """
<h3>Python Sprite Viewer</h3>
<p>Version 2.0</p>
<p>A modern sprite sheet animation viewer.</p>
<p>Features:</p>
<ul>
<li>Automatic frame extraction</li>
<li>Smooth animation playback</li>
<li>Frame export (PNG, JPG, BMP)</li>
<li>Sprite sheet generation</li>
</ul>
        """
        QMessageBox.about(self, "About Sprite Viewer", about_text)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()
        modifiers = event.modifiers()

        # Build key sequence using Qt's built-in functionality
        q_key_sequence = QKeySequence(
            key | modifiers.value if hasattr(modifiers, "value") else int(modifiers)
        )
        key_sequence_str = q_key_sequence.toString()

        # For special keys not handled well by QKeySequence, use our mapping
        qt_key = Qt.Key(key)
        if qt_key in self.KEY_MAPPING:
            # Build custom sequence for special keys
            parts = []
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                parts.append("Ctrl")
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                parts.append("Shift")
            if modifiers & Qt.KeyboardModifier.AltModifier:
                parts.append("Alt")
            parts.append(self.KEY_MAPPING[qt_key])
            key_sequence_str = "+".join(parts)
        elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            # Handle single letter keys specially - QKeySequence may not format them correctly
            if modifiers == Qt.KeyboardModifier.NoModifier:
                # For single letters with no modifiers, use the letter directly
                key_sequence_str = chr(key)
            # else let QKeySequence handle modified letters (Ctrl+A, etc.)
        elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            # Handle single digit keys specially
            if modifiers == Qt.KeyboardModifier.NoModifier:
                # For single digits with no modifiers, use the digit directly
                key_sequence_str = chr(key)
            # else let QKeySequence handle modified digits (Alt+1, etc.)
        elif key == Qt.Key.Key_BracketLeft:
            # Handle bracket keys specially
            key_sequence_str = "["
        elif key == Qt.Key.Key_BracketRight:
            key_sequence_str = "]"
        else:
            # Let parent handle other keys
            super().keyPressEvent(event)
            return

        # Try to find and trigger matching action
        if self._handle_shortcut(key_sequence_str):
            event.accept()
        else:
            super().keyPressEvent(event)

    def _handle_shortcut(self, key_sequence: str) -> bool:
        """
        Handle a keyboard shortcut.

        Args:
            key_sequence: String representation of key sequence

        Returns:
            True if shortcut was handled
        """
        # Find action with matching shortcut
        for action_id, (shortcut_key, _) in SHORTCUTS.items():
            if shortcut_key == key_sequence and action_id in self._actions:
                action = self._actions[action_id]
                if action.isEnabled():
                    action.trigger()
                    return True
        return False

    # ============================================================================
    # EXPORT OPERATIONS
    # ============================================================================

    def _on_export_frames_requested(self) -> None:
        """Show export dialog for exporting frames and animation segments."""
        if not self._export_coordinator.validate_export():
            return

        dialog = ExportDialog(
            self,
            frame_count=len(self._sprite_model.sprite_frames),
            current_frame=self._sprite_model.current_frame,
            segment_manager=self._segment_manager,
        )
        dialog.set_sprites(self._sprite_model.sprite_frames)
        dialog.exportRequested.connect(self._export_coordinator.handle_export_request)
        dialog.exec()

    def _on_export_current_frame_requested(self) -> None:
        """Export only the current frame."""
        if not self._export_coordinator.validate_export():
            return

        dialog = ExportDialog(
            self,
            frame_count=len(self._sprite_model.sprite_frames),
            current_frame=self._sprite_model.current_frame,
            segment_manager=self._segment_manager,
        )
        dialog.set_sprites(self._sprite_model.sprite_frames)
        dialog.exportRequested.connect(self._export_coordinator.handle_export_request)
        dialog.exec()

    def closeEvent(self, event):
        """Handle close event."""
        # Save settings
        self._settings_manager.save_window_geometry(self)

        # Clean up signal coordinator
        if self._signal_coordinator:
            self._signal_coordinator.disconnect_all()

        # Clean up controllers
        if self._animation_controller:
            self._animation_controller.shutdown()

        # Force settings sync to ensure all pending changes are saved
        self._settings_manager.sync()

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
