"""
UI Setup Helper for SpriteViewer refactoring.
Handles all UI component creation and initialization.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

from .base import CoordinatorBase
from config import Config
from utils import StyleManager


class UISetupHelper(CoordinatorBase):
    """
    Coordinator responsible for UI setup and initialization.
    
    Extracts UI creation logic from SpriteViewer to improve
    maintainability and testability.
    """
    
    def __init__(self, main_window):
        """Initialize UI setup helper."""
        super().__init__(main_window)
        
        # References to created UI components
        self.central_widget = None
        self.tab_widget = None
        self.canvas = None
        self.playback_controls = None
        self.frame_extractor = None
        self.grid_view = None
        self.info_label = None
        self.zoom_label = None
        self.main_toolbar = None
        self.status_manager = None
        self.menus = None
    
    def initialize(self, dependencies):
        """
        Initialize helper with required dependencies.
        
        Args:
            dependencies: Dict containing:
                - menu_manager: MenuManager instance
                - action_manager: ActionManager instance
                - shortcut_manager: ShortcutManager instance
                - segment_manager: AnimationSegmentManager instance
                - sprite_model: SpriteModel instance
                - segment_controller: AnimationSegmentController instance
        """
        self.menu_manager = dependencies['menu_manager']
        self.action_manager = dependencies['action_manager']
        self.shortcut_manager = dependencies['shortcut_manager']
        self.segment_manager = dependencies['segment_manager']
        self.sprite_model = dependencies['sprite_model']
        self.segment_controller = dependencies.get('segment_controller')  # Optional for now
        
        # Import UI components here to avoid circular imports
        from ui import (
            SpriteCanvas, PlaybackControls, FrameExtractor,
            AnimationGridView, EnhancedStatusBar, StatusBarManager
        )
        
        self._canvas_class = SpriteCanvas
        self._playback_controls_class = PlaybackControls
        self._frame_extractor_class = FrameExtractor
        self._grid_view_class = AnimationGridView
        self._status_bar_class = EnhancedStatusBar
        self._status_manager_class = StatusBarManager
    
    def cleanup(self):
        """Clean up resources."""
        # UI components are owned by Qt and will be cleaned up automatically
        pass
    
    def setup_ui(self):
        """
        Set up complete user interface.
        
        Returns:
            dict: Dictionary of created UI components
        """
        self._setup_window()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_main_content()
        
        return {
            'central_widget': self.central_widget,
            'tab_widget': self.tab_widget,
            'canvas': self.canvas,
            'playback_controls': self.playback_controls,
            'frame_extractor': self.frame_extractor,
            'grid_view': self.grid_view,
            'info_label': self.info_label,
            'zoom_label': self.zoom_label,
            'main_toolbar': self.main_toolbar,
            'status_manager': self.status_manager,
            'menus': self.menus
        }
    
    def _setup_window(self):
        """Set up main window properties."""
        self.main_window.setWindowTitle("Python Sprite Viewer")
        self.main_window.setMinimumSize(Config.UI.MIN_WINDOW_WIDTH, Config.UI.MIN_WINDOW_HEIGHT)
        self.main_window.setAcceptDrops(True)
    
    def _setup_menu_bar(self):
        """Set up menu bar using MenuManager."""
        menubar = self.main_window.menuBar()
        self.menus = self.menu_manager.create_menu_bar(menubar)
    
    def _setup_toolbar(self):
        """Set up toolbar using MenuManager."""
        # Create main toolbar
        self.main_toolbar = self.menu_manager.create_toolbar('main')
        
        # Apply styling
        if self.main_toolbar:
            self.main_toolbar.setStyleSheet(StyleManager.get_main_toolbar())
            
            # Add zoom display widget
            self.main_toolbar.addSeparator()
            self.zoom_label = QLabel("100%")
            self.zoom_label.setMinimumWidth(Config.UI.ZOOM_LABEL_MIN_WIDTH)
            self.zoom_label.setAlignment(Qt.AlignCenter)
            self.zoom_label.setStyleSheet(StyleManager.get_zoom_display())
            self.main_toolbar.addWidget(self.zoom_label)
    
    def _setup_status_bar(self):
        """Set up status bar."""
        status_bar = self._status_bar_class(self.main_window)
        self.main_window.setStatusBar(status_bar)
        self.status_manager = self._status_manager_class(status_bar)
    
    def _setup_main_content(self):
        """Set up main content area with tabbed interface."""
        # Create central widget
        self.central_widget = QWidget()
        self.main_window.setCentralWidget(self.central_widget)
        
        # Main vertical layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Canvas view tab
        canvas_tab = self._create_canvas_tab()
        self.tab_widget.addTab(canvas_tab, "Frame View")
        
        # Grid view tab for animation splitting
        grid_tab = self._create_grid_tab()
        self.tab_widget.addTab(grid_tab, "Animation Splitting")
        
        # Info label at bottom
        self.info_label = QLabel("Ready - Drag and drop a sprite sheet or use File > Open")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(StyleManager.get_info_label())
        main_layout.addWidget(self.info_label)
    
    def _create_canvas_tab(self):
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
        self.canvas = self._create_canvas_section()
        splitter.addWidget(self.canvas)
        
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
        # Initialize grid view
        self.grid_view = self._grid_view_class()
        
        # Synchronize grid view with existing segments
        self.grid_view.sync_segments_with_manager(self.segment_manager)
        
        # Add refresh button for debugging
        container = QWidget()
        layout = QVBoxLayout(container)
        
        refresh_btn = QPushButton("🔄 Refresh Grid View")
        
        # Connect refresh button to segment controller if available
        if self.segment_controller:
            refresh_btn.clicked.connect(self.segment_controller.update_grid_view_frames)
            # Connect tab widget signal
            self.tab_widget.currentChanged.connect(self.segment_controller.on_tab_changed)
        
        layout.addWidget(refresh_btn)
        layout.addWidget(self.grid_view)
        
        return container
    
    def _create_canvas_section(self):
        """Create canvas section."""
        self.canvas = self._canvas_class()
        # Set sprite model reference for canvas to get current frame
        self.canvas.set_sprite_model(self.sprite_model)
        return self.canvas
    
    def _create_controls_section(self):
        """Create controls section."""
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)
        
        # Playback controls
        self.playback_controls = self._playback_controls_class()
        controls_layout.addWidget(self.playback_controls)
        
        # Frame extractor
        self.frame_extractor = self._frame_extractor_class()
        controls_layout.addWidget(self.frame_extractor)
        
        # Stretch to push everything to top
        controls_layout.addStretch()
        
        return controls_widget