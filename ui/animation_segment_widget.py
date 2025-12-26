"""
Animation Segment Export Widget
Modern animation segment selection and export interface.
Part of Phase 1: Export Dialog Redesign - Animation Segments Support.
"""

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from managers.animation_segment_manager import AnimationSegmentManager
else:
    try:
        from managers.animation_segment_manager import AnimationSegmentManager
    except ImportError:
        # Fallback if animation segment manager is not available
        class AnimationSegmentManager:  # type: ignore[no-redef]
            def get_all_segments(self) -> list[Any]:
                return []
            def get_segment(self, name: str) -> Any:
                return None


class AnimationSegmentSelector(QGroupBox):
    """Modern animation segment selector with visual design."""

    segmentSelectionChanged = Signal(list)  # List of selected segment names

    def __init__(self, segment_manager: AnimationSegmentManager | None = None):
        super().__init__("Animation Segments")
        self.segment_manager = segment_manager
        self._selected_segments: list[str] = []

        self._setup_ui()
        self._connect_signals()
        self._update_segment_list()

    def _setup_ui(self):
        """Set up the segment selector UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Check if segments are available
        if not self.segment_manager or not self.segment_manager.get_all_segments():
            self._create_no_segments_ui(layout)
            return

        # Segment list
        self._create_segment_list(layout)

        # Segment info display
        self._create_segment_info(layout)

        # Selection controls
        self._create_selection_controls(layout)

        # Export options specific to segments
        self._create_segment_export_options(layout)

    def _create_no_segments_ui(self, layout: QVBoxLayout):
        """Create UI for when no segments are available."""
        no_segments_frame = QFrame()
        no_segments_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        no_segments_layout = QVBoxLayout(no_segments_frame)
        no_segments_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_label = QLabel("🎭")
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_segments_layout.addWidget(icon_label)

        # Message
        message_label = QLabel("No Animation Segments Available")
        message_font = QFont()
        message_font.setPointSize(12)
        message_font.setBold(True)
        message_label.setFont(message_font)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("color: #6c757d; margin: 10px;")
        no_segments_layout.addWidget(message_label)

        # Help text
        help_label = QLabel("Create animation segments in the Animation Splitting tab to use this feature.")
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        no_segments_layout.addWidget(help_label)

        layout.addWidget(no_segments_frame)

        # Hide the group box title when no segments
        self.setTitle("")

    def _create_segment_list(self, layout: QVBoxLayout):
        """Create the segment list widget."""
        list_label = QLabel("Select animation segments to export:")
        list_font = QFont()
        list_font.setPointSize(10)
        list_font.setBold(True)
        list_label.setFont(list_font)
        layout.addWidget(list_label)

        self.segment_list = QListWidget()
        self.segment_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.segment_list.setMaximumHeight(150)
        self.segment_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
                border-left: 3px solid #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.segment_list)

    def _create_segment_info(self, layout: QVBoxLayout):
        """Create segment information display."""
        self.segment_info = QTextEdit()
        self.segment_info.setMaximumHeight(80)
        self.segment_info.setReadOnly(True)
        self.segment_info.setPlaceholderText("Select segments to see details...")
        self.segment_info.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-size: 10px;
                color: #495057;
            }
        """)
        layout.addWidget(self.segment_info)

    def _create_selection_controls(self, layout: QVBoxLayout):
        """Create segment selection control buttons."""
        controls_layout = QHBoxLayout()

        # Select all button
        select_all_btn = QPushButton("Select All")
        select_all_btn.setFixedHeight(28)
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        select_all_btn.clicked.connect(self._select_all_segments)
        controls_layout.addWidget(select_all_btn)

        # Clear selection button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(28)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        clear_btn.clicked.connect(self._clear_selection)
        controls_layout.addWidget(clear_btn)

        controls_layout.addStretch()

        # Selection summary
        self.selection_summary = QLabel("0 segments selected")
        self.selection_summary.setStyleSheet("color: #666; font-size: 10px;")
        controls_layout.addWidget(self.selection_summary)

        layout.addLayout(controls_layout)

    def _create_segment_export_options(self, layout: QVBoxLayout):
        """Create segment-specific export options."""
        options_group = QGroupBox("Segment Export Options")
        options_layout = QFormLayout(options_group)
        options_layout.setSpacing(8)

        # Segment export mode
        self.segment_mode_combo = QComboBox()
        self.segment_mode_combo.addItems([
            "Individual segments (separate folders)",
            "Combined sprite sheet per segment",
            "All frames (with segment prefixes)"
        ])
        self.segment_mode_combo.setToolTip("Choose how to organize exported segments")
        options_layout.addRow("Organization:", self.segment_mode_combo)

        # Include metadata
        self.include_metadata_check = QCheckBox()
        self.include_metadata_check.setChecked(True)
        self.include_metadata_check.setToolTip("Include JSON file with segment information")
        options_layout.addRow("Include Metadata:", self.include_metadata_check)

        layout.addWidget(options_group)

    def _connect_signals(self):
        """Connect internal signals."""
        if hasattr(self, 'segment_list'):
            self.segment_list.itemSelectionChanged.connect(self._on_selection_changed)

        if self.segment_manager:
            # Connect to segment manager signals if available (dynamic signal checking)
            if hasattr(self.segment_manager, 'segmentAdded'):
                self.segment_manager.segmentAdded.connect(self._update_segment_list)  # type: ignore[attr-defined]
            if hasattr(self.segment_manager, 'segmentRemoved'):
                self.segment_manager.segmentRemoved.connect(self._update_segment_list)  # type: ignore[attr-defined]

    def _update_segment_list(self):
        """Update the segment list display."""
        if not hasattr(self, 'segment_list') or not self.segment_manager:
            return

        self.segment_list.clear()
        segments = self.segment_manager.get_all_segments()

        for segment in segments:
            # Create display text
            item_text = f"{segment.name} (Frames {segment.start_frame}-{segment.end_frame})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, segment.name)

            # Set color based on segment color if available
            if hasattr(segment, 'color') and segment.color:
                item.setBackground(segment.color.lighter(160))

            self.segment_list.addItem(item)

        self._update_selection_summary()

    def _on_selection_changed(self):
        """Handle segment selection changes."""
        if not hasattr(self, 'segment_list'):
            return

        selected_items = self.segment_list.selectedItems()
        self._selected_segments = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

        # Update info display
        if selected_items and self.segment_manager:
            info_parts = []
            total_frames: int = 0

            for item in selected_items:
                segment_name = item.data(Qt.ItemDataRole.UserRole)
                segment = self.segment_manager.get_segment(segment_name)
                if segment:
                    frame_count = getattr(segment, 'frame_count',
                                        segment.end_frame - segment.start_frame + 1)
                    info_parts.append(
                        f"• {segment.name}: {frame_count} frames "
                        f"({segment.start_frame}-{segment.end_frame})"
                    )
                    total_frames += int(frame_count)

            info_parts.append(f"\nTotal: {total_frames} frames")
            self.segment_info.setText("\n".join(info_parts))
        else:
            self.segment_info.clear()

        self._update_selection_summary()
        self.segmentSelectionChanged.emit(self._selected_segments)

    def _select_all_segments(self):
        """Select all available segments."""
        if hasattr(self, 'segment_list'):
            self.segment_list.selectAll()

    def _clear_selection(self):
        """Clear segment selection."""
        if hasattr(self, 'segment_list'):
            self.segment_list.clearSelection()

    def _update_selection_summary(self):
        """Update the selection summary label."""
        if not hasattr(self, 'selection_summary'):
            return

        selected_count = len(self._selected_segments)
        total_count = self.segment_list.count() if hasattr(self, 'segment_list') else 0

        self.selection_summary.setText(f"{selected_count} of {total_count} segments selected")

    def get_selected_segments(self) -> list[str]:
        """Get list of selected segment names."""
        return self._selected_segments.copy()

    def get_export_settings(self) -> dict[str, Any]:
        """Get export settings for animation segments."""
        if not hasattr(self, 'segment_mode_combo'):
            return {}

        return {
            'selected_segments': self.get_selected_segments(),
            'segment_mode': self.segment_mode_combo.currentText(),
            'segment_mode_index': self.segment_mode_combo.currentIndex(),
            'include_metadata': getattr(self.include_metadata_check, 'isChecked', lambda: False)(),
        }

    def has_segments(self) -> bool:
        """Check if any segments are available."""
        return (self.segment_manager is not None and
                bool(self.segment_manager.get_all_segments()))

    def has_selected_segments(self) -> bool:
        """Check if any segments are selected."""
        return bool(self._selected_segments)


# Convenience function for easy integration
def create_segment_selector(segment_manager: AnimationSegmentManager | None = None) -> AnimationSegmentSelector:
    """Create an animation segment selector widget."""
    return AnimationSegmentSelector(segment_manager)
