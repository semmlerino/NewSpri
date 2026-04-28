"""Sprite loading and extraction flow coordination."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from sprite_model.extraction_mode import ExtractionMode, extraction_mode_label

if TYPE_CHECKING:
    from sprite_viewer import SpriteViewer


class SpriteLoadCoordinator:
    """Sprite-loading and extraction cascade for ``SpriteViewer``.

    The coordinator owns the load, confirm, detect, extract, and display update
    pipeline. It still works against the main window because the current UI
    wiring is tightly integrated; keeping it in its own module makes that
    dependency explicit and easier to narrow later.
    """

    def __init__(self, view: SpriteViewer) -> None:
        self._view = view

    # ---- Loading ---------------------------------------------------------

    def load(self, file_path: str) -> bool:
        """Load a sprite file with validation. Re-entrant guard via the view."""
        view = self._view
        if view._loading_in_progress:
            return False
        view._loading_in_progress = True
        try:
            if not self._confirm_load_over_segments(file_path):
                return False

            success, error_message = view._sprite_model.load_sprite_sheet(file_path)
            if not success:
                QMessageBox.critical(view, "Load Error", error_message)
                return False
            return True
        finally:
            view._loading_in_progress = False

    def _confirm_load_over_segments(self, file_path: str) -> bool:
        """Ask user to confirm if loading a new sprite would clear existing segments."""
        view = self._view
        current_path = view._sprite_model.file_path
        if not current_path or current_path == file_path:
            return True

        existing_segments = view._segment_manager.get_all_segments()
        if not existing_segments:
            return True

        reply = QMessageBox.question(
            view,
            "Clear Segments?",
            f"Loading a new sprite will clear {len(existing_segments)} existing segment(s).\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def trigger_post_load_detection(self) -> None:
        """Trigger appropriate frame detection based on current extraction mode."""
        view = self._view
        current_mode = view._frame_extractor.get_extraction_mode()
        if current_mode is ExtractionMode.CCL:
            view._status_bar.show_message("Running CCL extraction...")
            self.update_frame_slicing()
        else:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            QApplication.processEvents()
            try:
                view._auto_detection_controller.run_comprehensive_detection_with_dialog()
            finally:
                QApplication.restoreOverrideCursor()

    # ---- Sprite-loaded handler ------------------------------------------

    def on_sprite_loaded(self, file_path: str) -> None:
        """Handle ``SpriteModel.dataLoaded`` and kick off detection."""
        view = self._view
        view._recent_files.add_file_to_recent(file_path)
        view._update_recent_files_menu()

        self.clear_extracted_frame_views()

        view._status_bar.show_message(f"Loaded sprite sheet: {file_path}")
        self.trigger_post_load_detection()

    def clear_extracted_frame_views(self) -> None:
        """Clear all UI surfaces that display extracted frames."""
        view = self._view
        view._canvas.clear_pixmap()
        view._canvas.set_frame_info(0, 0)
        view._grid_view.set_frames([])
        view._grid_view.clear_segments()
        view._segment_preview.set_frames([])
        view._segment_preview.clear_segments()

    # ---- Extraction cascade ---------------------------------------------

    def update_frame_slicing(self) -> None:
        """Update frame slicing based on current settings."""
        view = self._view
        if not view._sprite_model.original_sprite_sheet:
            return

        success, error_message, total_frames = self.extract_frames_by_mode()

        if not success:
            self.clear_extracted_frame_views()
            view._update_has_frames_actions()
            QMessageBox.warning(view, "Frame Extraction Error", error_message)
            return

        view._info_label.setText(view._sprite_model.sprite_info)
        view._update_has_frames_actions()

        if total_frames > 0:
            view._sprite_model.set_current_frame(0)
            self.push_current_frame_to_canvas()

    def extract_frames_by_mode(self) -> tuple[bool, str, int]:
        """Run frame extraction using the current mode, with a wait cursor."""
        view = self._view
        mode = view._frame_extractor.get_extraction_mode()

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        try:
            grid_config = (
                view._frame_extractor.get_grid_config() if mode is ExtractionMode.GRID else None
            )
            return view._sprite_model.extract_frames_for_mode(mode, grid_config)
        finally:
            QApplication.restoreOverrideCursor()

    def push_current_frame_to_canvas(self) -> None:
        """Push the current frame pixmap to the canvas if valid."""
        view = self._view
        pixmap = view._sprite_model.current_frame_pixmap
        if pixmap and not pixmap.isNull():
            view._canvas.set_pixmap(pixmap, auto_fit=False)
        else:
            view._canvas.clear_pixmap()

    # ---- Post-extraction signal handlers --------------------------------

    def on_extraction_completed(self, frame_count: int) -> None:
        """Handle extraction completion."""
        view = self._view
        view._update_playback_for_extraction(frame_count)

        if frame_count > 0:
            current_frame = view._sprite_model.current_frame
            view._canvas.set_frame_info(current_frame, frame_count)

            if view._sprite_model.file_path:
                view._segment_controller.set_sprite_context_and_sync(
                    view._sprite_model.file_path, frame_count, refresh_frames=True
                )
            else:
                view._segment_controller.update_grid_view_frames()
        else:
            self.clear_extracted_frame_views()

        view._update_has_frames_actions()
        self.push_current_frame_to_canvas()

    def on_frame_settings_detected(self, width: int, height: int) -> None:
        """Auto-detection produced new frame dimensions; apply and re-extract."""
        view = self._view
        view._slicing_debounce_timer.stop()
        view._frame_extractor.apply_grid_settings(
            width,
            height,
            view._sprite_model.offset_x,
            view._sprite_model.offset_y,
            view._sprite_model.spacing_x,
            view._sprite_model.spacing_y,
        )
        self.update_frame_slicing()

    def on_extraction_mode_changed(self, mode: ExtractionMode) -> None:
        """Extraction strategy switched; re-extract."""
        view = self._view
        if not view._sprite_model.original_sprite_sheet:
            return

        self.update_frame_slicing()

        view._info_label.setText(view._sprite_model.sprite_info)
        view._status_bar.show_message(f"Switched to {extraction_mode_label(mode)} extraction mode")

    def on_settings_changed_debounced(self) -> None:
        """Restart debounce timer on settings change."""
        self._view._slicing_debounce_timer.start()
