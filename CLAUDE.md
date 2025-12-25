# CLAUDE.md

## Quick Reference

### Essential Commands
```bash
# Run application
python sprite_viewer.py

# Testing (pytest is configured in pyproject.toml with sensible defaults)
uv run pytest                              # All tests
uv run pytest tests/unit/                  # Unit tests only
uv run pytest tests/integration/           # Integration tests
uv run pytest -m unit                      # By marker
uv run pytest path/to/test.py::test_name   # Single test

# Linting and type checking
uv run ruff check .                        # Lint
uv run ruff check . --fix                  # Lint and auto-fix
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
  dialogs/export_dialog.py  - Main export dialog
  dialogs/simple_dialog.py  - Quick export dialog
  widgets/preview_widget.py - Export preview
  widgets/settings_widget.py - Settings controls
```

Formats: PNG, JPG, BMP, GIF. Scale factors: 0.5x-4.0x. Shortcuts: Ctrl+E (all), Ctrl+Shift+E (current).

## Testing Notes

### Test Infrastructure
- `tests/conftest.py` - Main fixtures
- `tests/fixtures/` - Shared fixtures and mocks
- Qt tests require `pytest-qt` and may need display

### When Tests Fail
1. Run single test with full output: `uv run pytest path/to/test.py::test_name -vv --tb=long -s`
2. Check if it's an API contract issue (see table above)
3. Fix implementation, not tests - tests reveal real bugs

## Development Workflow

### Adding Features
1. Identify layer (Model/View/Controller)
2. Use `config.py` for any new constants
3. Follow existing signal/slot patterns
4. Add tests
5. Run `uv run ruff check . && uv run basedpyright` before committing

### Modifying UI
1. Locate component file
2. Maintain signal interface contracts
3. Update styling through `styles.py`
4. Test independently before integration

## Files to Ignore

- `archive/` - Historical documentation, not active code
- `web_backend/`, `web_frontend/` - Separate web interface (untracked)
- `debug_*.py` - Debug utilities, not production code
- `venv/` - Virtual environment
