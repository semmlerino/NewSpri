# Maintainability Plan

Last updated: 2026-04-27

This plan tracks the maintainer review follow-up work. Keep items scoped to
changes that reduce ownership ambiguity, hidden coupling, or test friction.

## Completed

- [x] Fix signal lifecycle ownership.
  - Commit: `f407f2c Fix signal coordinator disconnect lifecycle`
  - Files: `coordinators/signal_coordinator.py`, `tests/unit/test_signal_coordinator.py`
  - Outcome: `disconnect_all()` now disconnects tracked signal/slot pairs and reconnection no
    longer leaves duplicate live callbacks behind.

- [x] Centralize extraction mode dispatch.
  - Commit: `a39bc5b Add extraction mode strategies`
  - Files: `sprite_model/extraction_strategies.py`, `sprite_model/core.py`,
    `ui/frame_extractor.py`, `sprite_viewer.py`
  - Outcome: Grid and CCL extraction now use strategy objects through
    `SpriteModel.extract_frames_for_mode()` instead of parallel branches in the viewer and model.

- [x] Remove obsolete CCL mode-switch cache.
  - Commit: `b106af8 Remove obsolete CCL mode switch cache`
  - Files: `sprite_model/sprite_ccl.py`
  - Outcome: `CCLOperations` no longer keeps stale mode-switching logic or cached frames that
    duplicate `SpriteModel` responsibilities.

## Phase 1: SpriteViewer Responsibility Split

Rating: Needs Work

Risk: `sprite_viewer.py` is still the main long-term maintenance bottleneck. It owns window
construction, file loading, mode changes, extraction updates, playback status, keyboard handling,
drag/drop, and export launch flow.

- [ ] Extract sprite loading workflow from `SpriteViewer`.
  - Move `_load_sprites()`, `_load_sprite_file()`, `_confirm_load_over_segments()`, and recent-file
    update behavior into a small controller or service.
  - Keep UI prompts in the viewer or inject prompt callbacks so the workflow is testable without a
    full window.
  - Add tests covering successful load, canceled segment overwrite, failed load, and recent-file
    update.

- [ ] Extract extraction workflow orchestration from `SpriteViewer`.
  - Move `_on_extraction_mode_changed()`, `_update_frame_slicing()`, `_extract_frames_by_mode()`,
    and the frame-display success/failure branch behind a controller-level API.
  - Keep `FrameExtractor` as the owner of widget settings and `SpriteModel` as the owner of domain
    extraction.
  - Add tests for mode-change success, mode-change rollback, extraction failure clearing stale
    views, and first-frame display after extraction.

- [ ] Leave `SpriteViewer` focused on composition.
  - Acceptance target: setup/wiring methods remain in `SpriteViewer`; workflow decisions live in
    controllers with focused tests.
  - Run `uv run pytest tests/unit/test_sprite_viewer_init.py tests/integration/test_viewer_state_synchronization.py -q`.

## Phase 2: Export Dialog and Preview Boundaries

Rating: Needs Work

Risk: `export/dialogs/modern_settings_preview.py` mixes settings widgets, preview rendering,
validation, summary generation, and data serialization in one large module.

- [ ] Move preview layout calculations into export-core helpers.
  - Candidate helpers: sheet grid calculation, segment grid calculation, spacing/frame-dimension
    derivation, placeholder preview creation.
  - Keep QPixmap rendering behind a small renderer API so layout math can be unit tested.

- [ ] Split settings data collection from widget construction.
  - Create a settings DTO or builder that produces the data consumed by export execution.
  - Add unit tests for sheet, individual-frame, selected-frame, and segment export data.

- [ ] Preserve dialog behavior with UI smoke coverage.
  - Run `uv run pytest tests/unit/test_export_wizard_workflow.py tests/ui/test_export_dialog.py -q`.

## Phase 3: Detection and Extraction Algorithm Modules

Rating: Acceptable

Risk: `sprite_model/sprite_extraction.py` and `sprite_model/sprite_detection.py` contain cohesive
algorithm code, but each file is large enough that adding another detection path could increase
review and test cost.

- [ ] Separate CCL detection analysis helpers from grid extraction helpers.
  - Keep `GridConfig`, `GridLayout`, and grid extraction together.
  - Move CCL mask loading, bounds merging, and result analysis into a CCL detection module.

- [ ] Add focused tests before moving functions.
  - Cover irregular sprite analysis, merge behavior, grid inference, and color-key background
    detection with existing fixture patterns.

- [ ] Keep public imports stable during the move.
  - Either re-export moved functions from `sprite_model.sprite_extraction` or update callers and
    tests in one commit.

## Phase 4: Testability and Encapsulation

Rating: Acceptable

Risk: some tests still reach private attributes such as `_ccl_operations` and model internals. That
keeps refactors possible but noisy.

- [ ] Add narrow public test hooks where they represent real model state.
  - Candidate: reset CCL detection state without exposing the operations object directly.
  - Replace private test access only when the public API is clearer than the direct access.

- [ ] Keep unit tests close to ownership boundaries.
  - Model tests should assert model behavior, strategy tests should assert dispatch/dependency
    injection, UI tests should assert widget state and emitted signals.

## Standard Verification Checklist

- [ ] `uv run ruff check .`
- [ ] `uv run basedpyright`
- [ ] `uv run pytest -m unit -q`
- [ ] Focused integration/UI tests for touched workflows
- [ ] Commit each coherent slice
- [ ] Push `master`
