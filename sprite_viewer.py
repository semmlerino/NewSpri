"""
Sprite Viewer - Main application window.
Modern sprite sheet animation viewer with centralized managers.
"""

import os
import sys
from collections.abc import Callable, Sequence

from PySide6.QtCore import QMimeData, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDropEvent,
    QKeyEvent,
    QKeySequence,
    QPixmap,
)
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
from coordinators import SignalCoordinator, SpriteLoadCoordinator
from core import (
    AnimationController,
    AnimationSegmentController,
    AutoDetectionController,
    ExportCoordinator,
)
from export import ExportDialog
from managers import (
    AnimationSegmentManager,
    RecentFilesManager,
    SettingsManager,
    get_settings_manager,
)
from sprite_model import SpriteModel
from sprite_model.extraction_mode import ExtractionMode
from ui import (
    AnimationGridView,
    EnhancedStatusBar,
    FrameExtractor,
    PlaybackControls,
    SpriteCanvas,
)
from ui.animation_segment_preview import AnimationSegmentPreview
from utils.styles import StyleManager


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
    _, ext = os.path.splitext(file_path)
    return ext.lower() in Config.File.SUPPORTED_EXTENSIONS


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

    Responsibilities:
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
        Qt.Key.Key_BracketLeft: "[",
        Qt.Key.Key_BracketRight: "]",
    }

    def __init__(
        self,
        settings_manager: "SettingsManager | None" = None,
        recent_files_manager: "RecentFilesManager | None" = None,
    ):
        """
        Initialize sprite viewer with manager-based architecture.

        Args:
            settings_manager: SettingsManager instance to use; defaults to the
                global singleton via ``get_settings_manager()`` for backwards
                compatibility with ``python sprite_viewer.py``. Tests should
                pass an explicit instance to keep state isolated.
            recent_files_manager: RecentFilesManager instance to use; defaults
                to a per-window manager backed by ``settings_manager``.

        Initialization order:
        1. Managers (constructor-injected, with singleton fallback)
        2. Core components (model, controllers)
        3. UI setup (all widgets)
        4. Controller/coordinator initialization (with constructor DI)
        5. Signal connections (via SignalCoordinator)
        6. Final setup (settings, welcome message)
        """
        super().__init__()

        # Resolve injected managers (fall back to singletons for the entrypoint)
        self._settings_manager = settings_manager or get_settings_manager()
        self._recent_files = recent_files_manager or RecentFilesManager(
            settings_manager=self._settings_manager
        )

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
        self._loading_in_progress = False

        # Initialize controllers with all dependencies
        self._init_controllers()

        # Debounce timer for frame slicing (prevents per-keystroke extraction).
        # Must exist BEFORE SpriteLoadCoordinator is created — coordinator
        # methods reach for ``view._slicing_debounce_timer`` from their first
        # invocation onward.
        self._slicing_debounce_timer = QTimer(self)
        self._slicing_debounce_timer.setSingleShot(True)
        self._slicing_debounce_timer.setInterval(300)
        self._slicing_debounce_timer.timeout.connect(self._update_frame_slicing)

        # Sprite-load + extraction cascade collaborator. Created after the
        # debounce timer (which it reads) and before the signal coordinator
        # (which wires the load handlers).
        self._load_coordinator = SpriteLoadCoordinator(self)

        # Initial action enabled state — coordinator wires the rest of the
        # cross-component signals below.
        self._update_has_frames_actions()

        # Create signal coordinator and connect all signals
        self._init_signal_coordinator()

        # Apply settings and show welcome
        self._apply_settings()
        self._show_welcome_message()

    def _init_managers(self):
        """Allocate per-instance manager scratch state.

        ``self._settings_manager`` and ``self._recent_files`` are set in
        ``__init__`` from the constructor arguments (with singleton fallback).
        """
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
        # (manager itself is injected via __init__)
        def on_recent_file(path: str) -> None:
            self._load_sprite_file(path)

        self._recent_files.set_file_open_callback(on_recent_file)

    def _init_controllers(self):
        """Initialize controllers with all dependencies (single-step init)."""
        self._animation_controller = AnimationController(
            sprite_model=self._sprite_model,
        )

        self._auto_detection_controller = AutoDetectionController(
            sprite_model=self._sprite_model,
        )

        # Export coordinator must be before segment controller
        self._export_coordinator = ExportCoordinator(
            sprite_model=self._sprite_model,
            segment_manager=self._segment_manager,
            parent=self,
        )

        self._segment_controller = AnimationSegmentController(
            segment_manager=self._segment_manager,
            grid_view=self._grid_view,
            sprite_model=self._sprite_model,
            tab_widget=self._tab_widget,
            segment_preview=self._segment_preview,
            export_coordinator=self._export_coordinator,
            parent=self,
        )

        # Connect UI signals to segment controller (deferred from _create_grid_tab)
        self._refresh_grid_btn.clicked.connect(self._segment_controller.update_grid_view_frames)
        self._tab_widget.currentChanged.connect(self._segment_controller.on_tab_changed)

    def _init_signal_coordinator(self):
        """Create signal coordinator and connect all signals."""
        self._signal_coordinator = SignalCoordinator(
            sprite_model=self._sprite_model,
            animation_controller=self._animation_controller,
            auto_detection_controller=self._auto_detection_controller,
            segment_controller=self._segment_controller,
            canvas=self._canvas,
            playback_controls=self._playback_controls,
            frame_extractor=self._frame_extractor,
            grid_view=self._grid_view,
            status_bar=self._status_bar,
            actions=self._actions,
            # Handler callbacks
            on_frame_changed=self._on_frame_changed,
            on_sprite_loaded=self._on_sprite_loaded,
            on_extraction_completed=self._on_extraction_completed,
            on_playback_started=self._on_playback_started,
            on_playback_paused=self._on_playback_paused,
            on_playback_ended=self._on_playback_ended,
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

    def _setup_window(self):
        """Set up main window properties."""
        self.setWindowTitle(Config.App.WINDOW_TITLE)
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
        self._main_toolbar.setStyleSheet(StyleManager.main_toolbar())

        # Add toolbar actions
        self._main_toolbar.addAction(self._actions["file_open"])
        self._main_toolbar.addSeparator()
        self._main_toolbar.addAction(self._actions["toolbar_export"])

        # Add zoom display widget
        self._main_toolbar.addSeparator()
        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(Config.UI.ZOOM_LABEL_MIN_WIDTH)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_label.setStyleSheet(StyleManager.zoom_display())
        self._main_toolbar.addWidget(self._zoom_label)

    def _setup_status_bar(self):
        """Set up status bar."""
        self._status_bar = EnhancedStatusBar(self)
        self.setStatusBar(self._status_bar)

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

        # Canvas view tab (index must match Config.App.TAB_INDEX_FRAME_VIEW)
        canvas_tab = self._create_canvas_tab()
        self._tab_widget.addTab(canvas_tab, "Frame View")

        # Grid view tab (index must match Config.App.TAB_INDEX_ANIMATION_SPLIT)
        grid_tab = self._create_grid_tab()
        self._tab_widget.addTab(grid_tab, "Animation Splitting")

        # Info label at bottom
        self._info_label = QLabel(Config.App.WELCOME_MESSAGE)
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet(StyleManager.info_label())
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
        """Main entry point for loading sprites (delegated to load coordinator)."""
        return self._load_coordinator.load(file_path)

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
        self._status_bar.show_message("Animation restarted")

    def _step_animation_speed(self, increase: bool):
        """Step animation speed up or down by one entry in SPEED_STEPS."""
        current_fps = self._animation_controller.current_fps
        speed_steps = Config.Animation.SPEED_STEPS
        if increase:
            target = next((s for s in speed_steps if current_fps < s), None)
        else:
            target = next((s for s in reversed(speed_steps) if current_fps > s), None)
        if target is not None:
            self._animation_controller.set_fps(target)

    def _decrease_animation_speed(self):
        """Decrease animation speed by one step."""
        self._step_animation_speed(increase=False)

    def _increase_animation_speed(self):
        """Increase animation speed by one step."""
        self._step_animation_speed(increase=True)

    # ============================================================================
    # SIGNAL HANDLERS
    # ============================================================================

    def _on_frame_changed(self, frame_index: int, total_frames: int):
        """Handle frame change."""
        # Update canvas frame info
        self._canvas.set_frame_info(frame_index, total_frames)
        self._push_current_frame_to_canvas()

        # Update playback controls
        self._playback_controls.set_current_frame(frame_index)

        # Update button states based on current position
        has_frames = total_frames > 0
        at_start = frame_index == 0
        at_end = frame_index >= total_frames - 1 if total_frames > 0 else True
        self._playback_controls.update_button_states(
            has_frames=has_frames, at_start=at_start, at_end=at_end
        )

    def _on_sprite_loaded(self, file_path: str):
        """Sprite loaded — handler wired by SignalCoordinator (delegated)."""
        self._load_coordinator.on_sprite_loaded(file_path)

    def _on_playback_started(self):
        """Handle playback start."""
        # Disable nav buttons during active playback. at_start=True/at_end=True disables
        # both prev and next; _on_frame_changed will update to accurate position each tick.
        self._playback_controls.update_button_states(has_frames=True, at_start=True, at_end=True)

    def _on_playback_paused(self):
        """Handle playback pause."""
        # Compute actual position so prev/next are correctly enabled after pausing.
        frame_count = self._sprite_model.frame_count
        current = self._sprite_model.current_frame
        at_start = current == 0
        at_end = current >= frame_count - 1 if frame_count > 0 else True
        self._playback_controls.update_button_states(
            has_frames=frame_count > 0, at_start=at_start, at_end=at_end
        )

    def _on_playback_ended(self):
        """Handle playback stop and completion."""
        self._playback_controls.update_button_states(has_frames=True, at_start=True, at_end=False)

    def _on_animation_error(self, error_message: str):
        """Handle animation controller error."""
        QMessageBox.warning(self, "Animation Error", error_message)

    def _update_playback_for_extraction(self, frame_count: int):
        """Update playback controls after extraction completion."""
        if frame_count > 0:
            self._playback_controls.set_frame_range(frame_count - 1)
            self._playback_controls.update_button_states(
                has_frames=True, at_start=True, at_end=False
            )
        else:
            self._playback_controls.set_frame_range(0)
            self._playback_controls.update_button_states(
                has_frames=False, at_start=False, at_end=False
            )

    def _on_extraction_completed(self, frame_count: int):
        """Extraction completed — handler wired by SignalCoordinator (delegated)."""
        self._load_coordinator.on_extraction_completed(frame_count)

    def _on_frame_settings_detected(self, width: int, height: int):
        """Frame settings detected — handler wired by SignalCoordinator (delegated)."""
        self._load_coordinator.on_frame_settings_detected(width, height)

    def _on_extraction_mode_changed(self, mode: ExtractionMode):
        """Extraction mode change — handler wired by SignalCoordinator (delegated)."""
        self._load_coordinator.on_extraction_mode_changed(mode)

    def _on_settings_changed_debounced(self):
        """Restart debounce timer on settings change (delegated to load coordinator)."""
        self._load_coordinator.on_settings_changed_debounced()

    def _update_frame_slicing(self):
        """Update frame slicing based on current settings (delegated)."""
        self._load_coordinator.update_frame_slicing()

    def _push_current_frame_to_canvas(self):
        """Push the current frame pixmap to the canvas (delegated)."""
        self._load_coordinator.push_current_frame_to_canvas()

    def _show_welcome_message(self):
        """Show welcome message."""
        self._info_label.setText(Config.App.WELCOME_MESSAGE)

    def _on_grid_frame_preview(self, frame_index: int):
        """Handle frame preview request (double-click) - switch to main view."""
        self._tab_widget.setCurrentIndex(Config.App.TAB_INDEX_FRAME_VIEW)
        self._sprite_model.set_current_frame(frame_index)
        self._status_bar.show_message(f"Previewing frame {frame_index}")

    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if _is_valid_sprite_drop(event.mimeData()):
            event.acceptProposedAction()
            self._canvas.setStyleSheet(StyleManager.canvas_drag_hover())

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        """Handle drag leave event."""
        self._canvas.setStyleSheet(StyleManager.canvas_normal())
        if self._sprite_model.is_loaded:
            self._info_label.setText(self._sprite_model.sprite_info)
        else:
            self._show_welcome_message()
        event.accept()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        self._canvas.setStyleSheet(StyleManager.canvas_normal())
        file_path = _extract_file_from_drop(event)
        if file_path:
            self._load_sprite_file(file_path)
            event.acceptProposedAction()

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
        about_text = f"""
<h3>{Config.App.APP_NAME}</h3>
<p>Version {Config.App.APP_VERSION}</p>
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

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        key_sequence_str = self._build_key_sequence(event)
        if key_sequence_str is None:
            super().keyPressEvent(event)
            return

        if self._handle_shortcut(key_sequence_str):
            event.accept()
        else:
            super().keyPressEvent(event)

    def _build_key_sequence(self, event: QKeyEvent) -> str | None:
        """Build a key sequence string from a key event, or None if unhandled."""
        key = event.key()
        modifiers = event.modifiers()
        qt_key = Qt.Key(key)

        if qt_key in self.KEY_MAPPING:
            # Special keys (Space, arrows, etc.) not handled well by QKeySequence
            parts = []
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                parts.append("Ctrl")
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                parts.append("Shift")
            if modifiers & Qt.KeyboardModifier.AltModifier:
                parts.append("Alt")
            parts.append(self.KEY_MAPPING[qt_key])
            return "+".join(parts)

        if (Qt.Key.Key_A <= key <= Qt.Key.Key_Z) or (Qt.Key.Key_0 <= key <= Qt.Key.Key_9):
            if modifiers == Qt.KeyboardModifier.NoModifier:
                return chr(key)
            # Let QKeySequence handle modified keys (Ctrl+A, Alt+1, etc.)
            q_key_sequence = QKeySequence(key | modifiers.value)
            return q_key_sequence.toString()

        # Unrecognized key -- let parent handle
        return None

    def _handle_shortcut(self, key_sequence: str) -> bool:
        """
        Handle a keyboard shortcut.

        Args:
            key_sequence: String representation of key sequence

        Returns:
            True if shortcut was handled
        """
        action_id = self._shortcut_to_action.get(key_sequence)
        if action_id is not None and action_id in self._actions:
            action = self._actions[action_id]
            if action.isEnabled():
                action.trigger()
                return True
        return False

    # ============================================================================
    # EXPORT OPERATIONS
    # ============================================================================

    def _on_export_frames_requested(self) -> None:
        """Show export dialog for exporting all frames and animation segments."""
        self._show_export_dialog(self._sprite_model.sprite_frames, self._sprite_model.current_frame)

    def _on_export_current_frame_requested(self) -> None:
        """Export only the current frame."""
        current_idx = self._sprite_model.current_frame
        frames = self._sprite_model.sprite_frames
        if not frames or current_idx >= len(frames):
            return
        self._show_export_dialog([frames[current_idx]], 0)

    def _show_export_dialog(self, sprites: Sequence[QPixmap], current_frame: int) -> None:
        """Show export dialog with the given sprites."""
        if not self._export_coordinator.validate_export():
            return
        dialog = ExportDialog(
            self,
            frame_count=len(sprites),
            current_frame=current_frame,
            sprites=sprites,
            segment_manager=self._segment_manager,
            settings_manager=self._settings_manager,
        )
        dialog.exportRequested.connect(self._export_coordinator.handle_export_request)
        dialog.exec()

    def closeEvent(self, event: QCloseEvent):
        """Handle close event."""
        # Save settings
        self._settings_manager.save_window_geometry(self)

        # Stop segment preview timers before signal disconnects
        if getattr(self, "_segment_preview", None):
            self._segment_preview.clear_segments()

        # Clean up signal coordinator
        if getattr(self, "_signal_coordinator", None):
            self._signal_coordinator.disconnect_all()

        # Clean up controllers
        if getattr(self, "_animation_controller", None):
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
