"""
Export Segment Handling - Animation segment export logic for export dialog
Part of Phase 1 refactoring to split export_dialog.py into smaller modules.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QCheckBox, QPushButton
)
from PySide6.QtCore import Qt, Signal

from config import Config


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
        self.segment_list.setSelectionMode(QListWidget.ExtendedSelection)
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
            item.setData(Qt.UserRole, segment_name)
            item.setData(Qt.UserRole + 1, segment_data)
            
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
            segment_name = item.data(Qt.UserRole)
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
                import os
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