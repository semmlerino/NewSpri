"""
Unit tests for export.core.export_presets.

Pins the preset registry shape and lookup contract so adding/removing presets
is an explicit, reviewed change.
"""

from __future__ import annotations

import pytest

from export.core.export_presets import _PRESETS, ExportPreset, get_preset
from export.core.frame_exporter import ExportMode

EXPECTED_PRESET_NAMES = frozenset(
    {
        "individual_frames",
        "sprite_sheet",
        "selected_frames",
        "segments_per_row",
    }
)


# ============================================================================
# Registry shape
# ============================================================================


class TestPresetRegistryShape:
    @pytest.mark.smoke
    def test_all_expected_presets_are_registered(self):
        assert set(_PRESETS.keys()) == EXPECTED_PRESET_NAMES

    @pytest.mark.smoke
    def test_each_preset_exposes_required_fields(self):
        for name, preset in _PRESETS.items():
            assert isinstance(preset, ExportPreset), name
            assert preset.name == name, f"{name}: preset.name disagrees with key"
            assert preset.display_name, name
            assert preset.icon, name
            assert preset.description, name
            assert isinstance(preset.mode, ExportMode), name
            assert preset.format, name
            assert preset.scale > 0, name
            assert isinstance(preset.use_cases, list) and preset.use_cases, name

    def test_preset_modes_are_unique(self):
        modes = [preset.mode for preset in _PRESETS.values()]
        assert len(modes) == len(set(modes)), "presets must map 1:1 to ExportMode values"

    def test_sprite_sheet_modes_have_layout(self):
        for preset in _PRESETS.values():
            if preset.mode in (ExportMode.SPRITE_SHEET, ExportMode.SEGMENTS_SHEET):
                assert preset.sprite_sheet_layout is not None, (
                    f"{preset.name}: sprite-sheet style preset must define layout"
                )


# ============================================================================
# Lookup
# ============================================================================


class TestGetPreset:
    @pytest.mark.parametrize("name", sorted(EXPECTED_PRESET_NAMES))
    def test_known_preset_lookup_returns_instance(self, name: str):
        preset = get_preset(name)
        assert preset is not None
        assert preset.name == name

    def test_unknown_preset_returns_none(self):
        assert get_preset("nonexistent_preset") is None

    def test_empty_string_returns_none(self):
        assert get_preset("") is None
