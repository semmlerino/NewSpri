# Repository Guidelines

At the start, › Call serena.activate_project, serena.check_onboarding_performed and serena.initial_instructions

## Project Structure & Module Organization
Core application entry points live at `sprite_viewer.py` and `config.py`.  
Feature code is split by responsibility:
- `ui/`: PySide6 widgets and presentation logic
- `core/`: controllers and workflow orchestration
- `sprite_model/`: frame extraction and sprite-processing algorithms
- `managers/`, `coordinators/`, `utils/`: app services, signal wiring, shared helpers
- `export/`: export engine and dialogs
- `tests/`: `unit/`, `integration/`, `ui/`, and `performance/` suites
- `spritetests/`: sample sprite sheets used by tests and manual verification

## Build, Test, and Development Commands
- `uv sync --all-extras`: install runtime and dev dependencies.
- `python sprite_viewer.py`: launch the desktop app locally.
- `uv run pytest`: run full test suite (configured in `pyproject.toml`).
- `uv run pytest -m unit` / `uv run pytest -m integration` / `uv run pytest tests/ui/`: run targeted suites.
- `python run_tests.py --unit --coverage`: helper runner with coverage output.
- `uv run ruff check . --fix`: lint and auto-fix.
- `uv run ruff format .`: apply formatting.
- `uv run basedpyright`: static type checks.

## Coding Style & Naming Conventions
Use Python 3.11+ with 4-space indentation. Formatting and linting are governed by Ruff (`line-length = 100`, double quotes).  
Naming:
- modules/functions/variables: `snake_case`
- classes: `PascalCase`
- constants: `UPPER_SNAKE_CASE`

Prefer adding configuration values to `config.py` instead of hardcoding UI or timing constants.

## Testing Guidelines
Use `pytest` with markers (`unit`, `integration`, `ui`, `performance`, `smoke`, etc.).  
Test files follow `test_*.py`; test functions follow `test_*`.  
For UI tests, use `pytest-qt` fixtures (`qtbot`, `qapp`) and avoid `time.sleep()`.  
Before opening a PR, run lint, type checks, and tests relevant to changed modules; run full suite for cross-cutting refactors.

## Commit & Pull Request Guidelines
Follow the existing commit style: short, imperative subjects (examples: `Fix ...`, `Remove ...`, `Extract ...`).  
Keep commits focused and logically grouped.  
PRs should include:
- what changed and why
- linked issue/task (if any)
- test evidence (commands run)
- screenshots/GIFs for UI-visible changes
