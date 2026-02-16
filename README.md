# Python Sprite Viewer

PySide6 desktop application for previewing sprite sheets, extracting frames, splitting animations into segments, and exporting assets.

## Architecture Overview

### Project Structure
```
sprite_viewer.py                 # Main window and app wiring
config.py                        # Centralized configuration

ui/                              # Widgets and presentation
core/                            # Controllers/workflow orchestration
managers/                        # Settings, recent files, segment persistence
coordinators/                    # Signal wiring between components
sprite_model/                    # Frame extraction and image-processing logic
export/                          # Export engine and dialogs
tests/                           # Unit/integration/UI/performance-marked tests
spritetests/                     # Sample sprite sheets used by tests/manual checks
```

### Key Modules
- `ui/`: `sprite_canvas.py`, `playback_controls.py`, `frame_extractor.py`, `animation_grid_view.py`, `animation_segment_preview.py`, `animation_segment_widget.py`, `enhanced_status_bar.py`
- `core/`: `animation_controller.py`, `animation_segment_controller.py`, `auto_detection_controller.py`, `export_coordinator.py`
- `managers/`: `animation_segment_manager.py`, `recent_files_manager.py`, `settings_manager.py`
- `coordinators/`: `signal_coordinator.py`
- `export/`: `core/` + `dialogs/` (no separate `widgets/` directory)

## Features

- Sprite sheet loading via file dialog, drag/drop, and recent-files menu
- Frame extraction in `grid` mode and `ccl` (connected-component labeling) mode
- Playback controls with precise FPS control (1-60), frame stepping, and looping
- Canvas zoom/pan and optional grid overlay
- Animation splitting with named segments and persisted segment metadata
- Export presets for individual frames, sprite sheets, and segments-per-row layouts
- Export formats: `PNG`, `JPG`, `BMP`

Supported input formats: `PNG`, `JPG`, `JPEG`, `BMP`, `GIF`.

## Installation

### Recommended
```bash
uv sync --all-extras
```

### Alternative (pip)
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows
pip install -r requirements-dev.txt
```

## Usage

Launch the desktop app:
```bash
python sprite_viewer.py
```

### Core Shortcuts
| Key | Action |
|---|---|
| `Space` | Play/pause |
| `←` / `→` | Previous/next frame |
| `Home` / `End` | First/last frame |
| `G` | Toggle grid overlay |
| `Ctrl+O` | Open sprite sheet |
| `Ctrl++` / `Ctrl+-` | Zoom in/out |
| `Ctrl+0` | Fit to window |
| `Ctrl+1` | Reset zoom (100%) |
| `Ctrl+E` | Export frames |
| `Ctrl+Shift+E` | Export current frame |
| `Alt+1` to `Alt+9` | Open recent file slot |
| `Ctrl+Q` | Quit |

## Development

### Run tests
```bash
uv run pytest
uv run pytest -m unit
uv run pytest -m integration
uv run pytest tests/ui/
```

### Run helper test runner
```bash
python3 run_tests.py --unit
python3 run_tests.py --integration
python3 run_tests.py --coverage
```

### Lint / format / type-check
```bash
uv run ruff check . --fix
uv run ruff format .
uv run basedpyright
```

## Additional Documentation

- `CLAUDE.md`: assistant-oriented engineering notes and API contracts
- `tests/README.md`: current testing workflow and markers
- `WEB_UI_README.md`: status of the web UI effort (currently not active in this repo)

## License

Open source; use and modify as needed.
