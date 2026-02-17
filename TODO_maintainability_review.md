**Maintainability TODO**

Last updated: 2026-02-17

## Done

- **Typed export system**: `ExportConfig` dataclass replaces `dict[str, Any]` handoff. `LayoutMode`, `BackgroundMode` enums replace string comparisons. `ExportPreset.mode` is `ExportMode` enum. All `.value` comparisons converted to enum identity (`is`).
- **Structured detection protocol**: `DetectionResult` with `DetectionStepResult` list replaces string parsing. `extract_confidence_from_message` deleted. Controller uses structured step iteration for confidence updates.
- **Config cleanup**: Removed `Config.Export.LAYOUT_MODES`, `DEFAULT_LAYOUT_MODE`, `BACKGROUND_MODES`, `DEFAULT_BACKGROUND_MODE` (replaced by enum defaults).
- **Stale test reference**: Fixed `_debounce_timer` → `_preview_timer` in `test_export_integrated_workflow.py`.
- **File I/O exception catches narrowed**: `sprite_file_ops.py` (`OSError`), `animation_segment_manager.py` (`OSError`/`JSONDecodeError`/`ValueError`/`KeyError`), `frame_exporter.py` (`OSError`). Remaining broad catches in detection/extraction/controller are intentional boundary catches for complex numpy/PIL operations.
- **Dead code cleanup**: `animation_segment_widget.py` deleted. Legacy compat layers removed in prior commits. Remaining: 3 test-only settings methods (`save_extraction_settings`, `save_display_settings`, `save_animation_settings`) — low priority.
- **Styling unified**: Migrated all `Config.Styles` constants to `StyleManager` static methods. Deleted `Config.Styles` class. All styling now flows through `utils/styles.py`.
- **Export tests strengthened**: Wizard navigation tests verify step index. Config preparation tests verify field values (not just `hasattr`). Added tests for selected-frames and current-frame export modes.
- **Pre-existing test failures fixed**: `test_segment_creation_workflow` (signal not connected), `test_segment_preview_after_grid_refresh` (missing sync call), `test_file_operations` exception types (matched to narrowed catches).

## Deferred (not worth the churn for project scale)

These were identified in the original review but are over-engineering for a personal project:

- **Strategy registry for export modes** — fixed set of modes; enum typing is sufficient
- **Break SpriteViewer into AppShell + controllers** — large refactor, works fine as-is
- **DI for singletons** — not justified at this scale
- **Segment state consolidation** — revisit only if sync bugs surface
- **SignalCoordinator callback typing** — `object` callbacks work, tightening adds churn
