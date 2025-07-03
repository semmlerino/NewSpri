# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python Sprite Viewer is a professional PySide6-based application for previewing and editing sprite sheet animations. It features animation splitting, segment management, comprehensive export capabilities, and is built with a complete MVC component-based architecture.

## Development Environment Setup

### Virtual Environment Setup
The project has a virtual environment in the `venv/` directory with all dependencies pre-installed:

```bash
# Activate the existing virtual environment
source venv/bin/activate  # Linux/Mac/WSL
# or
venv\Scripts\activate     # Windows

# Verify PySide6 installation
python -c "import PySide6; print('PySide6 version:', PySide6.__version__)"
```

### Manual Dependencies Installation (if needed)
```bash
# Create new virtual environment if venv/ doesn't exist
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
- pytest>=6.0.0 (Testing framework)

### Testing with PySide6
For testing UI components and running the full application:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the main application
python sprite_viewer.py

# Test animation splitting functionality
python test_animation_splitting.py
```

## Running the Application

### Main Application
```bash
python sprite_viewer.py
```

### Testing
The project uses pytest as the primary testing framework:
```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest -m unit              # Unit tests only
python -m pytest -m integration       # Integration tests only
python -m pytest tests/unit/          # All unit tests
python -m pytest tests/ui/            # UI component tests

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test files
python -m pytest tests/unit/test_animation_segment_controller.py
python -m pytest tests/ui/test_animation_grid_view.py
```

### Development Scripts
These debug scripts are available in the root directory for testing specific functionality:
- `debug_spacing.py` - Test spacing detection algorithms
- `debug_scoring.py` - Evaluate frame detection scoring
- `test_animation_splitting.py` - Test animation segment creation

## Architecture Overview

### Component-Based MVC Structure
```
📁 Core Architecture
├── 🎨 UI Components
│   ├── sprite_viewer.py               - Main application window
│   ├── sprite_canvas.py               - Zoom/pan display widget
│   ├── playback_controls.py           - Animation control panel
│   ├── frame_extractor.py             - Configuration interface
│   ├── animation_grid_view.py         - Animation splitting interface
│   └── animation_segment_preview.py   - Segment preview panel
├── 🧠 Core Architecture
│   ├── sprite_model/                  - Data layer & algorithms
│   ├── animation_controller.py        - Animation timing control
│   ├── animation_segment_controller.py - Segment management
│   └── auto_detection_controller.py   - Frame detection logic
├── 📦 Managers
│   ├── animation_segment_manager.py   - Segment persistence
│   ├── menu_manager.py                - Menu system
│   └── recent_files_manager.py       - Recent files tracking
├── ⚙️ Foundation Layer
│   ├── config.py                      - Centralized configuration
│   └── styles.py                      - Centralized styling
└── 📚 Export System
    ├── export/core/                   - Export engine
    ├── export/dialogs/                - Export dialogs
    └── export/widgets/                - Export UI components
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
- `Config.Export` - Export formats, scales, and naming patterns
- `Config.AnimationSplitting` - Grid columns, selection modes

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
- `AnimationGridView.segmentCreated(segment)` - New segment created
- `AnimationGridView.segmentDeleted(name)` - Segment deleted
- `AnimationSegmentManager.segmentRemoved(name)` - Manager segment removal

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
- `archive/phase-documentation/` has detailed refactoring history
- `archive/feature-documentation/` contains feature implementation details
- `archive/export-dialog-development/` contains export system evolution

### Assets and Testing
- `assets/` and `spritetests/` contain test sprite sheets
- `Archer/` contains sample animation sprites
- Support for PNG, JPG, JPEG, BMP, GIF formats

## Export Functionality

The application includes comprehensive export capabilities:
- **Individual Frames**: Export each frame as a separate file
- **Sprite Sheet**: Export all frames as a single sprite sheet
- **Animation Segments**: Export specific animation segments
- **Animated GIF**: Export frames as an animated GIF
- **Segments Per Row**: Control sprite sheet layout

### Export System Architecture
```
export/
├── core/
│   ├── frame_exporter.py      - Main export engine
│   └── export_settings.py     - Export configuration
├── dialogs/
│   ├── export_dialog.py       - Main export dialog
│   └── simple_dialog.py       - Quick export dialog
└── widgets/
    ├── preview_widget.py      - Export preview
    └── settings_widget.py     - Settings controls
```

### Export Settings
- Formats: PNG, JPG, BMP, GIF
- Scale factors: 0.5x to 4.0x
- Naming patterns with variables
- Keyboard shortcuts: Ctrl+E (export all), Ctrl+Shift+E (export current)

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

## Animation Splitting Feature

The animation splitting feature allows users to divide sprite sheets into named segments:

### Usage
1. Switch to "Animation Splitting" tab
2. Select frames by clicking, dragging, or using Shift/Ctrl
3. Right-click to create named segments
4. Segments are color-coded and persist with the sprite sheet

### Key Components
- `AnimationGridView` - Frame selection and segment visualization
- `AnimationSegmentManager` - Segment persistence and management
- `AnimationSegmentController` - Coordination between components
- `AnimationSegmentPreview` - Individual segment playback

### Segment Export Features
Enhanced export functionality specifically designed for animation segments:

#### Segments Per Row Export
- Each animation segment becomes one row in the sprite sheet
- Segments can have different numbers of frames
- Perfect for game engines that expect animations in rows

#### Multiple Export Access Points
1. **Export Dialog**: Animation menu → Export → "Segments Per Row" (auto-highlighted when segments exist)
2. **Segment Preview**: Right-click any segment in preview panel → Export as Individual Frames/Sprite Sheet
3. **Grid View**: Right-click on frame → Segment menu → Export options

#### Smart UI Enhancement
- Export dialog automatically detects segments and recommends "Segments Per Row"
- Visual emphasis with blue border and recommendation banner
- Pre-selects optimal export mode when segments are present

### Segment Data
Segments are saved as JSON files alongside sprite sheets:
```json
{
  "sprite_sheet": "character.png",
  "segments": [
    {
      "name": "Walk",
      "start_frame": 0,
      "end_frame": 7,
      "color": [233, 30, 99]
    }
  ]
}
```

## Recent Changes and Fixes

### Color Persistence Fix
- Fixed issue where segment colors would persist after deletion
- Added proper synchronization between segment manager and grid view
- Implemented `force_clear_style()` method for complete style reset

### Alt+1 Shortcut Fix
- Fixed Alt+1 through Alt+9 shortcuts for recent files
- Added proper callback connection in FileController

### Segment Export Preview Fix
- Fixed preview format issue for "Segments Per Row" export mode
- Added segment_manager parameter to ModernExportSettings
- Implemented proper preview generation for segments per row layout
- Added error handling to prevent crashes when segment data is missing

This codebase demonstrates professional software engineering with modular architecture, comprehensive testing, and systematic development practices.