"""Tests for export preview pixmap rendering."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor, QPixmap

from export.core.frame_exporter import BackgroundMode, ExportMode, LayoutMode
from export.dialogs.export_preview_renderer import (
    _ExportPreviewRenderer,
    _ExportPreviewRequest,
)
from managers import AnimationSegment

pytestmark = pytest.mark.requires_qt


def _sprites(count: int, width: int = 10, height: int = 8) -> list[QPixmap]:
    sprites: list[QPixmap] = []
    for index in range(count):
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor.fromHsv((index * 45) % 360, 200, 200))
        sprites.append(pixmap)
    return sprites


def test_sheet_preview_renders_from_explicit_request(qapp):
    renderer = _ExportPreviewRenderer()

    result = renderer.render(
        _ExportPreviewRequest(
            mode=ExportMode.SPRITE_SHEET,
            sprites=_sprites(4),
            layout_mode=LayoutMode.COLUMNS,
            columns=2,
            spacing=1,
            background_mode=BackgroundMode.SOLID,
            background_color=(255, 255, 255, 255),
        )
    )

    assert result.pixmap.width() == 21
    assert result.pixmap.height() == 17
    assert result.info_text == "Sprite Sheet: 2x2 grid, 21x17px"


def test_segments_preview_uses_supplied_segments(qapp):
    renderer = _ExportPreviewRenderer()

    result = renderer.render(
        _ExportPreviewRequest(
            mode=ExportMode.SEGMENTS_SHEET,
            sprites=_sprites(4, width=10, height=10),
            spacing=2,
            segments=[
                AnimationSegment("Walk", 0, 1),
                AnimationSegment("Run", 2, 3),
            ],
        )
    )

    assert result.pixmap.width() == 22
    assert result.pixmap.height() == 22
    assert result.info_text == "Segments Per Row: 2 segments"


def test_segments_preview_without_segments_returns_placeholder(qapp):
    renderer = _ExportPreviewRenderer()

    result = renderer.render(
        _ExportPreviewRequest(
            mode=ExportMode.SEGMENTS_SHEET,
            sprites=_sprites(2),
            segments=[],
        )
    )

    assert result.pixmap.width() == 400
    assert result.pixmap.height() == 200
    assert result.info_text == "Segments Per Row: No segments"


def test_segments_preview_without_segment_source_preserves_unavailable_message(qapp):
    renderer = _ExportPreviewRenderer()

    result = renderer.render(
        _ExportPreviewRequest(
            mode=ExportMode.SEGMENTS_SHEET,
            sprites=_sprites(2),
            segments_available=False,
        )
    )

    assert result.info_text == "Segments Per Row: No segments defined"


def test_selected_frames_preview_reports_selection_count(qapp):
    renderer = _ExportPreviewRenderer()

    result = renderer.render(
        _ExportPreviewRequest(
            mode=ExportMode.SELECTED_FRAMES,
            sprites=_sprites(6),
            selected_indices=[1, 3, 5],
        )
    )

    assert result.info_text == "Selected: 3 frames"
