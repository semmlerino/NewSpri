"""
Export Dialog Wizard with Integrated Settings and Preview
Simplified two-step wizard with live preview functionality.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap, QShowEvent
from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from collections.abc import Sequence

    from managers.animation_segment_manager import AnimationSegmentManager
    from managers.settings_manager import SettingsManager

from config import Config

from ..core.export_presets import ExportPreset
from ..core.frame_exporter import (
    BackgroundMode,
    ExportConfig,
    ExportFormat,
    ExportMode,
    LayoutMode,
    SpriteSheetLayout,
)
from .base.wizard_base import _WizardWidget
from .modern_settings_preview import _ModernExportSettings
from .type_selection import _ExportTypeStep

logger = logging.getLogger(__name__)


class ExportDialog(QDialog):
    """
    Integrated export dialog with live preview.
    Two steps: Type selection -> Settings with live preview.
    """

    # Signals
    exportRequested = Signal(object)  # Emitted when export is requested

    def __init__(
        self,
        parent: QWidget | None = None,
        frame_count: int = 0,
        current_frame: int = 0,
        sprites: "Sequence[QPixmap] | None" = None,
        segment_manager: "AnimationSegmentManager | None" = None,
        settings_manager: "SettingsManager | None" = None,
    ):
        super().__init__(parent)

        self.frame_count = frame_count
        self.current_frame = current_frame
        self.sprites: list[QPixmap] = list(sprites) if sprites else []
        self.segment_manager = segment_manager  # Store for compatibility
        self._settings_manager = settings_manager

        # Dialog settings
        self.setWindowTitle("Export Sprites")
        self.setModal(True)
        self.resize(900, 650)  # Optimized for modern compact layout

        # Initialize wizard
        self._setup_ui()
        self._setup_wizard()

        # Center on screen
        self._center_on_screen()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create wizard widget
        self.wizard = _WizardWidget()
        layout.addWidget(self.wizard)

        # Connect wizard signals
        self.wizard.wizardFinished.connect(self._on_wizard_finished)
        self.wizard.wizardCancelled.connect(self.reject)

    def _setup_wizard(self):
        """Set up wizard steps."""
        # Step 1: Export type selection
        self.type_step = _ExportTypeStep(
            frame_count=self.frame_count, segment_manager=self.segment_manager, parent=self.wizard
        )
        self.wizard.add_step(self.type_step)

        # Step 2: Settings with live preview
        self.settings_preview_step = _ModernExportSettings(
            frame_count=self.frame_count,
            current_frame=self.current_frame,
            sprites=self.sprites,
            segment_manager=self.segment_manager,
            parent=self.wizard,
            settings_manager=self._settings_manager,
        )
        self.wizard.add_step(self.settings_preview_step)

        # Connect export button directly
        self.settings_preview_step.export_btn.clicked.connect(self._on_export_clicked)

    def _on_export_clicked(self):
        """Handle export button click."""
        logger.debug("Export button clicked")
        logger.debug("Segment manager available: %s", self.segment_manager is not None)
        if self.segment_manager:
            segments = self.segment_manager.get_all_segments()
            logger.debug("Number of segments available: %d", len(segments))
            for i, seg in enumerate(segments):
                logger.debug(
                    "  Segment %d: '%s' frames %d-%d", i, seg.name, seg.start_frame, seg.end_frame
                )

        # Trigger wizard finish to collect all data
        logger.debug("Triggering wizard finish to collect data")
        self.wizard.finish()

    def _on_wizard_finished(self, data: dict[str, Any]):
        """Handle wizard completion - emit export request and close."""
        logger.debug("_on_wizard_finished called")

        preset = data.get("step_0", {}).get("preset")
        settings = data.get("step_1", {})

        if not preset:
            QMessageBox.warning(self, "Export Error", "No export type selected.")
            return

        export_config = self._prepare_export_config(preset, settings)
        self.exportRequested.emit(export_config)
        self.accept()

    def _prepare_export_config(
        self, preset: ExportPreset, settings: dict[str, Any]
    ) -> ExportConfig:
        """Prepare typed export configuration from wizard settings."""
        format_str = settings.get("format", "PNG")
        try:
            export_format = ExportFormat.from_string(format_str)
        except (ValueError, KeyError):
            export_format = ExportFormat.PNG

        scale = settings.get("scale", 1.0)

        # Build sprite_sheet_layout for sheet modes
        sprite_sheet_layout = None
        if preset.mode in (ExportMode.SPRITE_SHEET, ExportMode.SEGMENTS_SHEET):
            if preset.mode is ExportMode.SEGMENTS_SHEET:
                sprite_sheet_layout = preset.sprite_sheet_layout
            else:
                layout_mode = settings.get("layout_mode", LayoutMode.AUTO)
                bg_mode = settings.get("background_mode", BackgroundMode.TRANSPARENT)

                sprite_sheet_layout = SpriteSheetLayout(
                    mode=layout_mode,
                    spacing=settings.get("spacing", 0),
                    max_columns=settings.get("columns", 8)
                    if layout_mode is LayoutMode.ROWS
                    else None,
                    max_rows=settings.get("rows", 8) if layout_mode is LayoutMode.COLUMNS else None,
                    custom_columns=settings.get("columns", 8)
                    if layout_mode is LayoutMode.CUSTOM
                    else None,
                    custom_rows=settings.get("rows", 8)
                    if layout_mode is LayoutMode.CUSTOM
                    else None,
                    background_mode=bg_mode,
                    background_color=settings.get("background_color", (255, 255, 255, 255)),
                )

        # Determine base_name
        if preset.mode in (ExportMode.SPRITE_SHEET, ExportMode.SEGMENTS_SHEET):
            base_name = settings.get("single_filename", "spritesheet")
        else:
            base_name = settings.get("base_name", "frame")

        # Get selected indices
        selected_indices = None
        if preset.mode is ExportMode.SELECTED_FRAMES:
            selected_indices = settings.get("selected_indices", [])

        return ExportConfig(
            output_dir=Path(settings.get("output_dir", "")),
            base_name=base_name,
            format=export_format,
            mode=preset.mode,
            scale_factor=float(scale),
            pattern=settings.get("pattern", Config.Export.DEFAULT_PATTERN),
            sprite_sheet_layout=sprite_sheet_layout,
            selected_indices=selected_indices,
        )

    def _center_on_screen(self):
        """Center the dialog on screen."""
        from PySide6.QtWidgets import QApplication

        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            dialog_rect = self.frameGeometry()
            center_point = screen_rect.center()
            dialog_rect.moveCenter(center_point)
            self.move(dialog_rect.topLeft())

    def showEvent(self, event: QShowEvent):
        """Handle dialog show event."""
        super().showEvent(event)
        # Ensure wizard starts at first step
        self.wizard.set_current_step(0)
