"""Tests for dialog-side export-mode wiring."""

from __future__ import annotations

from export.core.frame_exporter import ExportMode
from export.dialogs.export_mode_ui_registry import UI_MODE_SPECS, get_ui_mode_spec


def test_ui_mode_registry_covers_every_export_mode():
    assert set(UI_MODE_SPECS) == set(ExportMode)


def test_segments_sheet_uses_sheet_settings_ui():
    sheet_spec = get_ui_mode_spec(ExportMode.SPRITE_SHEET)
    segments_spec = get_ui_mode_spec(ExportMode.SEGMENTS_SHEET)

    assert segments_spec.panel_factory is sheet_spec.panel_factory
    assert segments_spec.data_extractor is sheet_spec.data_extractor
