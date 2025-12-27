"""
Animation Segment Controller
============================

Manages animation segment creation, naming conflicts, grid view synchronization,
and segment export operations. Extracted from sprite_viewer.py for better
separation of concerns and testability.

Part of safe refactoring phase to reduce god class responsibilities.
"""

import time
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog, QMessageBox

from managers import AnimationSegmentManager


class AnimationSegmentController(QObject):
    """
    Coordinates animation segment operations between UI components and managers.

    Responsibilities:
    - Handle segment creation with automatic naming conflict resolution
    - Manage segment deletion
    - Coordinate segment export operations
    - Synchronize segment data between grid view and manager
    - Handle segment selection and preview
    """

    # Signals for status updates
    statusMessage = Signal(str)
    exportRequested = Signal(dict)  # Export settings

    def __init__(
        self,
        segment_manager: AnimationSegmentManager,
        grid_view,
        sprite_model,
        tab_widget,
        segment_preview,
        parent=None,
    ):
        """
        Initialize animation segment controller with all dependencies.

        Args:
            segment_manager: Animation segment manager for persistence
            grid_view: Animation grid view for frame selection
            sprite_model: Sprite model for frame data
            tab_widget: Tab widget for view switching
            segment_preview: Segment preview widget
            parent: Parent QObject
        """
        super().__init__(parent)

        # Store dependencies
        self._segment_manager = segment_manager
        self._grid_view = grid_view
        self._sprite_model = sprite_model
        self._tab_widget = tab_widget
        self._segment_preview = segment_preview

        # Configuration
        self.MAX_NAME_RETRY_ATTEMPTS = 10

        # Connect signals
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect all signals from dependencies."""
        # Grid view signals
        if self._grid_view:
            self._grid_view.exportRequested.connect(self._on_export_requested)

        # Manager signals
        if self._segment_manager:
            self._segment_manager.segmentRemoved.connect(self._on_manager_segment_removed)
            self._segment_manager.segmentsCleared.connect(self._on_manager_segments_cleared)

        # Preview widget signals
        if self._segment_preview:
            self._segment_preview.segmentRemoved.connect(self.delete_segment)
            self._segment_preview.playbackStateChanged.connect(self._on_preview_playback_changed)
            self._segment_preview.segmentBounceChanged.connect(self._on_segment_bounce_changed)
            self._segment_preview.segmentFrameHoldsChanged.connect(
                self._on_segment_frame_holds_changed
            )

    # ============================================================================
    # SEGMENT CREATION
    # ============================================================================

    def create_segment(self, segment) -> tuple[bool, str]:
        """Create a new segment with automatic name conflict resolution. Returns (success, message)."""
        original_name = segment.name

        # Try to add segment to manager
        success, error = self._segment_manager.add_segment(
            segment.name,
            segment.start_frame,
            segment.end_frame,
            segment.color,
            getattr(segment, "description", ""),
        )

        # Handle name conflicts with automatic resolution
        if not success and "already exists" in error:
            success, final_name = self._resolve_name_conflict(segment, original_name)

            if success:
                message = (
                    f"Created animation segment '{final_name}' with {segment.frame_count} frames "
                    f"(renamed from '{original_name}' to resolve conflict)"
                )
                self.statusMessage.emit(message)
                return True, message

        if not success:
            # Clean up grid view if segment was added there but failed in manager
            if self._grid_view:
                self._grid_view.delete_segment(original_name)
            error_msg = f"{error}\n\nPlease try a different name."
            return False, error_msg

        # Success case
        message = f"Created animation segment '{segment.name}' with {segment.frame_count} frames"
        self.statusMessage.emit(message)

        # Add to preview panel if available
        self._add_segment_to_preview(
            segment.name,
            segment.start_frame,
            segment.end_frame,
            segment.color,
            segment.bounce_mode,
            segment.frame_holds,
        )

        return True, message

    def _resolve_name_conflict(self, segment, original_name: str) -> tuple[bool, str | None]:
        """Generate unique name variants until one succeeds. Returns (success, final_name)."""
        base_name = original_name.split("_")[0] if "_" in original_name else original_name
        retry_count = 0

        while retry_count < self.MAX_NAME_RETRY_ATTEMPTS:
            retry_count += 1

            # Generate new unique name with timestamp
            timestamp = int(time.time() * 1000) % 10000
            new_name = f"{base_name}_{timestamp}"

            success, _error = self._segment_manager.add_segment(
                new_name,
                segment.start_frame,
                segment.end_frame,
                segment.color,
                getattr(segment, "description", ""),
            )

            if success:
                # Update segment name in grid view
                if self._grid_view:
                    self._grid_view.rename_segment(original_name, new_name)

                # Add to preview panel with new name
                self._add_segment_to_preview(
                    new_name,
                    segment.start_frame,
                    segment.end_frame,
                    segment.color,
                    segment.bounce_mode,
                    segment.frame_holds,
                )
                return True, new_name

        return False, None

    def _add_segment_to_preview(
        self,
        name: str,
        start_frame: int,
        end_frame: int,
        color,
        bounce_mode: bool,
        frame_holds: dict[int, int] | None,
    ) -> None:
        """Add segment to preview panel if available and frames exist."""
        if not self._segment_preview or not self._sprite_model:
            return
        frames = self._sprite_model.get_all_frames()
        if not frames:
            return
        if not self._segment_preview.has_frames():
            self._segment_preview.set_frames(frames)
        self._segment_preview.add_segment(
            name, start_frame, end_frame, color, bounce_mode, frame_holds
        )

    # ============================================================================
    # SEGMENT OPERATIONS
    # ============================================================================

    def rename_segment(self, old_name: str, new_name: str) -> tuple[bool, str]:
        """Rename an animation segment. Returns (success, message)."""
        success, error = self._segment_manager.rename_segment(old_name, new_name)

        if success:
            message = f"Renamed segment '{old_name}' to '{new_name}'"
            self.statusMessage.emit(message)

            # Update preview panel if available
            if self._segment_preview:
                self._segment_preview.remove_segment(old_name)
                segment = self._segment_manager.get_segment(new_name)
                if segment:
                    self._add_segment_to_preview(
                        new_name,
                        segment.start_frame,
                        segment.end_frame,
                        segment.color,
                        segment.bounce_mode,
                        segment.frame_holds,
                    )

            return True, message

        return False, error

    def delete_segment(self, segment_name: str) -> tuple[bool, str]:
        """Delete an animation segment. Returns (success, message)."""
        if self._segment_manager.remove_segment(segment_name):
            message = f"Deleted animation segment '{segment_name}'"
            self.statusMessage.emit(message)

            if self._segment_preview:
                self._segment_preview.remove_segment(segment_name)

            return True, message

        return False, f"Failed to delete segment '{segment_name}'"

    def select_segment(self, segment) -> None:
        """Handle segment selection (without switching views)."""
        message = (
            f"Selected segment '{segment.name}' "
            f"(frames {segment.start_frame}-{segment.end_frame}) - "
            f"Use 'Export Selected' to export"
        )
        self.statusMessage.emit(message)

    def preview_segment(self, segment) -> None:
        """Preview a segment by showing its start frame."""
        if self._sprite_model:
            self._sprite_model.set_current_frame(segment.start_frame)

        message = (
            f"Segment '{segment.name}' selected (frames {segment.start_frame}-{segment.end_frame})"
        )
        self.statusMessage.emit(message)

    def _on_preview_playback_changed(self, segment_name: str, is_playing: bool) -> None:
        """Handle playback state change from preview panel."""
        action = "Playing" if is_playing else "Paused"
        self.statusMessage.emit(f"{action} animation segment '{segment_name}'")

    def _on_segment_bounce_changed(self, segment_name: str, bounce_mode: bool) -> None:
        """Handle bounce mode change from preview panel."""
        success, error = self._segment_manager.set_bounce_mode(segment_name, bounce_mode)
        if success:
            mode_text = "enabled" if bounce_mode else "disabled"
            self.statusMessage.emit(f"Bounce mode {mode_text} for segment '{segment_name}'")
        else:
            self.statusMessage.emit(f"Failed to update bounce mode: {error}")

    def _on_segment_frame_holds_changed(
        self, segment_name: str, frame_holds: dict[int, int]
    ) -> None:
        """Handle frame holds change from preview panel."""
        success, error = self._segment_manager.set_frame_holds(segment_name, frame_holds)
        if success:
            if frame_holds:
                hold_count = len(frame_holds)
                self.statusMessage.emit(
                    f"Updated {hold_count} frame hold{'s' if hold_count != 1 else ''} for segment '{segment_name}'"
                )
            else:
                self.statusMessage.emit(f"Cleared frame holds for segment '{segment_name}'")
        else:
            self.statusMessage.emit(f"Failed to update frame holds: {error}")

    # ============================================================================
    # SEGMENT EXPORT
    # ============================================================================

    def _on_export_requested(self, segment_name: str) -> None:
        """Handle export request from grid view or preview panel."""
        segment = next(
            (s for s in self._segment_manager.get_all_segments() if s.name == segment_name), None
        )
        if segment:
            self.export_segment(segment, self._tab_widget or self._grid_view)

    def export_segment(self, segment, parent_widget=None) -> None:
        """Export a specific animation segment."""
        if not self._sprite_model or not self._segment_manager:
            QMessageBox.warning(
                parent_widget, "Export Error", "Required components not initialized"
            )
            return

        all_frames = self._sprite_model.get_all_frames()
        segment_frames = self._segment_manager.extract_frames_for_segment(segment.name, all_frames)

        if not segment_frames:
            QMessageBox.warning(
                parent_widget, "Export Error", f"No frames available for segment '{segment.name}'"
            )
            return

        from export import ExportDialog

        dialog = ExportDialog(
            parent_widget,
            frame_count=len(segment_frames),
            current_frame=0,
            segment_manager=self._segment_manager,
        )
        dialog.set_sprites(segment_frames)
        dialog.exportRequested.connect(
            lambda settings: self._handle_segment_export(settings, segment_frames, segment.name)
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.statusMessage.emit(f"Exported segment '{segment.name}'")

    def _handle_segment_export(
        self, settings: dict[str, Any], segment_frames: list, segment_name: str
    ) -> None:
        """Handle segment-specific export request."""
        required = {"output_dir", "base_name", "format", "mode", "scale_factor"}
        if not segment_frames or not required.issubset(settings):
            return

        from export.core.frame_exporter import get_frame_exporter

        get_frame_exporter().export_frames(
            frames=segment_frames,
            output_dir=settings["output_dir"],
            base_name=f"{settings['base_name']}_{segment_name}",
            format=settings["format"],
            mode=settings["mode"],
            scale_factor=settings["scale_factor"],
            pattern=settings.get("pattern"),
            sprite_sheet_layout=settings.get("sprite_sheet_layout"),
        )

    # ============================================================================
    # GRID VIEW SYNCHRONIZATION
    # ============================================================================

    def update_grid_view_frames(self) -> None:
        """Update grid view with current sprite model frames."""
        if not self._grid_view or not self._sprite_model:
            return

        frames = self._sprite_model.get_all_frames()

        if frames:
            self._grid_view.set_frames(frames)

            if self._segment_preview:
                self._segment_preview.set_frames(frames)
                self._segment_preview.clear_segments()

                for seg in self._segment_manager.get_all_segments():
                    self._segment_preview.add_segment(
                        seg.name,
                        seg.start_frame,
                        seg.end_frame,
                        seg.color,
                        seg.bounce_mode,
                        seg.frame_holds,
                    )

            sprite_path = self._sprite_model.file_path
            if sprite_path:
                self._segment_manager.set_sprite_context(sprite_path, len(frames))
        else:
            self._grid_view.set_frames([])
            if self._segment_preview:
                self._segment_preview.set_frames([])
                self._segment_preview.clear_segments()

    def on_tab_changed(self, index: int) -> None:
        """Handle tab change event to refresh grid view."""
        if index == 1 and self._grid_view:
            self.update_grid_view_frames()

    def _on_manager_segment_removed(self, segment_name: str) -> None:
        """Handle segment removal from manager by updating grid view."""
        if self._grid_view:
            self._grid_view.delete_segment(segment_name)

    def _on_manager_segments_cleared(self) -> None:
        """Handle all segments being cleared from manager."""
        if self._grid_view:
            self._grid_view.clear_segments()
