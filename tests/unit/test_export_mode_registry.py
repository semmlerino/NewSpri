"""Tests for the core export-mode dispatch registry."""

from __future__ import annotations

from export.core.export_mode_registry import MODE_SPECS, get_mode_spec
from export.core.export_mode_spec import ExportModeSpec
from export.core.frame_exporter import ExportMode, _ExportWorker


def test_core_mode_registry_covers_every_export_mode():
    assert set(MODE_SPECS) == set(ExportMode)


def test_core_mode_specs_do_not_expose_dialog_hooks():
    spec = get_mode_spec(ExportMode.INDIVIDUAL_FRAMES)

    assert isinstance(spec, ExportModeSpec)
    assert not hasattr(spec, "panel_factory")
    assert not hasattr(spec, "data_extractor")


def test_selected_frames_reuses_individual_worker_method():
    spec = get_mode_spec(ExportMode.SELECTED_FRAMES)

    assert spec.worker_method is _ExportWorker._export_individual_frames
