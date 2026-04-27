"""Unit tests for extraction strategy dispatch and behavior."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor, QPixmap

from sprite_model import SpriteModel
from sprite_model.extraction_mode import ExtractionMode
from sprite_model.extraction_strategies import (
    CclExtractionStrategy,
    ExtractionContext,
    GridExtractionStrategy,
    get_extraction_strategy,
)
from sprite_model.sprite_ccl import CCLOperations
from sprite_model.sprite_extraction import CCLDetectionResult, GridConfig

pytestmark = pytest.mark.requires_qt


def _sprite_sheet(width: int = 64, height: int = 32) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(255, 255, 255))
    return pixmap


def test_get_extraction_strategy_returns_mode_strategy() -> None:
    assert get_extraction_strategy(ExtractionMode.GRID).mode is ExtractionMode.GRID
    assert get_extraction_strategy(ExtractionMode.CCL).mode is ExtractionMode.CCL


def test_grid_strategy_extracts_frames_and_sets_grid_mode(qapp) -> None:
    ccl_operations = CCLOperations()
    ccl_operations.set_current_mode(ExtractionMode.CCL)
    context = ExtractionContext(
        sprite_sheet=_sprite_sheet(),
        sprite_sheet_path="",
        ccl_operations=ccl_operations,
    )

    result = GridExtractionStrategy().extract(context, GridConfig(width=32, height=32))

    assert result.success is True
    assert result.frame_count == 2
    assert len(result.frames) == 2
    assert ccl_operations.get_extraction_mode() is ExtractionMode.GRID


def test_grid_strategy_rejects_missing_config(qapp) -> None:
    ccl_operations = CCLOperations()
    context = ExtractionContext(
        sprite_sheet=_sprite_sheet(),
        sprite_sheet_path="",
        ccl_operations=ccl_operations,
    )

    result = GridExtractionStrategy().extract(context)

    assert result.success is False
    assert result.frame_count == 0
    assert "settings are not configured" in result.message


def test_ccl_strategy_uses_injected_detection_dependencies(qapp, tmp_path) -> None:
    sprite_path = tmp_path / "sheet.png"
    _sprite_sheet().save(str(sprite_path), "PNG")
    detected_paths: list[str] = []
    background_paths: list[str] = []

    def detect_sprites(path: str) -> CCLDetectionResult:
        detected_paths.append(path)
        return CCLDetectionResult(success=True, ccl_sprite_bounds=[(0, 0, 32, 32)])

    def detect_background(path: str) -> tuple[tuple[int, int, int], int]:
        background_paths.append(path)
        return (255, 255, 255), 10

    ccl_operations = CCLOperations()
    context = ExtractionContext(
        sprite_sheet=_sprite_sheet(),
        sprite_sheet_path=str(sprite_path),
        ccl_operations=ccl_operations,
        detect_sprites_ccl_enhanced=detect_sprites,
        detect_background_color=detect_background,
    )

    result = CclExtractionStrategy().extract(context)

    assert result.success is True
    assert result.frame_count == 1
    assert len(result.frames) == 1
    assert detected_paths == [str(sprite_path)]
    assert background_paths == [str(sprite_path)]
    assert ccl_operations.get_extraction_mode() is ExtractionMode.CCL


def test_sprite_model_extract_frames_for_mode_updates_grid_state(qapp, tmp_path) -> None:
    sprite_path = tmp_path / "sheet.png"
    _sprite_sheet().save(str(sprite_path), "PNG")

    model = SpriteModel()
    success, message = model.load_sprite_sheet(str(sprite_path))
    assert success, message

    success, message, frame_count = model.extract_frames_for_mode(
        ExtractionMode.GRID,
        GridConfig(width=16, height=16, offset_x=0, offset_y=0, spacing_x=0, spacing_y=0),
    )

    assert success is True
    assert frame_count == 8
    assert model.frame_width == 16
    assert model.frame_height == 16
    assert model.get_extraction_mode() is ExtractionMode.GRID
