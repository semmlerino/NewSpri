"""
Export Settings Step (Simplified)
Clean, user-friendly export settings with visual organization.
"""

from typing import Optional, Dict, Any, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox,
    QFrame, QButtonGroup, QListWidget, QListWidgetItem,
    QSizePolicy, QFileDialog, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QPixmap, QPainter, QBrush, QIcon

from .wizard_widget import WizardStep
from .export_presets import ExportPreset
from config import Config


class SettingsCard(QFrame):
    """Visual card for grouping related settings."""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            SettingsCard {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 16px;
            }
            SettingsCard:hover {
                border-color: #dee2e6;
                background-color: #ffffff;
            }
        """)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)
        
        # Title
        title_label = QLabel(f"{icon} {title}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        self.layout.addWidget(title_label)
        
        # Content area
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        self.layout.addLayout(self.content_layout)
    
    def add_row(self, label: str, widget: QWidget, help_text: str = ""):
        """Add a labeled row to the card."""
        # Create container widget for the row
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(100)
        row_layout.addWidget(label_widget)
        
        # Widget
        row_layout.addWidget(widget, 1)
        
        self.content_layout.addWidget(row_widget)
        
        # Help text
        if help_text:
            help_label = QLabel(help_text)
            help_label.setWordWrap(True)
            help_label.setStyleSheet("color: #6c757d; font-size: 11px; margin-left: 112px;")
            self.content_layout.addWidget(help_label)
        
        # Return the row widget for visibility control
        return row_widget


class SimpleDirectorySelector(QWidget):
    """Simplified directory selector with inline validation."""
    
    directoryChanged = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Path display
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px 12px;
            }
        """)
        layout.addWidget(self.path_edit, 1)
        
        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse)
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
        """)
        layout.addWidget(self.browse_button)
        
        # Status icon
        self.status_label = QLabel()
        self.status_label.setFixedSize(20, 20)
        layout.addWidget(self.status_label)
    
    def _browse(self):
        """Open directory browser."""
        current_dir = self.path_edit.text() or str(Config.File.get_default_export_directory())
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            current_dir,
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.set_directory(directory)
    
    def set_directory(self, path: str):
        """Set the directory path."""
        self.path_edit.setText(path)
        self._update_status()
        self.directoryChanged.emit(path)
    
    def get_directory(self) -> str:
        """Get the current directory."""
        return self.path_edit.text()
    
    def _update_status(self):
        """Update status icon."""
        path = self.path_edit.text()
        if not path:
            self.status_label.setText("⚠️")
            self.status_label.setToolTip("Please select a directory")
        else:
            from pathlib import Path
            if Path(path).exists() or Path(path).parent.exists():
                self.status_label.setText("✅")
                self.status_label.setToolTip("Valid directory")
            else:
                self.status_label.setText("❌")
                self.status_label.setToolTip("Directory does not exist")
    
    def is_valid(self) -> bool:
        """Check if directory is valid."""
        path = self.path_edit.text()
        if not path:
            return False
        from pathlib import Path
        return Path(path).exists() or Path(path).parent.exists()


class QuickScaleButtons(QWidget):
    """Quick scale selection buttons."""
    
    scaleChanged = Signal(float)
    
    def __init__(self, scales: List[float] = None, parent=None):
        super().__init__(parent)
        self.scales = scales or [0.5, 1.0, 2.0, 4.0]
        self._current_scale = 1.0
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        self.button_group = QButtonGroup()
        
        for scale in self.scales:
            btn = QPushButton(f"{scale}x")
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setMinimumWidth(48)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
                QPushButton:checked {
                    background-color: #007bff;
                    color: white;
                    border-color: #0056b3;
                }
            """)
            btn.clicked.connect(lambda checked, s=scale: self._on_scale_clicked(s))
            self.button_group.addButton(btn)
            layout.addWidget(btn)
            
            if scale == 1.0:
                btn.setChecked(True)
        
        layout.addStretch()
    
    def _on_scale_clicked(self, scale: float):
        self._current_scale = scale
        self.scaleChanged.emit(scale)
    
    def get_scale(self) -> float:
        return self._current_scale
    
    def set_scale(self, scale: float):
        self._current_scale = scale
        for btn in self.button_group.buttons():
            if btn.text() == f"{scale}x":
                btn.setChecked(True)
                break


