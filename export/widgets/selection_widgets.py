"""
Export Selection Widgets - Frame and segment selection UI components for export dialog
Consolidates frame_selection.py and segment_handling.py.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QRadioButton, QButtonGroup,
    QPushButton, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal


# =============================================================================
# Frame Selection Widgets
# =============================================================================

class FrameSelectionWidget(QWidget):
    """Widget for frame selection in export dialog."""

    # Signals
    selectionChanged = Signal()
    frameScopeChanged = Signal()

    def __init__(self, frame_count: int = 0, current_frame: int = 0, parent=None):
        super().__init__(parent)
        self.frame_count = frame_count
        self.current_frame = current_frame
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the frame selection UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Frame scope selection
        scope_layout = QHBoxLayout()
        scope_layout.setContentsMargins(0, 0, 0, 0)

        self.scope_group = QButtonGroup()

        self.all_frames_radio = QRadioButton("All frames")
        self.all_frames_radio.setChecked(True)
        self.scope_group.addButton(self.all_frames_radio, 0)
        scope_layout.addWidget(self.all_frames_radio)

        self.selected_frames_radio = QRadioButton("Selected frames")
        self.scope_group.addButton(self.selected_frames_radio, 1)
        scope_layout.addWidget(self.selected_frames_radio)

        self.current_frame_radio = QRadioButton(f"Current frame (#{self.current_frame + 1})")
        self.scope_group.addButton(self.current_frame_radio, 2)
        scope_layout.addWidget(self.current_frame_radio)

        scope_layout.addStretch()
        layout.addLayout(scope_layout)

        # Frame list (shown when selecting frames)
        self.frame_list = QListWidget()
        self.frame_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.frame_list.setMaximumHeight(150)
        self.frame_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.frame_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Populate frame list
        for i in range(self.frame_count):
            item = QListWidgetItem(f"Frame {i + 1}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.frame_list.addItem(item)

        # Initially hidden (shown only when "Selected frames" is chosen)
        self.frame_list.setVisible(False)
        layout.addWidget(self.frame_list)

        # Selection controls
        self.selection_controls = QWidget()
        controls_layout = QHBoxLayout(self.selection_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setMaximumWidth(80)
        self.select_all_btn.clicked.connect(self._select_all_frames)
        controls_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("Clear Selection")
        self.select_none_btn.setMaximumWidth(100)
        self.select_none_btn.clicked.connect(self._clear_selection)
        controls_layout.addWidget(self.select_none_btn)

        self.invert_btn = QPushButton("Invert")
        self.invert_btn.setMaximumWidth(60)
        self.invert_btn.clicked.connect(self._invert_selection)
        controls_layout.addWidget(self.invert_btn)

        controls_layout.addStretch()

        # Info label
        self.selection_info = QLabel("0 frames selected")
        self.selection_info.setStyleSheet("color: #666; font-size: 11px;")
        controls_layout.addWidget(self.selection_info)

        self.selection_controls.setVisible(False)
        layout.addWidget(self.selection_controls)

    def _connect_signals(self):
        """Connect internal signals."""
        self.scope_group.buttonClicked.connect(self._on_scope_changed)
        self.frame_list.itemSelectionChanged.connect(self._update_selection_info)

    def _on_scope_changed(self):
        """Handle frame scope change."""
        selected_id = self.scope_group.checkedId()

        # Show/hide frame list based on selection
        show_list = selected_id == 1  # Selected frames
        self.frame_list.setVisible(show_list)
        self.selection_controls.setVisible(show_list)

        if show_list and not self.frame_list.selectedItems():
            # Auto-select all frames when switching to selected mode
            self._select_all_frames()

        self.frameScopeChanged.emit()
        self.selectionChanged.emit()

    def _select_all_frames(self):
        """Select all frames in the list."""
        self.frame_list.selectAll()
        self._update_selection_info()

    def _clear_selection(self):
        """Clear frame selection."""
        self.frame_list.clearSelection()
        self._update_selection_info()

    def _invert_selection(self):
        """Invert frame selection."""
        for i in range(self.frame_list.count()):
            item = self.frame_list.item(i)
            item.setSelected(not item.isSelected())
        self._update_selection_info()

    def _update_selection_info(self):
        """Update selection info label."""
        count = len(self.frame_list.selectedItems())
        self.selection_info.setText(f"{count} frames selected")
        self.selectionChanged.emit()

    def get_selected_indices(self) -> List[int]:
        """Get list of selected frame indices."""
        scope_id = self.scope_group.checkedId()

        if scope_id == 0:  # All frames
            return list(range(self.frame_count))
        elif scope_id == 1:  # Selected frames
            indices = []
            for item in self.frame_list.selectedItems():
                indices.append(item.data(Qt.ItemDataRole.UserRole))
            return sorted(indices)
        elif scope_id == 2:  # Current frame
            return [self.current_frame]

        return []

    def get_frame_scope(self) -> str:
        """Get current frame scope as string."""
        scope_id = self.scope_group.checkedId()
        scope_map = {
            0: "all",
            1: "selected",
            2: "current"
        }
        return scope_map.get(scope_id, "all")

    def set_frame_scope(self, scope: str):
        """Set frame scope."""
        scope_map = {
            "all": 0,
            "selected": 1,
            "current": 2
        }

        if scope in scope_map:
            button = self.scope_group.button(scope_map[scope])
            if button:
                button.setChecked(True)
                self._on_scope_changed()

    def update_frame_count(self, frame_count: int, current_frame: int = 0):
        """Update frame count and refresh UI."""
        self.frame_count = frame_count
        self.current_frame = current_frame

        # Update radio button text
        self.current_frame_radio.setText(f"Current frame (#{self.current_frame + 1})")

        # Repopulate frame list
        self.frame_list.clear()
        for i in range(self.frame_count):
            item = QListWidgetItem(f"Frame {i + 1}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.frame_list.addItem(item)

        self._update_selection_info()


class FrameSelectionCompact(QGroupBox):
    """Compact frame selection group for advanced settings."""

    # Signals
    selectionChanged = Signal()

    def __init__(self, frame_count: int = 0, parent=None):
        super().__init__("Frame Selection", parent)
        self.frame_count = frame_count
        self._setup_ui()

    def _setup_ui(self):
        """Set up compact frame selection UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 12, 8, 8)

        # Range selection
        range_layout = QHBoxLayout()

        self.range_checkbox = QCheckBox("Export frame range:")
        self.range_checkbox.toggled.connect(self._on_range_toggled)
        range_layout.addWidget(self.range_checkbox)

        self.start_spin = QSpinBox()
        self.start_spin.setRange(1, self.frame_count)
        self.start_spin.setValue(1)
        self.start_spin.setPrefix("From ")
        self.start_spin.setMaximumWidth(80)
        self.start_spin.setEnabled(False)
        range_layout.addWidget(self.start_spin)

        self.end_spin = QSpinBox()
        self.end_spin.setRange(1, self.frame_count)
        self.end_spin.setValue(self.frame_count)
        self.end_spin.setPrefix("To ")
        self.end_spin.setMaximumWidth(80)
        self.end_spin.setEnabled(False)
        range_layout.addWidget(self.end_spin)

        range_layout.addStretch()
        layout.addLayout(range_layout)

        # Connect value changes
        self.start_spin.valueChanged.connect(self._on_range_changed)
        self.end_spin.valueChanged.connect(self._on_range_changed)

        # Info label
        self.info_label = QLabel("All frames will be exported")
        self.info_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        layout.addWidget(self.info_label)

    def _on_range_toggled(self, checked: bool):
        """Handle range checkbox toggle."""
        self.start_spin.setEnabled(checked)
        self.end_spin.setEnabled(checked)
        self._update_info()
        self.selectionChanged.emit()

    def _on_range_changed(self):
        """Handle range value change."""
        # Ensure valid range
        if self.start_spin.value() > self.end_spin.value():
            self.end_spin.setValue(self.start_spin.value())

        self._update_info()
        self.selectionChanged.emit()

    def _update_info(self):
        """Update info label."""
        if self.range_checkbox.isChecked():
            start = self.start_spin.value()
            end = self.end_spin.value()
            count = end - start + 1
            self.info_label.setText(f"{count} frames will be exported")
        else:
            self.info_label.setText("All frames will be exported")

    def get_selected_indices(self) -> Optional[List[int]]:
        """Get selected frame indices, or None for all frames."""
        if self.range_checkbox.isChecked():
            start = self.start_spin.value() - 1  # Convert to 0-based
            end = self.end_spin.value()
            return list(range(start, end))
        return None

    def update_frame_count(self, frame_count: int):
        """Update frame count."""
        self.frame_count = frame_count
        self.start_spin.setRange(1, frame_count)
        self.end_spin.setRange(1, frame_count)
        self.end_spin.setValue(frame_count)
        self._update_info()


