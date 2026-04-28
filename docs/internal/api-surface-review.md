# API Surface Review

Last updated: 2026-04-28

This document captures the public API of the Python Sprite Viewer codebase after the WU6 cleanup
series resolved the public-vs-private ambiguity.

## Status

The original review (eb6fa9a) flagged several mismatches between intended and actual API
boundaries. WU6a–e addressed every finding by either re-exporting the symbol from its package
root (when public) or renaming it to a leading underscore (when internal). The findings are now
**resolved**; this document records the resulting shape.

## Public API

### Application Entry Points

- `sprite_viewer.SpriteViewer`
- `sprite_viewer.main`
- `config.Config`

### Model API (`sprite_model`)

- `sprite_model.SpriteModel`
- `sprite_model.ExtractionMode`
- `sprite_model.extraction_mode_label`
- `sprite_model.GridConfig`
- `sprite_model.CCLDetectionResult`
- `sprite_model.DetectionResult`

Modules (each exposes a curated `__all__`):

- `sprite_model.sprite_extraction` — `GridConfig`, `GridLayout`, `CCLDetectionResult`,
  `extract_grid_frames`, `validate_frame_settings`
- `sprite_model.sprite_detection` — `DetectionResult`, `DetectionStepResult`,
  `comprehensive_auto_detect`, `detect_margins`, `detect_frame_size`, `detect_spacing`,
  `detect_rectangular_frames`, `detect_content_based`
- `sprite_model.extraction_strategies` — `ExtractionContext`, `ExtractionResult`,
  `get_extraction_strategy`. (`ExtractionStrategy`, `GridExtractionStrategy`,
  `CclExtractionStrategy` remain importable but unlisted; tests use them directly as an
  internal contract.)

### Export API (`export`)

- `export.ExportDialog`
- `export.ExportPreset`
- `export.get_preset`
- `export.get_frame_exporter`
- `export.FrameExporter`
- `export.ExportConfig`
- `export.ExportFormat`
- `export.ExportMode`
- `export.LayoutMode`
- `export.BackgroundMode`
- `export.SpriteSheetLayout`

### UI Composition API (`ui`)

- `ui.SpriteCanvas`
- `ui.PlaybackControls`
- `ui.FrameExtractor`
- `ui.AnimationGridView`
- `ui.AnimationSegmentPreview`
- `ui.EnhancedStatusBar`

### Utility API (`utils`)

- `utils.StyleManager`
- `utils.create_padded_pixmap`

### Manager / Controller API

Externally composable for embedding scenarios:

- `core.AnimationController`
- `core.AnimationSegmentController`
- `core.AutoDetectionController`
- `core.ExportCoordinator`
- `managers.AnimationSegment`
- `managers.AnimationSegmentManager`
- `managers.RecentFilesManager`
- `managers.SettingsManager`
- `managers.get_recent_files_manager`
- `managers.get_settings_manager`
- `coordinators.SignalCoordinator`

## Private (Underscore-Prefixed) Internals

These were renamed during WU6b–e and are not part of the supported API. They remain importable
from their defining module for tests, but the leading underscore signals "internal":

- Export workers: `_ExportTask`, `_ExportWorker` (`export.core.frame_exporter`)
- Export presets registry: `_PRESETS` (`export.core.export_presets`)
- Wizard scaffolding: `_WizardStep`, `_WizardWidget` (`export.dialogs.base.wizard_base`)
- Wizard steps: `_SimpleExportOption`, `_ExportTypeStep` (`export.dialogs.type_selection`),
  `_CompactLivePreview`, `_ModernExportSettings` (`export.dialogs.modern_settings_preview`)
- UI child widgets: `_FrameThumbnail` (`ui.animation_grid_view`),
  `_SegmentPreviewItem` (`ui.animation_segment_preview`)
- Utility helper: `_AutoButtonManager` (`utils.ui_common`) — single consumer is
  `ui.frame_extractor`
- Sprite model subcomponents: `_AnimationStateManager` (`sprite_model.sprite_animation`),
  `_CCLOperations` (`sprite_model.sprite_ccl`), `_FileLoader`, `_FileValidator`
  (`sprite_model.sprite_file_ops`)
- Sprite viewer module globals: `_SHORTCUTS`, `_ACTIONS_REQUIRING_FRAMES` (`sprite_viewer`)

## Deferred Decisions

- **`ExportProgressDialog`** stays at module scope without re-export. Its sole consumer remains
  `ExportCoordinator`, and there is no plan to expose progress UI for external customization.
- **Module-file renames** (`sprite_model/sprite_animation.py` → `_sprite_animation.py`, etc.)
  were not done. The class-level rename already conveys "internal", and renaming the modules
  would force a coordinated sweep across `sprite_model/core.py` and ~4 test files for marginal
  benefit.
- **`run_tests.py`** is a script, not part of the importable API. No change.
- **A documented `export.dialogs` reusable wizard API** is not currently planned. If the wizard
  framework becomes reusable, drop the underscores from `_WizardStep`/`_WizardWidget` and add
  them to `export.dialogs.__all__`.

## Notes

- Tests are allowed to import the underscore-prefixed names of the module under test. This
  follows Python's "tests are friends of the implementation" convention.
- `__all__` is set at the module level in every public module so `from foo import *` semantics
  match the intended boundary, and so static tooling (basedpyright) flags any accidental import
  of an unlisted symbol.
