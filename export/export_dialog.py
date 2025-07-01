"""
Export Dialog - Redesigned User Interface for Frame Export
Modern, user-friendly export dialog with preset selection and live preview.
Part of Phase 1: Export Dialog Redesign implementation.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox,
    QGroupBox, QFileDialog, QDialogButtonBox, QListWidget,
    QListWidgetItem, QProgressBar, QMessageBox, QRadioButton,
    QButtonGroup, QFormLayout, QSizePolicy, QFrame, QWidget,
    QScrollArea, QSpacerItem, QApplication, QColorDialog
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QFont

from config import Config
from utils.styles import StyleManager
from .frame_exporter import get_frame_exporter, ExportMode, ExportFormat, SpriteSheetLayout

# Import new components
from .export_presets import ExportPreset, ExportPresetType, get_preset_manager
from .export_preset_widget import ExportPresetSelector, PresetRecommendationWidget
from .export_preview_widget import ExportPreviewWidget, SizeWarningWidget
from .sprite_preview_widget import SpriteSheetPreviewWidget
from ui.validation_widgets import SmartDirectorySelector, SmartFilenameEdit, PatternEdit
from ui.collapsible_section import CollapsibleSection
from ui.animation_segment_widget import AnimationSegmentSelector

# Animation segment manager import with fallback
try:
    from managers.animation_segment_manager import AnimationSegmentManager
except ImportError:
    AnimationSegmentManager = None


class ExportDialog(QDialog):
    """Redesigned export dialog with improved usability and preset system."""
    
    # Signals
    exportRequested = Signal(dict)  # Export settings
    
    def __init__(self, parent=None, frame_count: int = 0, current_frame: int = 0,
                 segment_manager=None):
        """
        Initialize redesigned export dialog.
        
        Args:
            parent: Parent widget
            frame_count: Total number of frames available
            current_frame: Currently selected frame index
            segment_manager: Optional animation segment manager for segment export
        """
        super().__init__(parent)
        self.frame_count = frame_count
        self.current_frame = current_frame
        self.segment_manager = segment_manager
        self._exporter = get_frame_exporter()
        self._preset_manager = get_preset_manager()
        
        # Current state
        self._current_preset: Optional[ExportPreset] = None
        self._current_settings: Dict[str, Any] = {}
        self._current_sprites: List[QPixmap] = []  # For visual preview
        
        self._setup_ui()
        self._connect_signals()
        self._initialize_defaults()
    
    def _setup_ui(self):
        """Set up the redesigned dialog UI with smart sizing and scrolling."""
        self.setWindowTitle("Export Frames")
        self.setModal(True)
        
        # Smart sizing based on screen dimensions
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        max_width = min(900, int(screen_geometry.width() * 0.6))
        max_height = min(700, int(screen_geometry.height() * 0.8))
        
        self.setMinimumSize(650, 500)
        self.setMaximumSize(max_width, max_height)
        self.resize(700, 600)  # Reasonable default size
        
        # Main container layout
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Create scrollable content area
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(QScrollArea.NoFrame)
        
        # Main content widget inside scroll area
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(20, 20, 20, 10)
        main_layout.setSpacing(14)
        
        # Title section
        title_section = self._create_title_section()
        main_layout.addWidget(title_section)
        
        # Preset selection section
        preset_section = self._create_preset_section()
        main_layout.addWidget(preset_section)
        
        # Output location section
        output_section = self._create_output_section()
        main_layout.addWidget(output_section)
        
        # Preview section
        preview_section = self._create_preview_section()
        main_layout.addWidget(preview_section)
        
        # Layout configuration section (for sprite sheets)
        self.layout_section = self._create_layout_configuration_section()
        main_layout.addWidget(self.layout_section)
        
        # Animation segments section (conditionally visible)
        self.segments_section = self._create_segments_section()
        main_layout.addWidget(self.segments_section)
        
        # Advanced settings (collapsible)
        advanced_section = self._create_advanced_section()
        main_layout.addWidget(advanced_section)
        
        # Progress and status
        progress_section = self._create_progress_section()
        main_layout.addWidget(progress_section)
        
        # Add stretch to push everything up in the scroll area
        main_layout.addStretch()
        
        # Set the content widget in the scroll area
        scroll_area.setWidget(content_widget)
        container_layout.addWidget(scroll_area)
        
        # Action buttons stay outside scroll area (always visible)
        button_section = self._create_action_buttons()
        button_section.setStyleSheet("""
            QWidget {
                background-color: #fafafa;
                border-top: 1px solid #e0e0e0;
            }
        """)
        container_layout.addWidget(button_section)
        
        # Apply modern styling
        self.setStyleSheet("""
            QDialog {
                background-color: #fafafa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: white;
                color: #333;
            }
        """)
    
    def _create_title_section(self) -> QWidget:
        """Create the title section with frame count info."""
        section = QWidget()
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main title
        title_label = QLabel("Export Frames")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Frame count info
        if self.frame_count > 0:
            info_text = f"{self.frame_count} frames available"
            info_label = QLabel(info_text)
            info_label.setStyleSheet("""
                QLabel {
                    background-color: #e3f2fd;
                    color: #1976d2;
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: 500;
                }
            """)
            layout.addWidget(info_label)
        
        return section
    
    def _create_preset_section(self) -> QGroupBox:
        """Create the preset selection section."""
        group = QGroupBox()
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Preset selector
        self.preset_selector = ExportPresetSelector()
        layout.addWidget(self.preset_selector)
        
        # Recommendation widget
        self.recommendation_widget = PresetRecommendationWidget()
        layout.addWidget(self.recommendation_widget)
        
        return group
    
    def _create_output_section(self) -> QGroupBox:
        """Create the output location section."""
        group = QGroupBox("Output Location")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Smart directory selector
        self.directory_selector = SmartDirectorySelector()
        layout.addWidget(self.directory_selector)
        
        return group
    
    def _create_preview_section(self) -> QWidget:
        """Create the enhanced preview section with visual and export previews."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Create tab widget for different preview types
        from PySide6.QtWidgets import QTabWidget
        preview_tabs = QTabWidget()
        
        # Export preview tab (existing functionality)
        export_preview_container = QWidget()
        export_layout = QVBoxLayout(export_preview_container)
        export_layout.setContentsMargins(8, 8, 8, 8)
        
        self.preview_widget = ExportPreviewWidget()
        export_layout.addWidget(self.preview_widget)
        
        self.warning_widget = SizeWarningWidget()
        export_layout.addWidget(self.warning_widget)
        
        preview_tabs.addTab(export_preview_container, "📊 Export Info")
        
        # Visual preview tab (new Phase 4 functionality)
        visual_preview_container = QWidget()
        visual_layout = QVBoxLayout(visual_preview_container)
        visual_layout.setContentsMargins(8, 8, 8, 8)
        
        self.visual_preview_widget = SpriteSheetPreviewWidget()
        visual_layout.addWidget(self.visual_preview_widget)
        
        preview_tabs.addTab(visual_preview_container, "🖼️ Visual Preview")
        
        layout.addWidget(preview_tabs)
        
        return section
    
    def _create_segments_section(self) -> QWidget:
        """Create the animation segments section."""
        # Animation segment selector
        self.segment_selector = AnimationSegmentSelector(self.segment_manager)
        
        # Initially hidden - only show when segments preset is selected
        self.segment_selector.setVisible(False)
        
        return self.segment_selector
    
    def _create_layout_configuration_section(self) -> QGroupBox:
        """Create the layout configuration section for sprite sheet exports."""
        group = QGroupBox("Sprite Sheet Layout")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Top row: Layout mode and grid constraints
        mode_row = QWidget()
        mode_layout = QHBoxLayout(mode_row)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(12)
        
        # Layout mode selection
        mode_group = QGroupBox("Layout Mode")
        mode_group_layout = QVBoxLayout(mode_group)
        mode_group_layout.setSpacing(6)
        mode_group_layout.setContentsMargins(8, 12, 8, 8)
        
        self.layout_mode_combo = QComboBox()
        self.layout_mode_combo.addItems([
            "Auto (optimal)",
            "Rows (horizontal)",
            "Columns (vertical)", 
            "Square",
            "Custom grid"
        ])
        self.layout_mode_combo.setCurrentIndex(0)  # Default to auto
        mode_group_layout.addWidget(self.layout_mode_combo)
        
        # Grid constraints (visible based on mode)
        constraints_widget = QWidget()
        constraints_layout = QHBoxLayout(constraints_widget)
        constraints_layout.setContentsMargins(0, 0, 0, 0)
        constraints_layout.setSpacing(8)
        
        # Max columns (for rows mode)
        self.max_cols_label = QLabel("Max columns:")
        self.max_cols_spin = QSpinBox()
        self.max_cols_spin.setRange(1, Config.Export.MAX_GRID_SIZE)
        self.max_cols_spin.setValue(Config.Export.DEFAULT_MAX_COLUMNS)
        self.max_cols_spin.setMaximumWidth(60)
        
        # Max rows (for columns mode)
        self.max_rows_label = QLabel("Max rows:")
        self.max_rows_spin = QSpinBox()
        self.max_rows_spin.setRange(1, Config.Export.MAX_GRID_SIZE)
        self.max_rows_spin.setValue(Config.Export.DEFAULT_MAX_ROWS)
        self.max_rows_spin.setMaximumWidth(60)
        
        # Custom grid (for custom mode)
        self.custom_cols_label = QLabel("Columns:")
        self.custom_cols_spin = QSpinBox()
        self.custom_cols_spin.setRange(1, Config.Export.MAX_GRID_SIZE)
        self.custom_cols_spin.setValue(4)
        self.custom_cols_spin.setMaximumWidth(60)
        
        self.custom_rows_label = QLabel("Rows:")
        self.custom_rows_spin = QSpinBox()
        self.custom_rows_spin.setRange(1, Config.Export.MAX_GRID_SIZE)
        self.custom_rows_spin.setValue(4)
        self.custom_rows_spin.setMaximumWidth(60)
        
        constraints_layout.addWidget(self.max_cols_label)
        constraints_layout.addWidget(self.max_cols_spin)
        constraints_layout.addWidget(self.max_rows_label)
        constraints_layout.addWidget(self.max_rows_spin)
        constraints_layout.addWidget(self.custom_cols_label)
        constraints_layout.addWidget(self.custom_cols_spin)
        constraints_layout.addWidget(self.custom_rows_label)
        constraints_layout.addWidget(self.custom_rows_spin)
        constraints_layout.addStretch()
        
        mode_group_layout.addWidget(constraints_widget)
        mode_layout.addWidget(mode_group)
        
        # Spacing and padding controls
        spacing_group = QGroupBox("Spacing & Padding")
        spacing_group.setMaximumWidth(280)
        spacing_group_layout = QVBoxLayout(spacing_group)
        spacing_group_layout.setSpacing(6)
        spacing_group_layout.setContentsMargins(8, 12, 8, 8)
        
        # Sprite spacing
        spacing_row = QHBoxLayout()
        spacing_row.addWidget(QLabel("Spacing:"))
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(Config.Export.MIN_SPRITE_SPACING, Config.Export.MAX_SPRITE_SPACING)
        self.spacing_spin.setValue(Config.Export.DEFAULT_SPRITE_SPACING)
        self.spacing_spin.setSingleStep(Config.Export.SPRITE_SPACING_STEP)
        self.spacing_spin.setSuffix("px")
        self.spacing_spin.setMaximumWidth(80)
        spacing_row.addWidget(self.spacing_spin)
        spacing_row.addStretch()
        spacing_group_layout.addLayout(spacing_row)
        
        # Sheet padding
        padding_row = QHBoxLayout()
        padding_row.addWidget(QLabel("Padding:"))
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(Config.Export.MIN_SHEET_PADDING, Config.Export.MAX_SHEET_PADDING)
        self.padding_spin.setValue(Config.Export.DEFAULT_SHEET_PADDING)
        self.padding_spin.setSingleStep(Config.Export.SHEET_PADDING_STEP)
        self.padding_spin.setSuffix("px")
        self.padding_spin.setMaximumWidth(80)
        padding_row.addWidget(self.padding_spin)
        padding_row.addStretch()
        spacing_group_layout.addLayout(padding_row)
        
        mode_layout.addWidget(spacing_group)
        layout.addWidget(mode_row)
        
        # Bottom row: Background options
        background_row = QWidget()
        background_layout = QHBoxLayout(background_row)
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_layout.setSpacing(12)
        
        # Background mode selection
        background_group = QGroupBox("Background")
        background_group_layout = QVBoxLayout(background_group)
        background_group_layout.setSpacing(6)
        background_group_layout.setContentsMargins(8, 12, 8, 8)
        
        background_mode_row = QHBoxLayout()
        background_mode_row.addWidget(QLabel("Mode:"))
        self.background_combo = QComboBox()
        self.background_combo.addItems([
            "Transparent",
            "Solid color",
            "Checkerboard"
        ])
        self.background_combo.setCurrentIndex(0)  # Default to transparent
        self.background_combo.setMaximumWidth(120)
        background_mode_row.addWidget(self.background_combo)
        background_mode_row.addStretch()
        background_group_layout.addLayout(background_mode_row)
        
        # Color picker (for solid background)
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color:"))
        self.background_color_button = QPushButton()
        self.background_color_button.setMaximumWidth(60)
        self.background_color_button.setMaximumHeight(25)
        self.background_color_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
        self._current_background_color = (255, 255, 255, 255)  # Default white
        color_row.addWidget(self.background_color_button)
        color_row.addStretch()
        background_group_layout.addLayout(color_row)
        
        background_layout.addWidget(background_group)
        
        # Preview info (shows calculated dimensions)
        preview_group = QGroupBox("Layout Preview")
        preview_group_layout = QVBoxLayout(preview_group)
        preview_group_layout.setSpacing(4)
        preview_group_layout.setContentsMargins(8, 12, 8, 8)
        
        self.layout_preview_label = QLabel("Grid: Auto | Size: Calculating...")
        self.layout_preview_label.setStyleSheet("color: #666; font-size: 11px;")
        self.layout_preview_label.setWordWrap(True)
        preview_group_layout.addWidget(self.layout_preview_label)
        
        background_layout.addWidget(preview_group)
        layout.addWidget(background_row)
        
        # Initially hidden - only show for sprite sheet exports
        group.setVisible(False)
        
        return group
    
    def _create_advanced_section(self) -> CollapsibleSection:
        """Create the collapsible advanced settings section with compact layout."""
        # Advanced settings container with compact layout
        advanced_container = QWidget()
        advanced_layout = QVBoxLayout(advanced_container)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.setSpacing(8)  # Reduced spacing
        
        # Compact settings: Format and naming in horizontal layout
        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)
        
        # Format settings (more compact)
        format_group = self._create_compact_format_settings()
        top_layout.addWidget(format_group)
        
        # Naming settings (more compact)
        naming_group = self._create_compact_naming_settings()
        top_layout.addWidget(naming_group)
        
        advanced_layout.addWidget(top_row)
        
        # Frame selection (for individual frames with selection option) - keep full width
        self.selection_group = self._create_compact_selection_group()
        advanced_layout.addWidget(self.selection_group)
        
        # Create collapsible section
        collapsible = CollapsibleSection("Advanced Settings", advanced_container, expanded=False)
        collapsible.set_info_badge("Optional")
        
        return collapsible
    
    def _create_compact_format_settings(self) -> QGroupBox:
        """Create compact format and quality settings."""
        group = QGroupBox("Format & Scale")
        group.setMaximumWidth(280)  # Constrain width for side-by-side layout
        layout = QVBoxLayout(group)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 12, 8, 8)
        
        # Format row
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(Config.Export.IMAGE_FORMATS)
        self.format_combo.setCurrentText(Config.Export.DEFAULT_FORMAT)
        self.format_combo.setMaximumWidth(80)
        format_row.addWidget(self.format_combo)
        format_row.addStretch()
        layout.addLayout(format_row)
        
        # Scale row
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Scale:"))
        
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 10.0)
        self.scale_spin.setSingleStep(0.5)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setSuffix("x")
        self.scale_spin.setDecimals(1)
        self.scale_spin.setMaximumWidth(60)
        scale_row.addWidget(self.scale_spin)
        scale_row.addStretch()
        layout.addLayout(scale_row)
        
        # Quick scale buttons in a compact row
        button_row = QHBoxLayout()
        button_row.setSpacing(4)
        for scale in [0.5, 1.0, 2.0, 4.0]:
            btn = QPushButton(f"{scale}x")
            btn.setFixedSize(35, 20)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 9px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f8f8f8;
                    padding: 1px;
                }
                QPushButton:hover {
                    background-color: #e8e8e8;
                }
                QPushButton:pressed {
                    background-color: #d8d8d8;
                }
            """)
            btn.clicked.connect(lambda checked, s=scale: self.scale_spin.setValue(s))
            button_row.addWidget(btn)
        button_row.addStretch()
        layout.addLayout(button_row)
        
        return group
    
    def _create_compact_naming_settings(self) -> QGroupBox:
        """Create compact naming settings group."""
        group = QGroupBox("File Naming")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 12, 8, 8)
        
        # Base name row
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Base:"))
        self.base_name_edit = SmartFilenameEdit()
        self.base_name_edit.setText("frame")
        self.base_name_edit.setMaximumWidth(120)
        name_row.addWidget(self.base_name_edit)
        name_row.addStretch()
        layout.addLayout(name_row)
        
        # Pattern row
        pattern_row = QHBoxLayout()
        pattern_row.addWidget(QLabel("Pattern:"))
        self.pattern_edit = PatternEdit()
        self.pattern_edit.setText(Config.Export.DEFAULT_PATTERN)
        self.pattern_edit.setMaximumWidth(150)
        pattern_row.addWidget(self.pattern_edit)
        pattern_row.addStretch()
        layout.addLayout(pattern_row)
        
        # Pattern preview (compact)
        self.pattern_preview = QLabel()
        self.pattern_preview.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
        self.pattern_preview.setWordWrap(True)
        layout.addWidget(self.pattern_preview)
        
        return group
    
    def _create_compact_selection_group(self) -> QGroupBox:
        """Create compact frame selection group for advanced mode."""
        group = QGroupBox("Frame Selection")
        group.setVisible(False)  # Hidden by default
        
        layout = QVBoxLayout(group)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 12, 8, 8)
        
        # Compact frame list with reduced height
        self.frame_list = QListWidget()
        self.frame_list.setSelectionMode(QListWidget.MultiSelection)
        self.frame_list.setMaximumHeight(100)  # Reduced from 120
        self.frame_list.setStyleSheet("""
            QListWidget {
                font-size: 11px;
                alternate-background-color: #f8f8f8;
            }
            QListWidget::item {
                padding: 2px;
                border-bottom: 1px solid #f0f0f0;
            }
        """)
        
        # Populate frame list
        for i in range(self.frame_count):
            item = QListWidgetItem(f"Frame {i + 1}")
            item.setData(Qt.UserRole, i)
            self.frame_list.addItem(item)
            
            # Select current frame by default
            if i == self.current_frame:
                item.setSelected(True)
        
        layout.addWidget(self.frame_list)
        
        # Frame scope selection
        scope_layout = QHBoxLayout()
        scope_layout.setSpacing(12)
        
        scope_label = QLabel("Export:")
        scope_layout.addWidget(scope_label)
        
        # Frame scope radio buttons
        self.frame_scope_group = QButtonGroup()
        
        self.all_frames_radio = QRadioButton("All frames")
        self.all_frames_radio.setChecked(True)
        self.all_frames_radio.toggled.connect(self._on_frame_scope_changed)
        self.frame_scope_group.addButton(self.all_frames_radio, 0)
        scope_layout.addWidget(self.all_frames_radio)
        
        self.selected_frames_radio = QRadioButton("Selected frames only")
        self.selected_frames_radio.toggled.connect(self._on_frame_scope_changed)
        self.frame_scope_group.addButton(self.selected_frames_radio, 1)
        scope_layout.addWidget(self.selected_frames_radio)
        
        scope_layout.addStretch()
        layout.addLayout(scope_layout)
        
        # Compact selection controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)
        
        select_all_btn = QPushButton("All")
        select_all_btn.setFixedSize(50, 24)
        select_all_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                padding: 2px;
            }
        """)
        select_all_btn.clicked.connect(self.frame_list.selectAll)
        controls_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Clear")
        select_none_btn.setFixedSize(50, 24)
        select_none_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                padding: 2px;
            }
        """)
        select_none_btn.clicked.connect(self.frame_list.clearSelection)
        controls_layout.addWidget(select_none_btn)
        
        # Range selection helper
        range_label = QLabel("Tip: Ctrl+click for multiple, Shift+click for range")
        range_label.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
        controls_layout.addWidget(range_label)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        return group
    
    def _create_progress_section(self) -> QWidget:
        """Create progress and status section."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        return section
    
    def _create_action_buttons(self) -> QWidget:
        """Create action buttons with clear hierarchy."""
        section = QWidget()
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Cancel button (secondary)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedHeight(36)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self._export_in_progress = False
        
        layout.addWidget(self.cancel_button)
        layout.addStretch()
        
        # Export button (primary)
        self.export_button = QPushButton("Export Frames")
        self.export_button.setFixedHeight(36)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            QPushButton:disabled {
                background-color: #bbb;
                color: #666;
            }
        """)
        self.export_button.clicked.connect(self._on_export)
        
        layout.addWidget(self.export_button)
        
        return section
    
    def _connect_signals(self):
        """Connect all internal signals."""
        # Preset selection
        self.preset_selector.presetSelected.connect(self._on_preset_selected)
        
        # Handle any preset that was already selected during initialization
        current_preset = self.preset_selector.get_selected_preset()
        if current_preset:
            self._on_preset_selected(current_preset)
        
        # Directory changes
        self.directory_selector.directoryChanged.connect(self._update_preview)
        self.directory_selector.validationChanged.connect(self._on_directory_validation)
        
        # Settings changes
        self.format_combo.currentTextChanged.connect(self._update_preview)
        self.scale_spin.valueChanged.connect(self._update_preview)
        self.base_name_edit.textChanged.connect(self._update_preview)
        self.pattern_edit.textChanged.connect(self._update_preview)
        self.pattern_edit.previewChanged.connect(self._update_pattern_preview)
        
        # Frame selection changes
        self.frame_list.itemSelectionChanged.connect(self._update_preview)
        
        # Animation segment signals
        self.segment_selector.segmentSelectionChanged.connect(self._update_preview)
        
        # Layout configuration signals
        self.layout_mode_combo.currentIndexChanged.connect(self._on_layout_mode_changed)
        self.max_cols_spin.valueChanged.connect(self._update_layout_preview)
        self.max_rows_spin.valueChanged.connect(self._update_layout_preview)
        self.custom_cols_spin.valueChanged.connect(self._update_layout_preview)
        self.custom_rows_spin.valueChanged.connect(self._update_layout_preview)
        self.spacing_spin.valueChanged.connect(self._update_layout_preview)
        self.padding_spin.valueChanged.connect(self._update_layout_preview)
        self.background_combo.currentIndexChanged.connect(self._on_background_mode_changed)
        self.background_color_button.clicked.connect(self._on_background_color_clicked)
        
        # Visual preview signals
        if hasattr(self, 'visual_preview_widget'):
            self.visual_preview_widget.previewUpdated.connect(self._on_visual_preview_updated)
        
        # Exporter signals
        self._exporter.exportStarted.connect(self._on_export_started)
        self._exporter.exportProgress.connect(self._on_export_progress)
        self._exporter.exportFinished.connect(self._on_export_finished)
        self._exporter.exportError.connect(self._on_export_error)
    
    def _initialize_defaults(self):
        """Initialize default values and state."""
        # Set default directory with fallback logic
        default_dir = self._get_default_export_directory()
        self.directory_selector.set_directory(str(default_dir))
        
        # Show recommendation
        if self.frame_count > 0:
            self.recommendation_widget.show_recommendation(self.frame_count)
        
        # Update export button text
        self._update_export_button_text()
        
        # Initialize layout controls visibility
        self._initialize_layout_controls()
        
        # Initial preview update
        self._update_preview()
    
    def _get_default_export_directory(self) -> Path:
        """Get a reliable default export directory with fallback logic."""
        # Try Desktop first (most user-friendly)
        desktop = Path.home() / "Desktop"
        if desktop.exists() and os.access(desktop, os.W_OK):
            return desktop / "sprite_exports"
        
        # Try Documents as fallback
        documents = Path.home() / "Documents"
        if documents.exists() and os.access(documents, os.W_OK):
            return documents / "sprite_exports"
        
        # Try Downloads as second fallback
        downloads = Path.home() / "Downloads"
        if downloads.exists() and os.access(downloads, os.W_OK):
            return downloads / "sprite_exports"
        
        # Try current working directory as final fallback
        cwd = Path.cwd()
        if os.access(cwd, os.W_OK):
            return cwd / "sprite_exports"
        
        # Last resort: home directory
        return Path.home() / "sprite_exports"
    
    def _on_preset_selected(self, preset: ExportPreset):
        """Handle preset selection."""
        self._current_preset = preset
        
        # Update settings from preset
        self.format_combo.setCurrentText(preset.format)
        self.scale_spin.setValue(preset.scale)
        self.pattern_edit.setText(preset.default_pattern)
        
        # Show/hide UI sections based on preset mode
        if preset.mode == "segments":
            self.selection_group.setVisible(False)
            self.segment_selector.setVisible(True)
        elif preset.mode in ["individual"]:
            self.selection_group.setVisible(True)
            self.segment_selector.setVisible(False)
        else:
            self.selection_group.setVisible(False)
            self.segment_selector.setVisible(False)
        
        # Show/hide layout configuration for sprite sheet exports
        if hasattr(self, 'layout_section'):
            is_sheet_export = preset.mode == "sheet"
            self.layout_section.setVisible(is_sheet_export)
            
            # Apply preset layout settings if available
            if is_sheet_export and preset.sprite_sheet_layout:
                self._apply_preset_layout(preset.sprite_sheet_layout)
        
        # Update preview
        self._update_preview()
        self._update_export_button_text()
    
    def _on_frame_scope_changed(self):
        """Handle frame scope selection changes."""
        # Update the frame list selection state
        if hasattr(self, 'all_frames_radio') and self.all_frames_radio.isChecked():
            # Select all frames when "All frames" is chosen
            self.frame_list.selectAll()
        elif hasattr(self, 'selected_frames_radio') and self.selected_frames_radio.isChecked():
            # Clear selection when "Selected frames" is chosen to let user pick
            self.frame_list.clearSelection()
        
        # Update preview and button text
        self._update_preview()
        self._update_export_button_text()
    
    def _on_directory_validation(self, state: str, message: str):
        """Handle directory validation changes."""
        # Enable/disable export button based on validation
        is_valid = state in ["valid", "warning", "neutral"]
        self.export_button.setEnabled(is_valid and self.frame_count > 0)
    
    def _update_preview(self):
        """Update the export preview."""
        if not self._current_preset:
            return
        
        base_name = self.base_name_edit.text() or "frame"
        output_dir = self.directory_selector.get_directory()
        
        # Get frame count based on mode
        if self._current_preset.mode == "selected":
            frame_count = len(self.frame_list.selectedItems())
        elif self._current_preset.mode == "segments":
            # Calculate total frames from selected segments
            frame_count = 0
            if self.segment_selector.has_selected_segments() and self.segment_manager:
                for segment_name in self.segment_selector.get_selected_segments():
                    segment = self.segment_manager.get_segment(segment_name)
                    if segment:
                        segment_frames = getattr(segment, 'frame_count', 
                                              segment.end_frame - segment.start_frame + 1)
                        frame_count += segment_frames
        else:
            frame_count = self.frame_count
        
        # Update preview
        self.preview_widget.update_preview(
            self._current_preset, frame_count, base_name, output_dir
        )
        
        # Update warning widget
        preview_data = self.preview_widget.get_current_preview_data()
        if preview_data:
            self.warning_widget.check_and_show_warnings(preview_data)
    
    def _update_pattern_preview(self, preview_text: str):
        """Update pattern preview label."""
        self.pattern_preview.setText(preview_text)
    
    def _update_export_button_text(self):
        """Update export button text based on current settings."""
        if not self._current_preset:
            self.export_button.setText("Export Frames")
            return
        
        if (self._current_preset.mode == "individual" and 
            hasattr(self, 'selected_frames_radio') and 
            self.selected_frames_radio.isChecked()):
            selected_count = len(self.frame_list.selectedItems())
            if selected_count == 0:
                self.export_button.setText("Select Frames to Export")
                self.export_button.setEnabled(False)
            else:
                self.export_button.setText(f"Export {selected_count} Selected Frames →")
                self.export_button.setEnabled(True)
        elif self._current_preset.mode == "segments":
            selected_segments = self.segment_selector.get_selected_segments()
            if not selected_segments:
                self.export_button.setText("Export Segments")
                self.export_button.setEnabled(False)
            else:
                self.export_button.setText(f"Export {len(selected_segments)} Segments →")
                self.export_button.setEnabled(True)
        else:
            if self.frame_count > 0:
                self.export_button.setText(f"Export {self.frame_count} Frames →")
                self.export_button.setEnabled(True)
            else:
                self.export_button.setText("No Frames to Export")
                self.export_button.setEnabled(False)
    
    def _validate_settings(self) -> Tuple[bool, str]:
        """Validate all export settings."""
        # Check directory
        if not self.directory_selector.is_valid():
            return False, "Please select a valid output directory."
        
        # Check base name
        if not self.base_name_edit.is_valid():
            return False, "Please enter a valid base filename."
        
        # Check pattern
        if not self.pattern_edit.is_valid():
            return False, "Please enter a valid naming pattern."
        
        # Check frame selection for selected frames mode
        if (self._current_preset and self._current_preset.mode == "individual" and 
            hasattr(self, 'selected_frames_radio') and 
            self.selected_frames_radio.isChecked()):
            if not self.frame_list.selectedItems():
                return False, "Please select at least one frame."
        
        # Check segment selection for segments mode
        if self._current_preset and self._current_preset.mode == "segments":
            if not self.segment_selector.has_selected_segments():
                return False, "Please select at least one animation segment."
        
        # Check if directory needs to be created
        directory = self.directory_selector.get_directory()
        if not Path(directory).exists():
            success, message = self.directory_selector.create_directory_if_needed()
            if not success:
                return False, f"Cannot create directory: {message}"
        
        # Check disk space for the export
        preview_data = self.preview_widget.get_current_preview_data()
        if preview_data:
            estimated_size_mb = preview_data.get('total_size_mb', 0)
            if estimated_size_mb > 10:  # Only check for exports > 10MB
                has_space, space_message = self._check_disk_space(directory, estimated_size_mb)
                if not has_space:
                    return False, f"Insufficient disk space: {space_message}"
        
        # Check for existing files that would be overwritten
        if self._current_preset:
            overwrite_risk = self._check_file_overwrite_risk()
            if overwrite_risk:
                # This will be handled in _on_export with user confirmation
                pass
        
        return True, "Settings are valid"
    
    def _check_disk_space(self, directory: str, estimated_size_mb: float) -> Tuple[bool, str]:
        """Check if sufficient disk space is available."""
        try:
            import shutil
            free_space_bytes = shutil.disk_usage(directory).free
            free_space_mb = free_space_bytes / (1024 * 1024)
            required_space_mb = estimated_size_mb * 1.2  # 20% buffer
            
            if free_space_mb >= required_space_mb:
                return True, f"Sufficient space available"
            else:
                return False, f"Need {required_space_mb:.1f} MB, only {free_space_mb:.1f} MB available"
        except Exception as e:
            # If we can't check disk space, don't block the export
            return True, f"Could not check disk space: {str(e)}"
    
    def _check_file_overwrite_risk(self) -> bool:
        """Check if export would overwrite existing files."""
        try:
            directory = self.directory_selector.get_directory()
            base_name = self.base_name_edit.text() or "frame"
            pattern = self.pattern_edit.text()
            
            # Generate a few sample filenames to check
            existing_files = []
            dir_path = Path(directory)
            
            if not dir_path.exists():
                return False  # No risk if directory doesn't exist
            
            # Check based on export mode
            if self._current_preset.mode == "individual":
                # Check first few frame files
                for i in range(min(5, self.frame_count)):
                    filename = pattern.format(name=base_name, index=i, frame=i+1)
                    file_path = dir_path / f"{filename}.{self.format_combo.currentText().lower()}"
                    if file_path.exists():
                        existing_files.append(file_path.name)
            elif self._current_preset.mode == "selected":
                # Check selected frame files
                selected_items = self.frame_list.selectedItems()[:5]  # Check first 5
                for item in selected_items:
                    i = item.data(Qt.UserRole)
                    filename = pattern.format(name=base_name, index=i, frame=i+1)
                    file_path = dir_path / f"{filename}.{self.format_combo.currentText().lower()}"
                    if file_path.exists():
                        existing_files.append(file_path.name)
            elif self._current_preset.mode in ["sheet", "gif"]:
                # Check single output file
                filename = pattern.format(name=base_name, index=0, frame=1)
                file_path = dir_path / f"{filename}.{self.format_combo.currentText().lower()}"
                if file_path.exists():
                    existing_files.append(file_path.name)
            
            return len(existing_files) > 0
            
        except Exception:
            # If we can't check, assume no risk to avoid blocking exports
            return False
    
    def _gather_settings(self) -> Dict[str, Any]:
        """Gather all export settings."""
        if not self._current_preset:
            return {}
        
        settings = {
            'output_dir': self.directory_selector.get_directory(),
            'base_name': self.base_name_edit.text(),
            'format': self.format_combo.currentText(),
            'mode': self._current_preset.mode,
            'scale_factor': self.scale_spin.value(),
            'pattern': self.pattern_edit.text(),
            'preset_name': self._current_preset.name
        }
        
        # Add mode-specific settings
        if self._current_preset.mode == "selected":
            selected_indices = []
            for item in self.frame_list.selectedItems():
                selected_indices.append(item.data(Qt.UserRole))
            settings['selected_indices'] = selected_indices
        elif self._current_preset.mode == "segments":
            # Add segment export settings
            segment_settings = self.segment_selector.get_export_settings()
            settings.update(segment_settings)
        
        # Add sprite sheet layout for sheet exports
        if self._current_preset.mode == "sheet":
            sprite_sheet_layout = self._create_sprite_sheet_layout()
            if sprite_sheet_layout:
                settings['sprite_sheet_layout'] = sprite_sheet_layout
        
        return settings
    
    def _on_export(self):
        """Handle export button click."""
        # Validate settings
        is_valid, error_message = self._validate_settings()
        if not is_valid:
            QMessageBox.warning(self, "Export Error", error_message)
            return
        
        # Gather settings
        settings = self._gather_settings()
        if not settings:
            QMessageBox.warning(self, "Export Error", "No preset selected.")
            return
        
        # Check for file overwrite risk and get user confirmation
        if self._check_file_overwrite_risk():
            reply = QMessageBox.question(
                self, "Overwrite Existing Files?",
                "Some files already exist in the target directory and will be overwritten.\n\n"
                "Do you want to continue and overwrite the existing files?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        # Show confirmation for large exports
        preview_data = self.preview_widget.get_current_preview_data()
        if preview_data and preview_data.get('size_category') in ['large', 'very_large']:
            file_count = preview_data.get('file_count', 0)
            size_mb = preview_data.get('total_size_mb', 0)
            
            reply = QMessageBox.question(
                self, "Large Export Warning",
                f"This export will create {file_count} files totaling ~{size_mb:.1f} MB.\n\n"
                "This may take some time. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        # Emit export request
        self._export_in_progress = True
        self.exportRequested.emit(settings)
    
    def _on_cancel_clicked(self):
        """Handle cancel button click - different behavior during export vs. normal."""
        if self._export_in_progress:
            # During export, try to cancel the operation
            reply = QMessageBox.question(
                self, "Cancel Export?",
                "Are you sure you want to cancel the current export?\n\n"
                "Any files already created will remain in the output directory.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Signal export system to cancel (would need export system support)
                self.status_label.setText("⏹️ Cancelling export...")
                # Note: Actual export cancellation would need support from frame_exporter
                self._export_in_progress = False
                self.reject()
        else:
            # Normal cancel - just close the dialog
            self.reject()
    
    def _on_export_started(self):
        """Handle export start."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.export_button.setEnabled(False)
        self.cancel_button.setText("Cancel Export")
        self.status_label.setText("Starting export...")
    
    def _on_export_progress(self, current: int, total: int, message: str):
        """Handle export progress."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
        
        # Update preview with progress
        self.preview_widget.show_export_progress(current, total, message)
    
    def _on_export_finished(self, success: bool, message: str):
        """Handle export completion."""
        self._export_in_progress = False
        self.progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        self.cancel_button.setText("Close")
        
        # Reset preview
        self.preview_widget.reset_to_preview_mode()
        
        if success:
            self.status_label.setText(f"✅ {message}")
            
            # Show success message with option to open folder
            reply = QMessageBox.information(
                self, "Export Complete", 
                f"{message}\n\nWould you like to open the output folder?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                output_dir = self.directory_selector.get_directory()
                if os.path.exists(output_dir):
                    try:
                        os.startfile(output_dir)  # Windows 11
                    except Exception as e:
                        # Fallback: show error but don't crash
                        print(f"Could not open folder: {e}")
            
            # Auto-close after successful export
            QTimer.singleShot(2000, self.accept)
        else:
            self.status_label.setText(f"❌ {message}")
    
    def _on_export_error(self, error_message: str):
        """Handle export error."""
        self._export_in_progress = False
        self.progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        self.status_label.setText(f"❌ Export failed: {error_message}")
        
        QMessageBox.critical(self, "Export Error", error_message)
    
    def _initialize_layout_controls(self):
        """Initialize layout controls visibility and state."""
        if not hasattr(self, 'layout_mode_combo'):
            return
        
        # Set initial visibility based on default mode (auto)
        self._on_layout_mode_changed(0)
        
        # Set initial background mode visibility (transparent)
        self._on_background_mode_changed(0)
        
        # Update initial layout preview
        self._update_layout_preview()
    
    def _apply_preset_layout(self, layout: SpriteSheetLayout):
        """Apply preset layout settings to UI controls."""
        if not hasattr(self, 'layout_mode_combo'):
            return
        
        try:
            # Set layout mode
            mode_map = ['auto', 'rows', 'columns', 'square', 'custom']
            mode_index = mode_map.index(layout.mode) if layout.mode in mode_map else 0
            self.layout_mode_combo.setCurrentIndex(mode_index)
            
            # Set grid constraints
            if layout.max_columns is not None:
                self.max_cols_spin.setValue(layout.max_columns)
            if layout.max_rows is not None:
                self.max_rows_spin.setValue(layout.max_rows)
            if layout.custom_columns is not None:
                self.custom_cols_spin.setValue(layout.custom_columns)
            if layout.custom_rows is not None:
                self.custom_rows_spin.setValue(layout.custom_rows)
            
            # Set spacing and padding
            self.spacing_spin.setValue(layout.spacing)
            self.padding_spin.setValue(layout.padding)
            
            # Set background mode
            bg_modes = ['transparent', 'solid', 'checkerboard']
            bg_index = bg_modes.index(layout.background_mode) if layout.background_mode in bg_modes else 0
            self.background_combo.setCurrentIndex(bg_index)
            
            # Set background color
            self._current_background_color = layout.background_color
            if layout.background_mode == 'solid':
                r, g, b = layout.background_color[:3]
                self.background_color_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgb({r}, {g}, {b});
                        border: 1px solid #ccc;
                        border-radius: 3px;
                    }}
                """)
            
            # Update visibility and preview
            self._on_layout_mode_changed(mode_index)
            self._on_background_mode_changed(bg_index)
            
        except Exception as e:
            print(f"Error applying preset layout: {e}")
    
    def _on_layout_mode_changed(self, index: int):
        """Handle layout mode change - show/hide appropriate controls."""
        mode_map = ['auto', 'rows', 'columns', 'square', 'custom']
        mode = mode_map[index] if 0 <= index < len(mode_map) else 'auto'
        
        # Show/hide constraints based on mode
        self.max_cols_label.setVisible(mode == 'rows')
        self.max_cols_spin.setVisible(mode == 'rows')
        self.max_rows_label.setVisible(mode == 'columns')
        self.max_rows_spin.setVisible(mode == 'columns')
        self.custom_cols_label.setVisible(mode == 'custom')
        self.custom_cols_spin.setVisible(mode == 'custom')
        self.custom_rows_label.setVisible(mode == 'custom')
        self.custom_rows_spin.setVisible(mode == 'custom')
        
        # Update layout preview
        self._update_layout_preview()
    
    def _on_background_mode_changed(self, index: int):
        """Handle background mode change - show/hide color picker."""
        modes = ['transparent', 'solid', 'checkerboard']
        mode = modes[index] if 0 <= index < len(modes) else 'transparent'
        
        # Show color picker only for solid background
        self.background_color_button.setVisible(mode == 'solid')
        
        # Update layout preview
        self._update_layout_preview()
    
    def _on_background_color_clicked(self):
        """Open color picker for background color selection."""
        current_color = QColor(*self._current_background_color[:3])  # RGB only for QColor
        
        color = QColorDialog.getColor(current_color, self, "Select Background Color")
        
        if color.isValid():
            # Update stored color (with alpha)
            self._current_background_color = (color.red(), color.green(), color.blue(), 255)
            
            # Update button appearance
            self.background_color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgb({color.red()}, {color.green()}, {color.blue()});
                    border: 1px solid #ccc;
                    border-radius: 3px;
                }}
            """)
            
            # Update layout preview
            self._update_layout_preview()
    
    def _update_layout_preview(self):
        """Update the layout preview label and visual preview with current settings."""
        if not self._current_preset or self._current_preset.mode != 'sheet':
            self.layout_preview_label.setText("Layout preview available for sprite sheet exports")
            if hasattr(self, 'visual_preview_widget'):
                self.visual_preview_widget.clear_preview()
            return
        
        try:
            # Get current layout settings
            layout = self._create_sprite_sheet_layout()
            if not layout:
                return
            
            # Calculate estimated dimensions
            frame_width = 32  # Default frame size for preview
            frame_height = 32
            frame_count = max(1, self.frame_count)
            
            estimated_width, estimated_height = layout.calculate_estimated_dimensions(
                frame_width, frame_height, frame_count
            )
            
            # Create preview text
            mode_names = {
                'auto': 'Auto',
                'rows': 'Rows',
                'columns': 'Columns', 
                'square': 'Square',
                'custom': 'Custom'
            }
            
            mode_name = mode_names.get(layout.mode, layout.mode.title())
            spacing_text = f", {layout.spacing}px spacing" if layout.spacing > 0 else ""
            padding_text = f", {layout.padding}px padding" if layout.padding > 0 else ""
            
            preview_text = f"Grid: {mode_name} | Size: ~{estimated_width}×{estimated_height}px{spacing_text}{padding_text}"
            self.layout_preview_label.setText(preview_text)
            
            # Update visual preview
            self._update_visual_preview()
            
        except Exception as e:
            self.layout_preview_label.setText(f"Preview error: {str(e)}")
    
    def _create_sprite_sheet_layout(self) -> Optional[SpriteSheetLayout]:
        """Create SpriteSheetLayout from current UI settings."""
        if not hasattr(self, 'layout_mode_combo'):
            return None
        
        try:
            # Get layout mode
            mode_map = ['auto', 'rows', 'columns', 'square', 'custom']
            mode_index = self.layout_mode_combo.currentIndex()
            mode = mode_map[mode_index] if 0 <= mode_index < len(mode_map) else 'auto'
            
            # Get grid constraints
            max_columns = self.max_cols_spin.value() if mode == 'rows' else None
            max_rows = self.max_rows_spin.value() if mode == 'columns' else None
            custom_columns = self.custom_cols_spin.value() if mode == 'custom' else None
            custom_rows = self.custom_rows_spin.value() if mode == 'custom' else None
            
            # Get spacing and padding
            spacing = self.spacing_spin.value()
            padding = self.padding_spin.value()
            
            # Get background settings
            bg_modes = ['transparent', 'solid', 'checkerboard']
            bg_index = self.background_combo.currentIndex()
            background_mode = bg_modes[bg_index] if 0 <= bg_index < len(bg_modes) else 'transparent'
            
            return SpriteSheetLayout(
                mode=mode,
                spacing=spacing,
                padding=padding,
                max_columns=max_columns,
                max_rows=max_rows,
                custom_columns=custom_columns,
                custom_rows=custom_rows,
                background_mode=background_mode,
                background_color=self._current_background_color
            )
            
        except Exception as e:
            print(f"Error creating sprite sheet layout: {e}")
            return None
    
    def set_sprites(self, sprites: List[QPixmap]):
        """Set the sprites for visual preview."""
        self._current_sprites = sprites
        self._update_visual_preview()
    
    def _update_visual_preview(self):
        """Update the visual preview with current sprites and layout."""
        if not hasattr(self, 'visual_preview_widget'):
            return
        
        if not self._current_preset or self._current_preset.mode != 'sheet':
            self.visual_preview_widget.clear_preview()
            return
        
        if not self._current_sprites:
            self.visual_preview_widget.clear_preview()
            return
        
        layout = self._create_sprite_sheet_layout()
        if layout:
            self.visual_preview_widget.update_preview(self._current_sprites, layout)
    
    def _on_visual_preview_updated(self):
        """Handle visual preview updates."""
        # Could add additional logic here if needed
        pass


# Keep backward compatibility
class LegacyExportDialog:
    """Legacy export dialog - preserved for fallback."""
    pass  # Implementation would be in export_dialog_legacy.py