# =============================================================================
# Segment Selection Widgets
# =============================================================================

class SegmentExportWidget(QWidget):
    """Widget for handling animation segment export."""

    # Signals
    segmentsChanged = Signal()

    def __init__(self, segment_manager=None, parent=None):
        super().__init__(parent)
        self.segment_manager = segment_manager
        self._setup_ui()
        self._refresh_segments()

    def _setup_ui(self):
        """Set up the segment export UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Select Animation Segments to Export:")
        header_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Segment list
        self.segment_list = QListWidget()
        self.segment_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.segment_list.setMaximumHeight(200)
        layout.addWidget(self.segment_list)

        # Selection controls
        controls_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setMaximumWidth(80)
        self.select_all_btn.clicked.connect(self._select_all_segments)
        controls_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("Clear")
        self.select_none_btn.setMaximumWidth(60)
        self.select_none_btn.clicked.connect(self._clear_selection)
        controls_layout.addWidget(self.select_none_btn)

        controls_layout.addStretch()

        # Info label
        self.info_label = QLabel("0 segments selected")
        self.info_label.setStyleSheet("color: #666; font-size: 11px;")
        controls_layout.addWidget(self.info_label)

        layout.addLayout(controls_layout)

        # Export options
        options_group = QGroupBox("Segment Export Options")
        options_layout = QVBoxLayout(options_group)

        self.separate_folders_check = QCheckBox("Export each segment to separate folder")
        self.separate_folders_check.setChecked(True)
        options_layout.addWidget(self.separate_folders_check)

        self.include_segment_name_check = QCheckBox("Include segment name in filenames")
        self.include_segment_name_check.setChecked(True)
        options_layout.addWidget(self.include_segment_name_check)

        layout.addWidget(options_group)

        # Connect signals
        self.segment_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _refresh_segments(self):
        """Refresh the segment list from segment manager."""
        self.segment_list.clear()

        if not self.segment_manager:
            return

        segments = self.segment_manager.get_all_segments()
        for segment_name, segment_data in segments.items():
            # Create item with segment info
            frame_count = segment_data.end_frame - segment_data.start_frame + 1
            item_text = f"{segment_name} ({frame_count} frames)"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, segment_name)
            item.setData(Qt.ItemDataRole.UserRole + 1, segment_data)

            # Add tooltip with more info
            tooltip = f"Frames {segment_data.start_frame + 1} - {segment_data.end_frame + 1}"
            if hasattr(segment_data, 'color'):
                tooltip += f"\nColor: {segment_data.color}"
            item.setToolTip(tooltip)

            self.segment_list.addItem(item)

        self._update_info()

    def _select_all_segments(self):
        """Select all segments."""
        self.segment_list.selectAll()
        self._update_info()

    def _clear_selection(self):
        """Clear segment selection."""
        self.segment_list.clearSelection()
        self._update_info()

    def _on_selection_changed(self):
        """Handle selection change."""
        self._update_info()
        self.segmentsChanged.emit()

    def _update_info(self):
        """Update info label."""
        count = len(self.segment_list.selectedItems())
        self.info_label.setText(f"{count} segments selected")

    def get_selected_segments(self) -> List[str]:
        """Get list of selected segment names."""
        segments = []
        for item in self.segment_list.selectedItems():
            segment_name = item.data(Qt.ItemDataRole.UserRole)
            if segment_name:
                segments.append(segment_name)
        return segments

    def get_segment_export_settings(self) -> Dict[str, Any]:
        """Get segment-specific export settings."""
        return {
            'separate_folders': self.separate_folders_check.isChecked(),
            'include_segment_name': self.include_segment_name_check.isChecked(),
            'selected_segments': self.get_selected_segments()
        }

    def has_selected_segments(self) -> bool:
        """Check if any segments are selected."""
        return len(self.segment_list.selectedItems()) > 0

    def set_segment_manager(self, segment_manager):
        """Update segment manager and refresh list."""
        self.segment_manager = segment_manager
        self._refresh_segments()


class SegmentExportHandler:
    """Handler for segment-specific export operations."""

    @staticmethod
    def prepare_segment_export_settings(
        base_settings: Dict[str, Any],
        segment_settings: Dict[str, Any],
        segment_manager
    ) -> List[Dict[str, Any]]:
        """
        Prepare export settings for each selected segment.

        Args:
            base_settings: Base export settings
            segment_settings: Segment-specific settings
            segment_manager: Animation segment manager

        Returns:
            List of export settings, one per segment
        """
        import os

        export_configs = []
        selected_segments = segment_settings.get('selected_segments', [])

        for segment_name in selected_segments:
            segment = segment_manager.get_segment(segment_name)
            if not segment:
                continue

            # Create segment-specific settings
            segment_config = base_settings.copy()

            # Update output directory if using separate folders
            if segment_settings.get('separate_folders', True):
                segment_config['output_dir'] = os.path.join(
                    base_settings['output_dir'],
                    segment_name
                )

            # Update base name if including segment name
            if segment_settings.get('include_segment_name', True):
                segment_config['base_name'] = f"{base_settings['base_name']}_{segment_name}"

            # Add segment-specific metadata
            segment_config['segment_name'] = segment_name
            segment_config['segment_start'] = segment.start_frame
            segment_config['segment_end'] = segment.end_frame
            segment_config['frame_indices'] = list(range(segment.start_frame, segment.end_frame + 1))

            export_configs.append(segment_config)

        return export_configs

    @staticmethod
    def calculate_total_frames_for_segments(
        selected_segments: List[str],
        segment_manager
    ) -> int:
        """Calculate total number of frames across selected segments."""
        total = 0

        for segment_name in selected_segments:
            segment = segment_manager.get_segment(segment_name)
            if segment:
                total += segment.end_frame - segment.start_frame + 1

        return total
