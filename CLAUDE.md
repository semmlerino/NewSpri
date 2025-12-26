# CLAUDE.md

## Quick Reference

### Essential Commands
```bash
# Run application
python sprite_viewer.py

# Testing (pytest is configured in pyproject.toml with sensible defaults)
uv run pytest                              # All tests (serial, useful summary)
uv run pytest tests/unit/                  # Unit tests only
uv run pytest tests/integration/           # Integration tests
uv run pytest -m unit                      # By marker
uv run pytest path/to/test.py::test_name   # Single test
uv run pytest --lf                         # Re-run only failures
uv run pytest -k "test_name" -vv --maxfail=1 --tb=long  # Debug one test

# Linting and type checking
uv run ruff check .                        # Lint
uv run ruff check . --fix                  # Lint and auto-fix
uv run ruff format .                       # Format code
uv run basedpyright                        # Type check

# Install dev dependencies
uv sync --all-extras
```

### Test Markers
Key markers: `unit`, `integration`, `ui`, `slow`, `smoke`, `regression`, `requires_qt`, `signal_test`

Full list in `pyproject.toml` under `[tool.pytest.ini_options].markers`.

## Project Overview

PySide6 sprite sheet animation viewer/editor with MVC architecture. Features: animation splitting, segment management, comprehensive export.

## Architecture

```
Root Directory:
  sprite_viewer.py          - Main application window
  sprite_canvas.py          - Zoom/pan display widget
  playback_controls.py      - Animation control panel
  frame_extractor.py        - Configuration interface
  animation_grid_view.py    - Animation splitting interface
  animation_segment_preview.py - Segment preview panel
  animation_controller.py   - Animation timing control
  animation_segment_controller.py - Segment management
  auto_detection_controller.py - Frame detection logic
  animation_segment_manager.py - Segment persistence
  menu_manager.py           - Menu system
  config.py                 - Centralized configuration
  styles.py                 - Centralized styling

sprite_model/               - Data layer & algorithms
coordinators/               - Component coordination
export/                     - Export system (core/, dialogs/, widgets/)
tests/                      - Test suite (unit/, integration/, ui/, performance/)
archive/                    - Historical documentation (ignore for development)
```

## Critical Patterns

### Configuration - No Magic Numbers
```python
from config import Config

# CORRECT
button_height = Config.UI.PLAYBACK_BUTTON_MIN_HEIGHT

# WRONG
button_height = 40
```

Key config classes: `Config.Canvas`, `Config.Animation`, `Config.FrameExtraction`, `Config.UI`, `Config.Drawing`, `Config.File`, `Config.Export`, `Config.AnimationSplitting`

### Signal/Slot Communication
Component communication uses Qt signals. Key signals:
- `SpriteModel.frameChanged(int, int)` - Frame updates
- `SpriteModel.dataLoaded(str)` - New sprite loaded
- `AnimationController.statusChanged(str)` - Status updates
- `AutoDetectionController.detectionCompleted(...)` - Detection results
- `AnimationGridView.segmentCreated(segment)` / `segmentDeleted(name)` - Segment changes
- `AnimationSegmentManager.segmentRemoved(name)` - Manager removal

### Import Organization
1. Standard library
2. Third-party (PySide6)
3. Local (config, components)

## API Contracts - Must Follow

These are real API contracts discovered through testing. Violating them causes runtime errors:

| Component | Correct API | Wrong API |
|-----------|-------------|-----------|
| `PlaybackControls` | `set_current_frame(n)` | `on_frame_changed(n)` |
| `SpriteModel.sprite_frames` | Read-only property | Cannot be set directly |
| `FrameExtractor` | `width_spin`, `height_spin` | `frame_width_spin` |
| `ViewCoordinator` zoom | `canvas.set_zoom(level)` | `zoom_in()`, `zoom_out()` |
| `ViewCoordinator` grid | `set_grid_overlay(bool)` | `toggle_grid()` |

