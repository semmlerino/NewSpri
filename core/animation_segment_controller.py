"""
Animation Segment Controller
============================

Manages animation segment creation, naming conflicts, grid view synchronization,
and segment export operations. Extracted from sprite_viewer.py for better
separation of concerns and testability.

Part of safe refactoring phase to reduce god class responsibilities.
"""

import contextlib
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

    def __init__(self, parent=None):
        """
        Initialize animation segment controller.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)

        # Dependencies injected via setters
        self._segment_manager: AnimationSegmentManager | None = None
        self._grid_view = None
        self._sprite_model = None
        self._tab_widget = None
        self._segment_preview = None

        # Configuration
        self.MAX_NAME_RETRY_ATTEMPTS = 10

        # Track signal connections for cleanup
        self._manager_signals_connected = False
        self._signal_connections: list[tuple] = []

    # ============================================================================
    # DEPENDENCY INJECTION
    # ============================================================================

    def set_segment_manager(self, manager: AnimationSegmentManager) -> None:
        """Set the animation segment manager dependency."""
        self._segment_manager = manager

        # Connect manager signals to update grid view
        if self._segment_manager and self._grid_view:
            self._connect_manager_signals()

    def set_grid_view(self, grid_view) -> None:
        """Set the animation grid view dependency."""
        self._grid_view = grid_view

        # Connect grid view signals - track for cleanup
        if self._grid_view and hasattr(self._grid_view, 'exportRequested'):
            signal = self._grid_view.exportRequested
            signal.connect(self._on_export_requested)
            self._signal_connections.append((signal, self._on_export_requested))

        # Connect manager signals to update grid view if manager already set
        if self._segment_manager and self._grid_view:
            self._connect_manager_signals()

    def set_sprite_model(self, model) -> None:
        """Set the sprite model dependency."""
        self._sprite_model = model

    def set_tab_widget(self, tab_widget) -> None:
        """Set the tab widget dependency for view switching."""
        self._tab_widget = tab_widget

    def set_segment_preview(self, preview_widget) -> None:
        """Set the animation segment preview widget dependency."""
        self._segment_preview = preview_widget
        if self._segment_preview:
            # Connect preview widget signals - track for cleanup
            connections = [
                (self._segment_preview.segmentRemoved, self.delete_segment),
                (self._segment_preview.playbackStateChanged, self._on_preview_playback_changed),
                (self._segment_preview.segmentBounceChanged, self._on_segment_bounce_changed),
                (self._segment_preview.segmentFrameHoldsChanged, self._on_segment_frame_holds_changed),
            ]
            for signal, slot in connections:
                signal.connect(slot)
                self._signal_connections.append((signal, slot))

    # ============================================================================
    # SEGMENT CREATION
    # ============================================================================

    def create_segment(self, segment) -> tuple[bool, str]:
        """
        Create a new animation segment with automatic name conflict resolution.

        Args:
            segment: Segment object with name, start_frame, end_frame, color, etc.

        Returns:
            Tuple of (success, message)
        """
        if not self._segment_manager:
            return False, "Segment manager not initialized"

        original_name = segment.name

        # Try to add segment to manager
        success, error = self._segment_manager.add_segment(
            segment.name,
            segment.start_frame,
            segment.end_frame,
            segment.color,
            getattr(segment, 'description', '')
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
            self._remove_from_grid_view(original_name)
            error_msg = f"{error}\n\nPlease try a different name."
            return False, error_msg

        # Success case
        message = f"Created animation segment '{segment.name}' with {segment.frame_count} frames"
        self.statusMessage.emit(message)

        # Add to preview panel if available
        if self._segment_preview and self._sprite_model:
            # Use the same frame-getting logic as update_grid_view_frames
            frames = self._get_sprite_frames()
            if frames:
                # Ensure preview has frames set
                if not self._segment_preview.has_frames():
                    self._segment_preview.set_frames(frames)

                self._segment_preview.add_segment(
                    segment.name,
                    segment.start_frame,
                    segment.end_frame,
                    segment.color,
                    segment.bounce_mode,
                    segment.frame_holds
                )

        return True, message

    def _resolve_name_conflict(self, segment, original_name: str) -> tuple[bool, str | None]:
        """
        Attempt to resolve naming conflicts by generating unique names.

        Args:
            segment: The segment object to add
            original_name: Original segment name that conflicted

        Returns:
            Tuple of (success, final_name)
        """
        base_name = original_name.split('_')[0] if '_' in original_name else original_name
        retry_count = 0

        while retry_count < self.MAX_NAME_RETRY_ATTEMPTS:
            retry_count += 1

            # Generate new unique name with timestamp
            timestamp = int(time.time() * 1000) % 10000
            new_name = f"{base_name}_{timestamp}"

            assert self._segment_manager is not None
            success, _error = self._segment_manager.add_segment(
                new_name,
                segment.start_frame,
                segment.end_frame,
                segment.color,
                getattr(segment, 'description', '')
            )

            if success:
                # Update segment data in grid view
                self._update_grid_view_segment_name(original_name, new_name, segment)

                # Add to preview panel with new name
                if self._segment_preview and self._sprite_model:
                    frames = self._get_sprite_frames()
                    if frames:
                        # Ensure preview has frames set
                        if not self._segment_preview.has_frames():
                            self._segment_preview.set_frames(frames)

                        self._segment_preview.add_segment(
                            new_name,
                            segment.start_frame,
                            segment.end_frame,
                            segment.color,
                            segment.bounce_mode,
                            segment.frame_holds
                        )

                return True, new_name

        return False, None

    def _update_grid_view_segment_name(self, old_name: str, new_name: str, segment) -> None:
        """Update segment name in grid view after successful rename."""
        if not self._grid_view:
            return

        # Use public API to rename segment
        if hasattr(self._grid_view, 'rename_segment'):
            self._grid_view.rename_segment(old_name, new_name)
        elif hasattr(self._grid_view, 'has_segment') and self._grid_view.has_segment(old_name):
            # Fallback for backward compatibility
            self._grid_view.delete_segment(old_name)
            self._grid_view.add_segment(segment)

    def _remove_from_grid_view(self, segment_name: str) -> None:
        """Remove failed segment from grid view."""
        if not self._grid_view:
            return

        # Use public API to delete segment
        if hasattr(self._grid_view, 'delete_segment'):
            self._grid_view.delete_segment(segment_name)

    # ============================================================================
    # SEGMENT OPERATIONS
    # ============================================================================

    def rename_segment(self, old_name: str, new_name: str) -> tuple[bool, str]:
        """
        Rename an animation segment.

        Args:
            old_name: Current name of the segment
            new_name: New name for the segment

        Returns:
            Tuple of (success, message)
        """
        if not self._segment_manager:
            return False, "Segment manager not initialized"

        success, error = self._segment_manager.rename_segment(old_name, new_name)

        if success:
            message = f"Renamed segment '{old_name}' to '{new_name}'"
            self.statusMessage.emit(message)

            # Update preview panel if available
            if self._segment_preview:
                # Get the segment data
                segment = self._segment_manager.get_segment(new_name)
                if segment:
                    # Remove old and add new
                    self._segment_preview.remove_segment(old_name)
                    if self._sprite_model:
                        frames = self._get_sprite_frames()
                        if frames and not self._segment_preview.has_frames():
                            self._segment_preview.set_frames(frames)

                        self._segment_preview.add_segment(
                            new_name,
                            segment.start_frame,
                            segment.end_frame,
                            segment.color,
                            segment.bounce_mode,
                            segment.frame_holds
                        )

            return True, message

        return False, error

    def delete_segment(self, segment_name: str) -> tuple[bool, str]:
        """
        Delete an animation segment.

        Args:
            segment_name: Name of segment to delete

        Returns:
            Tuple of (success, message)
        """
        if not self._segment_manager:
            return False, "Segment manager not initialized"

        if self._segment_manager.remove_segment(segment_name):
            message = f"Deleted animation segment '{segment_name}'"
            self.statusMessage.emit(message)

            # Remove from preview panel if available
            if self._segment_preview:
                self._segment_preview.remove_segment(segment_name)

            return True, message

        return False, f"Failed to delete segment '{segment_name}'"

    def select_segment(self, segment) -> None:
        """
        Handle segment selection (without switching views).

        Args:
            segment: Selected segment object
        """
        message = (
            f"Selected segment '{segment.name}' "
            f"(frames {segment.start_frame}-{segment.end_frame}) - "
            f"Use 'Export Selected' to export"
        )
        self.statusMessage.emit(message)

    def preview_segment(self, segment) -> None:
        """
        Preview a segment by showing its start frame.

        Args:
            segment: Segment to preview
        """
        if self._sprite_model:
            self._sprite_model.set_current_frame(segment.start_frame)

        message = (
            f"Segment '{segment.name}' selected "
            f"(frames {segment.start_frame}-{segment.end_frame})"
        )
        self.statusMessage.emit(message)

    def _on_preview_playback_changed(self, segment_name: str, is_playing: bool) -> None:
        """
        Handle playback state change from preview panel.

        Args:
            segment_name: Name of segment
            is_playing: Whether segment is playing
        """
        if is_playing:
            self.statusMessage.emit(f"Playing animation segment '{segment_name}'")
        else:
            self.statusMessage.emit(f"Paused animation segment '{segment_name}'")

    def _on_segment_bounce_changed(self, segment_name: str, bounce_mode: bool) -> None:
        """
        Handle bounce mode change from preview panel.

        Args:
            segment_name: Name of segment
            bounce_mode: Whether bounce mode is enabled
        """
        if not self._segment_manager:
            return

        success, error = self._segment_manager.set_bounce_mode(segment_name, bounce_mode)
        if success:
            mode_text = "enabled" if bounce_mode else "disabled"
            self.statusMessage.emit(f"Bounce mode {mode_text} for segment '{segment_name}'")
        else:
            self.statusMessage.emit(f"Failed to update bounce mode: {error}")

    def _on_segment_frame_holds_changed(self, segment_name: str, frame_holds: dict[int, int]) -> None:
        """
        Handle frame holds change from preview panel.

        Args:
            segment_name: Name of segment
            frame_holds: Dictionary of frame indices to hold durations
        """
        if not self._segment_manager:
            return

        success, error = self._segment_manager.set_frame_holds(segment_name, frame_holds)
        if success:
            if frame_holds:
                hold_count = len(frame_holds)
                self.statusMessage.emit(f"Updated {hold_count} frame hold{'s' if hold_count != 1 else ''} for segment '{segment_name}'")
            else:
                self.statusMessage.emit(f"Cleared frame holds for segment '{segment_name}'")
        else:
            self.statusMessage.emit(f"Failed to update frame holds: {error}")

    # ============================================================================
    # SEGMENT EXPORT
    # ============================================================================

    def _on_export_requested(self, segment_name: str) -> None:
        """
        Handle export request from grid view or preview panel.

        Args:
            segment_name: Name of segment to export
        """
        if not self._segment_manager:
            return

        # Get segment data
        segments = self._segment_manager.get_all_segments()
        segment = None
        for seg in segments:
            if seg.name == segment_name:
                segment = seg
                break

        if segment:
            # Find parent widget - try tab widget first, then grid view
            parent_widget = self._tab_widget or self._grid_view
            self.export_segment(segment, parent_widget)

    def export_segment(self, segment, parent_widget=None) -> None:
        """
        Export a specific animation segment.

        Args:
            segment: Segment to export
            parent_widget: Parent widget for dialogs
        """
        if not self._sprite_model or not self._segment_manager:
            QMessageBox.warning(
                parent_widget,
                "Export Error",
                "Required components not initialized"
            )
            return

        # Get frames for the segment
        all_frames = self._sprite_model.get_all_frames()
        segment_frames = self._segment_manager.extract_frames_for_segment(
            segment.name, all_frames
        )

        if not segment_frames:
            QMessageBox.warning(
                parent_widget,
                "Export Error",
                f"No frames available for segment '{segment.name}'"
            )
            return

        # Import here to avoid circular dependency
        from export import ExportDialog

        # Open export dialog
        dialog = ExportDialog(
            parent_widget,
            frame_count=len(segment_frames),
            current_frame=0,
            segment_manager=self._segment_manager
        )

        # Set sprites for visual preview
        dialog.set_sprites(segment_frames)

        # Connect to handler
        dialog.exportRequested.connect(
            lambda settings: self._handle_segment_export(
                settings, segment_frames, segment.name
            )
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.statusMessage.emit(f"Exported segment '{segment.name}'")

    def _handle_segment_export(
        self,
        settings: dict[str, Any],
        segment_frames: list,
        segment_name: str
    ) -> None:
        """
        Handle segment-specific export request.

        Args:
            settings: Export settings
            segment_frames: Frames to export
            segment_name: Name of segment being exported
        """
        from export.core.frame_exporter import get_frame_exporter

        required_keys = ['output_dir', 'base_name', 'format', 'mode', 'scale_factor']
        for key in required_keys:
            if key not in settings:
                return

        if not segment_frames:
            return

        exporter = get_frame_exporter()
        base_name = f"{settings['base_name']}_{segment_name}"

        exporter.export_frames(
            frames=segment_frames,
            output_dir=settings['output_dir'],
            base_name=base_name,
            format=settings['format'],
            mode=settings['mode'],
            scale_factor=settings['scale_factor'],
            pattern=settings.get('pattern'),
            sprite_sheet_layout=settings.get('sprite_sheet_layout'),
        )

    # ============================================================================
    # GRID VIEW SYNCHRONIZATION
    # ============================================================================

    def update_grid_view_frames(self) -> None:
        """Update grid view with current sprite model frames."""
        if not self._grid_view or not self._sprite_model:
            return

        # Try multiple ways to get frames for backward compatibility
        frames = self._get_sprite_frames()

        if frames:
            self._grid_view.set_frames(frames)

            # Update preview panel with frames
            if self._segment_preview:
                self._segment_preview.set_frames(frames)

                # Sync existing segments to preview
                if self._segment_manager:
                    segments = self._segment_manager.get_all_segments()
                    for segment_data in segments:
                        self._segment_preview.add_segment(
                            segment_data.name,
                            segment_data.start_frame,
                            segment_data.end_frame,
                            segment_data.color,
                            segment_data.bounce_mode,
                            segment_data.frame_holds
                        )

            # Update segment manager context
            sprite_path = self._get_sprite_path()
            if sprite_path and self._segment_manager:
                self._segment_manager.set_sprite_context(sprite_path, len(frames))
        else:
            self._grid_view.set_frames([])  # Clear grid view
            if self._segment_preview:
                self._segment_preview.set_frames([])
                self._segment_preview.clear_segments()

    def _get_sprite_frames(self) -> list:
        """Get frames from sprite model using various methods."""
        frames = []

        if not self._sprite_model:
            return frames

        # Method 1: Try get_all_frames if available
        if hasattr(self._sprite_model, 'get_all_frames'):
            frames = self._sprite_model.get_all_frames()

        # Method 2: Try sprite_frames property as fallback
        if not frames and hasattr(self._sprite_model, 'sprite_frames'):
            frames = self._sprite_model.sprite_frames

        # Method 3: Try _sprite_frames attribute as last resort
        if not frames and hasattr(self._sprite_model, '_sprite_frames'):
            frames = self._sprite_model._sprite_frames

        return frames

    def _get_sprite_path(self) -> str:
        """Get sprite sheet path from model."""
        if not self._sprite_model:
            return ""
        if hasattr(self._sprite_model, '_file_path'):
            return self._sprite_model._file_path
        elif hasattr(self._sprite_model, '_sprite_sheet_path'):
            return self._sprite_model._sprite_sheet_path
        return ""

    def on_tab_changed(self, index: int) -> None:
        """
        Handle tab change event to refresh grid view.

        Args:
            index: Tab index
        """
        # Assuming Animation Splitting is tab index 1
        if index == 1 and self._grid_view:
            self.update_grid_view_frames()

    def _on_manager_segment_removed(self, segment_name: str) -> None:
        """
        Handle segment removal from manager by updating grid view.

        Args:
            segment_name: Name of removed segment
        """
        if self._grid_view and hasattr(self._grid_view, 'delete_segment'):
            # Use public API to update visualization
            self._grid_view.delete_segment(segment_name)

    def _on_manager_segments_cleared(self) -> None:
        """Handle all segments being cleared from manager."""
        if self._grid_view and hasattr(self._grid_view, 'clear_segments'):
            # Clear all segments in grid view
            self._grid_view.clear_segments()

    def _connect_manager_signals(self) -> None:
        """Connect segment manager signals to grid view updates."""
        if not self._manager_signals_connected and self._segment_manager and self._grid_view:
            # Connect signals only once - track for cleanup
            connections = [
                (self._segment_manager.segmentRemoved, self._on_manager_segment_removed),
                (self._segment_manager.segmentsCleared, self._on_manager_segments_cleared),
            ]
            for signal, slot in connections:
                signal.connect(slot)
                self._signal_connections.append((signal, slot))
            self._manager_signals_connected = True

    def cleanup(self) -> None:
        """Clean up signal connections to prevent memory leaks."""
        for signal, slot in self._signal_connections:
            with contextlib.suppress(RuntimeError, TypeError):
                signal.disconnect(slot)
        self._signal_connections.clear()
        self._manager_signals_connected = False
