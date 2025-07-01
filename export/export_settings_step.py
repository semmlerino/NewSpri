"""
Export Settings Step
Second step of the export wizard - contextual settings based on export type.
Part of Export Dialog Usability Improvements.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox,
    QGroupBox, QFrame, QRadioButton, QButtonGroup, QListWidget,
    QListWidgetItem, QFormLayout, QSizePolicy, QColorDialog,
    QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap, QPainter, QBrush

from .wizard_widget import WizardStep
from .export_presets import ExportPreset
from ui.validation_widgets import SmartDirectorySelector, SmartFilenameEdit, PatternEdit
from config import Config


class ExportSettingsStep(WizardStep):
    """
    Second step of export wizard - contextual settings.
    Shows only relevant options based on selected export type.
    """
    
    def __init__(self, frame_count: int = 0, current_frame: int = 0, parent=None):
        super().__init__(
            title="Configure Export Settings",
            subtitle="",  # Will be updated based on export type
            parent=parent
        )
        self.frame_count = frame_count
        self.current_frame = current_frame
        self._current_preset: Optional[ExportPreset] = None
        self._settings_widgets = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the base UI structure."""
        # Main layout with consistent padding
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 24, 32, 24)
        self.main_layout.setSpacing(20)
        
        # Container for dynamic content
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)
        
        self.main_layout.addWidget(self.content_container, 1)
    
    def on_entering(self):
        """Called when entering this step - update based on preset."""
        # Get preset from wizard data
        # Need to get the wizard widget, not just parent (which is QStackedWidget)
        wizard = self.parent()
        while wizard and not hasattr(wizard, 'get_wizard_data'):
            wizard = wizard.parent()
        
        if wizard:
            wizard_data = wizard.get_wizard_data()
            preset = wizard_data.get('step_0', {}).get('preset')
            if preset:
                self._setup_for_preset(preset)
    
    def _setup_for_preset(self, preset: ExportPreset):
        """Set up UI based on selected preset."""
        self._current_preset = preset
        
        # Update subtitle
        self.subtitle = f"Configure settings for {preset.display_name.lower()} export"
        # Find the wizard widget to update subtitle
        wizard = self.parent()
        while wizard and not hasattr(wizard, 'step_subtitle_label'):
            wizard = wizard.parent()
        if wizard:
            wizard.step_subtitle_label.setText(self.subtitle)
        
        # Clear existing content
        self._clear_content()
        
        # Build appropriate UI based on export mode
        if preset.mode == "individual":
            self._build_individual_frames_ui()
        elif preset.mode == "sheet":
            self._build_sprite_sheet_ui()
        elif preset.mode == "selected":
            self._build_selected_frames_ui()
        else:
            self._build_generic_ui()
        
        # Validate after building
        self._validate_settings()
    
    def _clear_content(self):
        """Clear all content from the container."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._settings_widgets.clear()
    
    def _build_individual_frames_ui(self):
        """Build UI for individual frames export."""
        # Output location section
        location_group = self._create_output_location_section()
        self.content_layout.addWidget(location_group)
        
        # File naming section
        naming_group = self._create_file_naming_section()
        self.content_layout.addWidget(naming_group)
        
        # Format and quality section
        format_group = self._create_format_quality_section()
        self.content_layout.addWidget(format_group)
        
        # Frame selection option
        selection_group = self._create_frame_selection_section()
        self.content_layout.addWidget(selection_group)
        
        self.content_layout.addStretch()
    
    def _build_sprite_sheet_ui(self):
        """Build UI for sprite sheet export."""
        # Output location section
        location_group = self._create_output_location_section(single_file=True)
        self.content_layout.addWidget(location_group)
        
        # Layout configuration section
        layout_group = self._create_sprite_layout_section()
        self.content_layout.addWidget(layout_group)
        
        # Spacing and background section
        style_group = self._create_sprite_style_section()
        self.content_layout.addWidget(style_group)
        
        # Format section (simplified)
        format_group = self._create_format_section_simple()
        self.content_layout.addWidget(format_group)
        
        self.content_layout.addStretch()
    
    def _build_selected_frames_ui(self):
        """Build UI for selected frames export."""
        # Frame selection section (primary)
        selection_group = self._create_enhanced_frame_selection_section()
        self.content_layout.addWidget(selection_group)
        
        # Output location section
        location_group = self._create_output_location_section()
        self.content_layout.addWidget(location_group)
        
        # File naming section
        naming_group = self._create_file_naming_section()
        self.content_layout.addWidget(naming_group)
        
        # Format and quality section
        format_group = self._create_format_quality_section()
        self.content_layout.addWidget(format_group)
        
        self.content_layout.addStretch()
    
    def _build_generic_ui(self):
        """Build generic UI as fallback."""
        # Basic settings
        location_group = self._create_output_location_section()
        self.content_layout.addWidget(location_group)
        
        format_group = self._create_format_quality_section()
        self.content_layout.addWidget(format_group)
        
        self.content_layout.addStretch()
    
    def _create_output_location_section(self, single_file: bool = False) -> QGroupBox:
        """Create output location section."""
        group = QGroupBox("📁 Output Location")
        group.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Directory selector
        self.directory_selector = SmartDirectorySelector()
        self.directory_selector.directoryChanged.connect(self._on_setting_changed)
        self.directory_selector.validationChanged.connect(self._on_validation_changed)
        layout.addWidget(self.directory_selector)
        
        # Set default directory
        default_dir = self._get_default_export_directory()
        self.directory_selector.set_directory(str(default_dir))
        
        # Single file name for sprite sheets/GIFs
        if single_file:
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("Filename:"))
            
            self.single_filename_edit = SmartFilenameEdit()
            self.single_filename_edit.setText("spritesheet" if "sheet" in self._current_preset.mode else "animation")
            self.single_filename_edit.textChanged.connect(self._on_setting_changed)
            name_layout.addWidget(self.single_filename_edit)
            
            layout.addLayout(name_layout)
            self._settings_widgets['single_filename'] = self.single_filename_edit
        
        self._settings_widgets['directory'] = self.directory_selector
        
        return group
    
    def _create_file_naming_section(self) -> QGroupBox:
        """Create file naming section for multiple files."""
        group = QGroupBox("📝 File Naming")
        group.setStyleSheet(self._get_group_style())
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # Base name
        self.base_name_edit = SmartFilenameEdit()
        self.base_name_edit.setText("frame")
        self.base_name_edit.setPlaceholderText("e.g., sprite, frame, character")
        self.base_name_edit.textChanged.connect(self._on_setting_changed)
        layout.addRow("Base name:", self.base_name_edit)
        
        # Pattern selection
        pattern_layout = QVBoxLayout()
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems([
            "Auto numbering (frame_001, frame_002...)",
            "Simple index (frame_0, frame_1...)",
            "Custom pattern..."
        ])
        self.pattern_combo.currentIndexChanged.connect(self._on_pattern_changed)
        pattern_layout.addWidget(self.pattern_combo)
        
        # Custom pattern input (hidden by default)
        self.pattern_edit = PatternEdit()
        self.pattern_edit.setText(Config.Export.DEFAULT_PATTERN)
        self.pattern_edit.setVisible(False)
        self.pattern_edit.textChanged.connect(self._on_setting_changed)
        pattern_layout.addWidget(self.pattern_edit)
        
        # Pattern preview
        self.pattern_preview = QLabel()
        self.pattern_preview.setStyleSheet("color: #6c757d; font-size: 11px; font-style: italic;")
        pattern_layout.addWidget(self.pattern_preview)
        
        layout.addRow("Pattern:", pattern_layout)
        
        self._settings_widgets['base_name'] = self.base_name_edit
        self._settings_widgets['pattern_combo'] = self.pattern_combo
        self._settings_widgets['pattern'] = self.pattern_edit
        
        # Update preview
        self._update_pattern_preview()
        
        return group
    
    def _create_format_quality_section(self) -> QGroupBox:
        """Create format and quality section."""
        group = QGroupBox("🖼️ Format & Quality")
        group.setStyleSheet(self._get_group_style())
        layout = QGridLayout(group)
        layout.setSpacing(12)
        
        # Format selection
        layout.addWidget(QLabel("Format:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(Config.Export.IMAGE_FORMATS)
        self.format_combo.setCurrentText(self._current_preset.format)
        self.format_combo.currentTextChanged.connect(self._on_setting_changed)
        layout.addWidget(self.format_combo, 0, 1)
        
        # Scale factor
        layout.addWidget(QLabel("Scale:"), 0, 2)
        scale_layout = QHBoxLayout()
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 10.0)
        self.scale_spin.setSingleStep(0.5)
        self.scale_spin.setValue(self._current_preset.scale)
        self.scale_spin.setSuffix("x")
        self.scale_spin.setDecimals(1)
        self.scale_spin.valueChanged.connect(self._on_setting_changed)
        scale_layout.addWidget(self.scale_spin)
        
        # Quick scale buttons
        for scale in [0.5, 1.0, 2.0, 4.0]:
            btn = QPushButton(f"{scale}x")
            btn.setFixedSize(40, 28)
            btn.setStyleSheet(self._get_quick_button_style())
            btn.clicked.connect(lambda checked, s=scale: self.scale_spin.setValue(s))
            scale_layout.addWidget(btn)
        
        layout.addLayout(scale_layout, 0, 3, 1, 2)
        
        # Quality slider for JPEG
        self.quality_label = QLabel("Quality:")
        self.quality_slider = QSpinBox()
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(95)
        self.quality_slider.setSuffix("%")
        self.quality_slider.valueChanged.connect(self._on_setting_changed)
        
        layout.addWidget(self.quality_label, 1, 0)
        layout.addWidget(self.quality_slider, 1, 1)
        
        # Show/hide quality based on format
        self._update_quality_visibility()
        
        self._settings_widgets['format'] = self.format_combo
        self._settings_widgets['scale'] = self.scale_spin
        self._settings_widgets['quality'] = self.quality_slider
        
        return group
    
    def _create_frame_selection_section(self) -> QGroupBox:
        """Create frame selection section for individual frames."""
        group = QGroupBox("🎯 Frame Selection")
        group.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Radio buttons for all/current
        self.frame_scope_group = QButtonGroup()
        
        self.all_frames_radio = QRadioButton(f"Export all frames ({self.frame_count} total)")
        self.all_frames_radio.setChecked(True)
        self.frame_scope_group.addButton(self.all_frames_radio, 0)
        layout.addWidget(self.all_frames_radio)
        
        self.current_frame_radio = QRadioButton(f"Export current frame only (Frame {self.current_frame + 1})")
        self.frame_scope_group.addButton(self.current_frame_radio, 1)
        layout.addWidget(self.current_frame_radio)
        
        self.custom_selection_radio = QRadioButton("Select specific frames...")
        self.frame_scope_group.addButton(self.custom_selection_radio, 2)
        layout.addWidget(self.custom_selection_radio)
        
        self.frame_scope_group.buttonClicked.connect(self._on_setting_changed)
        
        self._settings_widgets['frame_scope'] = self.frame_scope_group
        
        return group
    
    def _create_enhanced_frame_selection_section(self) -> QGroupBox:
        """Create enhanced frame selection for selected frames export."""
        group = QGroupBox("🎯 Select Frames to Export")
        group.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Instructions
        instructions = QLabel("Select the frames you want to export. Use Ctrl+click for multiple selections and Shift+click for ranges.")
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #6c757d; font-size: 12px;")
        layout.addWidget(instructions)
        
        # Frame list with preview
        list_container = QHBoxLayout()
        
        # Frame list
        self.frame_list = QListWidget()
        self.frame_list.setSelectionMode(QListWidget.MultiSelection)
        self.frame_list.setMaximumHeight(200)
        self.frame_list.setStyleSheet("""
            QListWidget {
                font-size: 12px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
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
        
        self.frame_list.itemSelectionChanged.connect(self._on_frame_selection_changed)
        list_container.addWidget(self.frame_list, 2)
        
        # Selection info panel
        info_panel = QFrame()
        info_panel.setFrameStyle(QFrame.Box)
        info_panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        info_layout = QVBoxLayout(info_panel)
        
        self.selection_info_label = QLabel("1 frame selected")
        self.selection_info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self.selection_info_label)
        
        # Quick selection buttons
        quick_select_layout = QVBoxLayout()
        quick_select_layout.setSpacing(8)
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.frame_list.selectAll)
        quick_select_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Clear Selection")
        select_none_btn.clicked.connect(self.frame_list.clearSelection)
        quick_select_layout.addWidget(select_none_btn)
        
        select_range_btn = QPushButton("Select Range...")
        select_range_btn.clicked.connect(self._show_range_selection)
        quick_select_layout.addWidget(select_range_btn)
        
        info_layout.addLayout(quick_select_layout)
        info_layout.addStretch()
        
        list_container.addWidget(info_panel, 1)
        layout.addLayout(list_container)
        
        self._settings_widgets['frame_list'] = self.frame_list
        
        return group
    
    def _create_sprite_layout_section(self) -> QGroupBox:
        """Create sprite sheet layout configuration."""
        group = QGroupBox("📐 Sheet Layout")
        group.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Layout mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Arrangement:"))
        
        self.layout_mode_combo = QComboBox()
        self.layout_mode_combo.addItems([
            "Automatic (recommended)",
            "Fixed columns",
            "Fixed rows",
            "Square grid",
            "Custom grid"
        ])
        self.layout_mode_combo.currentIndexChanged.connect(self._on_layout_mode_changed)
        mode_layout.addWidget(self.layout_mode_combo, 1)
        layout.addLayout(mode_layout)
        
        # Constraint inputs (hidden by default)
        self.constraint_container = QWidget()
        constraint_layout = QHBoxLayout(self.constraint_container)
        constraint_layout.setContentsMargins(20, 0, 0, 0)
        
        # Columns constraint
        self.columns_label = QLabel("Columns:")
        self.columns_spin = QSpinBox()
        self.columns_spin.setRange(1, 50)
        self.columns_spin.setValue(8)
        self.columns_spin.valueChanged.connect(self._on_setting_changed)
        constraint_layout.addWidget(self.columns_label)
        constraint_layout.addWidget(self.columns_spin)
        
        # Rows constraint
        self.rows_label = QLabel("Rows:")
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 50)
        self.rows_spin.setValue(8)
        self.rows_spin.valueChanged.connect(self._on_setting_changed)
        constraint_layout.addWidget(self.rows_label)
        constraint_layout.addWidget(self.rows_spin)
        
        constraint_layout.addStretch()
        self.constraint_container.setVisible(False)
        layout.addWidget(self.constraint_container)
        
        self._settings_widgets['layout_mode'] = self.layout_mode_combo
        self._settings_widgets['columns'] = self.columns_spin
        self._settings_widgets['rows'] = self.rows_spin
        
        return group
    
    def _create_sprite_style_section(self) -> QGroupBox:
        """Create sprite sheet style settings."""
        group = QGroupBox("🎨 Style & Spacing")
        group.setStyleSheet(self._get_group_style())
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # Sprite spacing
        spacing_layout = QHBoxLayout()
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 32)
        self.spacing_spin.setValue(0)
        self.spacing_spin.setSuffix(" px")
        self.spacing_spin.valueChanged.connect(self._on_setting_changed)
        spacing_layout.addWidget(self.spacing_spin)
        spacing_layout.addWidget(QLabel("between sprites"))
        spacing_layout.addStretch()
        layout.addRow("Spacing:", spacing_layout)
        
        # Sheet padding
        padding_layout = QHBoxLayout()
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 32)
        self.padding_spin.setValue(0)
        self.padding_spin.setSuffix(" px")
        self.padding_spin.valueChanged.connect(self._on_setting_changed)
        padding_layout.addWidget(self.padding_spin)
        padding_layout.addWidget(QLabel("around edges"))
        padding_layout.addStretch()
        layout.addRow("Padding:", padding_layout)
        
        # Background
        bg_layout = QHBoxLayout()
        self.background_combo = QComboBox()
        self.background_combo.addItems(["Transparent", "Solid color", "Checkerboard"])
        self.background_combo.currentIndexChanged.connect(self._on_background_changed)
        bg_layout.addWidget(self.background_combo)
        
        # Color picker button
        self.color_button = QPushButton()
        self.color_button.setFixedSize(60, 26)
        self.color_button.setVisible(False)
        self.color_button.clicked.connect(self._pick_background_color)
        self._current_bg_color = QColor(255, 255, 255)
        self._update_color_button()
        bg_layout.addWidget(self.color_button)
        
        bg_layout.addStretch()
        layout.addRow("Background:", bg_layout)
        
        self._settings_widgets['spacing'] = self.spacing_spin
        self._settings_widgets['padding'] = self.padding_spin
        self._settings_widgets['background'] = self.background_combo
        self._settings_widgets['bg_color'] = self._current_bg_color
        
        return group
    
    def _create_animation_settings_section(self) -> QGroupBox:
        """Create animation settings for GIF export."""
        group = QGroupBox("🎬 Animation Settings")
        group.setStyleSheet(self._get_group_style())
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # Frame rate
        fps_layout = QHBoxLayout()
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(12)
        self.fps_spin.setSuffix(" FPS")
        self.fps_spin.valueChanged.connect(self._on_setting_changed)
        fps_layout.addWidget(self.fps_spin)
        
        # Quick FPS buttons
        for fps in [8, 12, 24, 30]:
            btn = QPushButton(f"{fps}")
            btn.setFixedSize(32, 26)
            btn.setStyleSheet(self._get_quick_button_style())
            btn.clicked.connect(lambda checked, f=fps: self.fps_spin.setValue(f))
            fps_layout.addWidget(btn)
        
        fps_layout.addStretch()
        layout.addRow("Frame rate:", fps_layout)
        
        # Loop settings
        self.loop_checkbox = QCheckBox("Loop animation")
        self.loop_checkbox.setChecked(True)
        self.loop_checkbox.stateChanged.connect(self._on_setting_changed)
        layout.addRow("", self.loop_checkbox)
        
        # Duration info
        duration = self.frame_count / self.fps_spin.value()
        self.duration_label = QLabel(f"Duration: {duration:.1f} seconds")
        self.duration_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addRow("", self.duration_label)
        
        self._settings_widgets['fps'] = self.fps_spin
        self._settings_widgets['loop'] = self.loop_checkbox
        
        return group
    
    def _create_format_section_simple(self) -> QGroupBox:
        """Create simplified format section for sprite sheets."""
        group = QGroupBox("💾 Output Format")
        group.setStyleSheet(self._get_group_style())
        layout = QHBoxLayout(group)
        layout.setSpacing(12)
        
        layout.addWidget(QLabel("Format:"))
        self.sheet_format_combo = QComboBox()
        self.sheet_format_combo.addItems(["PNG", "JPG"])  # Limited options for sheets
        self.sheet_format_combo.setCurrentText("PNG")
        self.sheet_format_combo.currentTextChanged.connect(self._on_setting_changed)
        layout.addWidget(self.sheet_format_combo)
        
        layout.addStretch()
        
        self._settings_widgets['sheet_format'] = self.sheet_format_combo
        
        return group
    
    # Event handlers
    def _on_setting_changed(self):
        """Handle any setting change."""
        self._validate_settings()
        self.dataChanged.emit(self.get_data())
    
    def _on_validation_changed(self, state: str, message: str):
        """Handle validation state changes."""
        self._validate_settings()
    
    def _on_pattern_changed(self, index: int):
        """Handle pattern selection change."""
        # Show/hide custom pattern input
        self.pattern_edit.setVisible(index == 2)  # "Custom pattern..."
        self._update_pattern_preview()
        self._on_setting_changed()
    
    def _on_layout_mode_changed(self, index: int):
        """Handle layout mode change."""
        modes = ['auto', 'columns', 'rows', 'square', 'custom']
        mode = modes[index] if 0 <= index < len(modes) else 'auto'
        
        # Show/hide constraints
        self.constraint_container.setVisible(mode in ['columns', 'rows', 'custom'])
        self.columns_label.setVisible(mode in ['columns', 'custom'])
        self.columns_spin.setVisible(mode in ['columns', 'custom'])
        self.rows_label.setVisible(mode in ['rows', 'custom'])
        self.rows_spin.setVisible(mode in ['rows', 'custom'])
        
        self._on_setting_changed()
    
    def _on_background_changed(self, index: int):
        """Handle background mode change."""
        self.color_button.setVisible(index == 1)  # "Solid color"
        self._on_setting_changed()
    
    def _on_frame_selection_changed(self):
        """Handle frame selection changes."""
        selected_count = len(self.frame_list.selectedItems())
        if selected_count == 0:
            self.selection_info_label.setText("No frames selected")
        elif selected_count == 1:
            self.selection_info_label.setText("1 frame selected")
        else:
            self.selection_info_label.setText(f"{selected_count} frames selected")
        
        self._on_setting_changed()
    
    def _update_pattern_preview(self):
        """Update the pattern preview label."""
        base_name = self.base_name_edit.text() or "frame"
        
        if self.pattern_combo.currentIndex() == 0:  # Auto numbering
            preview = f"Example: {base_name}_001.png, {base_name}_002.png, ..."
        elif self.pattern_combo.currentIndex() == 1:  # Simple index
            preview = f"Example: {base_name}_0.png, {base_name}_1.png, ..."
        else:  # Custom
            pattern = self.pattern_edit.text()
            try:
                example1 = pattern.format(name=base_name, index=0, frame=1)
                example2 = pattern.format(name=base_name, index=1, frame=2)
                preview = f"Example: {example1}.png, {example2}.png, ..."
            except:
                preview = "Invalid pattern"
        
        self.pattern_preview.setText(preview)
    
    def _update_quality_visibility(self):
        """Show/hide quality slider based on format."""
        if hasattr(self, 'format_combo') and hasattr(self, 'quality_label'):
            is_jpeg = self.format_combo.currentText() in ["JPG", "JPEG"]
            self.quality_label.setVisible(is_jpeg)
            self.quality_slider.setVisible(is_jpeg)
    
    def _pick_background_color(self):
        """Open color picker for background."""
        color = QColorDialog.getColor(self._current_bg_color, self, "Select Background Color")
        if color.isValid():
            self._current_bg_color = color
            self._update_color_button()
            self._settings_widgets['bg_color'] = color
            self._on_setting_changed()
    
    def _update_color_button(self):
        """Update color button appearance."""
        pixmap = QPixmap(50, 20)
        pixmap.fill(self._current_bg_color)
        painter = QPainter(pixmap)
        painter.setPen(Qt.black)
        painter.drawRect(0, 0, 49, 19)
        painter.end()
        
        self.color_button.setIcon(pixmap)
    
    def _show_range_selection(self):
        """Show range selection dialog (placeholder)."""
        # TODO: Implement range selection dialog
        pass
    
    def _validate_settings(self):
        """Validate current settings."""
        is_valid = True
        
        # Check directory
        if hasattr(self, 'directory_selector'):
            is_valid &= self.directory_selector.is_valid()
        
        # Check filenames
        if hasattr(self, 'base_name_edit'):
            is_valid &= self.base_name_edit.is_valid()
        if hasattr(self, 'single_filename_edit'):
            is_valid &= self.single_filename_edit.is_valid()
        
        # Check frame selection for selected frames mode
        if self._current_preset and self._current_preset.mode == "selected":
            if hasattr(self, 'frame_list'):
                is_valid &= len(self.frame_list.selectedItems()) > 0
        
        self.stepValidated.emit(is_valid)
        return is_valid
    
    def validate(self) -> bool:
        """Validate the step."""
        return self._validate_settings()
    
    def get_data(self) -> Dict[str, Any]:
        """Get all settings data."""
        data = {
            'output_dir': '',
            'format': self._current_preset.format if self._current_preset else 'PNG',
            'scale': 1.0
        }
        
        # Collect data from widgets
        if 'directory' in self._settings_widgets:
            data['output_dir'] = self._settings_widgets['directory'].get_directory()
        
        if 'base_name' in self._settings_widgets:
            data['base_name'] = self._settings_widgets['base_name'].text()
        
        if 'single_filename' in self._settings_widgets:
            data['single_filename'] = self._settings_widgets['single_filename'].text()
        
        if 'format' in self._settings_widgets:
            data['format'] = self._settings_widgets['format'].currentText()
        elif 'sheet_format' in self._settings_widgets:
            data['format'] = self._settings_widgets['sheet_format'].currentText()
        
        if 'scale' in self._settings_widgets:
            data['scale'] = self._settings_widgets['scale'].value()
        
        if 'pattern_combo' in self._settings_widgets:
            if self._settings_widgets['pattern_combo'].currentIndex() == 0:
                data['pattern'] = "{name}_{index:03d}"
            elif self._settings_widgets['pattern_combo'].currentIndex() == 1:
                data['pattern'] = "{name}_{index}"
            else:
                data['pattern'] = self._settings_widgets['pattern'].text()
        
        if 'frame_list' in self._settings_widgets:
            selected_indices = []
            for item in self._settings_widgets['frame_list'].selectedItems():
                selected_indices.append(item.data(Qt.UserRole))
            data['selected_indices'] = selected_indices
        
        if 'frame_scope' in self._settings_widgets:
            scope_id = self._settings_widgets['frame_scope'].checkedId()
            if scope_id == 1:  # Current frame only
                data['selected_indices'] = [self.current_frame]
            elif scope_id == 2:  # Custom selection
                # Would open selection dialog
                pass
        
        # Sprite sheet specific
        if 'layout_mode' in self._settings_widgets:
            modes = ['auto', 'columns', 'rows', 'square', 'custom']
            mode_index = self._settings_widgets['layout_mode'].currentIndex()
            data['layout_mode'] = modes[mode_index] if 0 <= mode_index < len(modes) else 'auto'
            
            if data['layout_mode'] in ['columns', 'custom']:
                data['columns'] = self._settings_widgets['columns'].value()
            if data['layout_mode'] in ['rows', 'custom']:
                data['rows'] = self._settings_widgets['rows'].value()
        
        if 'spacing' in self._settings_widgets:
            data['spacing'] = self._settings_widgets['spacing'].value()
        if 'padding' in self._settings_widgets:
            data['padding'] = self._settings_widgets['padding'].value()
        if 'background' in self._settings_widgets:
            bg_modes = ['transparent', 'solid', 'checkerboard']
            bg_index = self._settings_widgets['background'].currentIndex()
            data['background_mode'] = bg_modes[bg_index]
            if data['background_mode'] == 'solid' and 'bg_color' in self._settings_widgets:
                color = self._settings_widgets['bg_color']
                if isinstance(color, QColor):
                    data['background_color'] = (color.red(), color.green(), color.blue(), 255)
        
        # Animation specific
        if 'fps' in self._settings_widgets:
            data['fps'] = self._settings_widgets['fps'].value()
        if 'loop' in self._settings_widgets:
            data['loop'] = self._settings_widgets['loop'].isChecked()
        if 'optimize' in self._settings_widgets:
            data['optimize'] = self._settings_widgets['optimize'].isChecked()
        
        return data
    
    def _get_default_export_directory(self):
        """Get default export directory."""
        from pathlib import Path
        import os
        
        # Try Desktop first
        desktop = Path.home() / "Desktop"
        if desktop.exists() and os.access(desktop, os.W_OK):
            return desktop / "sprite_exports"
        
        # Fallback to Documents
        documents = Path.home() / "Documents"
        if documents.exists() and os.access(documents, os.W_OK):
            return documents / "sprite_exports"
        
        # Last resort: current directory
        return Path.cwd() / "sprite_exports"
    
    def _get_group_style(self) -> str:
        """Get consistent group box styling."""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #ffffff;
                color: #212529;
            }
        """
    
    def _get_quick_button_style(self) -> str:
        """Get quick button styling."""
        return """
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """