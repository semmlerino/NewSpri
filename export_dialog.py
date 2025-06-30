"""
Export Dialog - User interface for frame export settings
Provides a dialog for users to configure export options.
Part of Phase 4: Frame Export System implementation.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox,
    QGroupBox, QFileDialog, QDialogButtonBox, QListWidget,
    QListWidgetItem, QProgressBar, QMessageBox, QRadioButton,
    QButtonGroup, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap

from config import Config
from styles import StyleManager
from frame_exporter import get_frame_exporter, ExportMode, ExportFormat


class ExportDialog(QDialog):
    """Dialog for configuring frame export settings."""
    
    # Signals
    exportRequested = Signal(dict)  # Export settings
    
    def __init__(self, parent=None, frame_count: int = 0, current_frame: int = 0):
        """
        Initialize export dialog.
        
        Args:
            parent: Parent widget
            frame_count: Total number of frames available
            current_frame: Currently selected frame index
        """
        super().__init__(parent)
        self.frame_count = frame_count
        self.current_frame = current_frame
        self._exporter = get_frame_exporter()
        
        self._setup_ui()
        self._connect_signals()
        self._update_ui_state()
        
        # Set default values
        self._set_defaults()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Export Frames")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Export mode group
        mode_group = self._create_mode_group()
        layout.addWidget(mode_group)
        
        # Format and quality group
        format_group = self._create_format_group()
        layout.addWidget(format_group)
        
        # Output settings group
        output_group = self._create_output_group()
        layout.addWidget(output_group)
        
        # Frame selection group (for selected frames mode)
        self.selection_group = self._create_selection_group()
        layout.addWidget(self.selection_group)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self._on_export)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Apply basic styling
        # Could add custom dialog styling if needed
    
    def _create_mode_group(self) -> QGroupBox:
        """Create export mode selection group."""
        group = QGroupBox("Export Mode")
        layout = QVBoxLayout()
        
        # Create radio buttons for export modes
        self.mode_group = QButtonGroup()
        
        self.individual_radio = QRadioButton("Individual Frames")
        self.individual_radio.setToolTip("Export each frame as a separate file")
        self.individual_radio.setChecked(True)
        layout.addWidget(self.individual_radio)
        self.mode_group.addButton(self.individual_radio, 0)
        
        self.sheet_radio = QRadioButton("Sprite Sheet")
        self.sheet_radio.setToolTip("Export all frames as a single sprite sheet")
        layout.addWidget(self.sheet_radio)
        self.mode_group.addButton(self.sheet_radio, 1)
        
        self.selected_radio = QRadioButton("Selected Frames Only")
        self.selected_radio.setToolTip("Export only selected frames")
        layout.addWidget(self.selected_radio)
        self.mode_group.addButton(self.selected_radio, 2)
        
        self.gif_radio = QRadioButton("Animated GIF")
        self.gif_radio.setToolTip("Export frames as an animated GIF")
        layout.addWidget(self.gif_radio)
        self.mode_group.addButton(self.gif_radio, 3)
        
        group.setLayout(layout)
        return group
    
    def _create_format_group(self) -> QGroupBox:
        """Create format and quality settings group."""
        group = QGroupBox("Format & Quality")
        layout = QFormLayout()
        
        # Format selection
        self.format_combo = QComboBox()
        self.format_combo.addItems(Config.Export.IMAGE_FORMATS)
        self.format_combo.setCurrentText(Config.Export.DEFAULT_FORMAT)
        layout.addRow("Format:", self.format_combo)
        
        # Scale factor
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 10.0)
        self.scale_spin.setSingleStep(0.5)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setSuffix("x")
        self.scale_spin.setDecimals(1)
        self.scale_spin.setToolTip("Scale factor for exported images")
        layout.addRow("Scale:", self.scale_spin)
        
        # Add common scale presets
        scale_layout = QHBoxLayout()
        for scale in Config.Export.DEFAULT_SCALE_FACTORS:
            btn = QPushButton(f"{scale}x")
            btn.setFixedWidth(50)
            btn.clicked.connect(lambda checked, s=scale: self.scale_spin.setValue(s))
            scale_layout.addWidget(btn)
        scale_layout.addStretch()
        layout.addRow("", scale_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_output_group(self) -> QGroupBox:
        """Create output settings group."""
        group = QGroupBox("Output Settings")
        layout = QFormLayout()
        
        # Output directory
        dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Select output directory...")
        dir_layout.addWidget(self.output_dir_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output_dir)
        dir_layout.addWidget(browse_btn)
        layout.addRow("Directory:", dir_layout)
        
        # Base filename
        self.base_name_edit = QLineEdit("frame")
        self.base_name_edit.setToolTip("Base name for exported files")
        layout.addRow("Base Name:", self.base_name_edit)
        
        # Naming pattern (for individual frames)
        self.pattern_edit = QLineEdit(Config.Export.DEFAULT_PATTERN)
        self.pattern_edit.setToolTip(
            "Naming pattern for files. Use {name} for base name, "
            "{index} for zero-based index, {frame} for one-based frame number"
        )
        layout.addRow("Pattern:", self.pattern_edit)
        
        # Pattern preview
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("QLabel { color: #888; }")
        layout.addRow("Preview:", self.preview_label)
        
        group.setLayout(layout)
        return group
    
    def _create_selection_group(self) -> QGroupBox:
        """Create frame selection group."""
        group = QGroupBox("Frame Selection")
        layout = QVBoxLayout()
        
        # Frame list
        self.frame_list = QListWidget()
        self.frame_list.setSelectionMode(QListWidget.MultiSelection)
        self.frame_list.setMaximumHeight(150)
        
        # Populate frame list
        for i in range(self.frame_count):
            item = QListWidgetItem(f"Frame {i + 1}")
            item.setData(Qt.UserRole, i)
            self.frame_list.addItem(item)
            
            # Select current frame by default
            if i == self.current_frame:
                item.setSelected(True)
        
        layout.addWidget(self.frame_list)
        
        # Selection controls
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all_frames)
        button_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self._select_no_frames)
        button_layout.addWidget(select_none_btn)
        
        select_range_btn = QPushButton("Select Range...")
        select_range_btn.clicked.connect(self._select_frame_range)
        button_layout.addWidget(select_range_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Selection info
        self.selection_info_label = QLabel()
        self._update_selection_info()
        layout.addWidget(self.selection_info_label)
        
        group.setLayout(layout)
        return group
    
    def _connect_signals(self):
        """Connect dialog signals."""
        # Mode changes
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        
        # Format changes
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        
        # Output settings changes
        self.base_name_edit.textChanged.connect(self._update_preview)
        self.pattern_edit.textChanged.connect(self._update_preview)
        
        # Frame selection changes
        self.frame_list.itemSelectionChanged.connect(self._update_selection_info)
        
        # Exporter signals
        self._exporter.exportStarted.connect(self._on_export_started)
        self._exporter.exportProgress.connect(self._on_export_progress)
        self._exporter.exportFinished.connect(self._on_export_finished)
        self._exporter.exportError.connect(self._on_export_error)
    
    def _set_defaults(self):
        """Set default values."""
        # Set default output directory to current directory
        default_dir = os.path.join(os.getcwd(), Config.Export.DEFAULT_EXPORT_DIR)
        self.output_dir_edit.setText(default_dir)
        
        # Update preview
        self._update_preview()
    
    def _update_ui_state(self):
        """Update UI state based on current mode."""
        mode_id = self.mode_group.checkedId()
        
        # Show/hide elements based on mode
        is_individual = mode_id == 0
        is_selected = mode_id == 2
        is_gif = mode_id == 3
        
        # Pattern only for individual frames
        self.pattern_edit.setEnabled(is_individual or is_selected)
        
        # Frame selection only for selected mode
        self.selection_group.setVisible(is_selected)
        
        # Format selection disabled for GIF
        self.format_combo.setEnabled(not is_gif)
        if is_gif:
            self.format_combo.setCurrentText("GIF")
    
    def _browse_output_dir(self):
        """Browse for output directory."""
        current_dir = self.output_dir_edit.text() or os.getcwd()
        
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def _select_all_frames(self):
        """Select all frames in the list."""
        for i in range(self.frame_list.count()):
            self.frame_list.item(i).setSelected(True)
    
    def _select_no_frames(self):
        """Deselect all frames."""
        self.frame_list.clearSelection()
    
    def _select_frame_range(self):
        """Select a range of frames."""
        # Simple implementation - could be enhanced with a custom dialog
        selected_items = self.frame_list.selectedItems()
        if len(selected_items) >= 2:
            # Get min and max indices
            indices = [self.frame_list.row(item) for item in selected_items]
            min_idx = min(indices)
            max_idx = max(indices)
            
            # Select all frames in range
            for i in range(min_idx, max_idx + 1):
                self.frame_list.item(i).setSelected(True)
        else:
            QMessageBox.information(
                self,
                "Select Range",
                "Please select at least two frames to define a range."
            )
    
    def _update_selection_info(self):
        """Update frame selection information label."""
        selected_count = len(self.frame_list.selectedItems())
        self.selection_info_label.setText(
            f"{selected_count} of {self.frame_count} frames selected"
        )
    
    def _update_preview(self):
        """Update filename preview."""
        try:
            base_name = self.base_name_edit.text() or "frame"
            pattern = self.pattern_edit.text() or Config.Export.DEFAULT_PATTERN
            
            # Generate preview for first frame
            preview = pattern.format(
                name=base_name,
                index=0,
                frame=1
            )
            
            # Add extension based on format
            format_str = self.format_combo.currentText()
            if self.mode_group.checkedId() == 3:  # GIF mode
                preview = f"{base_name}.gif"
            else:
                preview += f".{format_str.lower()}"
            
            self.preview_label.setText(preview)
        except Exception:
            self.preview_label.setText("Invalid pattern")
    
    def _on_mode_changed(self):
        """Handle export mode change."""
        self._update_ui_state()
        self._update_preview()
    
    def _on_format_changed(self):
        """Handle format change."""
        self._update_preview()
    
    def _on_export(self):
        """Handle export button click."""
        # Validate settings
        if not self._validate_settings():
            return
        
        # Gather export settings
        settings = self._gather_settings()
        
        # Emit signal for parent to handle
        self.exportRequested.emit(settings)
        
        # Don't close dialog yet - wait for export to complete
    
    def _validate_settings(self) -> bool:
        """Validate export settings."""
        # Check output directory
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "Validation Error", "Please select an output directory.")
            return False
        
        # Check base name
        base_name = self.base_name_edit.text().strip()
        if not base_name:
            QMessageBox.warning(self, "Validation Error", "Please enter a base filename.")
            return False
        
        # Check pattern
        pattern = self.pattern_edit.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Validation Error", "Please enter a naming pattern.")
            return False
        
        # Validate pattern
        try:
            pattern.format(name="test", index=0, frame=1)
        except Exception:
            QMessageBox.warning(self, "Validation Error", "Invalid naming pattern.")
            return False
        
        # Check frame selection for selected mode
        if self.mode_group.checkedId() == 2:  # Selected frames mode
            if not self.frame_list.selectedItems():
                QMessageBox.warning(self, "Validation Error", "Please select at least one frame.")
                return False
        
        return True
    
    def _gather_settings(self) -> dict:
        """Gather all export settings."""
        mode_id = self.mode_group.checkedId()
        mode_map = {
            0: ExportMode.INDIVIDUAL_FRAMES.value,
            1: ExportMode.SPRITE_SHEET.value,
            2: ExportMode.SELECTED_FRAMES.value,
            3: ExportMode.ANIMATED_GIF.value
        }
        
        settings = {
            'output_dir': self.output_dir_edit.text().strip(),
            'base_name': self.base_name_edit.text().strip(),
            'format': self.format_combo.currentText(),
            'mode': mode_map[mode_id],
            'scale_factor': self.scale_spin.value(),
            'pattern': self.pattern_edit.text().strip()
        }
        
        # Add selected indices for selected frames mode
        if mode_id == 2:
            selected_indices = []
            for item in self.frame_list.selectedItems():
                selected_indices.append(item.data(Qt.UserRole))
            settings['selected_indices'] = selected_indices
        
        return settings
    
    def _on_export_started(self):
        """Handle export start."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.status_label.setText("Starting export...")
    
    def _on_export_progress(self, current: int, total: int, message: str):
        """Handle export progress."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
    
    def _on_export_finished(self, success: bool, message: str):
        """Handle export completion."""
        self.progress_bar.setVisible(False)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        
        if success:
            self.status_label.setText(f"✓ {message}")
            # Auto-close after successful export
            QTimer.singleShot(1000, self.accept)
        else:
            self.status_label.setText(f"✗ {message}")
    
    def _on_export_error(self, error_message: str):
        """Handle export error."""
        QMessageBox.critical(self, "Export Error", error_message)