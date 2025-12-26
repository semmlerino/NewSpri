"""
Export Type Selection Step (Simplified)
Clean, simple export type selection without clutter.
"""

import logging
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QButtonGroup, QFrame, QLabel, QRadioButton, QVBoxLayout, QWidget

from ..core.export_presets import ExportPreset, get_preset_manager
from ..dialogs.base.wizard_base import WizardStep

logger = logging.getLogger(__name__)


class SimpleExportOption(QFrame):
    """Simple, clean export option widget."""

    clicked = Signal()

    def __init__(self, preset: ExportPreset, parent=None):
        super().__init__(parent)
        self.preset = preset
        self._is_selected = False
        self._radio_button = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the simple option UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # Radio button with icon and title
        title_text = f"{self.preset.icon} {self.preset.display_name}"
        self._radio_button = QRadioButton(title_text)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self._radio_button.setFont(title_font)
        layout.addWidget(self._radio_button)

        # Simple description
        desc_label = QLabel(self.preset.short_description or self.preset.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6c757d; margin-left: 23px;")
        layout.addWidget(desc_label)

        # Use cases (compact)
        if self.preset.use_cases and len(self.preset.use_cases) > 0:
            uses_text = "Best for: " + ", ".join(self.preset.use_cases[:3])
            uses_label = QLabel(uses_text)
            uses_label.setWordWrap(True)
            uses_label.setStyleSheet("color: #6c757d; font-size: 10px; margin-left: 23px;")
            layout.addWidget(uses_label)

        self._update_style()

    def _update_style(self):
        """Update frame style based on selection."""
        if self._is_selected:
            self.setStyleSheet("""
                SimpleExportOption {
                    background-color: #e7f3ff;
                    border: 2px solid #007bff;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                SimpleExportOption {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                }
                SimpleExportOption:hover {
                    background-color: #f8f9fa;
                    border: 1px solid #007bff;
                }
            """)

    def set_selected(self, selected: bool):
        """Set selection state."""
        self._is_selected = selected
        if self._radio_button is not None:
            self._radio_button.setChecked(selected)
        self._update_style()

    def mousePressEvent(self, event):
        """Handle mouse press to select option."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ExportTypeStepSimple(WizardStep):
    """
    Simplified export type selection step.
    Clean, focused interface without clutter.
    """

    # Signal emitted when a preset is selected
    presetSelected = Signal(ExportPreset)

    def __init__(self, frame_count: int = 0, parent=None, segment_manager=None):
        super().__init__(
            title="Choose Export Type",
            subtitle="Select how you want to export your sprite frames",
            parent=parent
        )
        self.frame_count = frame_count
        self.segment_manager = segment_manager
        self._preset_manager = get_preset_manager()
        self._selected_preset: ExportPreset | None = None
        self._options: list[SimpleExportOption] = []
        self._button_group = QButtonGroup()
        self._has_segments = False

        self._setup_ui()

    def _setup_ui(self):
        """Set up the simplified UI."""
        logger.debug("ExportTypeStepSimple._setup_ui called")
        logger.debug("Frame count: %d", self.frame_count)
        logger.debug("Segment manager available: %s", self.segment_manager is not None)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Check if we have segments
        if self.segment_manager:
            segments = self.segment_manager.get_all_segments()
            self._has_segments = len(segments) > 0
            logger.debug("Found %d segments, has_segments = %s", len(segments), self._has_segments)
            for i, seg in enumerate(segments):
                logger.debug("  Segment %d: '%s' frames %d-%d", i, seg.name, seg.start_frame, seg.end_frame)
        else:
            logger.debug("No segment manager available")
            self._has_segments = False

        # Show recommendation if segments exist
        if self._has_segments:
            rec_frame = QFrame()
            rec_frame.setStyleSheet("""
                QFrame {
                    background-color: #e3f2fd;
                    border: 1px solid #2196f3;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            rec_layout = QVBoxLayout(rec_frame)
            rec_layout.setContentsMargins(12, 8, 12, 8)

            rec_label = QLabel("💡 <b>Animation segments detected!</b>")
            rec_label.setStyleSheet("color: #1976d2; font-size: 12px;")
            rec_layout.addWidget(rec_label)

            rec_desc = QLabel("We recommend using 'Segments Per Row' to export each animation as a separate row.")
            rec_desc.setWordWrap(True)
            rec_desc.setStyleSheet("color: #424242; font-size: 11px;")
            rec_layout.addWidget(rec_desc)

            layout.addWidget(rec_frame)

        # Main options
        options_widget = self._create_export_options()
        layout.addWidget(options_widget, 1)

        # Simple help text
        help_label = QLabel("Select an export type above to continue.")
        help_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(help_label)

    def _create_export_options(self) -> QWidget:
        """Create the export options list."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # Define which presets to show, prioritizing segments_per_row if segments exist
        if self._has_segments:
            # Put segments_per_row first when segments exist
            preset_names = [
                "segments_per_row",
                "sprite_sheet",
                "individual_frames",
                "selected_frames"
            ]
        else:
            # Normal order when no segments
            preset_names = [
                "individual_frames",
                "sprite_sheet",
                "selected_frames",
                "segments_per_row"
            ]

        # Create option widgets
        first_option = True
        for preset_name in preset_names:
            preset = self._preset_manager.get_preset(preset_name)
            if preset:
                option = SimpleExportOption(preset)
                option.clicked.connect(lambda p=preset: self._on_option_clicked(p))
                self._options.append(option)

                # Add visual emphasis to segments_per_row when segments exist
                if self._has_segments and preset_name == "segments_per_row":
                    option.setStyleSheet("""
                        SimpleExportOption {
                            border: 2px solid #2196f3;
                            background-color: #f5f5f5;
                        }
                        SimpleExportOption:hover {
                            background-color: #e3f2fd;
                        }
                    """)
                    # Pre-select it
                    if first_option and option._radio_button is not None:
                        option._radio_button.setChecked(True)
                        self._select_preset(preset)

                layout.addWidget(option)

                # Add radio button to group
                if option._radio_button is not None:
                    self._button_group.addButton(option._radio_button)
                first_option = False

        layout.addStretch()
        return container

    def _on_option_clicked(self, preset: ExportPreset):
        """Handle option selection."""
        logger.debug("Option clicked: %s (%s)", preset.name, preset.mode)
        self._select_preset(preset)

    def _select_preset(self, preset: ExportPreset):
        """Select a preset and update UI."""
        logger.debug("_select_preset called with: %s (%s)", preset.name, preset.mode)
        self._selected_preset = preset

        # Update option selection states
        for option in self._options:
            option.set_selected(option.preset == preset)

        # Emit signals
        logger.debug("Emitting stepValidated(True) and preset data")
        self.stepValidated.emit(True)
        self.dataChanged.emit(self.get_data())
        self.presetSelected.emit(preset)

    def validate(self) -> bool:
        """Validate that a preset is selected."""
        return self._selected_preset is not None

    def get_data(self) -> dict[str, Any]:
        """Get the selected preset data."""
        logger.debug("ExportTypeStep.get_data() called")
        logger.debug("Selected preset: %s", self._selected_preset.name if self._selected_preset else 'None')
        logger.debug("Selected preset mode: %s", self._selected_preset.mode if self._selected_preset else 'None')

        if self._selected_preset:
            data = {
                'preset': self._selected_preset,
                'preset_name': self._selected_preset.name,
                'export_mode': self._selected_preset.mode
            }
            logger.debug("Returning preset data: %s", data)
            return data

        logger.debug("No preset selected, returning empty dict")
        return {}

    def set_data(self, data: dict[str, Any]):
        """Set data (for going back in wizard)."""
        preset_name = data.get('preset_name')
        if preset_name:
            preset = self._preset_manager.get_preset(preset_name)
            if preset:
                self._select_preset(preset)


@dataclass
class EnhancedExportPreset(ExportPreset):
    """Enhanced export preset with additional metadata."""

    recommended_for: list[str] | None = None

    def __post_init__(self):
        if self.recommended_for is None:
            self.recommended_for = []
