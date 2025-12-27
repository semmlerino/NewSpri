"""
Export Coordinator - Orchestrates export operations between UI and exporter.

Consolidates export logic that was previously split between SpriteViewer
and AnimationSegmentController.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from export.core.frame_exporter import (
    FrameExporter,
    SpriteSheetLayout,
    get_frame_exporter,
)
from export.dialogs.progress_dialog import ExportProgressDialog

if TYPE_CHECKING:
    from PySide6.QtGui import QPixmap

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
            QMessageBox.warning(
                self._parent_widget, "No Frames", "No frames to export."
            )
            return False
        return True

    # -------------------------------------------------------------------------
    # Main Export Entry Point
    # -------------------------------------------------------------------------

    def handle_export_request(self, settings: dict[str, Any]) -> None:
        """
        Handle unified export request from dialog.

        Routes to appropriate export method based on mode in settings.

        Args:
            settings: Export settings dictionary with keys:
                - mode: 'individual', 'selected', 'sheet', 'segments', 'segments_sheet'
                - output_dir: Output directory path
                - base_name: Base filename
                - format: Export format (png, jpg, etc.)
                - scale_factor: Scale multiplier
                - And mode-specific options
        """
        mode = settings.get("mode", "")

        # Determine export type name for progress dialog
        export_type_names = {
            "individual": "Individual Frames",
            "selected": "Selected Frames",
            "sheet": "Sprite Sheet",
            "segments": "Animation Segments",
            "segments_sheet": "Segments Per Row Sheet",
        }
        export_type = export_type_names.get(mode, "Frames")

        # Get frame count for progress dialog
        frame_count = (
            len(self._sprite_model.sprite_frames)
            if self._sprite_model.sprite_frames
            else 0
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

        # Route to appropriate export handler
        if mode == "segments" and "selected_segments" in settings:
            self._export_segments(settings)
        elif mode == "segments_sheet":
            self._export_segments_per_row(settings)
        else:
            self._export_frames(settings)

    # -------------------------------------------------------------------------
    # Export Methods
    # -------------------------------------------------------------------------

    def _export_frames(self, settings: dict[str, Any]) -> None:
        """Handle standard frame export (individual or sheet)."""
        required_keys = ["output_dir", "base_name", "format", "mode", "scale_factor"]
        for key in required_keys:
            if key not in settings:
                self._show_error(f"Missing required setting: {key}")
                return

        if not self._sprite_model.sprite_frames:
            self._show_warning("No frames available to export.")
            return

        all_frames = self._sprite_model.sprite_frames
        frames_to_export = all_frames
        export_mode = settings["mode"]
        selected_indices = settings.get("selected_indices", [])

        if selected_indices:
            valid_indices = [i for i in selected_indices if 0 <= i < len(all_frames)]
            if not valid_indices:
                self._show_warning("No valid frames selected for export.")
                return

            frames_to_export = [all_frames[i] for i in valid_indices]
            export_mode = "individual"

            if len(valid_indices) != len(selected_indices):
                invalid_count = len(selected_indices) - len(valid_indices)
                self._show_info(
                    f"Exported {len(valid_indices)} frames. "
                    f"{invalid_count} invalid selection(s) skipped."
                )

        # Create sprite sheet layout if mode is 'sheet' and layout not provided
        sprite_sheet_layout = settings.get("sprite_sheet_layout")
        if export_mode == "sheet" and sprite_sheet_layout is None:
            layout_mode = settings.get("layout_mode", "auto")
            sprite_sheet_layout = SpriteSheetLayout(
                mode=layout_mode,
                spacing=settings.get("spacing", 0),
                padding=settings.get("padding", 0),
                max_columns=settings.get("columns", 8) if layout_mode == "rows" else None,
                max_rows=settings.get("rows", 8) if layout_mode == "columns" else None,
                custom_columns=settings.get("columns", 8) if layout_mode == "custom" else None,
                custom_rows=settings.get("rows", 8) if layout_mode == "custom" else None,
                background_mode=settings.get("background_mode", "transparent"),
                background_color=settings.get("background_color", (255, 255, 255, 255)),
            )

        success = self._exporter.export_frames(
            frames=frames_to_export,
            output_dir=settings["output_dir"],
            base_name=settings["base_name"],
            format=settings["format"],
            mode=export_mode,
            scale_factor=settings["scale_factor"],
            pattern=settings.get("pattern"),
            selected_indices=selected_indices if selected_indices else None,
            sprite_sheet_layout=sprite_sheet_layout,
        )

        if not success:
            self._show_error("Failed to start export.")

    def _export_segments_per_row(self, settings: dict[str, Any]) -> None:
        """Handle segments per row sprite sheet export."""
        if not self._sprite_model.sprite_frames:
            self._show_warning("No frames available to export.")
            return

        if not self._segment_manager:
            self._show_error("Segment manager not available.")
            return

        segments = self._segment_manager.get_all_segments()
        if not segments:
            self._show_warning("No animation segments defined.")
            return

        segment_info = sorted(
            [
                {"name": s.name, "start_frame": s.start_frame, "end_frame": s.end_frame}
                for s in segments
            ],
            key=lambda x: x["start_frame"],
        )

        success = self._exporter.export_frames(
            frames=self._sprite_model.sprite_frames,
            output_dir=settings["output_dir"],
            base_name=settings["base_name"],
            format=settings["format"],
            mode="segments_sheet",
            scale_factor=settings["scale_factor"],
            sprite_sheet_layout=settings.get("sprite_sheet_layout"),
            segment_info=segment_info,
        )

        if not success:
            self._show_error("Failed to start segments per row export.")

    def _export_segments(self, settings: dict[str, Any]) -> None:
        """Handle animation segment export (batch export of selected segments)."""
        selected_segments = settings.get("selected_segments", [])

        if not selected_segments:
            self._show_warning("No animation segments selected for export.")
            return

        if not self._sprite_model.sprite_frames:
            self._show_warning("No frames available to export.")
            return

        if not self._segment_manager:
            self._show_error("Segment manager not available.")
            return

        all_frames = self._sprite_model.sprite_frames

        for segment_name in selected_segments:
            segment = self._segment_manager.get_segment(segment_name)
            if not segment:
                continue

            segment_frames = self._segment_manager.extract_frames_for_segment(
                segment_name, all_frames
            )
            if not segment_frames:
                continue

            base_output_dir = settings["output_dir"]
            segment_output_dir = Path(base_output_dir) / segment_name
            segment_output_dir.mkdir(parents=True, exist_ok=True)

            mode_index = settings.get("mode_index", 0)

            if mode_index == 0:  # Individual segments (separate folders)
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(segment_output_dir),
                    base_name=settings.get("base_name", segment_name),
                    format=settings["format"],
                    mode="individual",
                    scale_factor=settings["scale_factor"],
                )
            elif mode_index == 1:  # Combined sprite sheet
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(segment_output_dir),
                    base_name=f"{segment_name}_sheet",
                    format=settings["format"],
                    mode="sheet",
                    scale_factor=settings["scale_factor"],
                )
            else:  # All frames (with segment prefixes)
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(base_output_dir),
                    base_name=f"{settings.get('base_name', 'frame')}_{segment_name}",
                    format=settings["format"],
                    mode="individual",
                    scale_factor=settings["scale_factor"],
                )

            if not success:
                self._show_error(f"Failed to export segment '{segment_name}'.")

    def export_single_segment(
        self,
        segment_name: str,
        frames: "list[QPixmap]",
        settings: dict[str, Any],
    ) -> bool:
        """
        Export a single segment with provided frames.

        Used by AnimationSegmentController for context menu exports.

        Args:
            segment_name: Name of the segment
            frames: List of QPixmap frames to export
            settings: Export settings dictionary

        Returns:
            True if export started successfully
        """
        required = {"output_dir", "base_name", "format", "mode", "scale_factor"}
        if not frames or not required.issubset(settings):
            return False

        return self._exporter.export_frames(
            frames=frames,
            output_dir=settings["output_dir"],
            base_name=f"{settings['base_name']}_{segment_name}",
            format=settings["format"],
            mode=settings["mode"],
            scale_factor=settings["scale_factor"],
            pattern=settings.get("pattern"),
            sprite_sheet_layout=settings.get("sprite_sheet_layout"),
        )

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
                self._exporter.exportProgress.disconnect(
                    self._progress_dialog.update_progress
                )
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
