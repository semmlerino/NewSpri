"""
Export Coordinator for SpriteViewer.
Handles export dialog creation, validation, and direct export execution.
"""

from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog, QLabel, QMessageBox, QProgressBar, QPushButton, QVBoxLayout

from .core.frame_exporter import SpriteSheetLayout, get_frame_exporter
from .dialogs.export_wizard import ExportDialog


class ExportProgressDialog(QDialog):
    """Simple progress dialog for export operations."""

    cancelled = Signal()

    def __init__(self, export_type: str, total_frames: int, parent=None):
        super().__init__(parent)

        self.total_frames = total_frames
        self.current_frame = 0

        self.setWindowTitle("Exporting...")
        self.setModal(True)
        self.setFixedSize(400, 150)

        # Setup UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Export type label
        self.type_label = QLabel(f"Exporting {export_type}")
        font = self.type_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.type_label.setFont(font)
        layout.addWidget(self.type_label)

        # Progress label
        self.progress_label = QLabel("Preparing export...")
        layout.addWidget(self.progress_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(total_frames)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)

    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress display."""
        self.current_frame = current
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

        if message:
            self.progress_label.setText(message)
        else:
            self.progress_label.setText(f"Processing frame {current} of {total}")

    def _on_cancel(self):
        """Handle cancel button."""
        self.cancelled.emit()
        self.reject()


class ExportCoordinator(QObject):
    """
    Coordinator responsible for export operations.

    Manages export dialog creation, frame/segment export handling,
    and coordination between sprite model and segment manager.
    """

    # Signals
    exportRequested = Signal(dict)  # Emitted when export is requested with config

    def __init__(self, main_window):
        """Initialize export coordinator."""
        super().__init__()
        self.main_window = main_window
        self._initialized = False
        self._exporter = get_frame_exporter()
        self._progress_dialog: ExportProgressDialog | None = None

        # Component references
        self.sprite_model = None
        self.segment_manager = None

    def initialize(self, dependencies):
        """
        Initialize coordinator with required dependencies.

        Args:
            dependencies: Dict containing:
                - sprite_model: SpriteModel instance
                - segment_manager: AnimationSegmentManager instance
        """
        self.sprite_model = dependencies['sprite_model']
        self.segment_manager = dependencies['segment_manager']

        self._initialized = True

    @property
    def is_ready(self) -> bool:
        """Check if coordinator has been initialized with required dependencies."""
        return self._initialized

    # ============================================================================
    # EXPORT OPERATIONS
    # ============================================================================

    def export_frames(self):
        """Show enhanced export dialog for exporting frames and animation segments."""
        if not self._validate_export():
            return

        # Emit signal to notify export has been requested
        self.exportRequested.emit({'mode': 'all_frames'})

        # sprite_model guaranteed non-None after _validate_export() succeeds
        assert self.sprite_model is not None

        dialog = self._create_export_dialog()

        # Set sprites for visual preview (Phase 4 enhancement)
        dialog.set_sprites(self.sprite_model.sprite_frames)

        dialog.exportRequested.connect(self._handle_export_request)
        dialog.exec()

    def export_current_frame(self):
        """Export only the current frame."""
        if not self._validate_export():
            return

        # Emit signal to notify export has been requested
        self.exportRequested.emit({'mode': 'current_frame'})

        # sprite_model guaranteed non-None after _validate_export() succeeds
        assert self.sprite_model is not None

        dialog = self._create_export_dialog()

        # Set sprites for visual preview (Phase 4 enhancement)
        dialog.set_sprites(self.sprite_model.sprite_frames)

        # The new dialog will automatically handle single frame export via presets
        dialog.exportRequested.connect(self._handle_export_request)
        dialog.exec()

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _validate_export(self) -> bool:
        """
        Validate that export can proceed.

        Returns:
            bool: True if export can proceed, False otherwise
        """
        if not self.sprite_model or not self.sprite_model.sprite_frames:
            QMessageBox.warning(
                self.main_window,
                "No Frames",
                "No frames to export."
            )
            return False
        return True

    def _create_export_dialog(self) -> ExportDialog:
        """
        Create and configure export dialog.

        Returns:
            ExportDialog: Configured export dialog
        """
        # Callers must validate sprite_model before calling this method
        assert self.sprite_model is not None
        return ExportDialog(
            self.main_window,
            frame_count=len(self.sprite_model.sprite_frames),
            current_frame=self.sprite_model.current_frame,
            segment_manager=self.segment_manager
        )

    def _handle_export_request(self, settings: dict[str, Any]):
        """
        Handle unified export request from dialog.

        Args:
            settings: Export settings dictionary
        """
        mode = settings.get('mode', '')

        # Determine export type name for progress dialog
        export_type_names = {
            'individual': 'Individual Frames',
            'selected': 'Selected Frames',
            'sheet': 'Sprite Sheet',
            'segments': 'Animation Segments',
            'segments_sheet': 'Segments Per Row Sheet',
        }
        export_type = export_type_names.get(mode, 'Frames')

        # Get frame count for progress dialog
        frame_count = 0
        if self.sprite_model and self.sprite_model.sprite_frames:
            frame_count = len(self.sprite_model.sprite_frames)

        # Create and configure progress dialog
        self._progress_dialog = ExportProgressDialog(
            export_type=export_type,
            total_frames=frame_count,
            parent=self.main_window
        )

        # Connect exporter signals
        self._exporter.exportProgress.connect(self._progress_dialog.update_progress)
        self._exporter.exportFinished.connect(self._on_export_finished)
        self._exporter.exportError.connect(self._on_export_error)
        self._progress_dialog.cancelled.connect(self._exporter.cancel_export)

        # Show progress dialog
        self._progress_dialog.show()

        # Route to appropriate export handler
        if mode == 'segments' and 'selected_segments' in settings:
            self._export_segments(settings)
        elif mode == 'segments_sheet':
            self._export_segments_per_row(settings)
        else:
            self._export_frames(settings)

    def _export_frames(self, settings: dict[str, Any]):
        """Handle standard frame export."""
        required_keys = ['output_dir', 'base_name', 'format', 'mode', 'scale_factor']
        for key in required_keys:
            if key not in settings:
                self._show_error(f"Missing required setting: {key}")
                return

        if not self.sprite_model or not self.sprite_model.sprite_frames:
            self._show_warning("No frames available to export.")
            return

        all_frames = self.sprite_model.sprite_frames
        frames_to_export = all_frames
        export_mode = settings['mode']
        selected_indices = settings.get('selected_indices', [])

        if selected_indices:
            valid_indices = [i for i in selected_indices if 0 <= i < len(all_frames)]
            if not valid_indices:
                self._show_warning("No valid frames selected for export.")
                return

            frames_to_export = [all_frames[i] for i in valid_indices]
            export_mode = 'individual'

            if len(valid_indices) != len(selected_indices):
                invalid_count = len(selected_indices) - len(valid_indices)
                self._show_info(
                    f"Exported {len(valid_indices)} frames. "
                    f"{invalid_count} invalid selection(s) skipped."
                )

        # Create sprite sheet layout if mode is 'sheet' and layout not provided
        sprite_sheet_layout = settings.get('sprite_sheet_layout')
        if export_mode == 'sheet' and sprite_sheet_layout is None:
            layout_mode = settings.get('layout_mode', 'auto')
            sprite_sheet_layout = SpriteSheetLayout(
                mode=layout_mode,
                spacing=settings.get('spacing', 0),
                padding=settings.get('padding', 0),
                max_columns=settings.get('columns', 8) if layout_mode == 'rows' else None,
                max_rows=settings.get('rows', 8) if layout_mode == 'columns' else None,
                custom_columns=settings.get('columns', 8) if layout_mode == 'custom' else None,
                custom_rows=settings.get('rows', 8) if layout_mode == 'custom' else None,
                background_mode=settings.get('background_mode', 'transparent'),
                background_color=settings.get('background_color', (255, 255, 255, 255))
            )

        success = self._exporter.export_frames(
            frames=frames_to_export,
            output_dir=settings['output_dir'],
            base_name=settings['base_name'],
            format=settings['format'],
            mode=export_mode,
            scale_factor=settings['scale_factor'],
            pattern=settings.get('pattern'),
            selected_indices=selected_indices if selected_indices else None,
            sprite_sheet_layout=sprite_sheet_layout,
        )

        if not success:
            self._show_error("Failed to start export.")

    def _export_segments_per_row(self, settings: dict[str, Any]):
        """Handle segments per row sprite sheet export."""
        if not self.sprite_model or not self.sprite_model.sprite_frames:
            self._show_warning("No frames available to export.")
            return

        if not self.segment_manager:
            self._show_error("Segment manager not available.")
            return

        segments = self.segment_manager.get_all_segments()
        if not segments:
            self._show_warning("No animation segments defined.")
            return

        segment_info = sorted(
            [{'name': s.name, 'start_frame': s.start_frame, 'end_frame': s.end_frame}
             for s in segments],
            key=lambda x: x['start_frame']
        )

        success = self._exporter.export_frames(
            frames=self.sprite_model.sprite_frames,
            output_dir=settings['output_dir'],
            base_name=settings['base_name'],
            format=settings['format'],
            mode='segments_sheet',
            scale_factor=settings['scale_factor'],
            sprite_sheet_layout=settings.get('sprite_sheet_layout'),
            segment_info=segment_info,
        )

        if not success:
            self._show_error("Failed to start segments per row export.")

    def _export_segments(self, settings: dict[str, Any]):
        """Handle animation segment export."""
        selected_segments = settings.get('selected_segments', [])

        if not selected_segments:
            self._show_warning("No animation segments selected for export.")
            return

        if not self.sprite_model or not self.sprite_model.sprite_frames:
            self._show_warning("No frames available to export.")
            return

        if not self.segment_manager:
            self._show_error("Segment manager not available.")
            return

        all_frames = self.sprite_model.sprite_frames

        for segment_name in selected_segments:
            segment = self.segment_manager.get_segment(segment_name)
            if not segment:
                continue

            segment_frames = self.segment_manager.extract_frames_for_segment(
                segment_name, all_frames
            )
            if not segment_frames:
                continue

            base_output_dir = settings['output_dir']
            segment_output_dir = Path(base_output_dir) / segment_name
            segment_output_dir.mkdir(parents=True, exist_ok=True)

            mode_index = settings.get('mode_index', 0)

            if mode_index == 0:  # Individual segments (separate folders)
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(segment_output_dir),
                    base_name=settings.get('base_name', segment_name),
                    format=settings['format'],
                    mode='individual',
                    scale_factor=settings['scale_factor'],
                )
            elif mode_index == 1:  # Combined sprite sheet
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(segment_output_dir),
                    base_name=f"{segment_name}_sheet",
                    format=settings['format'],
                    mode='sheet',
                    scale_factor=settings['scale_factor'],
                )
            else:  # All frames (with segment prefixes)
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(base_output_dir),
                    base_name=f"{settings.get('base_name', 'frame')}_{segment_name}",
                    format=settings['format'],
                    mode='individual',
                    scale_factor=settings['scale_factor'],
                )

            if not success:
                self._show_error(f"Failed to export segment '{segment_name}'.")

    def _show_error(self, message: str):
        """Show error message box."""
        QMessageBox.critical(self.main_window, "Export Error", message)

    def _show_warning(self, message: str):
        """Show warning message box."""
        QMessageBox.warning(self.main_window, "Export Warning", message)

    def _show_info(self, message: str):
        """Show information message box."""
        QMessageBox.information(self.main_window, "Export Info", message)

    def _on_export_finished(self, success: bool, message: str):
        """Handle export completion."""
        # Disconnect signals and close progress dialog
        if self._progress_dialog:
            try:
                self._exporter.exportProgress.disconnect(self._progress_dialog.update_progress)
                self._exporter.exportFinished.disconnect(self._on_export_finished)
                self._exporter.exportError.disconnect(self._on_export_error)
            except RuntimeError:
                pass  # Signals may already be disconnected
            self._progress_dialog.close()
            self._progress_dialog = None

        # Show result message
        if success:
            QMessageBox.information(
                self.main_window,
                "Export Complete",
                f"Export completed successfully!\n\n{message}"
            )
        else:
            QMessageBox.warning(
                self.main_window,
                "Export Failed",
                f"Export failed:\n\n{message}"
            )

    def _on_export_error(self, error_message: str):
        """Handle export error."""
        # Disconnect signals and close progress dialog
        if self._progress_dialog:
            try:
                self._exporter.exportProgress.disconnect(self._progress_dialog.update_progress)
                self._exporter.exportFinished.disconnect(self._on_export_finished)
                self._exporter.exportError.disconnect(self._on_export_error)
            except RuntimeError:
                pass  # Signals may already be disconnected
            self._progress_dialog.close()
            self._progress_dialog = None

        # Show error message
        QMessageBox.critical(
            self.main_window,
            "Export Error",
            f"Export failed:\n\n{error_message}"
        )

    # ============================================================================
    # STATE QUERIES
    # ============================================================================

    def has_frames(self) -> bool:
        """Check if there are frames available for export."""
        return bool(self.sprite_model and self.sprite_model.sprite_frames)

    def get_frame_count(self) -> int:
        """Get the total number of frames."""
        if self.sprite_model and self.sprite_model.sprite_frames:
            return len(self.sprite_model.sprite_frames)
        return 0

    def get_current_frame_index(self) -> int:
        """Get the current frame index."""
        if self.sprite_model:
            return self.sprite_model.current_frame
        return 0
