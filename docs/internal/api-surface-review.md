# API Surface Review

Last updated: 2026-04-28

This document captures a read-only API design review of the current Python Sprite Viewer codebase.
It focuses on symbols that are public-looking but not clearly part of a supported public API.

## Summary

The public API is only partly clear. Several package `__init__.py` files define intentional
re-exports, but many submodules expose public-looking classes and functions directly because they
lack `__all__`, use non-underscore names, and are imported directly by app code and tests.

The main ambiguity is that reusable algorithm/data types, UI implementation widgets, and internal
workflow pieces all use the same public naming style. The largest API cleanup opportunities are in:

- `export.core.frame_exporter`: required export DTOs and enums are not re-exported from `export`.
- `sprite_model.*`: model internals and reusable extraction/detection APIs are mixed together.
- `export.dialogs.*`: dialog implementation widgets look reusable, but only `ExportDialog` is the
  clear public entry point.
- `ui.*`: composite widgets are re-exported, while child implementation widgets remain directly
  importable and tested.

## Findings

### Top-Level Import Layout

- Name / location: `config`, `core`, `ui`, `export`, `sprite_model`, `managers`, `utils`,
  `sprite_viewer`; package metadata in `pyproject.toml`
- Current status: unclear / ambiguous
- Problem: The distribution name is `sprite-viewer`, but code exposes many top-level import roots.
  There is no single import namespace or console script that defines the application API boundary.
- Recommendation: Either document this as an app-internal codebase, or move toward one curated
  namespace. Avoid treating direct imports from `core.*`, `ui.*`, and implementation submodules as
  stable external API unless they are explicitly re-exported and documented.

### Export Configuration And Engine Types

- Name / location: `ExportConfig`, `ExportFormat`, `ExportMode`, `LayoutMode`,
  `BackgroundMode`, `SpriteSheetLayout`, `FrameExporter`;
  `export/core/frame_exporter.py`
- Current status: accidentally exposed but not clearly public
- Problem: These types are required by `ExportDialog` and `ExportCoordinator` workflows, but
  `export.__all__` only exports `ExportDialog`, `ExportPreset`, and `get_frame_exporter`.
- Recommendation: Make these explicitly public by adding `__all__` in
  `export/core/frame_exporter.py` and re-exporting them from `export/__init__.py`.

### Export Worker Internals

- Name / location: `ExportTask`, `ExportWorker`; `export/core/frame_exporter.py`
- Current status: unclear / ambiguous
- Problem: They are public-looking implementation details of `FrameExporter`. Tests import them
  directly, but the package API does not advertise them.
- Recommendation: Prefer making them private (`_ExportTask`, `_ExportWorker`) and testing through
  `FrameExporter`. If direct worker tests remain useful, document them as low-level test/advanced
  API and include them in module `__all__`.

### Export Presets Registry

- Name / location: `PRESETS`, `get_preset`; `export/core/export_presets.py`
- Current status: ambiguous
- Problem: `ExportPreset` is exported from `export`, but the actual preset accessor is not.
  `PRESETS` is mutable and public-looking.
- Recommendation: Re-export `get_preset` from `export`. Rename `PRESETS` to `_PRESETS`, or expose
  a read-only `EXPORT_PRESETS` mapping if callers should enumerate presets.

### Export Dialog Implementation Widgets

- Name / location: `WizardStep`, `WizardWidget`, `SimpleExportOption`, `ExportTypeStep`,
  `CompactLivePreview`, `ModernExportSettings`;
  `export/dialogs/base/wizard_base.py`, `export/dialogs/type_selection.py`,
  `export/dialogs/modern_settings_preview.py`
- Current status: accidentally exposed
- Problem: These are implementation widgets for `ExportDialog`, but their module and class names
  look public. `export/dialogs/__init__.py` is empty, so no boundary says which dialog pieces are
  supported.
- Recommendation: Keep `ExportDialog` as the public dialog API and make these implementation
  classes private, or define a documented `export.dialogs` API if the wizard framework is intended
  for reuse.

### Export Progress Dialog

- Name / location: `ExportProgressDialog`; `export/dialogs/progress_dialog.py`
- Current status: unclear
- Problem: The module has `__all__`, but the class is only used by `ExportCoordinator` and is not
  re-exported from `export.dialogs`.
- Recommendation: Leave it internal and remove public signaling, or re-export it from
  `export.dialogs` if callers should customize export progress UI.

### Extraction Mode

- Name / location: `ExtractionMode`, `extraction_mode_label`; `sprite_model/extraction_mode.py`
- Current status: accidentally hidden / ambiguous
- Problem: UI and integration code import this module directly, but `sprite_model.__all__` only
  exposes `SpriteModel`.
- Recommendation: Treat this as public model API. Add module `__all__` and re-export
  `ExtractionMode` and `extraction_mode_label` from `sprite_model/__init__.py`.

### Extraction And Detection Data/API

- Name / location: `GridConfig`, `GridLayout`, `CCLDetectionResult`, `DetectionResult`,
  `DetectionStepResult`, `extract_grid_frames`, `validate_frame_settings`,
  `detect_background_color`, `detect_sprites_ccl_enhanced`, `detect_margins`,
  `detect_frame_size`, `detect_rectangular_frames`, `detect_content_based`, `detect_spacing`,
  `comprehensive_auto_detect`;
  `sprite_model/sprite_extraction.py`, `sprite_model/sprite_detection.py`
