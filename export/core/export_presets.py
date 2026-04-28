"""Export Presets System - predefined export configurations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .export_mode_spec import ExportModeSpec
from .frame_exporter import (
    BackgroundMode,
    ExportConfig,
    ExportMode,
    ExportWorker,
    LayoutMode,
    SpriteSheetLayout,
)

if TYPE_CHECKING:
    from PySide6.QtGui import QPixmap

    from core.export_coordinator import ExportCoordinator
    from export.dialogs.modern_settings_preview import (
        ModernExportSettings,
        _SettingsPanelBase,
    )


@dataclass
class ExportPreset:
    """Defines an export preset configuration."""

    name: str
    display_name: str
    icon: str  # Unicode emoji or icon identifier
    description: str
    mode: ExportMode
    format: str
    scale: float
    use_cases: list[str]  # Examples of when to use this preset
    sprite_sheet_layout: SpriteSheetLayout | None = None
    short_description: str | None = None


# All available presets keyed by name
PRESETS: dict[str, ExportPreset] = {
    "individual_frames": ExportPreset(
        name="individual_frames",
        display_name="Individual Frames",
        icon="📁",
        description="Export frames as separate PNG files",
        mode=ExportMode.INDIVIDUAL_FRAMES,
        format="PNG",
        scale=1.0,
        use_cases=[
            "Game assets",
            "Video editing",
            "Frame analysis",
            "Individual editing",
            "Key frames",
            "Specific poses",
        ],
        short_description="Perfect for editing",
    ),
    "sprite_sheet": ExportPreset(
        name="sprite_sheet",
        display_name="Sprite Sheet",
        icon="📋",
        description="Combine all frames into a single image",
        mode=ExportMode.SPRITE_SHEET,
        format="PNG",
        scale=1.0,
        use_cases=["Web games", "Texture atlases", "CSS sprites", "Unity animations"],
        sprite_sheet_layout=SpriteSheetLayout(
            mode=LayoutMode.AUTO, spacing=0, background_mode=BackgroundMode.TRANSPARENT
        ),
        short_description="Optimized for game engines",
    ),
    "selected_frames": ExportPreset(
        name="selected_frames",
        display_name="Selected Frames",
        icon="🎯",
        description="Export only specific frames you choose",
        mode=ExportMode.SELECTED_FRAMES,
        format="PNG",
        scale=1.0,
        use_cases=["Key frames", "Specific poses", "Reference frames", "Partial exports"],
        short_description="Export specific frames",
    ),
    "segments_per_row": ExportPreset(
        name="segments_per_row",
        display_name="Segments Per Row",
        icon="🎬",
        description="Export sprite sheet with each segment on its own row",
        mode=ExportMode.SEGMENTS_SHEET,
        format="PNG",
        scale=1.0,
        use_cases=[
            "Game engines",
            "Animation tools",
            "Organized sprite sheets",
            "State-based animations",
        ],
        sprite_sheet_layout=SpriteSheetLayout(
            mode=LayoutMode.SEGMENTS_PER_ROW,
            spacing=0,
            background_mode=BackgroundMode.TRANSPARENT,
        ),
        short_description="One row per animation",
    ),
}


def get_preset(name: str) -> ExportPreset | None:
    """Get a preset by name."""
    return PRESETS.get(name)


# ============================================================================
# Mode-spec registry (separate axis from PRESETS)
# ============================================================================
#
# PRESETS: user-facing configuration recipes (multiple per mode possible).
# MODE_SPECS: machinery dispatch — one per ExportMode — wires together the
# settings panel, data extractor, worker method, and coordinator method.
#
# UI-side callables (panel factories + data extractors) live in
# export/dialogs/modern_settings_preview.py, which imports from this module.
# To break the resulting import cycle the factory/extractor entries are wrapped
# in lazy import shims defined below.


def _sheet_panel(parent: ModernExportSettings) -> _SettingsPanelBase:
    from export.dialogs.modern_settings_preview import _SheetSettingsPanel

    return _SheetSettingsPanel(parent)


def _individual_panel(parent: ModernExportSettings) -> _SettingsPanelBase:
    from export.dialogs.modern_settings_preview import _IndividualSettingsPanel

    return _IndividualSettingsPanel(parent)


def _selected_panel(parent: ModernExportSettings) -> _SettingsPanelBase:
    from export.dialogs.modern_settings_preview import _SelectedSettingsPanel

    return _SelectedSettingsPanel(parent)


def _sheet_data(parent: ModernExportSettings) -> dict[str, Any]:
    return parent._get_sheet_data()


def _individual_data(parent: ModernExportSettings) -> dict[str, Any]:
    return parent._get_individual_frames_data()


def _selected_data(parent: ModernExportSettings) -> dict[str, Any]:
    return parent._get_selected_frames_data()


def _coord_export_frames(
    coord: ExportCoordinator, config: ExportConfig, frames: list[QPixmap] | None
) -> None:
    coord._export_frames(config, frames=frames)


def _coord_export_segments_per_row(
    coord: ExportCoordinator, config: ExportConfig, frames: list[QPixmap] | None
) -> None:
    # frames argument intentionally unused — segment export reads from the model.
    del frames
    coord._export_segments_per_row(config)


MODE_SPECS: dict[ExportMode, ExportModeSpec] = {
    ExportMode.INDIVIDUAL_FRAMES: ExportModeSpec(
        mode=ExportMode.INDIVIDUAL_FRAMES,
        display_name="Individual Frames",
        panel_factory=_individual_panel,
        data_extractor=_individual_data,
        worker_method=ExportWorker._export_individual_frames,
        coordinator_method=_coord_export_frames,
    ),
    ExportMode.SELECTED_FRAMES: ExportModeSpec(
        mode=ExportMode.SELECTED_FRAMES,
        display_name="Selected Frames",
        panel_factory=_selected_panel,
        data_extractor=_selected_data,
        worker_method=ExportWorker._export_individual_frames,
        coordinator_method=_coord_export_frames,
    ),
    ExportMode.SPRITE_SHEET: ExportModeSpec(
        mode=ExportMode.SPRITE_SHEET,
        display_name="Sprite Sheet",
        panel_factory=_sheet_panel,
        data_extractor=_sheet_data,
        worker_method=ExportWorker._export_sprite_sheet,
        coordinator_method=_coord_export_frames,
    ),
    ExportMode.SEGMENTS_SHEET: ExportModeSpec(
        mode=ExportMode.SEGMENTS_SHEET,
        display_name="Segments Per Row Sheet",
        panel_factory=_sheet_panel,
        data_extractor=_sheet_data,
        worker_method=ExportWorker._export_sprite_sheet,
        coordinator_method=_coord_export_segments_per_row,
    ),
}


def get_mode_spec(mode: ExportMode) -> ExportModeSpec:
    """Look up the ExportModeSpec for a given mode.

    Raises KeyError if the mode is not registered (i.e. the registry is out of
    sync with the ExportMode enum) — that's a programmer error, not a runtime
    condition to handle silently.
    """
    return MODE_SPECS[mode]
