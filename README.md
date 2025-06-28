# Python Sprite Viewer

A professional PySide6-based application for previewing sprite sheet animations with modern MVC architecture.

## 🏗️ Architecture Overview

The application features a **complete component-based MVC architecture** after comprehensive refactoring:

### **Component Structure**
```
📁 Python Sprite Viewer - Professional Architecture
├── 🏗️ UI Components
│   ├── sprite_viewer.py         - Main application window
│   ├── sprite_canvas.py         - Zoom/pan display widget  
│   ├── playback_controls.py     - Animation control panel
│   └── frame_extractor.py       - Configuration interface
├── 🧠 MVC Architecture  
│   ├── sprite_model.py          - Data layer & algorithms
│   └── animation_controller.py  - Animation timing & control
├── ⚙️ Foundation
│   ├── config.py                - Centralized configuration
│   └── styles.py                - Centralized styling
└── 📚 Documentation
    └── PHASE_*_COMPLETE.md      - Comprehensive architecture docs
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

### **Technical Highlights**
- **Performance Optimized** - Real-time FPS monitoring and smart UI updates
- **Memory Efficient** - Optimized pixmap handling and resource management
- **Cross-Platform** - Pure PySide6 implementation for Windows/Mac/Linux
- **Extensible Design** - Plugin-ready architecture for future enhancements

## 📋 Installation

### **Requirements**
- Python 3.8+
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

Comprehensive documentation available:
- **PHASE_*_COMPLETE.md** - Detailed architecture transformation docs
- **CODE_REVIEW_FINAL.md** - Complete code quality analysis
- **archive/documentation/** - Historical development documentation

## 🔧 Development

### **Architecture Highlights**
The codebase demonstrates **professional software engineering** with:

- **38% Main File Reduction** - Clean component extraction (1,188→736 lines)
- **Zero Circular Dependencies** - Proper import hierarchy
- **Event-Driven Design** - Qt signals for loose coupling
- **Single Responsibility** - Each module has clear, focused purpose
- **Enterprise Quality** - Production-ready code organization

### **Future Enhancement Ready**
The architecture enables advanced features:
- Plugin systems for custom functionality
- Advanced export capabilities (GIF, video)
- Cloud integration for sprite sharing
- Machine learning-powered auto-detection
- Professional timeline editing tools

---

**Python Sprite Viewer** - From functional application to **professional software engineering showcase** through systematic architectural transformation.

*Achieved through 5-phase refactoring: Configuration→Styling→Model→Controller→Components*