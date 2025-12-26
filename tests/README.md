# Python Sprite Viewer - Test Infrastructure

Modern pytest-based testing infrastructure with comprehensive coverage, performance monitoring, and CI/CD integration.

## 🏗️ **Architecture Overview**

```
tests/
├── conftest.py                 # Global fixtures and configuration
│   (Note: pytest config is in pyproject.toml, not pytest.ini)
├── fixtures/                   # Test data and utilities
│   ├── sprite_sheets.py        # Generated test sprite sheets
│   └── mock_data.py           # Mock data generators
├── unit/                       # Unit tests (fast, isolated)
│   ├── test_config.py          # Configuration system tests
│   ├── test_sprite_model.py    # Core model tests
│   └── test_animation_controller.py # Animation logic tests
├── integration/                # Integration tests (multi-component)
│   └── test_sprite_loading_workflow.py # End-to-end workflows
├── ui/                         # UI component tests (requires Qt)
│   └── test_*.py              # Widget behavior tests
└── performance/                # Performance and load tests
    └── test_*.py              # Memory and speed tests
```

## 🚀 **Quick Start**

### Install Test Dependencies
```bash
uv sync --all-extras
```

### Run Tests
```bash
# All tests
python run_tests.py

# Specific test types
python run_tests.py --unit          # Fast unit tests
python run_tests.py --integration   # Multi-component tests
python run_tests.py --ui            # UI widget tests
python run_tests.py --performance   # Performance tests
python run_tests.py --smoke         # Critical functionality only

# With coverage
python run_tests.py --coverage

# Parallel execution
python run_tests.py --parallel 4

# Development watch mode
python run_tests.py --watch
```

## 📊 **Test Categories**

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: Minimal, uses mocks
- **Coverage**: Core business logic, algorithms, configuration

**Examples:**
- `test_config.py`: Configuration validation and consistency
- `test_sprite_model.py`: Core model functionality 
- `test_animation_controller.py`: Animation timing and state

### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions and workflows
- **Speed**: Moderate (1-10 seconds per test)
- **Dependencies**: Multiple components, real data
- **Coverage**: End-to-end workflows, data flow

**Examples:**
- `test_sprite_loading_workflow.py`: Complete file loading process
- `test_auto_detection_workflow.py`: Detection algorithm integration

### UI Tests (`tests/ui/`)
- **Purpose**: Test Qt widgets and user interactions
- **Speed**: Moderate (requires Qt application)
- **Dependencies**: Qt display system, widgets
- **Coverage**: Widget behavior, signal/slot communication

### Performance Tests (`tests/performance/`)
- **Purpose**: Validate performance and memory usage
- **Speed**: Slow (10+ seconds per test)
- **Dependencies**: Large test data, benchmarking tools
- **Coverage**: Memory leaks, processing speed, scalability

## 🔧 **Test Configuration**

### Pytest Markers
Tests are organized using pytest markers:

```python
@pytest.mark.unit           # Unit test
@pytest.mark.integration    # Integration test  
@pytest.mark.ui            # UI component test
@pytest.mark.performance   # Performance test
@pytest.mark.slow          # Tests taking >2 seconds
@pytest.mark.smoke         # Critical functionality
@pytest.mark.requires_display  # Needs GUI display
@pytest.mark.requires_files    # Needs test sprite files
```

### Custom Fixtures
Global fixtures available in all tests:

```python
def test_example(qapp, sprite_model, mock_pixmap, sample_sprite_paths):
    # qapp: QApplication instance
    # sprite_model: Fresh SpriteModel instance
    # mock_pixmap: Test QPixmap
    # sample_sprite_paths: Paths to test sprite files
```

### Configuration Options
Key settings in `pytest.ini`:

- **Coverage**: 80% minimum threshold
- **Timeouts**: Automatic test timeout handling
- **Parallel**: Support for multi-worker execution
- **Reporting**: HTML, XML, and JSON output formats

## 📈 **Coverage and Quality**

### Coverage Reporting
```bash
# Generate coverage report
python run_tests.py --coverage

# View HTML report
open htmlcov/index.html
```

