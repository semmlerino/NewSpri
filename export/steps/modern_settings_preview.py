"""
Modern Export Settings with Live Preview
Redesigned for better usability and modern aesthetics.
"""

import logging
import math
import os
from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QPushButton, QFrame, QGraphicsScene, QGraphicsView,
    QSizePolicy, QTabWidget,
    QComboBox, QLineEdit, QSpinBox, QSlider, QButtonGroup,
    QRadioButton, QGridLayout, QListWidget,
    QListWidgetItem, QStackedWidget, QToolButton
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QFont

from ..dialogs.base.wizard_base import WizardStep
from ..core.export_presets import ExportPreset
from config import Config

logger = logging.getLogger(__name__)


class CompactLivePreview(QGraphicsView):
    """Modern preview widget with integrated controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Modern frame style
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QGraphicsView {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        
        # Checkerboard for transparency
        self.setBackgroundBrush(self._create_checkerboard())
        
        # Scene setup
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Preview state
        self._zoom_level = 1.0
        self._pixmap_item = None
        
    def _create_checkerboard(self) -> QBrush:
        """Create subtle checkerboard pattern."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(250, 250, 250))
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, 8, 8, QColor(240, 240, 240))
        painter.fillRect(8, 8, 8, 8, QColor(240, 240, 240))
        painter.end()
        return QBrush(pixmap)
    
    def wheelEvent(self, event):
        """Smooth zoom with mouse wheel."""
        zoom_in = 1.1
        zoom_out = 1 / zoom_in

        if event.angleDelta().y() > 0:
            self._zoom_level *= zoom_in
            self.scale(zoom_in, zoom_in)
        else:
            self._zoom_level *= zoom_out
            self.scale(zoom_out, zoom_out)
        
        # Limit zoom range
        if self._zoom_level < 0.1:
            self._zoom_level = 0.1
            self.resetTransform()
            self.scale(0.1, 0.1)
        elif self._zoom_level > 10:
            self._zoom_level = 10
            self.resetTransform()
            self.scale(10, 10)
    
    def update_preview(self, pixmap: QPixmap, info: Dict[str, Any]):
        """Update preview with modern styling."""
        self.scene.clear()
        
        if pixmap and not pixmap.isNull():
            # Add pixmap
            self._pixmap_item = self.scene.addPixmap(pixmap)
            
            # Auto-fit on first load
            QTimer.singleShot(50, self.fit_to_view)
        else:
            # Show placeholder
            text = self.scene.addText("No preview available")
            text.setDefaultTextColor(QColor(108, 117, 125))
            font = QFont("Segoe UI", 12)
            text.setFont(font)
    
    def fit_to_view(self):
        """Fit preview to view with padding."""
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
            self._zoom_level = 1.0
            # Add some padding
            self.scale(0.9, 0.9)
            self._zoom_level *= 0.9
    
    def reset_zoom(self):
        """Reset to 100% zoom."""
        self.resetTransform()
        self._zoom_level = 1.0


