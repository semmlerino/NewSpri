"""
Export Coordinator for SpriteViewer.
Handles export dialog creation, validation, and direct export execution.
"""

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Signal, QObject

from export import ExportDialog
from export.core.frame_exporter import get_frame_exporter


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
    
    def cleanup(self):
        """Clean up resources."""
        # No specific cleanup needed for export coordinator
        pass
    
    # ============================================================================
    # EXPORT OPERATIONS
    # ============================================================================
    
    def export_frames(self):
        """Show enhanced export dialog for exporting frames and animation segments."""
        if not self._validate_export():
            return
        
        # Emit signal to notify export has been requested
        self.exportRequested.emit({'mode': 'all_frames'})
        
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

        success = self._exporter.export_frames(
            frames=frames_to_export,
            output_dir=settings['output_dir'],
            base_name=settings['base_name'],
            format=settings['format'],
            mode=export_mode,
            scale_factor=settings['scale_factor'],
            pattern=settings.get('pattern'),
            selected_indices=selected_indices if selected_indices else None,
            sprite_sheet_layout=settings.get('sprite_sheet_layout'),
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
            elif mode_index == 2:  # Animated GIF per segment
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(segment_output_dir),
                    base_name=segment_name,
                    format='GIF',
                    mode='gif',
                    scale_factor=settings['scale_factor'],
                    fps=settings.get('fps', 10),
                    loop=settings.get('loop', True),
                )
            else:  # Individual frames (all segments)
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