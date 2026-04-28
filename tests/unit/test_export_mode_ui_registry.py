"""Tests for dialog-side export-mode wiring."""

from __future__ import annotations

import pytest

from export.core.export_presets import get_preset
from export.core.frame_exporter import ExportMode
from export.dialogs.export_mode_ui_registry import UI_MODE_SPECS, get_ui_mode_spec
from export.dialogs.modern_settings_preview import _ModernExportSettings

pytestmark = pytest.mark.requires_qt


def test_ui_mode_registry_covers_every_export_mode():
    assert set(UI_MODE_SPECS) == set(ExportMode)


def test_segments_sheet_uses_sheet_settings_ui():
    sheet_spec = get_ui_mode_spec(ExportMode.SPRITE_SHEET)
    segments_spec = get_ui_mode_spec(ExportMode.SEGMENTS_SHEET)

    assert segments_spec.panel_factory is sheet_spec.panel_factory
    assert segments_spec.data_extractor is sheet_spec.data_extractor


def test_sheet_data_collection_is_outside_settings_widget(qapp):
    step = _ModernExportSettings(frame_count=4, current_frame=0, sprites=[])
    step._setup_for_preset(get_preset("sprite_sheet"))

    step.path_edit.setText("/tmp/export")
    step.sheet_filename.setText("atlas")
    step.spacing_slider.setValue(3)
    step.bg_combo.setCurrentIndex(1)

    data = step.get_data()

    assert data["output_dir"] == "/tmp/export"
    assert data["single_filename"] == "atlas"
    assert data["spacing"] == 3
    assert data["background_color"] == (255, 255, 255, 255)
    assert not hasattr(step, "_get_sheet_data")


def test_individual_data_collection_uses_shared_pattern_state(qapp):
    step = _ModernExportSettings(frame_count=4, current_frame=0, sprites=[])
    step._setup_for_preset(get_preset("individual_frames"))

    step.base_name.setText("hero")
    pattern_group = step._settings_widgets["pattern_group"]
    pattern_group.button(1).setChecked(True)

    data = step.get_data()

    assert data["base_name"] == "hero"
    assert data["pattern"] == "{name}-{index}"
    assert not hasattr(step, "_get_individual_frames_data")


def test_selected_frame_data_collection_is_outside_settings_widget(qapp):
    step = _ModernExportSettings(frame_count=4, current_frame=1, sprites=[])
    step._setup_for_preset(get_preset("selected_frames"))

    step.frame_list.clearSelection()
    step.frame_list.item(0).setSelected(True)
    step.frame_list.item(3).setSelected(True)
    step.selected_base_name.setText("selected")

    data = step.get_data()

    assert data["selected_indices"] == [0, 3]
    assert data["base_name"] == "selected"
    assert not hasattr(step, "_get_selected_frames_data")