- Current status: unclear / ambiguous
- Problem: These are real reusable algorithm and result types, but they are not exposed through a
  package API and neither module defines a public `__all__`.
- Recommendation: Create explicit public modules such as `sprite_model.extraction` and
  `sprite_model.detection`, or re-export a carefully chosen subset from `sprite_model/__init__.py`.
  Add `__all__` to both modules to distinguish public algorithms from helpers.

### Extraction Strategy Plumbing

- Name / location: `ExtractionResult`, `ExtractionContext`, `ExtractionStrategy`,
  `GridExtractionStrategy`, `CclExtractionStrategy`, `get_extraction_strategy`;
  `sprite_model/extraction_strategies.py`
- Current status: intentionally private, currently exposed
- Problem: These symbols implement `SpriteModel` dispatch. They are useful for unit tests but are
  not a user-facing model API.
- Recommendation: Move to `_extraction_strategies.py`, or add module `__all__` with only the
  minimal symbol required by `SpriteModel`. If tests need strategy access, keep that as an internal
  test contract rather than a public API.

### Sprite Model Subcomponents

- Name / location: `AnimationStateManager`, `CCLOperations`, `FileValidator`, `FileLoader`;
  `sprite_model/sprite_animation.py`, `sprite_model/sprite_ccl.py`,
  `sprite_model/sprite_file_ops.py`
- Current status: intentionally private, currently exposed
- Problem: These are composition details behind `SpriteModel`, but non-underscore module and class
  names make them appear supported.
- Recommendation: Rename modules/classes with a leading underscore, or keep them public only if
  the project wants a lower-level model API. Current architecture points to private.

### UI Child Widgets

- Name / location: `FrameThumbnail`, `SegmentPreviewItem`;
  `ui/animation_grid_view.py`, `ui/animation_segment_preview.py`
- Current status: accidentally exposed
- Problem: `ui.__all__` exports composite widgets (`AnimationGridView`,
  `AnimationSegmentPreview`, etc.), not these child widgets. Tests import the child widgets
  directly, which makes them look supported.
- Recommendation: Make them private implementation classes (`_FrameThumbnail`,
  `_SegmentPreviewItem`) and test through the composite widgets where practical. If standalone
  embedding is intended, re-export and document them from `ui/__init__.py`.

### Utility API Inconsistency

- Name / location: `StyleManager`, `AutoButtonManager`;
  `utils/styles.py`, `utils/ui_common.py`, `utils/__init__.py`
- Current status: inconsistent
- Problem: `StyleManager` is widely imported by application code but is not exported from
  `utils.__all__`. `AutoButtonManager` is exported, but appears to be an implementation helper for
  `FrameExtractor`.
- Recommendation: Export `StyleManager` explicitly from `utils/__init__.py`. Make
  `AutoButtonManager` private unless it is intended for external widget authors.

### Sprite Viewer Module Globals

- Name / location: `SHORTCUTS`, `ACTIONS_REQUIRING_FRAMES`; `sprite_viewer.py`
- Current status: accidentally exposed
- Problem: These are internal action maps used only by `SpriteViewer`, but they are non-underscore
  module globals.
- Recommendation: Rename to `_SHORTCUTS` and `_ACTIONS_REQUIRING_FRAMES`.

### Test Runner

- Name / location: `TestRunner`, `main`; `run_tests.py`
- Current status: public-looking script internals
- Problem: `run_tests.py` is a script, but `TestRunner` is a public-looking top-level class with
  no script-specific `__all__`.
- Recommendation: Leave as-is if this remains a script. If import hygiene matters, rename to
  `_TestRunner` and expose only `main`.

## Suggested API Surface

### Application Entry Points

- `sprite_viewer.SpriteViewer`
- `sprite_viewer.main`
- `config.Config`

### Model API

- `sprite_model.SpriteModel`
- `sprite_model.ExtractionMode`
- `sprite_model.extraction_mode_label`
- Optional lower-level extraction API, if supported:
  - `GridConfig`
  - `CCLDetectionResult`
  - `DetectionResult`
  - selected detection/extraction functions

### Export API

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

### UI Composition API

- `ui.SpriteCanvas`
- `ui.PlaybackControls`
- `ui.FrameExtractor`
- `ui.AnimationGridView`
- `ui.AnimationSegmentPreview`
- `ui.EnhancedStatusBar`

### Manager / Controller API

Only expose these if external composition is supported:

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

### Internal-Only Candidates

- Export wizard step widgets and preview helpers
- `ExportTask` and `ExportWorker`
- Sprite model strategy/subcomponent classes
- UI child widgets such as `FrameThumbnail` and `SegmentPreviewItem`
- Shortcut/action maps in `sprite_viewer.py`
- Private detection/extraction helpers and module loggers

## Notes

- This review examined `pyproject.toml`, `README.md`, `CLAUDE.md`, package `__init__.py` files,
  and source modules under `core`, `export`, `managers`, `sprite_model`, `ui`, `utils`, and
  `sprite_viewer.py`.
- This review does not speculate about unexamined files.
- Private underscore helpers were not called out unless a surrounding public boundary made their
  exposure ambiguous.
- Tests currently import several implementation details directly. Those imports may be useful for
  coverage, but they should not define the public API by accident.