class ModernExportSettings(WizardStep):
    """
    Modern, compact export settings with live preview.
    """
    
    previewUpdateRequested = Signal()
    
    def __init__(self, frame_count: int = 0, current_frame: int = 0,
                 sprites: List[QPixmap] = None, segment_manager=None, parent=None):
        super().__init__(
            title="Export Settings",
            subtitle="Configure your export",
            parent=parent
        )
        self.frame_count = frame_count
        self.current_frame = current_frame
        self._sprites = sprites or []
        self._segment_manager = segment_manager
        self._current_preset: Optional[ExportPreset] = None
        self._settings_widgets = {}
        self._pattern_radios = []  # Track pattern radio buttons for updates
        
        # Preview debounce
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._update_preview)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create modern, compact UI."""
        # Remove default margins for full width
        self.setContentsMargins(0, 0, 0, 0)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Content splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
            }
        """)
        
        # Left: Settings panel
        settings_panel = self._create_settings_panel()
        self.splitter.addWidget(settings_panel)
        
        # Right: Preview panel
        preview_panel = self._create_preview_panel()
        self.splitter.addWidget(preview_panel)
        
        # Set proportions (40% settings, 60% preview)
        self.splitter.setSizes([350, 525])
        
        main_layout.addWidget(self.splitter, 1)
        
        # Bottom bar
        bottom_bar = self._create_bottom_bar()
        main_layout.addWidget(bottom_bar)
    
    def _create_settings_panel(self) -> QWidget:
        """Create compact settings panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.NoFrame)
        panel.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-right: 1px solid #dee2e6;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Essential settings (always visible)
        essential_widget = self._create_essential_settings()
        layout.addWidget(essential_widget)
        
        # Separator
        separator = QFrame()
        separator.setFrameStyle(QFrame.HLine)
        separator.setStyleSheet("background-color: #e9ecef;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Mode-specific settings (dynamic)
        self.mode_stack = QStackedWidget()
        self.mode_stack.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.mode_stack, 1)
        
        return panel
    
    def _create_essential_settings(self) -> QWidget:
        """Create always-visible essential settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Output location
        output_label = QLabel("Output Location")
        output_label.setStyleSheet("font-weight: bold; color: #212529;")
        layout.addWidget(output_label)
        
        output_layout = QHBoxLayout()
        output_layout.setSpacing(8)
        
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("Select output folder...")
        self.path_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
        """)
        
        # Load last used export directory from settings
        from managers.settings_manager import get_settings_manager
        settings_manager = get_settings_manager()
        last_export_dir = settings_manager.get_value('export/last_directory')
        
        if last_export_dir and os.path.exists(last_export_dir):
            self.path_edit.setText(last_export_dir)
            self.path_edit.setToolTip(last_export_dir)
        else:
            # Use default export directory
            default_dir = str(Config.File.get_default_export_directory())
            self.path_edit.setText(default_dir)
            self.path_edit.setToolTip(default_dir)
        
        output_layout.addWidget(self.path_edit, 1)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedSize(70, 32)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: #ffffff;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
        """)
        self.browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_btn)
        
        layout.addLayout(output_layout)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.setSpacing(12)
        
        format_label = QLabel("Format:")
        format_label.setStyleSheet("color: #495057;")
        format_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "BMP"])
        self.format_combo.setMinimumWidth(100)
        self.format_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QComboBox:hover {
                border-color: #adb5bd;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)
        
        format_layout.addStretch()
        
        # Scale selection (inline buttons)
        scale_label = QLabel("Scale:")
        scale_label.setStyleSheet("color: #495057;")
        format_layout.addWidget(scale_label)
        
        self.scale_group = QButtonGroup()
        for i, scale in enumerate([1, 2, 4]):
            btn = QPushButton(f"{scale}x")
            btn.setCheckable(True)
            btn.setFixedSize(40, 28)
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    background-color: #ffffff;
                    font-weight: 500;
                }
                QPushButton:checked {
                    background-color: #007bff;
                    border-color: #007bff;
                    color: white;
                }
                QPushButton:hover {
                    border-color: #007bff;
                }
            """)
            if scale == 1:
                btn.setChecked(True)
            self.scale_group.addButton(btn, scale)
            format_layout.addWidget(btn)
        
        self.scale_group.buttonClicked.connect(self._on_scale_changed)
        
        layout.addLayout(format_layout)
        
        self._settings_widgets['output_path'] = self.path_edit
        self._settings_widgets['format'] = self.format_combo
        self._settings_widgets['scale_group'] = self.scale_group
        
        return widget
    
    def _create_preview_panel(self) -> QWidget:
        """Create modern preview panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.NoFrame)
        panel.setStyleSheet("background-color: #f8f9fa;")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #212529;
        """)
        header_layout.addWidget(preview_label)
        
        header_layout.addStretch()
        
        # Zoom controls
        zoom_controls = self._create_zoom_controls()
        header_layout.addLayout(zoom_controls)
        
        layout.addLayout(header_layout)
        
        # Preview view
        self.preview_view = CompactLivePreview()
        self.preview_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.preview_view, 1)
        
        # Info overlay (floating)
        self.info_label = QLabel()
        self.info_label.setParent(self.preview_view)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(33, 37, 41, 0.9);
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        self.info_label.hide()
        
        return panel
    
    def _create_zoom_controls(self) -> QHBoxLayout:
        """Create compact zoom controls."""
        layout = QHBoxLayout()
        layout.setSpacing(4)
        
        # Fit button
        fit_btn = QToolButton()
        fit_btn.setText("Fit")
        fit_btn.setStyleSheet("""
            QToolButton {
                padding: 4px 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QToolButton:hover {
                background-color: #f8f9fa;
            }
        """)
        fit_btn.clicked.connect(lambda: self.preview_view.fit_to_view())
        layout.addWidget(fit_btn)
        
        # 100% button
        reset_btn = QToolButton()
        reset_btn.setText("100%")
        reset_btn.setStyleSheet(fit_btn.styleSheet())
        reset_btn.clicked.connect(lambda: self.preview_view.reset_zoom())
        layout.addWidget(reset_btn)
        
        return layout
    
    def _create_bottom_bar(self) -> QWidget:
        """Create bottom action bar."""
        bar = QFrame()
        bar.setFrameStyle(QFrame.NoFrame)
        bar.setFixedHeight(70)
        bar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }
        """)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Export summary
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("color: #6c757d;")
        layout.addWidget(self.summary_label)
        
        layout.addStretch()
        
        # Export button
        self.export_btn = QPushButton("Export Now")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setMinimumWidth(120)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        layout.addWidget(self.export_btn)
        
        return bar
    
    def _setup_for_preset(self, preset: ExportPreset):
        """Configure UI for selected preset."""
        logger.debug("_setup_for_preset called with: %s (mode: %s)", preset.name, preset.mode)
        self._current_preset = preset

        # Clear mode stack
        while self.mode_stack.count():
            self.mode_stack.removeWidget(self.mode_stack.widget(0))

        # Add appropriate settings widget
        if preset.mode == "sheet":
            logger.debug("Creating sheet settings widget")
            settings = self._create_sheet_settings()
        elif preset.mode == "segments_sheet":
            logger.debug("Creating sheet settings widget for segments_sheet mode")
            settings = self._create_sheet_settings()
        elif preset.mode == "selected":
            logger.debug("Creating selected settings widget")
            settings = self._create_selected_settings()
        else:  # individual
            logger.debug("Creating individual settings widget")
            settings = self._create_individual_settings()

        self.mode_stack.addWidget(settings)

        # Update UI
        logger.debug("Updating preview and summary after preset setup")
        self._update_preview()
        self._update_summary()
    
    def _create_sheet_settings(self) -> QWidget:
        """Create sprite sheet specific settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Filename
        filename_label = QLabel("Filename")
        filename_label.setStyleSheet("font-weight: bold; color: #212529;")
        layout.addWidget(filename_label)
        
        self.sheet_filename = QLineEdit()
        self.sheet_filename.setText("spritesheet")
        self.sheet_filename.setPlaceholderText("Enter filename (no extension)")
        self.sheet_filename.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
        """)
        self.sheet_filename.textChanged.connect(self._on_setting_changed)
        layout.addWidget(self.sheet_filename)
        
        # Layout tabs
        self.layout_tabs = QTabWidget()
        self.layout_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 6px 16px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007bff;
            }
        """)
        
        # Layout tab
        layout_tab = self._create_layout_tab()
        self.layout_tabs.addTab(layout_tab, "Layout")
        
        # Style tab
        style_tab = self._create_style_tab()
        self.layout_tabs.addTab(style_tab, "Style")
        
        layout.addWidget(self.layout_tabs, 1)
        
        self._settings_widgets['sheet_filename'] = self.sheet_filename
        
        return widget
    
    def _create_layout_tab(self) -> QWidget:
        """Create layout configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Grid mode
        mode_group = QButtonGroup()
        mode_layout = QGridLayout()
        mode_layout.setSpacing(8)
        
        modes = [
            ("Auto", "auto", "Best fit"),
            ("Fixed Columns", "columns", "Set columns"),
            ("Fixed Rows", "rows", "Set rows"),
            ("Square", "square", "Force square")
        ]
        
        for i, (label, value, tooltip) in enumerate(modes):
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            if value == "auto":
                radio.setChecked(True)
            mode_group.addButton(radio, i)
            mode_layout.addWidget(radio, i // 2, i % 2)
        
        layout.addLayout(mode_layout)
        
        # Manual controls (hidden by default)
        self.manual_controls = QWidget()
        manual_layout = QHBoxLayout(self.manual_controls)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 50)
        self.cols_spin.setValue(8)
        self.cols_spin.setPrefix("Columns: ")
        self.cols_spin.setEnabled(False)
        manual_layout.addWidget(self.cols_spin)
        
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 50)
        self.rows_spin.setValue(8)
        self.rows_spin.setPrefix("Rows: ")
        self.rows_spin.setEnabled(False)
        manual_layout.addWidget(self.rows_spin)
        
        manual_layout.addStretch()
        
        layout.addWidget(self.manual_controls)
        
        # Connect signals
        mode_group.buttonClicked.connect(lambda btn: self._on_layout_mode_changed(modes[mode_group.id(btn)][1]))
        self.cols_spin.valueChanged.connect(self._on_setting_changed)
        self.rows_spin.valueChanged.connect(self._on_setting_changed)
        
        layout.addStretch()
        
        self._settings_widgets['layout_mode'] = mode_group
        self._settings_widgets['cols_spin'] = self.cols_spin
        self._settings_widgets['rows_spin'] = self.rows_spin
        
        return widget
    
    def _create_style_tab(self) -> QWidget:
        """Create style configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # Spacing
        spacing_layout = QHBoxLayout()
        spacing_label = QLabel("Spacing:")
        spacing_layout.addWidget(spacing_label)
        
        self.spacing_slider = QSlider(Qt.Horizontal)
        self.spacing_slider.setRange(0, 32)
        self.spacing_slider.setValue(0)
        self.spacing_slider.setTickPosition(QSlider.TicksBelow)
        self.spacing_slider.setTickInterval(8)
        spacing_layout.addWidget(self.spacing_slider, 1)
        
        self.spacing_value = QLabel("0 px")
        self.spacing_value.setMinimumWidth(40)
        spacing_layout.addWidget(self.spacing_value)
        
        layout.addLayout(spacing_layout)
        
        # Background
        bg_layout = QHBoxLayout()
        bg_label = QLabel("Background:")
        bg_layout.addWidget(bg_label)
        
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["Transparent", "White", "Black", "Custom..."])
        bg_layout.addWidget(self.bg_combo, 1)
        
        layout.addLayout(bg_layout)
        
        # Connect signals
        self.spacing_slider.valueChanged.connect(
            lambda v: self.spacing_value.setText(f"{v} px")
        )
        self.spacing_slider.valueChanged.connect(self._on_setting_changed)
        self.bg_combo.currentIndexChanged.connect(self._on_setting_changed)
        
        layout.addStretch()
        
        self._settings_widgets['spacing'] = self.spacing_slider
        self._settings_widgets['background'] = self.bg_combo
        
        return widget
    
    def _create_individual_settings(self) -> QWidget:
        """Create individual frames settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Base name
        name_label = QLabel("Base Name")
        name_label.setStyleSheet("font-weight: bold; color: #212529;")
        layout.addWidget(name_label)
        
        self.base_name = QLineEdit()
        self.base_name.setText("frame")
        self.base_name.setPlaceholderText("Base filename")
        self.base_name.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
        """)
        self.base_name.textChanged.connect(self._on_base_name_changed)
        layout.addWidget(self.base_name)
        
        # Naming pattern
        pattern_label = QLabel("Naming Pattern")
        pattern_label.setStyleSheet("font-weight: bold; color: #212529; margin-top: 8px;")
        layout.addWidget(pattern_label)
        
        pattern_group = QButtonGroup()
        # Clear any existing pattern radios before adding new ones
        if not hasattr(self, '_pattern_radios'):
            self._pattern_radios = []
        else:
            self._pattern_radios.clear()
        
        patterns = [
            "{name}_{index:03d}",
            "{name}-{index}",
            "{name}{index}"
        ]
        
        for i, pattern in enumerate(patterns):
            # Generate initial display text
            display_text = self._generate_pattern_display(pattern, "frame")
            radio = QRadioButton(display_text)
            if i == 0:
                radio.setChecked(True)
            pattern_group.addButton(radio, i)
            radio.setProperty("pattern", pattern)  # Store pattern for later use
            self._pattern_radios.append(radio)
            layout.addWidget(radio)
        
        
        pattern_group.buttonClicked.connect(self._on_setting_changed)
        
        layout.addStretch()
        
        self._settings_widgets['base_name'] = self.base_name
        self._settings_widgets['pattern_group'] = pattern_group
        
        return widget
    
    def _create_selected_settings(self) -> QWidget:
        """Create selected frames settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Frame selection
        selection_label = QLabel("Select Frames")
        selection_label.setStyleSheet("font-weight: bold; color: #212529;")
        layout.addWidget(selection_label)
        
        # Quick select buttons
        quick_layout = QHBoxLayout()
        
        select_all = QPushButton("Select All")
        select_all.clicked.connect(self._select_all_frames)
        quick_layout.addWidget(select_all)
        
        select_none = QPushButton("Clear")
        select_none.clicked.connect(self._clear_frame_selection)
        quick_layout.addWidget(select_none)
        
        quick_layout.addStretch()
        layout.addLayout(quick_layout)
        
        # Frame list
        self.frame_list = QListWidget()
        self.frame_list.setSelectionMode(QListWidget.MultiSelection)
        self.frame_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
        """)
        
        # Populate frames
        for i in range(self.frame_count):
            item = QListWidgetItem(f"Frame {i + 1}")
            item.setData(Qt.UserRole, i)
            self.frame_list.addItem(item)
            if i == self.current_frame:
                item.setSelected(True)
        
        self.frame_list.itemSelectionChanged.connect(self._on_frame_selection_changed)
        layout.addWidget(self.frame_list, 1)
        
        # Selection info
        self.selection_info = QLabel()
        self.selection_info.setStyleSheet("color: #6c757d; font-size: 12px;")
        layout.addWidget(self.selection_info)
        
        self._update_selection_info()
        
        # Base name
        name_layout = QHBoxLayout()
        name_label = QLabel("Base name:")
        name_layout.addWidget(name_label)
        
        self.selected_base_name = QLineEdit("frame")
        self.selected_base_name.textChanged.connect(self._on_setting_changed)
        name_layout.addWidget(self.selected_base_name, 1)
        
        layout.addLayout(name_layout)
        
        self._settings_widgets['frame_list'] = self.frame_list
        self._settings_widgets['selected_base_name'] = self.selected_base_name
        
        return widget
    
    # Event handlers
    def _browse_output(self):
        """Browse for output directory."""
        from PySide6.QtWidgets import QFileDialog
        
        current = self.path_edit.text() or str(Config.File.get_default_export_directory())
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            current
        )
        
        if directory:
            self.path_edit.setText(directory)
            self.path_edit.setToolTip(directory)
            
            # Save last used directory to settings
            from managers.settings_manager import get_settings_manager
            settings_manager = get_settings_manager()
            settings_manager.set_value('export/last_directory', directory)
            
            self._on_setting_changed()
    
    def _on_format_changed(self, format: str):
        """Handle format change."""
        
        # Update pattern displays with new format
        try:
            if hasattr(self, '_pattern_radios') and self._pattern_radios and hasattr(self, 'base_name'):
                base_name = self.base_name.text() if self.base_name.text() else "frame"
                
                for i, radio in enumerate(self._pattern_radios):
                    pattern = radio.property("pattern")
                    if pattern:
                        new_display = self._generate_pattern_display(pattern, base_name)
                        radio.setText(new_display)
        except Exception as e:
            print(f"Warning: Error updating pattern displays on format change: {e}")
        
        # Show quality slider for JPG
        self._on_setting_changed()
    
    def _on_scale_changed(self, button):
        """Handle scale change."""
        self._on_setting_changed()
    
    def _on_layout_mode_changed(self, mode: str):
        """Handle layout mode change."""
        self.cols_spin.setEnabled(mode == "columns")
        self.rows_spin.setEnabled(mode == "rows")
        self._on_setting_changed()
    
    def _on_frame_selection_changed(self):
        """Handle frame selection change."""
        self._update_selection_info()
        self._on_setting_changed()
    
    def _update_selection_info(self):
        """Update frame selection info."""
        count = len(self.frame_list.selectedItems())
        self.selection_info.setText(
            f"{count} of {self.frame_count} frames selected"
        )
    
    def _select_all_frames(self):
        """Select all frames."""
        self.frame_list.selectAll()
    
    def _clear_frame_selection(self):
        """Clear frame selection."""
        self.frame_list.clearSelection()
    
    def _on_setting_changed(self):
        """Handle any setting change."""
        self._preview_timer.stop()
        self._preview_timer.start(100)  # 100ms debounce
        self._validate_settings()
        self._update_summary()
    
    def _validate_settings(self):
        """Validate current settings."""
        valid = bool(self.path_edit.text())
        
        if self._current_preset:
            if self._current_preset.mode == "sheet":
                valid &= bool(self._settings_widgets.get('sheet_filename', QLineEdit()).text())
            elif self._current_preset.mode == "individual":
                valid &= bool(self._settings_widgets.get('base_name', QLineEdit()).text())
            elif self._current_preset.mode == "selected":
                valid &= len(self.frame_list.selectedItems()) > 0
                valid &= bool(self._settings_widgets.get('selected_base_name', QLineEdit()).text())
        
        self.export_btn.setEnabled(valid)
        self.stepValidated.emit(valid)
    
    def _update_preview(self):
        """Update preview based on settings."""
        logger.debug("_update_preview called")
        logger.debug("Current preset: %s", self._current_preset)
        logger.debug("Current preset mode: %s", self._current_preset.mode if self._current_preset else 'None')
        logger.debug("Number of sprites: %d", len(self._sprites))
        logger.debug("Segment manager available: %s", self._segment_manager is not None)

        if not self._current_preset or not self._sprites:
            logger.debug("No preset or sprites, showing empty preview")
            self.preview_view.update_preview(QPixmap(), {})
            return

        # Generate preview
        if self._current_preset.mode == "sheet" or self._current_preset.mode == "segments_sheet":
            logger.debug("Generating sheet preview for mode: %s", self._current_preset.mode)
            pixmap = self._generate_sheet_preview()
        else:
            logger.debug("Generating frames preview for mode: %s", self._current_preset.mode)
            pixmap = self._generate_frames_preview()

        logger.debug("Generated preview pixmap size: %dx%d", pixmap.width(), pixmap.height())
        self.preview_view.update_preview(pixmap, {})
    
    def _generate_sheet_preview(self) -> QPixmap:
        """Generate sprite sheet preview."""
        logger.debug("_generate_sheet_preview called")

        if not self._sprites:
            logger.debug("No sprites available for sheet preview")
            return QPixmap()

        # Special handling for segments per row mode
        if self._current_preset and self._current_preset.mode == "segments_sheet":
            logger.debug("Detected segments_sheet mode, calling _generate_segments_preview")
            try:
                return self._generate_segments_preview()
            except Exception as e:
                # If segments preview fails, fall back to regular sheet preview
                logger.debug("Failed to generate segments preview: %s", e)
                logger.debug("Falling back to regular sheet preview")
                # Continue with regular sheet preview below
        
        # Get layout settings
        layout_mode = "auto"
        cols = rows = 8
        
        if 'layout_mode' in self._settings_widgets:
            mode_group = self._settings_widgets['layout_mode']
            modes = ["auto", "columns", "rows", "square"]
            for i, mode in enumerate(modes):
                if mode_group.button(i) and mode_group.button(i).isChecked():
                    layout_mode = mode
                    break
        
        if layout_mode == "columns":
            cols = self.cols_spin.value()
            rows = math.ceil(len(self._sprites) / cols)
        elif layout_mode == "rows":
            rows = self.rows_spin.value()
            cols = math.ceil(len(self._sprites) / rows)
        elif layout_mode == "square":
            side = math.ceil(math.sqrt(len(self._sprites)))
            cols = rows = side
        else:  # auto
            cols = math.ceil(math.sqrt(len(self._sprites)))
            rows = math.ceil(len(self._sprites) / cols)
        
        # Get spacing
        spacing = self._settings_widgets.get('spacing', QSlider()).value() if 'spacing' in self._settings_widgets else 0
        
        # Calculate size
        if self._sprites:
            fw = self._sprites[0].width()
            fh = self._sprites[0].height()
        else:
            fw = fh = 32
        
        sheet_w = cols * fw + (cols - 1) * spacing
        sheet_h = rows * fh + (rows - 1) * spacing
        
        # Create pixmap
        pixmap = QPixmap(sheet_w, sheet_h)
        
        # Background
        bg_index = self._settings_widgets.get('background', QComboBox()).currentIndex() if 'background' in self._settings_widgets else 0
        if bg_index == 0:  # Transparent
            pixmap.fill(Qt.transparent)
        elif bg_index == 1:  # White
            pixmap.fill(Qt.white)
        elif bg_index == 2:  # Black
            pixmap.fill(Qt.black)
        
        # Draw sprites
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for i, sprite in enumerate(self._sprites):
            if i >= cols * rows:
                break
            row = i // cols
            col = i % cols
            x = col * (fw + spacing)
            y = row * (fh + spacing)
            painter.drawPixmap(x, y, sprite)
        
        painter.end()
        
        # Update info
        self._update_preview_info(f"Sprite Sheet: {cols}×{rows} grid, {sheet_w}×{sheet_h}px")
        
        return pixmap
    
    def _generate_segments_preview(self) -> QPixmap:
        """Generate preview for segments per row mode."""
        logger.debug("_generate_segments_preview called")
        logger.debug("Sprites available: %d", len(self._sprites))
        logger.debug("Segment manager available: %s", self._segment_manager is not None)

        if not self._sprites or not self._segment_manager:
            logger.debug("No sprites or segment manager, showing placeholder")
            # Show placeholder if no segments available
            pixmap = QPixmap(400, 200)
            pixmap.fill(Qt.white)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw placeholder text
            font = QFont("Segoe UI", 12)
            painter.setFont(font)
            painter.setPen(QColor(108, 117, 125))
            
            text = "No animation segments available" if not self._segment_manager else "Loading segments preview..."
            painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
            
            painter.end()
            self._update_preview_info("Segments Per Row: No segments defined")
            return pixmap
        
        # Get all segments
        segments = self._segment_manager.get_all_segments() if self._segment_manager else []
        logger.debug("Retrieved %d segments from manager", len(segments))

        for i, seg in enumerate(segments):
            logger.debug("  Segment %d: '%s' frames %d-%d", i, seg.name, seg.start_frame, seg.end_frame)

        if not segments:
            logger.debug("No segments found, showing placeholder")
            # No segments, show placeholder
            pixmap = QPixmap(400, 200)
            pixmap.fill(Qt.white)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            font = QFont("Segoe UI", 12)
            painter.setFont(font)
            painter.setPen(QColor(108, 117, 125))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "No animation segments defined")
            
            painter.end()
            self._update_preview_info("Segments Per Row: No segments")
            return pixmap
        
        # Calculate layout for segments
        try:
            max_frames_in_segment = max(seg.end_frame - seg.start_frame + 1 for seg in segments)
            logger.debug("Max frames in any segment: %d", max_frames_in_segment)
        except (ValueError, AttributeError) as e:
            # Handle case where segments might be malformed
            logger.debug("Invalid segment data: %s", e)
            max_frames_in_segment = 1

        rows = len(segments)
        cols = max_frames_in_segment
        logger.debug("Preview layout will be %d rows x %d cols", rows, cols)
        
        # Get spacing
        spacing = self._settings_widgets.get('spacing', QSlider()).value() if 'spacing' in self._settings_widgets else 0
        
        # Calculate size
        if self._sprites:
            fw = self._sprites[0].width()
            fh = self._sprites[0].height()
        else:
            fw = fh = 32
        
        # Scale down for preview if too large
        max_preview_width = 800
        max_preview_height = 600
        
        # Calculate compact dimensions based on actual content
        # Width: longest segment with spacing
        sheet_w = max_frames_in_segment * fw + (max_frames_in_segment - 1) * spacing
        # Height: number of segments with spacing  
        sheet_h = rows * fh + (rows - 1) * spacing
        
        
        # Scale if needed
        scale = 1.0
        if sheet_w > max_preview_width:
            scale = max_preview_width / sheet_w
        if sheet_h * scale > max_preview_height:
            scale = max_preview_height / sheet_h
        
        if scale < 1.0:
            fw = int(fw * scale)
            fh = int(fh * scale)
            spacing = int(spacing * scale)
            # Recalculate compact dimensions with scaled values
            sheet_w = max_frames_in_segment * fw + (max_frames_in_segment - 1) * spacing
            sheet_h = rows * fh + (rows - 1) * spacing
        
        # Create pixmap
        pixmap = QPixmap(sheet_w, sheet_h)
        
        # Background
        bg_index = self._settings_widgets.get('background', QComboBox()).currentIndex() if 'background' in self._settings_widgets else 0
        if bg_index == 0:  # Transparent
            pixmap.fill(Qt.transparent)
        elif bg_index == 1:  # White
            pixmap.fill(Qt.white)
        elif bg_index == 2:  # Black
            pixmap.fill(Qt.black)
        
        # Draw segments
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for row_idx, segment in enumerate(segments):
            frames_drawn = 0
            # Draw frames for this segment
            for frame_idx in range(segment.start_frame, segment.end_frame + 1):
                if frame_idx < len(self._sprites):
                    col_idx = frame_idx - segment.start_frame
                    x = col_idx * (fw + spacing)
                    y = row_idx * (fh + spacing)
                    
                    if scale < 1.0:
                        scaled_sprite = self._sprites[frame_idx].scaled(
                            fw, fh, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                        painter.drawPixmap(x, y, scaled_sprite)
                    else:
                        painter.drawPixmap(x, y, self._sprites[frame_idx])
                    frames_drawn += 1
        
        painter.end()
        
        # Update info
        info = f"Segments Per Row: {rows} segments"
        if scale < 1.0:
            info += f" (preview scaled {int(scale*100)}%)"
        self._update_preview_info(info)
        
        return pixmap
    
    def _generate_frames_preview(self) -> QPixmap:
        """Generate individual frames preview."""
        if not self._sprites:
            return QPixmap()
        
        # Show grid of frames
        display_count = min(len(self._sprites), 6)
        cols = min(3, display_count)
        rows = math.ceil(display_count / cols)
        
        # Size for preview
        fw = min(self._sprites[0].width(), 100)
        fh = min(self._sprites[0].height(), 100)
        spacing = 10
        
        width = cols * fw + (cols - 1) * spacing
        height = rows * fh + (rows - 1) * spacing
        
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get selected frames if in selected mode
        selected_indices = []
        if self._current_preset.mode == "selected" and 'frame_list' in self._settings_widgets:
            for item in self._settings_widgets['frame_list'].selectedItems():
                selected_indices.append(item.data(Qt.UserRole))
        else:
            selected_indices = list(range(len(self._sprites)))
        
        # Draw frames
        for i in range(min(display_count, len(selected_indices))):
            frame_idx = selected_indices[i]
            if frame_idx < len(self._sprites):
                row = i // cols
                col = i % cols
                x = col * (fw + spacing)
                y = row * (fh + spacing)
                
                scaled = self._sprites[frame_idx].scaled(
                    fw, fh, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                painter.drawPixmap(x, y, scaled)
        
        painter.end()
        
        # Update info
        if self._current_preset.mode == "selected":
            info = f"Selected: {len(selected_indices)} frames"
        else:
            info = f"Individual: {len(self._sprites)} frames"
        
        if len(selected_indices) > display_count:
            info += f" (showing {display_count})"
        
        self._update_preview_info(info)
        
        return pixmap
    
    def _update_preview_info(self, text: str):
        """Update preview info overlay."""
        self.info_label.setText(text)
        self.info_label.adjustSize()
        self.info_label.move(10, 10)
        self.info_label.show()
        
        # Auto-hide after 3 seconds
        QTimer.singleShot(3000, self.info_label.hide)
    
    def _update_summary(self):
        """Update export summary."""
        parts = []
        
        # Output path
        output = self.path_edit.text()
        if output:
            if len(output) > 40:
                output = "..." + output[-37:]
            parts.append(f"📁 {output}")
        
        # Format and scale
        format = self.format_combo.currentText()
        scale = self.scale_group.checkedId() if self.scale_group.checkedButton() else 1
        parts.append(f"{format} @ {scale}x")
        
        # Mode specific
        if self._current_preset:
            if self._current_preset.mode == "sheet":
                filename = self._settings_widgets.get('sheet_filename', QLineEdit()).text()
                if filename:
                    parts.append(f"→ {filename}.{format.lower()}")
            elif self._current_preset.mode == "selected":
                count = len(self.frame_list.selectedItems()) if hasattr(self, 'frame_list') else 0
                parts.append(f"({count} frames)")
        
        self.summary_label.setText(" • ".join(parts))
    
    def on_entering(self):
        """Called when entering this step."""
        logger.debug("ModernExportSettings.on_entering called")

        # Get preset from wizard
        wizard = self.parent()
        while wizard and not hasattr(wizard, 'get_wizard_data'):
            wizard = wizard.parent()

        if wizard:
            wizard_data = wizard.get_wizard_data()
            logger.debug("Wizard data keys: %s", list(wizard_data.keys()))

            step_0_data = wizard_data.get('step_0', {})
            logger.debug("Step 0 data keys: %s", list(step_0_data.keys()))

            preset = step_0_data.get('preset')
            logger.debug("Retrieved preset: %s", preset.name if preset else 'None')

            if preset:
                self._setup_for_preset(preset)
            else:
                logger.debug("No preset found in wizard data")
        else:
            logger.debug("No wizard found in parent hierarchy")
    
    def validate(self) -> bool:
        """Validate the step."""
        return self.export_btn.isEnabled()
    
    def get_data(self) -> Dict[str, Any]:
        """Get all settings data."""
        logger.debug("ModernExportSettings.get_data() called")
        logger.debug("Current preset: %s", self._current_preset.name if self._current_preset else 'None')
        logger.debug("Current preset mode: %s", self._current_preset.mode if self._current_preset else 'None')

        data = {
            'output_dir': self.path_edit.text(),
            'format': self.format_combo.currentText(),
            'scale': self.scale_group.checkedId() if self.scale_group.checkedButton() else 1
        }

        logger.debug("Base data: output_dir='%s', format='%s', scale=%s", data['output_dir'], data['format'], data['scale'])
        
        if self._current_preset:
            if self._current_preset.mode == "sheet":
                data['single_filename'] = self._settings_widgets.get('sheet_filename', QLineEdit()).text()
                
                # Layout settings
                layout_mode = "auto"
                if 'layout_mode' in self._settings_widgets:
                    mode_group = self._settings_widgets['layout_mode']
                    modes = ["auto", "columns", "rows", "square"]
                    for i, mode in enumerate(modes):
                        if mode_group.button(i) and mode_group.button(i).isChecked():
                            layout_mode = mode
                            break
                
                data['layout_mode'] = layout_mode
                data['columns'] = self.cols_spin.value()
                data['rows'] = self.rows_spin.value()
                
                # Style settings
                data['spacing'] = self._settings_widgets.get('spacing', QSlider()).value()
                data['padding'] = 0
                
                bg_index = self._settings_widgets.get('background', QComboBox()).currentIndex()
                if bg_index == 0:
                    data['background_mode'] = 'transparent'
                elif bg_index == 1:
                    data['background_mode'] = 'solid'
                    data['background_color'] = (255, 255, 255, 255)
                else:
                    data['background_mode'] = 'solid'
                    data['background_color'] = (0, 0, 0, 255)
            
            elif self._current_preset.mode == "individual":
                # Get base name with proper fallback
                base_name_widget = self._settings_widgets.get('base_name')
                if base_name_widget and hasattr(base_name_widget, 'text'):
                    base_name = base_name_widget.text()
                    data['base_name'] = base_name if base_name else 'frame'
                else:
                    data['base_name'] = 'frame'
                
                # Pattern
                patterns = ["{name}_{index:03d}", "{name}-{index}", "{name}{index}"]
                pattern_group = self._settings_widgets.get('pattern_group')
                if pattern_group and pattern_group.checkedButton():
                    data['pattern'] = patterns[pattern_group.id(pattern_group.checkedButton())]
                else:
                    data['pattern'] = patterns[0]
            
            elif self._current_preset.mode == "selected":
                # Selected frames
                selected_indices = []
                if hasattr(self, 'frame_list'):
                    for item in self.frame_list.selectedItems():
                        selected_indices.append(item.data(Qt.UserRole))
                data['selected_indices'] = selected_indices
                
                # Get base name with proper fallback
                base_name_widget = self._settings_widgets.get('selected_base_name')
                if base_name_widget and hasattr(base_name_widget, 'text'):
                    base_name = base_name_widget.text()
                    data['base_name'] = base_name if base_name else 'frame'
                else:
                    data['base_name'] = 'frame'
                data['pattern'] = "{name}_{index:03d}"

        logger.debug("Final get_data() result: %s", data)
        logger.debug("Data keys: %s", list(data.keys()))
        return data
    
    def set_sprites(self, sprites: List[QPixmap]):
        """Set sprite frames."""
        self._sprites = sprites
        if self._current_preset:
            self._update_preview()
    
    def _generate_pattern_display(self, pattern: str, base_name: str) -> str:
        """Generate display text for a pattern with the given base name."""
        
        # Get format extension
        format_ext = self.format_combo.currentText().lower() if hasattr(self, 'format_combo') else 'png'
        
        # Replace placeholders
        if pattern == "{name}_{index:03d}":
            result = f"{base_name}_001.{format_ext}"
        elif pattern == "{name}-{index}":
            result = f"{base_name}-1.{format_ext}"
        elif pattern == "{name}{index}":
            result = f"{base_name}1.{format_ext}"
        else:
            result = f"{base_name}.{format_ext}"
        
        return result
    
    def _on_base_name_changed(self, text: str):
        """Handle base name change - update pattern displays."""
        
        if not hasattr(self, '_pattern_radios') or not self._pattern_radios:
            self._on_setting_changed()
            return
            
        # Update pattern radio button displays
        base_name = text if text else "frame"
        try:
            for i, radio in enumerate(self._pattern_radios):
                pattern = radio.property("pattern")
                if pattern:
                    new_display = self._generate_pattern_display(pattern, base_name)
                    radio.setText(new_display)
        except Exception as e:
            print(f"Warning: Error updating pattern displays: {e}")
        
        # Trigger regular setting change
        self._on_setting_changed()