"""Extraction strategy implementations for sprite frame modes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from sprite_model.extraction_mode import ExtractionMode
from sprite_model.sprite_extraction import (
    CCLDetectionResult,
    GridConfig,
    detect_background_color,
    detect_sprites_ccl_enhanced,
    extract_grid_frames,
)

if TYPE_CHECKING:
    from PySide6.QtGui import QPixmap

    from sprite_model.sprite_ccl import _CCLOperations


__all__ = ["ExtractionContext", "ExtractionResult", "get_extraction_strategy"]


DetectSpritesCcl = Callable[[str], CCLDetectionResult | None]
DetectBackgroundColor = Callable[[str], tuple[tuple[int, int, int], int] | None]


@dataclass(frozen=True)
class ExtractionResult:
    """Result returned by an extraction strategy."""

    success: bool
    message: str
    frame_count: int
    frames: list[QPixmap]


@dataclass(frozen=True)
class ExtractionContext:
    """Shared dependencies needed by extraction strategies."""

    sprite_sheet: QPixmap
    sprite_sheet_path: str
    ccl_operations: _CCLOperations
    detect_sprites_ccl_enhanced: DetectSpritesCcl = detect_sprites_ccl_enhanced
    detect_background_color: DetectBackgroundColor = detect_background_color


class ExtractionStrategy(Protocol):
    """Mode-specific frame extraction behavior."""

    mode: ExtractionMode

    def extract(
        self,
        context: ExtractionContext,
        grid_config: GridConfig | None = None,
    ) -> ExtractionResult:
        """Extract frames for this strategy's mode."""
        ...


class GridExtractionStrategy:
    """Extract frames using a rectangular grid."""

    mode = ExtractionMode.GRID

    def extract(
        self,
        context: ExtractionContext,
        grid_config: GridConfig | None = None,
    ) -> ExtractionResult:
        """Extract grid frames from the current sprite sheet."""
        if grid_config is None:
            return ExtractionResult(
                success=False,
                message="Grid extraction settings are not configured",
                frame_count=0,
                frames=[],
            )

        success, message, frames, skipped = extract_grid_frames(context.sprite_sheet, grid_config)
        if not success:
            return ExtractionResult(False, message, 0, [])

        if not frames:
            return ExtractionResult(
                success=False,
                message="No frames could be extracted with current settings. Check frame size and offsets.",
                frame_count=0,
                frames=[],
            )

        context.ccl_operations.set_current_mode(self.mode)

        if skipped > 0:
            result_message = (
                f"Extracted {len(frames)} frames ({skipped} skipped - exceeded sheet boundaries)"
            )
        else:
            result_message = f"Extracted {len(frames)} frames"
        return ExtractionResult(True, result_message, len(frames), frames)


class CclExtractionStrategy:
    """Extract frames using connected-component labeling."""

    mode = ExtractionMode.CCL

    def extract(
        self,
        context: ExtractionContext,
        grid_config: GridConfig | None = None,
    ) -> ExtractionResult:
        """Extract CCL frames from the current sprite sheet."""
        success, message, frame_count, frames = context.ccl_operations.extract_ccl_frames(
            sprite_sheet=context.sprite_sheet,
            sprite_sheet_path=context.sprite_sheet_path,
            detect_sprites_ccl_enhanced=context.detect_sprites_ccl_enhanced,
            detect_background_color=context.detect_background_color,
        )

        if success:
            context.ccl_operations.set_current_mode(self.mode)

        return ExtractionResult(success, message, frame_count, frames if success else [])


_STRATEGIES: dict[ExtractionMode, ExtractionStrategy] = {
    ExtractionMode.GRID: GridExtractionStrategy(),
    ExtractionMode.CCL: CclExtractionStrategy(),
}


def get_extraction_strategy(mode: ExtractionMode) -> ExtractionStrategy:
    """Return the extraction strategy for a mode."""
    return _STRATEGIES[mode]
