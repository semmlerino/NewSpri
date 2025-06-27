# Sprite Viewer Refactoring Plan

## Current Structure Analysis

### File Size: 1,342 lines, 67 total methods
- **SpriteCanvas**: ~200 lines (✅ manageable)
- **PlaybackControls**: ~196 lines (✅ well-structured)  
- **FrameExtractor**: ~156 lines (✅ well-structured)
- **SpriteViewer**: ~763 lines, 40 methods (❌ **TOO LARGE**)

## Critical Issues Identified

### 1. **God Class Problem** 🚨
- `SpriteViewer` has too many responsibilities:
  - UI setup and layout management
  - File loading and sprite sheet processing  
  - Animation timing and playback logic
  - Settings and configuration management
  - Event handling (drag/drop, keyboard, etc.)
  - Menu and toolbar management
  - Status updates and user feedback

### 2. **Mixed Concerns**
- `SpriteCanvas` mixes rendering with input handling
- Style definitions scattered throughout code
- Business logic mixed with UI code

### 3. **Code Quality Issues**
- Magic numbers everywhere (sizes, timers, etc.)
- Hardcoded CSS styles in multiple places
- Long methods (some 50+ lines)
- No centralized configuration
- Inconsistent error handling

## Step-by-Step Refactoring Plan

### Phase 1: Extract Configuration & Constants 🏗️
**Goal**: Centralize all magic numbers and settings
**Risk**: Low - No logic changes, just organization

```python
# config.py
class Config:
    # Canvas settings
    CANVAS_MIN_WIDTH = 600
    CANVAS_MIN_HEIGHT = 400
    ZOOM_MIN = 0.1
    ZOOM_MAX = 10.0
    
    # Animation settings  
    DEFAULT_FPS = 10
    FPS_MIN = 1
    FPS_MAX = 60
    
    # Frame size presets
    FRAME_PRESETS = [
        (16, 16, "Small icons"),
        (32, 32, "Standard tiles"),
        # ...
    ]
```

### Phase 2: Extract Style Manager 🎨
**Goal**: Centralize all styling and theming
**Risk**: Low - Pure UI changes

```python
# styles.py
class StyleManager:
    @staticmethod
    def get_canvas_style() -> str:
        return """QLabel { border: 2px solid #ccc; ... }"""
    
    @staticmethod  
    def get_button_style() -> str:
        return """QPushButton { ... }"""
```

### Phase 3: Extract Sprite Data Model 📊
**Goal**: Separate sprite data from UI logic
**Risk**: Medium - Touches core data handling

```python
# sprite_model.py
class SpriteModel:
    def __init__(self):
        self.frames: List[QPixmap] = []
        self.current_frame = 0
        self.original_sheet: Optional[QPixmap] = None
        # ... all sprite-related data
    
    def slice_sprite_sheet(self, width, height, offset_x, offset_y):
        # Extract slicing logic from main class
```

### Phase 4: Extract Animation Controller 🎬
**Goal**: Separate animation logic from UI
**Risk**: Medium - Timer and state management

```python
# animation_controller.py
class AnimationController(QObject):
    frameChanged = Signal(int)
    playbackStateChanged = Signal(bool)
    
    def __init__(self, sprite_model: SpriteModel):
        # Handle all animation timing and state
```

### Phase 5: Extract File Operations Manager 📁
**Goal**: Centralize all file I/O operations
**Risk**: Low-Medium - File handling logic

```python
# file_manager.py
class FileManager:
    @staticmethod
    def load_sprite_sheet(file_path: str) -> QPixmap:
        # All file loading logic
    
    @staticmethod
    def auto_detect_frame_size(pixmap: QPixmap) -> Tuple[int, int]:
        # Auto-detection logic
```

### Phase 6: Split SpriteViewer into Smaller Classes 🏢
**Goal**: Break up the god class
**Risk**: High - Major architectural change

```python
# main_window.py
class MainWindow(QMainWindow):
    # Only window-level concerns (menus, toolbar, status)

# workspace.py  
class Workspace(QWidget):
    # Canvas + controls layout

# settings_manager.py
class SettingsManager:
    # All application settings
```

### Phase 7: Improve Error Handling 🛡️
**Goal**: Consistent error handling strategy
**Risk**: Low - Additive changes

```python
# exceptions.py
class SpriteViewerError(Exception):
    pass

class FileLoadError(SpriteViewerError):
    pass
```

### Phase 8: Add Type Safety & Documentation 📝
**Goal**: Better type hints and documentation
**Risk**: Very Low - Documentation only

## Refactoring Order (Safest to Riskiest)

1. **Phase 1** - Extract Config ⚠️ **SAFE**
2. **Phase 2** - Extract Styles ⚠️ **SAFE**  
3. **Phase 7** - Error Handling ⚠️ **SAFE**
4. **Phase 8** - Documentation ⚠️ **SAFE**
5. **Phase 5** - File Manager ⚠️ **MEDIUM**
6. **Phase 3** - Sprite Model ⚠️ **MEDIUM**
7. **Phase 4** - Animation Controller ⚠️ **MEDIUM**
8. **Phase 6** - Split Main Class ⚠️ **RISKY**

## Testing Strategy

### After Each Phase:
1. ✅ **Smoke Test**: App launches without errors
2. ✅ **Basic Function Test**: Load sprite, play animation
3. ✅ **UI Test**: All controls still work
4. ✅ **Git Checkpoint**: Commit after each successful phase

### Rollback Plan:
- Each phase gets its own git commit
- If a phase fails, revert to previous commit
- Fix issues in isolation before proceeding

## Expected Benefits

### Code Quality:
- ✅ Single Responsibility Principle
- ✅ Easier testing and debugging
- ✅ Better maintainability
- ✅ Reduced coupling

### Development:
- ✅ Easier to add new features
- ✅ Better code reuse
- ✅ Clearer architecture
- ✅ Easier onboarding for new developers

## Risk Mitigation

### Low-Risk Phases First:
- Start with config and styles (no logic changes)
- Build confidence with successful easy wins
- Leave risky architectural changes for last

### Incremental Approach:
- One phase at a time
- Test thoroughly after each phase
- Commit after each successful phase
- Easy rollback if problems arise

### Git Safety Net:
- Feature branch for refactoring
- Regular commits and checkpoints
- Can always revert to working state

## Next Steps

1. **Start with Phase 1** (Config extraction)
2. **Create feature branch**: `refactor-architecture`
3. **Extract all magic numbers** to config module
4. **Test thoroughly** before proceeding
5. **Get user approval** before moving to Phase 2

Ready to begin? 🚀