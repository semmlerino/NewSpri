# Python Sprite Viewer Test Guide

This project uses `pytest` with markers configured in `pyproject.toml`.

## Layout

```
tests/
├── conftest.py                  # Global fixtures and Qt test setup
├── fixtures/
│   ├── common_fixtures.py       # Shared pytest fixtures
│   ├── qt_mocks.py              # Qt dialog/widget mocks
│   └── sprite_sheets.py         # Generated sprite-sheet test data
├── unit/                        # Unit tests
├── integration/                 # Multi-component workflow tests
├── ui/                          # UI/widget tests
└── performance/                 # Reserved package (performance tests are marker-based)
```

## Install Dependencies

Recommended:
```bash
uv sync --all-extras
```

Alternative:
```bash
pip install -r requirements-dev.txt
pip install -r tests/requirements-test.txt
```

## Running Tests

### Canonical (`pytest`)
```bash
uv run pytest
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m ui
uv run pytest -m performance
uv run pytest -m smoke
```

### Helper Runner (`run_tests.py`)
Supported options:
```bash
python3 run_tests.py
python3 run_tests.py --unit
python3 run_tests.py --integration
python3 run_tests.py --ui
python3 run_tests.py --performance
python3 run_tests.py --smoke
python3 run_tests.py --coverage
python3 run_tests.py --parallel 4
python3 run_tests.py --watch
python3 run_tests.py --report
python3 run_tests.py --suites
```

Notes:
- `run_tests.py` does not accept raw pytest flags like `-m`.
- For custom pytest expressions (`-m "not slow"`, `-k ...`, etc.), use `uv run pytest` directly.

## Coverage

`python3 run_tests.py --coverage` generates:
- `htmlcov/` (HTML report)
- `coverage.json`
- `coverage.xml`

## Markers

Markers are defined in `pyproject.toml` under `[tool.pytest.ini_options].markers`.
Common markers:
- `unit`, `integration`, `ui`, `performance`, `slow`, `smoke`
- `requires_qt`, `requires_display`, `requires_files`, `signal_test`

## Qt Test Notes

- Use `qtbot` / `qapp` fixtures from `pytest-qt`.
- Avoid `time.sleep()` in tests; use `qtbot.wait*` helpers.
- On headless Linux CI/local environments, run with `xvfb-run` when needed.

## CI

GitHub Actions workflow: `.github/workflows/tests.yml`
- Matrix tests (unit/integration/smoke/performance)
- Coverage upload (Codecov)
- Separate code-quality job (`ruff` + `basedpyright`)
