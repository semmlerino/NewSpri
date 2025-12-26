# Python Sprite Viewer

A professional PySide6-based application for previewing and editing sprite sheet animations with modern MVC architecture, advanced animation splitting, and comprehensive export capabilities.

## 🏗️ Architecture Overview

The application features a **complete component-based MVC architecture** after comprehensive refactoring:

### **Component Structure**
```
📁 Python Sprite Viewer - Professional Architecture
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
├── ⚙️ Foundation
│   ├── config.py                      - Centralized configuration
│   └── styles.py                      - Centralized styling
└── 📚 Export System
    ├── export/core/                   - Export engine
    ├── export/dialogs/                - Export dialogs
    └── export/widgets/                - Export UI components
```

### **Key Architectural Benefits**
- **✅ Complete MVC Separation** - Clean data/controller/view layers
- **✅ Component Modularity** - Reusable widgets across projects  
- **✅ Event-Driven Communication** - Professional Qt signal/slot architecture
- **✅ Team Development Ready** - Multiple developers can work simultaneously
- **✅ Test-Friendly Design** - Individual components fully testable

## 🚀 Features

### **Core Functionality**
- **Smart Sprite Sheet Processing** - Automatic frame extraction with pixel-perfect algorithms
- **Professional Animation Playback** - Precise timing control with performance monitoring
- **Advanced Display Engine** - Zoom, pan, overlays with smooth interaction
- **Intelligent Auto-Detection** - Frame size and margin detection algorithms
- **Comprehensive UI Controls** - Intuitive interface with keyboard shortcuts
- **Recent Files Menu** - Quick access to recently opened sprite sheets (Alt+1 through Alt+9)
- **Export System** - Export frames as individual files, sprite sheets, or animated GIFs
- **Animation Splitting** - Split sprite sheets into named animation segments with color coding
- **Segment Preview** - Individual playback controls for each animation segment
- **Connected Component Labeling** - Advanced frame extraction for complex sprite sheets

### **Technical Highlights**
- **Performance Optimized** - Real-time FPS monitoring and smart UI updates
- **Memory Efficient** - Optimized pixmap handling and resource management
- **Cross-Platform** - Pure PySide6 implementation for Windows/Mac/Linux
- **Extensible Design** - Plugin-ready architecture for future enhancements

## 📋 Installation

### **Requirements**
- Python 3.11+
- PySide6
- Modern Qt-compatible system

