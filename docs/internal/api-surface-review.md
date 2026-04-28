# API Surface Review

Last updated: 2026-04-28

This document records the current supported API boundary for Python Sprite Viewer after the
public-vs-private cleanup. The package roots are the primary public import surface. Lower-level
modules only expose public names when they define those names in `__all__`; internal modules set
`__all__ = []` and use leading underscores for implementation-only symbols.

## Status

The original API review flagged unclear boundaries around export internals, sprite model helpers,
UI child widgets, utility helpers, and module-level globals. Those findings are resolved by one of
two explicit decisions:

- Public symbols are listed in module/package `__all__` and, where appropriate, re-exported from
  the package root.
- Internal symbols use a leading underscore and are excluded from `__all__`.

Tests may still import underscore-prefixed implementation details from the module under test.
That is a test-only contract, not a supported application API.

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

Lower-level model modules with explicit public APIs:

- `sprite_model.core` - `SpriteModel`
- `sprite_model.extraction_mode` - `ExtractionMode`, `extraction_mode_label`
- `sprite_model.sprite_extraction` - `GridConfig`, `GridLayout`, `CCLDetectionResult`,
  `extract_grid_frames`, `validate_frame_settings`, `detect_background_color`,
  `detect_sprites_ccl_enhanced`
- `sprite_model.sprite_detection` - `DetectionResult`, `DetectionStepResult`,
  `comprehensive_auto_detect`, `detect_margins`, `detect_frame_size`, `detect_spacing`,
  `detect_rectangular_frames`, `detect_content_based`
- `sprite_model.extraction_strategies` - `ExtractionContext`, `ExtractionResult`,
  `get_extraction_strategy`

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

Lower-level export modules with explicit public APIs:

- `export.core.frame_exporter` - `BackgroundMode`, `ExportConfig`, `ExportFormat`,
  `ExportMode`, `FrameExporter`, `LayoutMode`, `SpriteSheetLayout`, `get_frame_exporter`
- `export.core.export_presets` - `ExportPreset`, `get_preset`
- `export.dialogs.export_wizard` - `ExportDialog`

### UI Composition API (`ui`)

- `ui.SpriteCanvas`
- `ui.PlaybackControls`
- `ui.FrameExtractor`
- `ui.AnimationGridView`
- `ui.AnimationSegmentPreview`
- `ui.EnhancedStatusBar`

Each defining UI module exposes only its top-level reusable widget in `__all__`.

### Utility API (`utils`)

- `utils.StyleManager`
- `utils.create_padded_pixmap`

### Manager / Controller / Coordinator API

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
- `coordinators.SpriteLoadCoordinator`
- `coordinators.SpriteLoadDependencies`

## Private Internals

These names are not part of the supported API:

- Export workers: `_ExportTask`, `_ExportWorker` (`export.core.frame_exporter`)
- Export mode dispatch: `_ExportModeSpec`, `_MODE_SPECS`, `_get_mode_spec`
  (`export.core.export_mode_spec`, `export.core.export_mode_registry`)
- Export presets registry: `_PRESETS` (`export.core.export_presets`)
- Export progress UI: `_ExportProgressDialog` (`export.dialogs.progress_dialog`)
- Export dialog mode UI wiring: `_ExportModeUiSpec`, `_UI_MODE_SPECS`, `_get_ui_mode_spec`
  (`export.dialogs.export_mode_ui_registry`)
- Export settings helpers: `_LAYOUT_MODES`, `_NAMING_PATTERNS`,
  `_ExportSettingsDataCollector`, `_ExportSettingsSummary`
  (`export.dialogs.export_settings_data`)
- Export preview helpers: `_ExportPreviewRequest`, `_ExportPreviewResult`,
  `_ExportPreviewRenderer` (`export.dialogs.export_preview_renderer`)
- Wizard scaffolding and steps: `_WizardStep`, `_WizardWidget`, `_SimpleExportOption`,
  `_ExportTypeStep`, `_CompactLivePreview`, `_ModernExportSettings`
- Sprite extraction strategy implementations: `_ExtractionStrategy`, `_GridExtractionStrategy`,
  `_CclExtractionStrategy`
- Sprite model subcomponents: `_AnimationStateManager`, `_CCLOperations`, `_FileLoader`,
  `_FileValidator`
- UI child widgets: `_FrameThumbnail`, `_SegmentPreviewItem`
- Utility helper: `_AutoButtonManager`
- Sprite viewer module globals: `_SHORTCUTS`, `_ACTIONS_REQUIRING_FRAMES`

## Deferred Decisions

- Module-file renames such as `sprite_model/sprite_animation.py` to `_sprite_animation.py`
  were not done. The class-level underscore plus `__all__ = []` makes those modules' API
  intent explicit without a broad file move.
- `run_tests.py` is a script, not part of the importable API.
- There is no reusable public `export.dialogs` wizard API. If one is needed later, remove the
  underscores from the chosen wizard types, add them to `export.dialogs.__all__`, and document
  their supported lifecycle.

## Notes

- Every importable source module under the application package roots now defines `__all__`.
- Empty package internals such as `export.core`, `export.dialogs`, and `export.dialogs.base`
  define `__all__ = []` so wildcard imports do not imply a supported sub-API.