class GridLayoutSelector(QWidget):
    """Visual grid layout selector."""
    
    layoutChanged = Signal(str, int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "auto"
        self._columns = 8
        self._rows = 8
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Mode buttons
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        
        self.mode_group = QButtonGroup()
        modes = [
            ("Auto", "auto", "Automatically arrange sprites"),
            ("Columns", "columns", "Fixed number of columns"),
            ("Rows", "rows", "Fixed number of rows"),
            ("Square", "square", "Force square grid")
        ]
        
        for i, (label, mode, tooltip) in enumerate(modes):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setMinimumHeight(36)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #f8f9fa;
                    border-color: #007bff;
                }
                QPushButton:checked {
                    background-color: #007bff;
                    color: white;
                    border-color: #0056b3;
                }
            """)
            btn.clicked.connect(lambda checked, m=mode: self._on_mode_changed(m))
            self.mode_group.addButton(btn, i)
            mode_layout.addWidget(btn)
            
            if i == 0:  # Auto
                btn.setChecked(True)
        
        layout.addLayout(mode_layout)
        
        # Constraint controls
        self.constraint_widget = QWidget()
        constraint_layout = QHBoxLayout(self.constraint_widget)
        constraint_layout.setContentsMargins(0, 0, 0, 0)
        constraint_layout.setSpacing(12)
        
        # Columns control
        self.columns_widget = QWidget()
        columns_layout = QHBoxLayout(self.columns_widget)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.addWidget(QLabel("Columns:"))
        self.columns_spin = QSpinBox()
        self.columns_spin.setRange(1, 32)
        self.columns_spin.setValue(8)
        self.columns_spin.valueChanged.connect(self._on_value_changed)
        columns_layout.addWidget(self.columns_spin)
        constraint_layout.addWidget(self.columns_widget)
        
        # Rows control
        self.rows_widget = QWidget()
        rows_layout = QHBoxLayout(self.rows_widget)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.addWidget(QLabel("Rows:"))
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 32)
        self.rows_spin.setValue(8)
        self.rows_spin.valueChanged.connect(self._on_value_changed)
        rows_layout.addWidget(self.rows_spin)
        constraint_layout.addWidget(self.rows_widget)
        
        constraint_layout.addStretch()
        
        # Hide by default
        self.constraint_widget.setVisible(False)
        layout.addWidget(self.constraint_widget)
    
    def _on_mode_changed(self, mode: str):
        self._mode = mode
        
        # Show/hide constraints
        self.constraint_widget.setVisible(mode in ["columns", "rows"])
        self.columns_widget.setVisible(mode == "columns")
        self.rows_widget.setVisible(mode == "rows")
        
        self._on_value_changed()
    
    def _on_value_changed(self):
        self._columns = self.columns_spin.value()
        self._rows = self.rows_spin.value()
        self.layoutChanged.emit(self._mode, self._columns, self._rows)
    
    def get_layout(self) -> Tuple[str, int, int]:
        return self._mode, self._columns, self._rows


class ExportSettingsStepSimple(WizardStep):
    """
    Simplified, user-friendly export settings step.
    Uses visual cards and progressive disclosure.
    """
    
    def __init__(self, frame_count: int = 0, current_frame: int = 0, parent=None):
        super().__init__(
            title="Configure Export Settings",
            subtitle="Customize how your sprites will be exported",
            parent=parent
        )
        self.frame_count = frame_count
        self.current_frame = current_frame
        self._current_preset: Optional[ExportPreset] = None
        self._settings_widgets = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the simplified UI."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 24, 32, 24)
        self.main_layout.setSpacing(20)
        
        # Content container with grid layout for cards
        self.content_container = QWidget()
        self.content_layout = QGridLayout(self.content_container)
        self.content_layout.setSpacing(16)
        
        self.main_layout.addWidget(self.content_container, 1)
    
    def on_entering(self):
        """Called when entering this step."""
        # Get preset from wizard data
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
        
        # Clear existing content
        self._clear_content()
        
        # Build UI based on export type
        if preset.mode == "sheet":
            self._build_sprite_sheet_ui()
        elif preset.mode == "selected":
            self._build_selected_frames_ui()
        else:  # individual
            self._build_individual_frames_ui()
    
    def _clear_content(self):
        """Clear all content."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._settings_widgets.clear()
    
    def _build_individual_frames_ui(self):
        """Build UI for individual frames export."""
        # Row 1: Output Location (full width)
        location_card = self._create_location_card()
        self.content_layout.addWidget(location_card, 0, 0, 1, 2)
        
        # Row 2: File Naming and Format
        naming_card = self._create_naming_card()
        self.content_layout.addWidget(naming_card, 1, 0)
        
        format_card = self._create_format_card()
        self.content_layout.addWidget(format_card, 1, 1)
        
        # Add spacer
        self.content_layout.setRowStretch(2, 1)
    
    def _build_sprite_sheet_ui(self):
        """Build UI for sprite sheet export."""
        # Row 1: Output and Layout
        location_card = self._create_location_card(single_file=True)
        self.content_layout.addWidget(location_card, 0, 0)
        
        layout_card = self._create_layout_card()
        self.content_layout.addWidget(layout_card, 0, 1)
        
        # Row 2: Appearance
        appearance_card = self._create_appearance_card()
        self.content_layout.addWidget(appearance_card, 1, 0, 1, 2)
        
        # Add spacer
        self.content_layout.setRowStretch(2, 1)
    
    def _build_selected_frames_ui(self):
        """Build UI for selected frames export."""
        # Row 1: Frame Selection (full width)
        selection_card = self._create_selection_card()
        self.content_layout.addWidget(selection_card, 0, 0, 1, 2)
        
        # Row 2: Output and Format
        location_card = self._create_location_card()
        self.content_layout.addWidget(location_card, 1, 0)
        
        format_card = self._create_format_card()
        self.content_layout.addWidget(format_card, 1, 1)
        
        # Add spacer
        self.content_layout.setRowStretch(2, 1)
    
    def _create_location_card(self, single_file: bool = False) -> SettingsCard:
        """Create output location card."""
        card = SettingsCard("Output Location", "📁")
        
        # Directory selector
        self.directory_selector = SimpleDirectorySelector()
        self.directory_selector.directoryChanged.connect(self._on_setting_changed)
        
        # Set default directory
        default_dir = Config.File.get_default_export_directory()
        self.directory_selector.set_directory(str(default_dir))
        
        card.add_row("Save to:", self.directory_selector)
        
        # Single file name for sprite sheets
        if single_file:
            name_widget = QLineEdit()
            name_widget.setText("spritesheet")
            name_widget.setPlaceholderText("Enter filename (without extension)")
            name_widget.textChanged.connect(self._on_setting_changed)
            card.add_row("Filename:", name_widget)
            self._settings_widgets['single_filename'] = name_widget
        
        self._settings_widgets['directory'] = self.directory_selector
        
        return card
    
    def _create_naming_card(self) -> SettingsCard:
        """Create file naming card."""
        card = SettingsCard("File Naming", "📝")
        
        # Base name
        name_widget = QLineEdit()
        name_widget.setText("frame")
        name_widget.setPlaceholderText("Base name for files")
        name_widget.textChanged.connect(self._on_setting_changed)
        card.add_row("Name:", name_widget)
        
        # Pattern
        pattern_widget = QComboBox()
        pattern_widget.addItems([
            "frame_001, frame_002...",
            "frame_0, frame_1...",
            "frame-1, frame-2..."
        ])
        pattern_widget.currentIndexChanged.connect(self._on_setting_changed)
        card.add_row("Pattern:", pattern_widget, "How files will be numbered")
        
        self._settings_widgets['base_name'] = name_widget
        self._settings_widgets['pattern_combo'] = pattern_widget
        
        return card
    
    def _create_format_card(self) -> SettingsCard:
        """Create format card."""
        card = SettingsCard("Format & Quality", "🖼️")
        
        # Format
        format_widget = QComboBox()
        format_widget.addItems(["PNG", "JPG", "BMP"])
        format_widget.currentTextChanged.connect(self._on_format_changed)
        card.add_row("Format:", format_widget)
        
        # Scale
        scale_widget = QuickScaleButtons()
        scale_widget.scaleChanged.connect(self._on_setting_changed)
        card.add_row("Scale:", scale_widget)
        
        # Quality (for JPG)
        self.quality_widget = QSpinBox()
        self.quality_widget.setRange(1, 100)
        self.quality_widget.setValue(95)
        self.quality_widget.setSuffix("%")
        self.quality_widget.valueChanged.connect(self._on_setting_changed)
        self.quality_row = card.add_row("Quality:", self.quality_widget)
        self.quality_widget.setVisible(False)
        
        self._settings_widgets['format'] = format_widget
        self._settings_widgets['scale'] = scale_widget
        self._settings_widgets['quality'] = self.quality_widget
        
        return card
    
    def _create_layout_card(self) -> SettingsCard:
        """Create sprite sheet layout card."""
        card = SettingsCard("Sheet Layout", "📐")
        
        # Grid layout selector
        layout_widget = GridLayoutSelector()
        layout_widget.layoutChanged.connect(self._on_setting_changed)
        card.content_layout.addWidget(layout_widget)
        
        self._settings_widgets['grid_layout'] = layout_widget
        
        return card
    
    def _create_appearance_card(self) -> SettingsCard:
        """Create appearance settings card."""
        card = SettingsCard("Appearance", "🎨")
        
        # Spacing
        spacing_widget = QWidget()
        spacing_layout = QHBoxLayout(spacing_widget)
        spacing_layout.setContentsMargins(0, 0, 0, 0)
        spacing_spin = QSpinBox()
        spacing_spin.setRange(0, 32)
        spacing_spin.setValue(0)
        spacing_spin.setSuffix(" px")
        spacing_spin.valueChanged.connect(self._on_setting_changed)
        spacing_layout.addWidget(spacing_spin)
        spacing_layout.addWidget(QLabel("between sprites"))
        spacing_layout.addStretch()
        card.add_row("Spacing:", spacing_widget)
        
        # Background
        bg_widget = QWidget()
        bg_layout = QHBoxLayout(bg_widget)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_combo = QComboBox()
        bg_combo.addItems(["Transparent", "White", "Black", "Custom Color"])
        bg_combo.currentIndexChanged.connect(self._on_setting_changed)
        bg_layout.addWidget(bg_combo)
        bg_layout.addStretch()
        card.add_row("Background:", bg_widget)
        
        self._settings_widgets['spacing'] = spacing_spin
        self._settings_widgets['background'] = bg_combo
        
        return card
    
    def _create_selection_card(self) -> SettingsCard:
        """Create frame selection card."""
        card = SettingsCard("Select Frames", "🎯")
        
        # Quick selection buttons
        quick_layout = QHBoxLayout()
        
        all_btn = QPushButton("Select All")
        all_btn.clicked.connect(lambda: self._select_frames("all"))
        quick_layout.addWidget(all_btn)
        
        none_btn = QPushButton("Clear")
        none_btn.clicked.connect(lambda: self._select_frames("none"))
        quick_layout.addWidget(none_btn)
        
        range_btn = QPushButton("Range...")
        range_btn.clicked.connect(lambda: self._select_frames("range"))
        quick_layout.addWidget(range_btn)
        
        quick_layout.addStretch()
        card.content_layout.addLayout(quick_layout)
        
        # Frame list
        self.frame_list = QListWidget()
        self.frame_list.setSelectionMode(QListWidget.MultiSelection)
        self.frame_list.setMaximumHeight(150)
        self.frame_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #ffffff;
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
        card.content_layout.addWidget(self.frame_list)
        
        # Selection info
        self.selection_label = QLabel("1 frame selected")
        self.selection_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        card.content_layout.addWidget(self.selection_label)
        
        self._settings_widgets['frame_list'] = self.frame_list
        
        return card
    
    def _on_setting_changed(self):
        """Handle setting changes."""
        self._validate_settings()
        self.dataChanged.emit(self.get_data())
    
    def _on_format_changed(self, format: str):
        """Handle format change."""
        # Show/hide quality for JPG
        if hasattr(self, 'quality_widget'):
            self.quality_widget.setVisible(format == "JPG")
        self._on_setting_changed()
    
    def _on_frame_selection_changed(self):
        """Handle frame selection changes."""
        count = len(self.frame_list.selectedItems())
        if count == 0:
            self.selection_label.setText("No frames selected")
        elif count == 1:
            self.selection_label.setText("1 frame selected")
        else:
            self.selection_label.setText(f"{count} frames selected")
        self._on_setting_changed()
    
    def _select_frames(self, mode: str):
        """Handle quick frame selection."""
        if mode == "all":
            self.frame_list.selectAll()
        elif mode == "none":
            self.frame_list.clearSelection()
        elif mode == "range":
            # TODO: Implement range selection dialog
            pass
    
    def _validate_settings(self):
        """Validate current settings."""
        # No preset means not ready
        if not self._current_preset:
            self.stepValidated.emit(False)
            return False
            
        is_valid = True
        
        # Check directory
        if 'directory' in self._settings_widgets:
            is_valid &= self._settings_widgets['directory'].is_valid()
        
        # Check filenames
        if 'base_name' in self._settings_widgets:
            is_valid &= bool(self._settings_widgets['base_name'].text())
        if 'single_filename' in self._settings_widgets:
            is_valid &= bool(self._settings_widgets['single_filename'].text())
        
        # Check frame selection
        if self._current_preset and self._current_preset.mode == "selected":
            if 'frame_list' in self._settings_widgets:
                is_valid &= len(self._settings_widgets['frame_list'].selectedItems()) > 0
        
        self.stepValidated.emit(is_valid)
        return is_valid
    
    def validate(self) -> bool:
        """Validate the step."""
        return self._validate_settings()
    
    def get_data(self) -> Dict[str, Any]:
        """Get all settings data."""
        data = {
            'output_dir': '',
            'format': 'PNG',
            'scale': 1.0
        }
        
        # Directory
        if 'directory' in self._settings_widgets:
            data['output_dir'] = self._settings_widgets['directory'].get_directory()
        
        # Filenames
        if 'base_name' in self._settings_widgets:
            data['base_name'] = self._settings_widgets['base_name'].text()
        if 'single_filename' in self._settings_widgets:
            data['single_filename'] = self._settings_widgets['single_filename'].text()
        
        # Format
        if 'format' in self._settings_widgets:
            data['format'] = self._settings_widgets['format'].currentText()
        
        # Scale
        if 'scale' in self._settings_widgets:
            data['scale'] = self._settings_widgets['scale'].get_scale()
        
        # Quality (only for JPG format)
        if 'quality' in self._settings_widgets and 'format' in self._settings_widgets:
            if self._settings_widgets['format'].currentText() == "JPG":
                data['quality'] = self._settings_widgets['quality'].value()
        
        # Pattern
        if 'pattern_combo' in self._settings_widgets:
            patterns = ["{name}_{index:03d}", "{name}_{index}", "{name}-{frame}"]
            data['pattern'] = patterns[self._settings_widgets['pattern_combo'].currentIndex()]
        
        # Frame selection
        if 'frame_list' in self._settings_widgets:
            selected_indices = []
            for item in self._settings_widgets['frame_list'].selectedItems():
                selected_indices.append(item.data(Qt.UserRole))
            data['selected_indices'] = selected_indices
        
        # Grid layout
        if 'grid_layout' in self._settings_widgets:
            mode, cols, rows = self._settings_widgets['grid_layout'].get_layout()
            data['layout_mode'] = mode
            if mode == 'columns':
                data['columns'] = cols
            elif mode == 'rows':
                data['rows'] = rows
        
        # Spacing
        if 'spacing' in self._settings_widgets:
            data['spacing'] = self._settings_widgets['spacing'].value()
            data['padding'] = 0  # Simplified - no separate padding control
        
        # Background
        if 'background' in self._settings_widgets:
            bg_index = self._settings_widgets['background'].currentIndex()
            if bg_index == 0:  # Transparent
                data['background_mode'] = 'transparent'
            elif bg_index == 1:  # White
                data['background_mode'] = 'solid'
                data['background_color'] = (255, 255, 255, 255)
            elif bg_index == 2:  # Black
                data['background_mode'] = 'solid'
                data['background_color'] = (0, 0, 0, 255)
            else:  # Custom
                data['background_mode'] = 'solid'
                data['background_color'] = (128, 128, 128, 255)  # Default gray
        
        return data