### **Setup**
1. **Clone and navigate:**
   ```bash
   git clone <repository>
   cd NewSpri
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🎮 Usage

### **Launch Application**
```bash
python sprite_viewer.py
```

### **File Loading**
- **📁 Open Button** - Browse and select sprite sheets
- **🖱️ Drag & Drop** - Drop image files directly onto canvas
- **⌨️ Ctrl+O** - Quick file open shortcut
- **⌨️ Alt+1 to Alt+9** - Quick access to recent files

**Supported Formats:** PNG, JPG, JPEG, BMP, GIF

### **Frame Extraction**
The application excels at intelligent sprite sheet processing:

- **🎯 Smart Presets** - Common sizes (32×32, 64×64, 128×128, 192×192)
- **⚙️ Custom Dimensions** - Precise width/height control
- **🔍 Auto-Detection** - Intelligent frame size and margin detection
- **📐 Offset Control** - Handle sprite sheet borders and padding
- **⚡ Real-Time Updates** - Instant visual feedback during configuration

### **Animation Controls**

**Playback Management:**
- **▶️ Play/Pause** - Spacebar or button control
- **⏮️⏭️ Frame Navigation** - Arrow keys or dedicated buttons
- **🏠🔚 Jump Controls** - Home/End for first/last frame
- **🔄 Loop Mode** - Continuous or single-play options

**Speed Control:**
- **📊 FPS Slider** - 1-60 FPS with real-time adjustment
- **📈 Performance Monitoring** - Actual vs target FPS display
- **⚡ Optimization** - Smart timing with precision indicators

### **Display Features**

**Viewing Controls:**
- **🔍 Zoom** - Mouse wheel or toolbar (10%-1000%)
- **🖱️ Pan** - Click and drag navigation
- **📐 Grid Overlay** - Alignment assistance (G key toggle)
- **🎨 Background Options** - Checkerboard or solid color
- **📏 Frame Info** - Real-time frame counter display

### **Animation Splitting**

**Segment Creation:**
- **🎯 Frame Selection** - Click, drag, or shift-click to select frames
- **✂️ Create Segments** - Right-click or button to create named segments
- **🎨 Color Coding** - Automatic distinct colors for each segment
- **💾 Auto-Save** - Segments persist with sprite sheet files

**Segment Management:**
- **▶️ Individual Playback** - Preview each segment separately
- **📤 Export Segments** - Export specific animations independently
- **🔄 Edit Segments** - Rename, delete, or modify segments
- **👁️ Visual Markers** - Clear start/end frame indicators

### **Keyboard Shortcuts**
| Key | Function |
|-----|----------|
| `Space` | Play/pause animation |
| `←` / `→` | Previous/next frame |
| `Home` / `End` | First/last frame |
| `G` | Toggle grid overlay |
| `Ctrl+O` | Open file dialog |
| `Ctrl++` / `Ctrl+-` | Zoom in/out |
| `Ctrl+0` | Fit to window |
| `Ctrl+1` | Reset zoom (100%) |
| `Ctrl+E` | Export all frames |
| `Ctrl+Shift+E` | Export current frame |
| `Alt+1` to `Alt+9` | Open recent file 1-9 |
| `Ctrl+Q` | Quit application |

## 🏆 Professional Features

### **Performance Excellence**
- **Real-Time Monitoring** - FPS accuracy tracking and quality indicators
- **Smart UI Updates** - Redundant update prevention for smooth performance  
- **Memory Optimization** - Efficient pixmap caching and resource management
- **Responsive Interface** - Non-blocking operations with progress feedback

### **Developer-Friendly Architecture**
- **Component Testing** - Individual widget testing capabilities
- **Signal Debugging** - Clear event flow for troubleshooting
- **Extensible Design** - Add new features without breaking existing code
- **Documentation** - Comprehensive phase documentation and code reviews

### **Production Quality**
- **Error Handling** - Graceful failure recovery with user feedback
- **Resource Management** - Proper cleanup and memory management
- **Cross-Platform** - Consistent behavior across operating systems
- **Accessibility** - Keyboard navigation and clear visual feedback

## 📚 Documentation

- **README.md** - This file - main project documentation
- **CLAUDE.md** - Instructions for Claude AI assistant when working with this codebase
- **requirements.txt** - Python package dependencies
- **pytest.ini** - Test configuration and markers

## 🔧 Development

### **Testing**
Run the comprehensive test suite:
```bash
# All tests
python -m pytest

# Specific test categories
python -m pytest -m unit          # Unit tests only
python -m pytest -m integration   # Integration tests
python -m pytest tests/ui/        # UI component tests

# With coverage
python -m pytest --cov=. --cov-report=html
```

### **Architecture Highlights**
The codebase demonstrates **professional software engineering** with:

- **Modular Design** - 20+ independent components with clear responsibilities
- **Zero Circular Dependencies** - Proper import hierarchy maintained
- **Event-Driven Architecture** - Qt signals for loose coupling
- **Comprehensive Testing** - Unit, integration, and UI tests
- **Enterprise Quality** - Production-ready code organization

### **Future Enhancement Ready**
The architecture enables advanced features:
- Plugin systems for custom functionality
- Advanced export capabilities (GIF, video)
- Cloud integration for sprite sharing
- Machine learning-powered auto-detection
- Professional timeline editing tools

## 📄 License

This project is open source. Feel free to use and modify for your needs.

---

**Python Sprite Viewer** - A professional sprite sheet animation tool built with modern software engineering principles.