### Quality Metrics
- **Unit Test Coverage**: >90% target
- **Integration Coverage**: >80% target  
- **Performance Benchmarks**: Memory and speed thresholds
- **Code Quality**: Automated linting and formatting

## 🎯 **Test Data and Fixtures**

### Generated Test Sprites
The test suite includes programmatically generated sprite sheets:

```python
from tests.fixtures.sprite_sheets import get_test_sprite_collection

# Get collection of test sprites
sprites = get_test_sprite_collection()
basic_sprite = sprites['basic_square']  # 32x32 frames, 2x4 grid
character_anim = sprites['character_anim']  # 32x48 frames with spacing
```

### Real Test Files
Sample sprite sheets in `spritetests/`:
- Character animations (Archer, Lancer series)
- Various frame sizes and layouts
- Debug and test images

## 🔄 **CI/CD Integration**

### GitHub Actions
Automated testing on:
- **Multiple OS**: Ubuntu, Windows, macOS
- **Multiple Python**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Test Types**: Unit, integration, smoke, performance
- **Quality Checks**: Code formatting, linting, type checking

### Coverage Tracking
- Automatic coverage upload to Codecov
- Pull request coverage reports
- Coverage trend monitoring

## 🛠️ **Development Workflow**

### Adding New Tests
1. **Unit Test**: Add to appropriate `tests/unit/test_*.py`
2. **Integration Test**: Add to `tests/integration/test_*.py`  
3. **Fixtures**: Add reusable test data to `tests/fixtures/`
4. **Markers**: Use appropriate pytest markers
5. **Documentation**: Update test descriptions

### Running During Development
```bash
# Watch mode - re-runs tests on file changes
python run_tests.py --watch

# Quick feedback - run only unit tests
python run_tests.py --unit

# Full validation before commit
python run_tests.py --coverage --quality
```

### Test-Driven Development
1. Write failing test for new feature
2. Implement minimal code to pass test
3. Refactor while keeping tests green
4. Add integration tests for workflows

## 🚨 **Troubleshooting**

### Common Issues

**Qt Application Errors:**
```bash
# Use virtual display on headless systems
xvfb-run -a python run_tests.py
```

**Import Errors:**
```bash
# Ensure project root in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Slow Tests:**
```bash
# Run only fast tests
python run_tests.py --unit -m "not slow"
```

**Coverage Issues:**
```bash
# Debug coverage exclusions
python -m pytest --cov=. --cov-report=term-missing -v
```

### Performance Debugging
```bash
# Profile test execution
python run_tests.py --performance --profile

# Memory usage monitoring
python run_tests.py --memray
```

## 📚 **Best Practices**

### Test Writing Guidelines
1. **AAA Pattern**: Arrange, Act, Assert
2. **Descriptive Names**: Test names should describe expected behavior
3. **Single Responsibility**: One concept per test
4. **Fast Feedback**: Unit tests should run in milliseconds
5. **Isolation**: Tests should not depend on each other

### Mock Usage
```python
# Good: Mock external dependencies
@patch('sprite_model.file_operations.load_image')
def test_load_sprite_sheet(mock_load):
    mock_load.return_value = mock_pixmap
    # Test implementation

# Avoid: Mocking too much internal logic
```

### Fixture Design
```python
# Good: Focused, reusable fixtures
@pytest.fixture
def configured_sprite_model(sprite_model, mock_sprite_frames):
    sprite_model._sprite_frames = mock_sprite_frames
    return sprite_model

# Avoid: Complex fixtures doing too much
```

---

## 🎉 **Summary**

This test infrastructure provides:
- ✅ **Comprehensive Coverage**: Unit, integration, UI, and performance tests
- ✅ **Modern Tooling**: pytest, coverage, parallel execution
- ✅ **CI/CD Ready**: GitHub Actions, multi-platform testing
- ✅ **Developer Friendly**: Watch mode, fast feedback, clear reporting
- ✅ **Quality Assurance**: Automated code quality checks
- ✅ **Performance Monitoring**: Memory and speed benchmarks

The testing infrastructure is designed to scale with your project and maintain high code quality as the codebase evolves.