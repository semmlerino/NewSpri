"""Core export-mode dispatch registry.

The registry maps each ``ExportMode`` to the worker and coordinator behavior
needed to run that mode. Dialog panel construction and settings extraction live
in ``export.dialogs.export_mode_ui_registry``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from export.core.export_mode_spec import ExportModeSpec
from export.core.frame_exporter import ExportMode, ExportWorker

if TYPE_CHECKING:
    from collections.abc import Sequence

    from PySide6.QtGui import QPixmap

    from core.export_coordinator import ExportCoordinator
    from export.core.frame_exporter import ExportConfig


def _coord_export_frames(
    coord: ExportCoordinator, config: ExportConfig, frames: Sequence[QPixmap] | None
) -> None:
    coord.export_frames(config, frames=frames)


def _coord_export_segments_per_row(
    coord: ExportCoordinator, config: ExportConfig, frames: Sequence[QPixmap] | None
) -> None:
    # Segment export reads frames from the model so it can validate segment bounds
    # against the same source of truth used by the segment manager.
    del frames
    coord.export_segments_per_row(config)


MODE_SPECS: dict[ExportMode, ExportModeSpec] = {
    ExportMode.INDIVIDUAL_FRAMES: ExportModeSpec(
        mode=ExportMode.INDIVIDUAL_FRAMES,
        display_name="Individual Frames",
        worker_method=ExportWorker._export_individual_frames,
        coordinator_method=_coord_export_frames,
    ),
    ExportMode.SELECTED_FRAMES: ExportModeSpec(
        mode=ExportMode.SELECTED_FRAMES,
        display_name="Selected Frames",
        worker_method=ExportWorker._export_individual_frames,
        coordinator_method=_coord_export_frames,
    ),
    ExportMode.SPRITE_SHEET: ExportModeSpec(
        mode=ExportMode.SPRITE_SHEET,
        display_name="Sprite Sheet",
        worker_method=ExportWorker._export_sprite_sheet,
        coordinator_method=_coord_export_frames,
    ),
    ExportMode.SEGMENTS_SHEET: ExportModeSpec(
        mode=ExportMode.SEGMENTS_SHEET,
        display_name="Segments Per Row Sheet",
        worker_method=ExportWorker._export_sprite_sheet,
        coordinator_method=_coord_export_segments_per_row,
    ),
}


def get_mode_spec(mode: ExportMode) -> ExportModeSpec:
    """Look up the core export-mode dispatch record."""
    return MODE_SPECS[mode]
