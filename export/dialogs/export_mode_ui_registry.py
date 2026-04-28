"""Dialog-side export-mode wiring.

Core export dispatch lives in ``export.core.export_mode_registry``. This module
keeps the widget factories and settings extraction close to the dialog layer so
``export.core`` does not import private dialog classes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from export.core.frame_exporter import ExportMode
from export.dialogs.export_settings_data import ExportSettingsDataCollector

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from export.dialogs.modern_settings_preview import (
        _ModernExportSettings,
        _SettingsPanelBase,
    )

PanelFactory = Callable[["_ModernExportSettings"], "_SettingsPanelBase"]
DataExtractor = Callable[["_ModernExportSettings"], dict[str, Any]]


@dataclass(frozen=True)
class ExportModeUiSpec:
    """Per-mode dialog behavior for settings panel construction and data collection."""

    mode: ExportMode
    panel_factory: PanelFactory
    data_extractor: DataExtractor

    def build_panel(self, parent: _ModernExportSettings) -> QWidget:
        """Construct the settings panel for this mode."""
        return self.panel_factory(parent).build()

    def collect_data(self, parent: _ModernExportSettings) -> dict[str, Any]:
        """Collect mode-specific settings from the dialog."""
        return self.data_extractor(parent)


def _sheet_panel(parent: _ModernExportSettings) -> _SettingsPanelBase:
    from export.dialogs.modern_settings_preview import _SheetSettingsPanel

    return _SheetSettingsPanel(parent)


def _individual_panel(parent: _ModernExportSettings) -> _SettingsPanelBase:
    from export.dialogs.modern_settings_preview import _IndividualSettingsPanel

    return _IndividualSettingsPanel(parent)


def _selected_panel(parent: _ModernExportSettings) -> _SettingsPanelBase:
    from export.dialogs.modern_settings_preview import _SelectedSettingsPanel

    return _SelectedSettingsPanel(parent)


def _sheet_data(parent: _ModernExportSettings) -> dict[str, Any]:
    return ExportSettingsDataCollector(parent).sheet_data()


def _individual_data(parent: _ModernExportSettings) -> dict[str, Any]:
    return ExportSettingsDataCollector(parent).individual_frames_data()


def _selected_data(parent: _ModernExportSettings) -> dict[str, Any]:
    return ExportSettingsDataCollector(parent).selected_frames_data()


UI_MODE_SPECS: dict[ExportMode, ExportModeUiSpec] = {
    ExportMode.INDIVIDUAL_FRAMES: ExportModeUiSpec(
        mode=ExportMode.INDIVIDUAL_FRAMES,
        panel_factory=_individual_panel,
        data_extractor=_individual_data,
    ),
    ExportMode.SELECTED_FRAMES: ExportModeUiSpec(
        mode=ExportMode.SELECTED_FRAMES,
        panel_factory=_selected_panel,
        data_extractor=_selected_data,
    ),
    ExportMode.SPRITE_SHEET: ExportModeUiSpec(
        mode=ExportMode.SPRITE_SHEET,
        panel_factory=_sheet_panel,
        data_extractor=_sheet_data,
    ),
    ExportMode.SEGMENTS_SHEET: ExportModeUiSpec(
        mode=ExportMode.SEGMENTS_SHEET,
        panel_factory=_sheet_panel,
        data_extractor=_sheet_data,
    ),
}


def get_ui_mode_spec(mode: ExportMode) -> ExportModeUiSpec:
    """Look up dialog behavior for an export mode."""
    return UI_MODE_SPECS[mode]
