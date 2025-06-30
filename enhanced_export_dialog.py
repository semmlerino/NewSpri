"""
Enhanced Export Dialog - Extended export functionality with animation segment support
Extends the original export dialog to support exporting animation segments.
Part of Animation Splitting Feature implementation.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox,
    QGroupBox, QFileDialog, QDialogButtonBox, QListWidget,
    QListWidgetItem, QProgressBar, QMessageBox, QRadioButton,
    QButtonGroup, QFormLayout, QSizePolicy, QTabWidget,
    QWidget, QTextEdit, QSlider, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QFont

from config import Config
from styles import StyleManager
from frame_exporter import get_frame_exporter, ExportMode, ExportFormat
from animation_segment_manager import AnimationSegmentData, AnimationSegmentManager


class AnimationSegmentExportTab(QWidget):
    """Tab for animation segment export functionality."""
    
    def __init__(self, segment_manager: AnimationSegmentManager):
        super().__init__()
        self.segment_manager = segment_manager
        self._setup_ui()
        self._connect_signals()
        self._update_segment_list()
    
    def _setup_ui(self):
        """Set up the animation segment export UI."""
        layout = QVBoxLayout(self)
        
        # Segment selection group
        segment_group = QGroupBox("Available Animation Segments")
        segment_layout = QVBoxLayout()
        
        self.segment_list = QListWidget()
        self.segment_list.setSelectionMode(QListWidget.MultiSelection)
        segment_layout.addWidget(self.segment_list)
        
        # Segment info display
        self.segment_info = QTextEdit()
        self.segment_info.setMaximumHeight(80)
        self.segment_info.setReadOnly(True)
        self.segment_info.setPlaceholderText("Select segments to see details...")
        segment_layout.addWidget(self.segment_info)
        
        segment_group.setLayout(segment_layout)
        layout.addWidget(segment_group)
        
        # Export options group
        options_group = QGroupBox("Segment Export Options")
        options_layout = QFormLayout()
        
        # Export mode for segments
        self.segment_mode_combo = QComboBox()
        self.segment_mode_combo.addItems([
            "Individual Segments (separate folders)",
            "Combined Sprite Sheet",
            "Animated GIF per Segment",
            "Individual Frames (all segments)"
        ])
        options_layout.addRow("Export Mode:", self.segment_mode_combo)
        
        # Include segment metadata
        self.include_metadata_check = QCheckBox()
        self.include_metadata_check.setChecked(True)
        self.include_metadata_check.setToolTip("Include JSON metadata file with segment information")
        options_layout.addRow("Include Metadata:", self.include_metadata_check)
        
        # Frame naming for segments
        self.segment_naming_edit = QLineEdit("{segment}_{frame:03d}")
        self.segment_naming_edit.setToolTip(
            "Naming pattern: {segment} = segment name, "
            "{frame} = frame number, {index} = frame index"
        )
        options_layout.addRow("Frame Naming:", self.segment_naming_edit)
        
        # Animation settings (for GIF export)
        gif_group = QGroupBox("Animation Settings (GIF)")
        gif_layout = QFormLayout()
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(10)
        self.fps_spin.setSuffix(" fps")
        gif_layout.addRow("Frame Rate:", self.fps_spin)
        
        self.loop_check = QCheckBox()
        self.loop_check.setChecked(True)
        gif_layout.addRow("Loop Animation:", self.loop_check)
        
        gif_group.setLayout(gif_layout)
        options_layout.addRow(gif_group)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Selection controls
        controls_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All Segments")
        select_all_btn.clicked.connect(self._select_all_segments)
        controls_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Clear Selection")
        select_none_btn.clicked.connect(self._clear_segment_selection)
        controls_layout.addWidget(select_none_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Selection summary
        self.selection_summary = QLabel()
        self._update_selection_summary()
        layout.addWidget(self.selection_summary)
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.segment_list.itemSelectionChanged.connect(self._on_segment_selection_changed)
        self.segment_manager.segmentAdded.connect(self._update_segment_list)
        self.segment_manager.segmentRemoved.connect(self._update_segment_list)
        self.segment_manager.segmentUpdated.connect(self._update_segment_list)
        self.segment_manager.segmentsCleared.connect(self._update_segment_list)
    
    def _update_segment_list(self):
        """Update the segment list display."""
        self.segment_list.clear()
        
        for segment in self.segment_manager.get_all_segments():
            item_text = f"{segment.name} (Frames {segment.start_frame}-{segment.end_frame})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, segment.name)
            
            # Color the item background
            item.setBackground(segment.color.lighter(180))
            
            self.segment_list.addItem(item)
        
        self._update_selection_summary()
    
    def _on_segment_selection_changed(self):
        """Handle segment selection changes."""
        selected_items = self.segment_list.selectedItems()
        
        if selected_items:
            # Show info for selected segments
            info_parts = []
            total_frames = 0
            
            for item in selected_items:
                segment_name = item.data(Qt.UserRole)
                segment = self.segment_manager.get_segment(segment_name)
                if segment:
                    info_parts.append(
                        f"• {segment.name}: {segment.frame_count} frames "
                        f"({segment.start_frame}-{segment.end_frame})"
                    )
                    total_frames += segment.frame_count
            
            info_parts.append(f"\nTotal: {total_frames} frames")
            self.segment_info.setText("\n".join(info_parts))
        else:
            self.segment_info.clear()
        
        self._update_selection_summary()
    
    def _select_all_segments(self):
        """Select all segments."""
        self.segment_list.selectAll()
    
    def _clear_segment_selection(self):
        """Clear segment selection."""
        self.segment_list.clearSelection()
    
    def _update_selection_summary(self):
        """Update the selection summary label."""
        selected_count = len(self.segment_list.selectedItems())
        total_count = self.segment_list.count()
        
        self.selection_summary.setText(
            f"Selected: {selected_count} of {total_count} segments"
        )
    
    def get_selected_segments(self) -> List[str]:
        """Get names of selected segments."""
        return [
            item.data(Qt.UserRole) 
            for item in self.segment_list.selectedItems()
        ]
    
    def get_export_settings(self) -> Dict[str, Any]:
        """Get export settings for animation segments."""
        return {
            "mode": self.segment_mode_combo.currentText(),
            "mode_index": self.segment_mode_combo.currentIndex(),
            "include_metadata": self.include_metadata_check.isChecked(),
            "naming_pattern": self.segment_naming_edit.text(),
            "fps": self.fps_spin.value(),
            "loop": self.loop_check.isChecked(),
            "selected_segments": self.get_selected_segments()
        }


class EnhancedExportDialog(QDialog):
    """Enhanced export dialog with animation segment support."""
    
    # Signals
    exportRequested = Signal(dict)  # Export settings
    segmentExportRequested = Signal(dict)  # Segment export settings
    
    def __init__(self, parent=None, frame_count: int = 0, current_frame: int = 0,
                 segment_manager: AnimationSegmentManager = None):
        """
        Initialize enhanced export dialog.
        
        Args:
            parent: Parent widget
            frame_count: Total number of frames available
            current_frame: Currently selected frame index
            segment_manager: Animation segment manager instance
        """
        super().__init__(parent)
        self.frame_count = frame_count
        self.current_frame = current_frame
        self.segment_manager = segment_manager or AnimationSegmentManager()
        self._exporter = get_frame_exporter()
        
        self._setup_ui()
        self._connect_signals()
        self._update_ui_state()
        self._set_defaults()
    
    def _setup_ui(self):
        """Set up the dialog UI with tabs."""
        self.setWindowTitle("Export Frames & Animation Segments")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Tab widget for different export modes
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Standard export tab
        self.standard_tab = self._create_standard_export_tab()
        self.tab_widget.addTab(self.standard_tab, "Standard Export")
        
        # Animation segments tab
        if self.segment_manager:
            self.segments_tab = AnimationSegmentExportTab(self.segment_manager)
            self.tab_widget.addTab(self.segments_tab, "Animation Segments")
        
        # Common settings group
        common_group = self._create_common_settings_group()
        layout.addWidget(common_group)
        
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
    
    def _create_standard_export_tab(self) -> QWidget:
        """Create the standard export tab (similar to original dialog)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Export mode group
        mode_group = self._create_mode_group()
        layout.addWidget(mode_group)
        
        # Frame selection group (for selected frames mode)
        self.selection_group = self._create_selection_group()
        layout.addWidget(self.selection_group)
        
        return tab
    
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
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_common_settings_group(self) -> QGroupBox:
        """Create common export settings group."""
        group = QGroupBox("Export Settings")
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
        layout.addRow("Scale:", self.scale_spin)
        
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
        layout.addRow("Base Name:", self.base_name_edit)
        
        group.setLayout(layout)
        return group
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.mode_group.buttonToggled.connect(self._update_ui_state)
        self.frame_list.itemSelectionChanged.connect(self._update_selection_info)
        self.base_name_edit.textChanged.connect(self._update_preview)
        
    def _update_ui_state(self):
        """Update UI state based on current selections."""
        # Show/hide frame selection based on mode
        selected_mode = self.selected_radio.isChecked()
        self.selection_group.setVisible(selected_mode)
        
    def _set_defaults(self):
        """Set default values."""
        # Set default output directory to user's desktop
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            self.output_dir_edit.setText(str(desktop))
    
    def _select_all_frames(self):
        """Select all frames."""
        self.frame_list.selectAll()
    
    def _select_no_frames(self):
        """Clear frame selection."""
        self.frame_list.clearSelection()
    
    def _update_selection_info(self):
        """Update selection information display."""
        pass  # Placeholder for selection info updates
    
    def _update_preview(self):
        """Update filename preview."""
        pass  # Placeholder for preview updates
    
    def _browse_output_dir(self):
        """Browse for output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", 
            self.output_dir_edit.text()
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def _on_export(self):
        """Handle export button click."""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Standard export
            self._export_standard()
        elif current_tab == 1:  # Animation segments
            self._export_segments()
    
    def _export_standard(self):
        """Export using standard mode."""
        # Get export settings
        settings = {
            "mode": "individual" if self.individual_radio.isChecked() else
                   "sheet" if self.sheet_radio.isChecked() else
                   "selected" if self.selected_radio.isChecked() else "gif",
            "format": self.format_combo.currentText(),
            "scale": self.scale_spin.value(),
            "output_dir": self.output_dir_edit.text(),
            "base_name": self.base_name_edit.text(),
            "selected_frames": [
                self.frame_list.item(i).data(Qt.UserRole)
                for i in range(self.frame_list.count())
                if self.frame_list.item(i).isSelected()
            ] if self.selected_radio.isChecked() else []
        }
        
        # Validate settings
        if not settings["output_dir"]:
            QMessageBox.warning(self, "Export Error", "Please select an output directory.")
            return
        
        if not settings["base_name"]:
            QMessageBox.warning(self, "Export Error", "Please enter a base filename.")
            return
        
        self.exportRequested.emit(settings)
        self.accept()
    
    def _export_segments(self):
        """Export animation segments."""
        if not hasattr(self, 'segments_tab'):
            QMessageBox.warning(self, "Export Error", "Animation segments not available.")
            return
        
        segment_settings = self.segments_tab.get_export_settings()
        
        if not segment_settings["selected_segments"]:
            QMessageBox.warning(self, "Export Error", "Please select at least one animation segment.")
            return
        
        # Combine with common settings
        settings = {
            **segment_settings,
            "format": self.format_combo.currentText(),
            "scale": self.scale_spin.value(),
            "output_dir": self.output_dir_edit.text(),
            "base_name": self.base_name_edit.text()
        }
        
        # Validate settings
        if not settings["output_dir"]:
            QMessageBox.warning(self, "Export Error", "Please select an output directory.")
            return
        
        self.segmentExportRequested.emit(settings)
        self.accept()
    
    def set_progress(self, value: int, message: str = ""):
        """Update progress bar and status."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
        
        if value >= 100:
            # Hide progress bar when complete
            QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))
    
    def show_error(self, message: str):
        """Show error message."""
        self.status_label.setText(f"Error: {message}")
        QMessageBox.critical(self, "Export Error", message)