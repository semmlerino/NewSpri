"""
Export Dialog Wizard with Integrated Settings and Preview
Simplified two-step wizard with live preview functionality.
"""

import logging
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout

from config import Config

from .base.wizard_base import WizardWidget
from .modern_settings_preview import ModernExportSettings
from .type_selection import ExportTypeStepSimple as ExportTypeStep

logger = logging.getLogger(__name__)


class ExportDialog(QDialog):
    """
    Integrated export dialog with live preview.
    Two steps: Type selection -> Settings with live preview.
    """

    # Signals
    exportRequested = Signal(dict)  # Emitted when export is requested (for compatibility)

    def __init__(
        self,
        parent=None,
        frame_count: int = 0,
        current_frame: int = 0,
        sprites: list[QPixmap] | None = None,
        segment_manager=None,
    ):
        super().__init__(parent)

        self.frame_count = frame_count
        self.current_frame = current_frame
        self.sprites = sprites or []
        self.segment_manager = segment_manager  # Store for compatibility

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
        self.wizard = WizardWidget()
        layout.addWidget(self.wizard)

        # Connect wizard signals
        self.wizard.wizardFinished.connect(self._on_wizard_finished)
        self.wizard.wizardCancelled.connect(self.reject)

    def _setup_wizard(self):
        """Set up wizard steps."""
        # Step 1: Export type selection
        self.type_step = ExportTypeStep(
            frame_count=self.frame_count, segment_manager=self.segment_manager, parent=self.wizard
        )
        self.wizard.add_step(self.type_step)

        # Step 2: Settings with live preview
        self.settings_preview_step = ModernExportSettings(
            frame_count=self.frame_count,
            current_frame=self.current_frame,
            sprites=self.sprites,
            segment_manager=self.segment_manager,
            parent=self.wizard,
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
        self.wizard._on_finish()

    def _on_wizard_finished(self, data: dict[str, Any]):
        """Handle wizard completion - emit export request and close."""
        logger.debug("_on_wizard_finished called")

        # Extract data from wizard steps
        preset = data.get("step_0", {}).get("preset")
        settings = data.get("step_1", {})

        if not preset:
            QMessageBox.warning(self, "Export Error", "No export type selected.")
            return

        # Prepare export configuration
        export_config = self._prepare_export_config(preset, settings)

        # Include selected_indices for 'selected' mode
        if preset.mode == "selected":
            export_config["selected_indices"] = settings.get("selected_indices", [])

        # Emit exportRequested for coordinator to handle export execution
        self.exportRequested.emit(export_config)

        # Close dialog - coordinator will handle export and show progress
        self.accept()

    def _prepare_export_config(self, preset, settings) -> dict[str, Any]:
        """Prepare export configuration from settings."""
        config = {
            "output_dir": settings.get("output_dir", ""),
            "format": settings.get("format", "PNG"),
            "scale": settings.get("scale", 1.0),
            "scale_factor": settings.get("scale", 1.0),  # Export handler expects scale_factor
            "pattern": settings.get("pattern", Config.Export.DEFAULT_PATTERN),
            "quality": settings.get("quality", 95),
            "background_mode": settings.get("background_mode", "transparent"),
            "background_color": settings.get("background_color", (255, 255, 255, 255)),
            "mode": preset.mode,  # Add mode for export handler
        }

        # Add base_name for all export types
        if preset.mode == "sheet" or preset.mode == "segments_sheet":
            # For sprite sheets, use single_filename as base_name
            config["base_name"] = settings.get("single_filename", "spritesheet")
            config.update(
                {
                    "layout_mode": settings.get("layout_mode", "auto"),
                    "columns": settings.get("columns", 8),
                    "rows": settings.get("rows", 8),
                    "spacing": settings.get("spacing", 0),
                    "padding": settings.get("padding", 0),
                    "single_filename": settings.get("single_filename", "spritesheet"),
                }
            )
            # Special handling for segments per row
            if preset.mode == "segments_sheet":
                config["sprite_sheet_layout"] = preset.sprite_sheet_layout
        else:
            # For individual/selected frames
            config["base_name"] = settings.get("base_name", "frame")

        return config

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

    def showEvent(self, event):
        """Handle dialog show event."""
        super().showEvent(event)
        # Ensure wizard starts at first step
        self.wizard.set_current_step(0)

    def set_sprites(self, sprites: list[QPixmap]):
        """Set sprite frames for export. Compatible with legacy API."""
        self.sprites = sprites or []
        # Update the settings step if it exists
        if hasattr(self, "settings_preview_step") and self.settings_preview_step:
            self.settings_preview_step.set_sprites(self.sprites)
