"""
Animation Segment Controller
============================

Manages animation segment creation, naming conflicts, grid view synchronization,
and segment export operations. Extracted from sprite_viewer.py for better
separation of concerns and testability.

Part of safe refactoring phase to reduce god class responsibilities.
"""

import re
from dataclasses import replace
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox, QTabWidget, QWidget

from config import Config
from managers import AnimationSegment, AnimationSegmentManager

if TYPE_CHECKING:
    from core.export_coordinator import ExportCoordinator
    from sprite_model import SpriteModel
    from ui import AnimationGridView
    from ui.animation_segment_preview import AnimationSegmentPreview


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
        grid_view: "AnimationGridView | None",
        sprite_model: "SpriteModel",
        tab_widget: QTabWidget,
        segment_preview: "AnimationSegmentPreview",
        export_coordinator: "ExportCoordinator | None" = None,
        parent: QWidget | None = None,
    ):
        """
        Initialize animation segment controller with all dependencies.

        Args:
            segment_manager: Animation segment manager for persistence
            grid_view: Animation grid view for frame selection
            sprite_model: Sprite model for frame data
            tab_widget: Tab widget for view switching
            segment_preview: Segment preview widget
            export_coordinator: Export coordinator for segment export
            parent: Parent QObject
        """
        super().__init__(parent)

        # Store dependencies
        self._segment_manager = segment_manager
        self._grid_view = grid_view
        self._sprite_model = sprite_model
        self._tab_widget = tab_widget
        self._segment_preview = segment_preview
        self._export_coordinator = export_coordinator

        # Guard flag: suppress _on_manager_segment_removed during rename
        self._renaming = False

        # Staleness tracking for on_tab_changed: avoid redundant full resyncs
        self._last_sync_frame_count: int = -1
        self._last_sync_sprite_path: str = ""

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

    def create_segment(self, segment: AnimationSegment) -> tuple[bool, str]:
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
            # Resync grid to match manager state (manager already has no record of this segment).
            if self._grid_view:
                self._grid_view.sync_segments_with_manager(self._segment_manager)
            error_msg = f"{error}\n\nPlease try a different name."
            return False, error_msg

        # Success case: resync grid from manager (single authoritative write path).
        if self._grid_view:
            self._grid_view.sync_segments_with_manager(self._segment_manager)
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

    def _resolve_name_conflict(
        self, segment: AnimationSegment, original_name: str
    ) -> tuple[bool, str | None]:
        """Generate unique name variants until one succeeds. Returns (success, final_name)."""
        # Strip only a previously-appended numeric suffix (_\d+) to preserve semantic names
        # e.g. "Walk_Left_1234" -> "Walk_Left", but "Walk_Left" stays "Walk_Left"
        base_name = re.sub(r"_\d+$", "", original_name)
        retry_count = 0

        while retry_count < self.MAX_NAME_RETRY_ATTEMPTS:
            retry_count += 1

            new_name = f"{base_name}_{retry_count}"

            success, _error = self._segment_manager.add_segment(
                new_name,
                segment.start_frame,
                segment.end_frame,
                segment.color,
                getattr(segment, "description", ""),
            )

            if success:
                # Resync grid from manager (single authoritative write path).
                if self._grid_view:
                    self._grid_view.sync_segments_with_manager(self._segment_manager)

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
        color: QColor,
        bounce_mode: bool,
        frame_holds: dict[int, int] | None,
    ) -> None:
        """Add segment to preview panel if available and frames exist."""
        if not self._segment_preview or not self._sprite_model:
            return
        frames = self._sprite_model.sprite_frames
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
        """Rename an animation segment (validate-first). Returns (success, message)."""
        # Guard: manager emits segmentRemoved during rename which would delete from grid
        self._renaming = True
        try:
            success, error = self._segment_manager.update_segment(old_name, new_name=new_name)
        finally:
            self._renaming = False

        if success:
            # Resync grid from manager after validated rename.
            if self._grid_view:
                self._grid_view.sync_segments_with_manager(self._segment_manager)

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

        self.statusMessage.emit(f"Rename failed: {error}")
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

    def select_segment(self, segment: AnimationSegment) -> None:
        """Handle segment selection (without switching views)."""
        message = (
            f"Selected segment '{segment.name}' "
            f"(frames {segment.start_frame}-{segment.end_frame}) - "
            f"Use 'Export Selected' to export"
        )
        self.statusMessage.emit(message)

    def preview_segment(self, segment: AnimationSegment) -> None:
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
        segment = self._segment_manager.get_segment(segment_name)
        if segment:
            self.export_segment(segment, self._tab_widget or self._grid_view)

    def export_segment(
        self, segment: AnimationSegment, parent_widget: QWidget | None = None
    ) -> None:
        """Export a specific animation segment."""
        if not self._sprite_model or not self._segment_manager:
            QMessageBox.warning(
                parent_widget, "Export Error", "Required components not initialized"
            )
            return

        all_frames = self._sprite_model.sprite_frames
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
            sprites=segment_frames,
            segment_manager=self._segment_manager,
        )
        coordinator = self._export_coordinator
        if coordinator is not None:
            dialog.exportRequested.connect(
                lambda config: coordinator.handle_export_request(
                    replace(config, base_name=f"{config.base_name}_{segment.name}"),
                    frames=segment_frames,
                )
            )

        dialog.exec()

    # ============================================================================
    # GRID VIEW SYNCHRONIZATION
    # ============================================================================

    def update_grid_view_frames(self) -> None:
        """Update grid view with current sprite model frames."""
        if not self._grid_view or not self._sprite_model:
            return

        frames = self._sprite_model.sprite_frames

        if frames:
            self._grid_view.set_frames(frames)
            # Reset per-frame overlays; they will be repopulated from manager state.
            self._grid_view.clear_segments()

            if self._segment_preview:
                self._segment_preview.set_frames(frames)
                self._segment_preview.clear_segments()
        else:
            self._grid_view.set_frames([])
            if self._segment_preview:
                self._segment_preview.set_frames([])
                self._segment_preview.clear_segments()

    def sync_segments_from_manager(self) -> None:
        """Synchronize grid/preview segment overlays from manager (source of truth)."""
        if self._grid_view and self._segment_manager:
            self._grid_view.sync_segments_with_manager(self._segment_manager)

        if self._segment_preview:
            self._segment_preview.clear_segments()
            for seg in self._segment_manager.get_all_segments():
                self._add_segment_to_preview(
                    seg.name,
                    seg.start_frame,
                    seg.end_frame,
                    seg.color,
                    seg.bounce_mode,
                    seg.frame_holds,
                )

    def set_sprite_context_and_sync(self, sprite_path: str, frame_count: int) -> None:
        """Set manager sprite context then synchronize all segment overlays."""
        if not self._segment_manager:
            return
        self._segment_manager.set_sprite_context(sprite_path, frame_count)
        self.sync_segments_from_manager()

    def on_tab_changed(self, index: int) -> None:
        """Handle tab change event to refresh grid view.

        Only performs a full clear+resync when the underlying frame data has
        actually changed (different sprite sheet or different frame count).
        This prevents destroying in-progress segment preview playback on every
        tab switch.
        """
        if index != Config.App.TAB_INDEX_ANIMATION_SPLIT or not self._grid_view:
            return

        current_frame_count = (
            len(self._sprite_model.sprite_frames)
            if self._sprite_model and self._sprite_model.sprite_frames
            else 0
        )
        current_sprite_path = self._sprite_model.file_path if self._sprite_model else ""

        frame_data_changed = (
            current_frame_count != self._last_sync_frame_count
            or current_sprite_path != self._last_sync_sprite_path
        )

        if frame_data_changed:
            self._last_sync_frame_count = current_frame_count
            self._last_sync_sprite_path = current_sprite_path
            self.update_grid_view_frames()
            self.sync_segments_from_manager()

    def _on_manager_segment_removed(self, _segment_name: str) -> None:
        """Handle segment removal from manager by resyncing grid to manager state."""
        if self._renaming:
            return  # Suppress during rename (sync after rename handles grid state)
        if self._grid_view:
            self._grid_view.sync_segments_with_manager(self._segment_manager)

    def _on_manager_segments_cleared(self) -> None:
        """Handle all segments being cleared from manager."""
        if self._grid_view:
            self._grid_view.clear_segments()
