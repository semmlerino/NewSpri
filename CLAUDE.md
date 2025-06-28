# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python Sprite Viewer is a professional PySide6-based application for previewing sprite sheet animations, built with a complete MVC component-based architecture. The project underwent a 5-phase architectural refactoring from a monolithic design to enterprise-quality modular components.

## Development Environment Setup

### Dependencies Installation
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Required Dependencies
- PySide6>=6.9.0 (Main UI framework)
- numpy>=1.21.0 (Numerical processing)
- Pillow>=8.0.0 (Image handling)
- scipy>=1.7.0 (Scientific computations)

## Running the Application

### Main Application
```bash
python sprite_viewer.py
```

### Testing
The project uses Python's built-in unittest framework (pytest is not available):
```bash
# Run main test suite
python tests/test_sprite_viewer.py

# Run specific component tests
python test_comprehensive.py
python test_rectangular_detection.py
python test_phase1.py
```

### Development Testing Scripts
```bash
# Debug specific algorithms
python debug_spacing.py
python debug_spacing_detailed.py
python debug_final.py
python debug_scoring.py
```

## Architecture Overview

### Component-Based MVC Structure
```
📁 Core Architecture (Post Phase-5 Refactoring)
├── 🏗️ UI Components (Extracted in Phase 5)
│   ├── sprite_viewer.py         - Main application window (736 lines)
│   ├── sprite_canvas.py         - Zoom/pan display widget (216 lines)
│   ├── playback_controls.py     - Animation control panel (136 lines)
│   └── frame_extractor.py       - Configuration interface (157 lines)
├── 🧠 MVC Logic Layer
│   ├── sprite_model.py          - Data layer & sprite processing algorithms
│   ├── animation_controller.py  - Animation timing & playback control
│   └── auto_detection_controller.py - Frame detection algorithms
├── ⚙️ Foundation Layer
│   ├── config.py                - Centralized configuration (323 lines)
│   └── styles.py                - Centralized styling system
```

### Key Architectural Principles
- **Complete MVC Separation**: Clean separation between data, controller, and view layers
- **Component Modularity**: Each UI component is self-contained and reusable
- **Event-Driven Communication**: Uses Qt signals/slots for loose coupling
- **Zero Circular Dependencies**: Proper import hierarchy maintained
- **Single Responsibility**: Each module has focused, clear purpose

## Configuration System

The application uses a comprehensive centralized configuration system in `config.py`:

### Key Configuration Classes
- `Config.Canvas` - Display and interaction settings
- `Config.Animation` - Playback timing and FPS settings  
- `Config.FrameExtraction` - Sprite extraction parameters and presets
- `Config.UI` - Layout, sizing, and responsive design settings
- `Config.Drawing` - Rendering and visual styling
- `Config.File` - Supported formats and I/O settings

### Modifying Configuration
Always use the Config classes instead of magic numbers:
```python
from config import Config

# Good
button_height = Config.UI.PLAYBACK_BUTTON_MIN_HEIGHT

# Bad
button_height = 40
```

## Signal/Slot Architecture

The application uses Qt's signal/slot system for component communication:

### Key Signals
- `SpriteModel.frameChanged(int, int)` - Frame updates
- `SpriteModel.dataLoaded(str)` - New sprite loaded
- `AnimationController.statusChanged(str)` - Status updates
- `AutoDetectionController.detectionCompleted(...)` - Detection results

### Adding New Signals
1. Define in the appropriate controller/model class
2. Connect in the main application
3. Update documentation in component docstrings

## Frame Detection Algorithms

The application includes sophisticated auto-detection capabilities:

### Detection Process
- Tests multiple frame sizes from `Config.FrameExtraction.BASE_SIZES`
- Supports common aspect ratios (1:1, 1:2, 2:1, 2:3, 3:2, 3:4, 4:3)
- Uses alpha threshold analysis for margin detection
- Validates reasonable frame counts (2-200 frames)

### Adding Detection Algorithms
Extend `auto_detection_controller.py` with new detection methods following the existing pattern.

## Testing Strategy

### Component Testing
Each major component can be tested independently:
```python
# Example component test pattern
from sprite_canvas import SpriteCanvas
from PySide6.QtWidgets import QApplication

app = QApplication([])
canvas = SpriteCanvas()
# Test component functionality
```

### Integration Testing
Use `test_comprehensive.py` for full application testing with real sprite sheets.

## Development Workflow

### Adding New Features
1. Identify the appropriate layer (Model/View/Controller)
2. Update relevant configuration in `config.py`
3. Implement using existing signal/slot patterns
4. Add component tests
5. Update main application integration

### Modifying UI Components
1. Locate the specific component file (`sprite_canvas.py`, `playback_controls.py`, etc.)
2. Maintain existing signal interface contracts
3. Update styling through `styles.py` when possible
4. Test component independently before integration

### Performance Considerations
- UI updates use smart redundancy prevention
- Animation timing uses precise QTimer calculations
- Memory optimization through efficient pixmap handling
- FPS monitoring with real-time accuracy tracking

## File Structure Notes

### Active Development Files
- Main application components are in root directory
- Test files use `test_*.py` pattern
- Debug utilities use `debug_*.py` pattern

### Archive Structure
- `archive/` contains historical documentation and deprecated files
- `archive/documentation/` has detailed refactoring history
- Phase completion files (`PHASE_*_COMPLETE.md`) document architectural evolution

### Assets and Testing
- `assets/` and `spritetests/` contain test sprite sheets
- `Archer/` contains sample animation sprites
- Support for PNG, JPG, JPEG, BMP, GIF formats

## Common Development Tasks

### Loading Test Sprites
The application includes built-in test sprite paths in `Config.File.TEST_SPRITE_PATHS`.

### Debugging Frame Detection
Use the debug utilities:
- `debug_spacing.py` - Test spacing algorithms
- `debug_scoring.py` - Evaluate detection scoring
- `debug_final.py` - Comprehensive detection testing

### Adding New Frame Size Presets
Update `Config.FrameExtraction.SQUARE_PRESETS` or `RECTANGULAR_PRESETS` with new (label, width, height, tooltip) tuples.

## Code Quality Standards

### Import Organization
Follow the established pattern:
1. Standard library imports
2. Third-party imports (PySide6)
3. Local application imports (config, components)

### Documentation
- Comprehensive docstrings for all classes and methods
- Inline comments for complex algorithms
- Architecture documentation in phase completion files

### Error Handling
- Graceful failure recovery with user feedback
- Proper resource cleanup and memory management
- Status message propagation through signal system

This codebase demonstrates professional software engineering with enterprise-quality architecture, comprehensive documentation, and systematic development practices.