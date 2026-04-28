"""Sprite loading and extraction flow coordination."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from sprite_model.extraction_mode import ExtractionMode, extraction_mode_label

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QLabel, QWidget

    from core import AnimationSegmentController, AutoDetectionController
    from managers import AnimationSegmentManager
    from sprite_model import SpriteModel
    from ui import AnimationGridView, EnhancedStatusBar, FrameExtractor, SpriteCanvas
    from ui.animation_segment_preview import AnimationSegmentPreview


@dataclass(frozen=True)
class SpriteLoadDependencies:
    """Explicit collaborators needed by the sprite loading/extraction flow."""

    parent: QWidget
    sprite_model: SpriteModel
    frame_extractor: FrameExtractor
    auto_detection_controller: AutoDetectionController
    segment_manager: AnimationSegmentManager
    segment_controller: AnimationSegmentController
    canvas: SpriteCanvas
    grid_view: AnimationGridView
    segment_preview: AnimationSegmentPreview
    status_bar: EnhancedStatusBar
    info_label: QLabel
    slicing_debounce_timer: QTimer
    add_recent_file: Callable[[str], None]
    update_recent_files_menu: Callable[[], None]
    update_has_frames_actions: Callable[[], None]
    update_playback_for_extraction: Callable[[int], None]


class SpriteLoadCoordinator:
    """Sprite-loading and extraction cascade for the main window.

    The coordinator owns the load, confirm, detect, extract, and display update
    pipeline. Dependencies are injected explicitly so this flow can be tested
    and evolved without depending on the full ``SpriteViewer`` implementation.
    """

    def __init__(self, dependencies: SpriteLoadDependencies) -> None:
        self._deps = dependencies
        self._loading_in_progress = False

    # ---- Loading ---------------------------------------------------------

    def load(self, file_path: str) -> bool:
        """Load a sprite file with validation and a re-entrant guard."""
        deps = self._deps
        if self._loading_in_progress:
            return False
        self._loading_in_progress = True
        try:
            if not self._confirm_load_over_segments(file_path):
                return False

            success, error_message = deps.sprite_model.load_sprite_sheet(file_path)
            if not success:
                QMessageBox.critical(deps.parent, "Load Error", error_message)
                return False
            return True
        finally:
            self._loading_in_progress = False

    def _confirm_load_over_segments(self, file_path: str) -> bool:
        """Ask user to confirm if loading a new sprite would clear existing segments."""
        deps = self._deps
        current_path = deps.sprite_model.file_path
        if not current_path or current_path == file_path:
            return True

        existing_segments = deps.segment_manager.get_all_segments()
        if not existing_segments:
            return True

        reply = QMessageBox.question(
            deps.parent,
            "Clear Segments?",
            f"Loading a new sprite will clear {len(existing_segments)} existing segment(s).\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def trigger_post_load_detection(self) -> None:
        """Trigger appropriate frame detection based on current extraction mode."""
        deps = self._deps
        current_mode = deps.frame_extractor.get_extraction_mode()
        if current_mode is ExtractionMode.CCL:
            deps.status_bar.show_message("Running CCL extraction...")
            self.update_frame_slicing()
        else:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            QApplication.processEvents()
            try:
                deps.auto_detection_controller.run_comprehensive_detection_with_dialog()
            finally:
                QApplication.restoreOverrideCursor()

    # ---- Sprite-loaded handler ------------------------------------------

    def on_sprite_loaded(self, file_path: str) -> None:
        """Handle ``SpriteModel.dataLoaded`` and kick off detection."""
        deps = self._deps
        deps.add_recent_file(file_path)
        deps.update_recent_files_menu()

        self.clear_extracted_frame_views()

        deps.status_bar.show_message(f"Loaded sprite sheet: {file_path}")
        self.trigger_post_load_detection()

    def clear_extracted_frame_views(self) -> None:
        """Clear all UI surfaces that display extracted frames."""
        deps = self._deps
        deps.canvas.clear_pixmap()
        deps.canvas.set_frame_info(0, 0)
        deps.grid_view.set_frames([])
        deps.grid_view.clear_segments()
        deps.segment_preview.set_frames([])
        deps.segment_preview.clear_segments()

    # ---- Extraction cascade ---------------------------------------------

    def update_frame_slicing(self) -> None:
        """Update frame slicing based on current settings."""
        deps = self._deps
        if not deps.sprite_model.original_sprite_sheet:
            return

        success, error_message, total_frames = self.extract_frames_by_mode()

        if not success:
            self.clear_extracted_frame_views()
            deps.update_has_frames_actions()
            QMessageBox.warning(deps.parent, "Frame Extraction Error", error_message)
            return

        deps.info_label.setText(deps.sprite_model.sprite_info)
        deps.update_has_frames_actions()

        if total_frames > 0:
            deps.sprite_model.set_current_frame(0)
            self.push_current_frame_to_canvas()

    def extract_frames_by_mode(self) -> tuple[bool, str, int]:
        """Run frame extraction using the current mode, with a wait cursor."""
        deps = self._deps
        mode = deps.frame_extractor.get_extraction_mode()

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        try:
            grid_config = (
                deps.frame_extractor.get_grid_config() if mode is ExtractionMode.GRID else None
            )
            return deps.sprite_model.extract_frames_for_mode(mode, grid_config)
        finally:
            QApplication.restoreOverrideCursor()

    def push_current_frame_to_canvas(self) -> None:
        """Push the current frame pixmap to the canvas if valid."""
        deps = self._deps
        pixmap = deps.sprite_model.current_frame_pixmap
        if pixmap and not pixmap.isNull():
            deps.canvas.set_pixmap(pixmap, auto_fit=False)
        else:
            deps.canvas.clear_pixmap()

    # ---- Post-extraction signal handlers --------------------------------

    def on_extraction_completed(self, frame_count: int) -> None:
        """Handle extraction completion."""
        deps = self._deps
        deps.update_playback_for_extraction(frame_count)

        if frame_count > 0:
            current_frame = deps.sprite_model.current_frame
            deps.canvas.set_frame_info(current_frame, frame_count)

            if deps.sprite_model.file_path:
                deps.segment_controller.set_sprite_context_and_sync(
                    deps.sprite_model.file_path, frame_count, refresh_frames=True
                )
            else:
                deps.segment_controller.update_grid_view_frames()
        else:
            self.clear_extracted_frame_views()

        deps.update_has_frames_actions()
        self.push_current_frame_to_canvas()

    def on_frame_settings_detected(self, width: int, height: int) -> None:
        """Auto-detection produced new frame dimensions; apply and re-extract."""
        deps = self._deps
        deps.slicing_debounce_timer.stop()
        deps.frame_extractor.apply_grid_settings(
            width,
            height,
            deps.sprite_model.offset_x,
            deps.sprite_model.offset_y,
            deps.sprite_model.spacing_x,
            deps.sprite_model.spacing_y,
        )
        self.update_frame_slicing()

    def on_extraction_mode_changed(self, mode: ExtractionMode) -> None:
        """Extraction strategy switched; re-extract."""
        deps = self._deps
        if not deps.sprite_model.original_sprite_sheet:
            return

        self.update_frame_slicing()

        deps.info_label.setText(deps.sprite_model.sprite_info)
        deps.status_bar.show_message(f"Switched to {extraction_mode_label(mode)} extraction mode")

    def on_settings_changed_debounced(self) -> None:
        """Restart debounce timer on settings change."""
        self._deps.slicing_debounce_timer.start()
