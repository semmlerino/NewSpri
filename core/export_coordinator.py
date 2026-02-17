"""
Export Coordinator - Orchestrates export operations between UI and exporter.

Consolidates export logic that was previously split between SpriteViewer
and AnimationSegmentController.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from export.core.frame_exporter import (
    ExportConfig,
    ExportMode,
    FrameExporter,
    get_frame_exporter,
)
from export.dialogs.progress_dialog import ExportProgressDialog

if TYPE_CHECKING:
    from managers.animation_segment_manager import AnimationSegmentManager
    from sprite_model import SpriteModel


class ExportCoordinator(QObject):
    """
    Coordinates export operations between UI, model, and exporter.

    Handles:
    - Individual frame export
    - Sprite sheet export
    - Segment export (individual and batch)
    - Progress dialog management
    - Error/warning/info dialogs
    """

    # Signals for status reporting
    exportCompleted = Signal(str)  # success message
    exportFailed = Signal(str)  # error message

    def __init__(
        self,
        sprite_model: "SpriteModel",
        segment_manager: "AnimationSegmentManager | None",
        exporter: FrameExporter | None = None,
        parent: QWidget | None = None,
    ):
        """
        Initialize the export coordinator.

        Args:
            sprite_model: The sprite model containing frames
            segment_manager: Manager for animation segments (optional)
            exporter: Frame exporter instance (uses singleton if not provided)
            parent: Parent widget for dialogs
        """
        super().__init__(parent)
        self._sprite_model = sprite_model
        self._segment_manager = segment_manager
        self._exporter = exporter or get_frame_exporter()
        self._parent_widget = parent
        self._progress_dialog: ExportProgressDialog | None = None

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def validate_export(self) -> bool:
        """
        Validate that export can proceed.

        Returns:
            True if export can proceed, False otherwise
        """
        if not self._sprite_model or not self._sprite_model.sprite_frames:
            QMessageBox.warning(self._parent_widget, "No Frames", "No frames to export.")
            return False
        return True

    # -------------------------------------------------------------------------
    # Main Export Entry Point
    # -------------------------------------------------------------------------

    def _validate_mode_preconditions(self, config: ExportConfig) -> tuple[bool, str]:
        """
        Validate mode-specific preconditions before creating progress dialog.

        Args:
            config: Export configuration dataclass

        Returns:
            Tuple of (success, error_message). If success is False, error_message
            contains the warning to show the user.
        """
        # Check segment-specific preconditions
        if config.mode is ExportMode.SEGMENTS_SHEET:
            if not self._segment_manager:
                return False, "Segment manager not available."
            segments = self._segment_manager.get_all_segments()
            if not segments:
                return False, "No animation segments defined."

        # Check selected indices preconditions
        selected_indices = config.selected_indices or []
        if selected_indices:
            all_frames = self._sprite_model.sprite_frames
            valid_indices = [i for i in selected_indices if 0 <= i < len(all_frames)]
            if not valid_indices:
                return False, "No valid frames selected for export."

        return True, ""

    def handle_export_request(self, config: ExportConfig, frames: list | None = None) -> None:
        """Handle unified export request from dialog."""
        # Validate mode-specific preconditions
        valid, error_message = self._validate_mode_preconditions(config)
        if not valid:
            self._show_warning(error_message)
            return

        mode = config.mode

        # Determine export type name for progress dialog
        export_type_names = {
            ExportMode.INDIVIDUAL_FRAMES: "Individual Frames",
            ExportMode.SELECTED_FRAMES: "Selected Frames",
            ExportMode.SPRITE_SHEET: "Sprite Sheet",
            ExportMode.SEGMENTS_SHEET: "Segments Per Row Sheet",
        }
        export_type = export_type_names.get(mode, "Frames")

        # Get frame count for progress dialog
        frame_count = (
            len(frames)
            if frames is not None
            else (len(self._sprite_model.sprite_frames) if self._sprite_model.sprite_frames else 0)
        )

        # Create and configure progress dialog
        self._progress_dialog = ExportProgressDialog(
            export_type=export_type, total_frames=frame_count, parent=self._parent_widget
        )

        # Connect exporter signals
        self._exporter.exportProgress.connect(self._progress_dialog.update_progress)
        self._exporter.exportFinished.connect(self._on_export_finished)
        self._exporter.exportError.connect(self._on_export_error)
        self._progress_dialog.cancelled.connect(self._exporter.cancel_export)

        # Show progress dialog
        self._progress_dialog.show()

        # Route to appropriate export handler with guaranteed cleanup
        try:
            if mode is ExportMode.SEGMENTS_SHEET:
                self._export_segments_per_row(config)
            else:
                self._export_frames(config, frames=frames)
        except Exception:
            self._cleanup_progress_dialog()
            raise

    # -------------------------------------------------------------------------
    # Export Methods
    # -------------------------------------------------------------------------

    def _export_frames(self, config: ExportConfig, frames: list | None = None) -> None:
        """Handle standard frame export (individual or sheet)."""
        all_frames = frames if frames is not None else self._sprite_model.sprite_frames
        frames_to_export = all_frames
        export_mode = config.mode
        selected_indices = config.selected_indices or []

        if selected_indices:
            valid_indices = [i for i in selected_indices if 0 <= i < len(all_frames)]
            frames_to_export = [all_frames[i] for i in valid_indices]
            export_mode = ExportMode.INDIVIDUAL_FRAMES

            if len(valid_indices) != len(selected_indices):
                invalid_count = len(selected_indices) - len(valid_indices)
                self._show_info(
                    f"Exported {len(valid_indices)} frames. "
                    f"{invalid_count} invalid selection(s) skipped."
                )

        # Use sprite_sheet_layout from config (wizard already built it)
        sprite_sheet_layout = config.sprite_sheet_layout

        success = self._exporter.export_frames(
            frames=frames_to_export,
            output_dir=str(config.output_dir),
            base_name=config.base_name,
            format=config.format.value,
            mode=export_mode.value,
            scale_factor=config.scale_factor,
            pattern=config.pattern or None,
            selected_indices=selected_indices if selected_indices else None,
            sprite_sheet_layout=sprite_sheet_layout,
        )

        if not success:
            self._show_error("Failed to start export.")

    def _export_segments_per_row(self, config: ExportConfig) -> None:
        """Handle segments per row sprite sheet export."""
        assert self._segment_manager is not None  # validated by _validate_mode_preconditions
        segments = self._segment_manager.get_all_segments()
        segment_info = sorted(
            [
                {"name": s.name, "start_frame": s.start_frame, "end_frame": s.end_frame}
                for s in segments
            ],
            key=lambda x: x["start_frame"],
        )

        success = self._exporter.export_frames(
            frames=self._sprite_model.sprite_frames,
            output_dir=str(config.output_dir),
            base_name=config.base_name,
            format=config.format.value,
            mode=ExportMode.SEGMENTS_SHEET.value,
            scale_factor=config.scale_factor,
            sprite_sheet_layout=config.sprite_sheet_layout,
            segment_info=segment_info,
        )

        if not success:
            self._show_error("Failed to start segments per row export.")

    # -------------------------------------------------------------------------
    # Signal Handlers
    # -------------------------------------------------------------------------

    def _on_export_finished(self, success: bool, message: str) -> None:
        """Handle export completion."""
        self._cleanup_progress_dialog()

        if success:
            QMessageBox.information(
                self._parent_widget,
                "Export Complete",
                f"Export completed successfully!\n\n{message}",
            )
            self.exportCompleted.emit(message)
        else:
            QMessageBox.warning(
                self._parent_widget,
                "Export Failed",
                f"Export failed:\n\n{message}",
            )
            self.exportFailed.emit(message)

    def _on_export_error(self, error_message: str) -> None:
        """Handle export error."""
        self._cleanup_progress_dialog()

        QMessageBox.critical(
            self._parent_widget,
            "Export Error",
            f"Export failed:\n\n{error_message}",
        )
        self.exportFailed.emit(error_message)

    def _cleanup_progress_dialog(self) -> None:
        """Disconnect signals and close progress dialog."""
        if self._progress_dialog:
            try:
                self._exporter.exportProgress.disconnect(self._progress_dialog.update_progress)
                self._exporter.exportFinished.disconnect(self._on_export_finished)
                self._exporter.exportError.disconnect(self._on_export_error)
            except RuntimeError:
                pass  # Signals may already be disconnected
            self._progress_dialog.close()
            self._progress_dialog = None

    # -------------------------------------------------------------------------
    # UI Feedback
    # -------------------------------------------------------------------------

    def _show_error(self, message: str) -> None:
        """Show export error message box."""
        QMessageBox.critical(self._parent_widget, "Export Error", message)

    def _show_warning(self, message: str) -> None:
        """Show export warning message box."""
        QMessageBox.warning(self._parent_widget, "Export Warning", message)

    def _show_info(self, message: str) -> None:
        """Show export information message box."""
        QMessageBox.information(self._parent_widget, "Export Info", message)
