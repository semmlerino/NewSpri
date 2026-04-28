"""Integration tests for viewer/model state synchronization."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from PySide6.QtGui import QColor, QPainter, QPixmap

from sprite_model.extraction_mode import ExtractionMode
from sprite_model.sprite_detection import DetectionResult
from sprite_viewer import SpriteViewer

pytestmark = [pytest.mark.integration, pytest.mark.requires_qt]


def _test_sheet(frame_count: int = 2, frame_size: int = 16) -> QPixmap:
    sheet = QPixmap(frame_count * frame_size, frame_size)
    sheet.fill(QColor(255, 255, 255))

    painter = QPainter(sheet)
    for index in range(frame_count):
        painter.fillRect(
            index * frame_size,
            0,
            frame_size,
            frame_size,
            QColor.fromHsv(index * 90, 200, 200),
        )
    painter.end()
    return sheet


def test_sprite_load_clears_stale_extracted_frame_views(qtbot) -> None:
    """Loading a sprite with no extracted frames should clear old canvas/grid state."""
    viewer = SpriteViewer()
    qtbot.addWidget(viewer)

    old_frame = QPixmap(16, 16)
    old_frame.fill(QColor(255, 0, 0))
    viewer._canvas.set_pixmap(old_frame)
    viewer._grid_view.set_frames([old_frame])
    viewer._segment_preview.set_frames([old_frame])
    viewer._sprite_model.clear_frames()

    viewer._on_sprite_loaded("new_sprite.png")

    assert viewer._canvas._pixmap is None
    assert viewer._grid_view._frames == []
    assert viewer._segment_preview._all_frames == []


def test_extraction_failure_clears_stale_frame_views(qtbot) -> None:
    """A failed extraction should not leave the previously displayed frames visible."""
    viewer = SpriteViewer()
    qtbot.addWidget(viewer)

    old_frame = QPixmap(16, 16)
    old_frame.fill(QColor(255, 0, 0))
    viewer._sprite_model._original_sprite_sheet = _test_sheet()
    viewer._canvas.set_pixmap(old_frame)
    viewer._grid_view.set_frames([old_frame])
    viewer._segment_preview.set_frames([old_frame])

    with (
        patch.object(
            viewer._load_coordinator,
            "extract_frames_by_mode",
            return_value=(False, "bad settings", 0),
        ),
        patch("coordinators.sprite_load_coordinator.QMessageBox.warning"),
    ):
        viewer._update_frame_slicing()

    assert viewer._canvas._pixmap is None
    assert viewer._grid_view._frames == []
    assert viewer._segment_preview._all_frames == []


def test_comprehensive_auto_detect_syncs_ui_to_grid_mode(qtbot, tmp_path) -> None:
    """Grid auto-detection should not be overwritten by the default CCL UI mode."""
    viewer = SpriteViewer()
    qtbot.addWidget(viewer)

    sprite_path = tmp_path / "sheet.png"
    sheet = _test_sheet(frame_count=2, frame_size=16)
    sheet.save(str(sprite_path), "PNG")
    success, error = viewer._sprite_model.load_sprite_sheet(str(sprite_path))
    assert success, error
    assert viewer._frame_extractor.get_extraction_mode() is ExtractionMode.CCL

    def fake_comprehensive_auto_detect() -> tuple[bool, DetectionResult]:
        result = DetectionResult()
        result.success = True
        result.frame_width = 16
        result.frame_height = 16
        result.offset_x = 0
        result.offset_y = 0
        result.spacing_x = 0
        result.spacing_y = 0
        result.confidence = 1.0
        result.messages = ["fake detection"]

        viewer._sprite_model._frame_width = result.frame_width
        viewer._sprite_model._frame_height = result.frame_height
        viewer._sprite_model._offset_x = result.offset_x
        viewer._sprite_model._offset_y = result.offset_y
        viewer._sprite_model._spacing_x = result.spacing_x
        viewer._sprite_model._spacing_y = result.spacing_y
        viewer._sprite_model._ccl_operations.set_current_mode(ExtractionMode.GRID)
        return True, result

    with (
        patch.object(
            viewer._sprite_model,
            "comprehensive_auto_detect",
            side_effect=fake_comprehensive_auto_detect,
        ),
        patch.object(viewer._auto_detection_controller, "_emit_detection_results"),
    ):
        viewer._auto_detection_controller.run_comprehensive_detection_with_dialog()

    assert viewer._frame_extractor.get_extraction_mode() is ExtractionMode.GRID
    assert viewer._sprite_model.get_extraction_mode() is ExtractionMode.GRID
    assert len(viewer._sprite_model.sprite_frames) == 2
    assert len(viewer._grid_view._frames) == 2
