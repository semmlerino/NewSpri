# Python Sprite Viewer

A lightweight PySide6-based application for previewing sprite sheet animations according to the specifications in Specs.md.

## Features

✅ **Complete Implementation:**
- PySide6-based GUI with minimal, intuitive interface
- **Proper sprite sheet slicing** - automatically extracts individual frames from sprite sheets
- **64×64 default frame size** - optimized for common sprite dimensions
- **Dynamic frame size adjustment** - real-time re-slicing when changing frame dimensions
- Animation playback controls (play/pause, FPS adjustment, loop toggle)
- Background options (transparent checkerboard, solid color)
- Zoom and pan functionality with mouse controls
- Grid overlay for alignment assessment
- Drag-and-drop file loading
- Keyboard shortcuts for quick navigation

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python sprite_viewer.py
```

### Controls

**Mouse:**
- Left click + drag: Pan the view
- Mouse wheel: Zoom in/out

**Keyboard Shortcuts:**
- `Space`: Play/pause animation
- `G`: Toggle grid overlay
- `Left Arrow`: Previous frame (stops playback)
- `Right Arrow`: Next frame (stops playback)
- `Ctrl+O`: Open file dialog
- `Ctrl+Q`: Quit application

**UI Controls:**
- **Load Sprites**: Import sprite sheets or image files
- **Frame Size**: Set dimensions for frame slicing
- **Show Grid**: Toggle grid overlay
- **Play/Pause**: Control animation playback
- **FPS Slider**: Adjust animation speed (1-60 FPS)
- **Loop**: Toggle animation looping
- **Zoom Slider**: Adjust zoom level (10%-1000%)
- **Background**: Choose between checkerboard or solid color

### File Support

The viewer supports common image formats:
- PNG
- JPG/JPEG
- BMP
- GIF

You can load files by:
1. Using the "Load Sprites..." button
2. Using Ctrl+O keyboard shortcut
3. Dragging and dropping files onto the application window

### Sprite Sheet Slicing

The viewer correctly slices sprite sheets based on **64×64 tilemap grid specification**:

- **Grid-Aligned**: Respects 64×64 pixel tilemap standard
- **Smart Default**: 192×192 pixels (3×3 tiles) for complete character sprites  
- **Quick Presets**: 64×64 (1 tile), 128×128 (2×2 tiles), 192×192 (3×3 tiles)
- **Manual Adjustment**: Frame width/height spinboxes for custom dimensions
- **Margin/Offset Controls**: X,Y offset for handling sprite sheet borders
- **Auto-Detect Margins**: Analyzes sprite content to find optimal boundaries
- **Real-time Updates**: See changes immediately as you adjust settings

**Correct Extraction Results**:
- **Archer_Idle.png** (1152×192): 6 complete 192×192 sprites (3×3 tiles each)
- **Archer_Run.png** (768×192): 4 complete 192×192 sprites (3×3 tiles each)
- **Archer_Shoot.png** (1536×192): 8 complete 192×192 sprites (3×3 tiles each)

**Perfect Grid Alignment**: Each character sprite spans exactly 3×3 tiles on the 64×64 grid, showing complete characters with proper proportions and perfect visual alignment!

## Architecture

The application consists of two main components:

1. **SpriteCanvas**: Custom widget handling sprite display, zoom, pan, and overlays
2. **SpriteViewer**: Main window with UI controls and application logic

The implementation follows PySide6 best practices with proper signal/slot connections and event handling for a responsive user experience.