**Maintainability TODO**

Last updated: 2026-02-17

## Done

- **Typed export system**: `ExportConfig` dataclass replaces `dict[str, Any]` handoff. `LayoutMode`, `BackgroundMode` enums replace string comparisons. `ExportPreset.mode` is `ExportMode` enum. All `.value` comparisons converted to enum identity (`is`).
- **Structured detection protocol**: `DetectionResult` with `DetectionStepResult` list replaces string parsing. `extract_confidence_from_message` deleted. Controller uses structured step iteration for confidence updates.
- **Config cleanup**: Removed `Config.Export.LAYOUT_MODES`, `DEFAULT_LAYOUT_MODE`, `BACKGROUND_MODES`, `DEFAULT_BACKGROUND_MODE` (replaced by enum defaults).

## Remaining (worth doing)

### 1. Fix stale test reference
The integration test `tests/integration/test_export_integrated_workflow.py:51` checks `_debounce_timer` but runtime uses `_preview_timer`. This causes the test to silently skip its wait logic.

### 2. Narrow broad `except Exception` catches
43 occurrences across 16 files. Worst offenders in critical paths:
- `sprite_model/sprite_detection.py` (11 catches)
- `core/auto_detection_controller.py` (5 catches)
- `sprite_model/sprite_extraction.py` (5 catches)
- `sprite_model/sprite_ccl.py` (3 catches)

Replace with specific exceptions where the failure mode is known. Keep broad catches only at top-level boundaries where enriching context and preserving traceback.

### 3. Unify styling system
Two overlapping systems: `Config.Styles` (used in 6 files) and `StyleManager` in `utils/styles.py`, plus inline styles in UI files. Pick one and migrate the other.

### 4. Remove dead code / unused APIs
- Legacy/compat layers in `managers/animation_segment_manager.py:143`, `ui/animation_segment_widget.py:43`
- Settings APIs that appear mostly test-exercised: `managers/settings_manager.py:162`
- Stale milestone-history comments in `sprite_model/core.py`, `ui/frame_extractor.py`

### 5. Strengthen shallow export tests
- `tests/ui/test_export_dialog.py` — assertion-light
- `tests/unit/test_export_wizard_workflow.py` — tests callability, not outcomes
- Add behavior tests for current-frame export semantics and `ExportConfig` translation

## Deferred (not worth the churn for project scale)

These were identified in the original review but are over-engineering for a personal project:

- **Strategy registry for export modes** — fixed set of modes; enum typing is sufficient
- **Break SpriteViewer into AppShell + controllers** — large refactor, works fine as-is
- **DI for singletons** — not justified at this scale
- **Segment state consolidation** — revisit only if sync bugs surface
- **SignalCoordinator callback typing** — `object` callbacks work, tightening adds churn