## Segment System

Segments are saved as JSON in `.sprite_segments/` directory alongside sprite sheets:
```json
{
  "sprite_sheet": "character.png",
  "segments": [{"name": "Walk", "start_frame": 0, "end_frame": 7, "color": [233, 30, 99]}]
}
```

Key components:
- `AnimationGridView` - Frame selection, visualization
- `AnimationSegmentManager` - Persistence
- `AnimationSegmentController` - Coordination
- `AnimationSegmentPreview` - Playback

When loading sprites: `set_sprite_context()` must be called to trigger segment loading, then `sync_segments_with_manager()` to synchronize with grid view.

## Export System

```
export/
  core/frame_exporter.py    - Main export engine
  core/export_settings.py   - Export configuration
  dialogs/export_wizard.py  - Main export wizard dialog
  widgets/sprite_preview_widget.py - Sprite sheet preview
  widgets/settings_widgets.py - Settings controls
```

Formats: PNG, JPG, BMP, GIF. Scale factors: 0.5x-4.0x. Shortcuts: Ctrl+E (all), Ctrl+Shift+E (current).

## Testing Notes

### Test Philosophy
- **Test logic more than widgets** - Put business logic in plain Python so tests stay fast and stable
- **Keep widget tests focused** - Test wiring, signals, basic interactions only
- **Run serial by default** - UI tests touch global state (QApplication, timers). Avoid `-n auto` unless suite is stable
- **One behavior per test** - Arrange → Act → Assert

### Test Infrastructure
- `tests/conftest.py` - Main fixtures, QApplication setup, offscreen platform config
- `tests/fixtures/` - Shared fixtures and mocks
- Qt tests require `pytest-qt` and may need display

### pytest-qt Patterns
```python
from PySide6.QtCore import Qt

def test_button_emits(qtbot):
    w = MyWidget()
    qtbot.addWidget(w)  # Ensures proper cleanup

    with qtbot.waitSignal(w.clicked, timeout=1000):
        qtbot.mouseClick(w.button, Qt.LeftButton)
```

**Critical rules:**
- Use `qtbot.waitSignal`, `qtbot.waitUntil`, `qtbot.wait` - never `time.sleep()`
- Always call `qtbot.addWidget(w)` so widgets are deleted properly
- Let pytest-qt manage QApplication via `qtbot`/`qapp` fixtures
- Never call `app.exec()` in tests

### When Tests Fail
1. Run single test with full output: `uv run pytest path/to/test.py::test_name -vv --tb=long -s`
2. Check if it's an API contract issue (see table above)
3. Fix implementation, not tests - tests reveal real bugs

### Flakiness Prevention
- Prefer deterministic timeouts (short + specific)
- Avoid `time.sleep()` - use `qtbot.wait*` methods
- Clean up widgets with `qtbot.addWidget()`
- Keep UI tests few and focused

## Development Workflow

### Canonical Check Sequence
Run before committing:
```bash
uv run ruff check . && uv run ruff format . && uv run basedpyright && uv run pytest
```

### Adding Features
1. Identify layer (Model/View/Controller)
2. Use `config.py` for any new constants
3. Follow existing signal/slot patterns
4. Add tests for logic; minimal tests for UI wiring
5. Run canonical check sequence before committing

### Modifying UI
1. Locate component file
2. Maintain signal interface contracts
3. Update styling through `styles.py`
4. Test independently before integration

### Small Diffs Principle
- Prefer incremental changes: edit → add/update tests → run checks
- Big multi-file refactors without tests are where regressions hide
- If a change affects threading, signals, IO, or persistence: add/adjust tests

## Files to Ignore

- `archive/` - Historical documentation, not active code
- `web_backend/`, `web_frontend/` - Separate web interface (untracked)
- `debug_*.py` - Debug utilities, not production code
- `venv/` - Virtual environment
