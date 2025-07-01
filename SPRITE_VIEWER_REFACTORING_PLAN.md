# SpriteViewer Class Refactoring Plan

## Overview
Safely refactor the 814-line SpriteViewer class by extracting responsibilities into focused coordinator classes while maintaining all functionality and ensuring no regressions.

## Current State Analysis

### Metrics
- **Total Lines**: 814
- **Private Methods**: 51
- **Direct Dependencies**: 15+ classes
- **Signal Connections**: 20+
- **Responsibilities**: 9 major areas

### Major Responsibility Areas
1. **Initialization & Setup** (lines 53-152)
2. **UI Construction** (lines 120-327)
3. **Signal Management** (lines 329-366)
4. **File Operations** (lines 391-425)
5. **Export Operations** (lines 429-472)
6. **View Operations** (lines 475-501)
7. **Animation Operations** (lines 504-521)
8. **Event Handling** (lines 710-788)
9. **Dialog Management** (lines 678-705)

## Refactoring Strategy

### Phase 1: Create Base Infrastructure (Low Risk)
**Goal**: Set up coordinator base classes and interfaces without changing functionality

### Phase 2: Extract UISetupHelper (Low-Medium Risk)
**Goal**: Move UI initialization logic to dedicated helper

### Phase 3: Extract ViewCoordinator (Medium Risk)
**Goal**: Handle tab management and view switching

### Phase 4: Extract ExportCoordinator (Medium Risk)
**Goal**: Manage export workflow and dialogs

### Phase 5: Extract AnimationCoordinator (Medium-High Risk)
**Goal**: Coordinate animation state between components

### Phase 6: Extract EventCoordinator (High Risk)
**Goal**: Centralize event handling logic

### Phase 7: Final Integration (High Risk)
**Goal**: Complete refactoring and optimize

## Detailed Implementation Plan

### Phase 1: Create Base Infrastructure
**Duration**: 30 minutes
**Risk**: Low

#### Steps:
1. Create `coordinators/` directory structure
2. Create base coordinator interface
3. Create coordinator registry
4. Add coordinator initialization to SpriteViewer

#### Testing Checkpoint 1.1 - Using Existing Pytest Infrastructure:
```bash
# Run smoke tests to ensure nothing is broken
python -m pytest -m smoke -v

# Run core unit tests
python -m pytest tests/unit/test_sprite_viewer_init.py -v

# Run integration test to verify application startup
python -m pytest tests/integration/test_sprite_loading_workflow.py::test_real_sprite_system_initialization -v

# Full application launch test with real Qt events
python -m pytest tests/ui/test_sprite_viewer.py::test_sprite_viewer_creation -v

# Verify no regression in critical paths
python run_tests.py --unit --coverage
```

#### Code Changes:
```python
# coordinators/__init__.py
from .base import CoordinatorBase, CoordinatorRegistry
from .ui_setup import UISetupHelper

# coordinators/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class CoordinatorBase(ABC):
    """Base class for all coordinators."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self._initialized = False
    
    @abstractmethod
    def initialize(self, dependencies: Dict[str, Any]):
        """Initialize coordinator with dependencies."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up resources."""
        pass

class CoordinatorRegistry:
    """Registry for managing coordinators."""
    
    def __init__(self):
        self._coordinators = {}
    
    def register(self, name: str, coordinator: CoordinatorBase):
        self._coordinators[name] = coordinator
    
    def get(self, name: str) -> CoordinatorBase:
        return self._coordinators.get(name)
    
    def initialize_all(self, dependencies: Dict[str, Any]):
        for coordinator in self._coordinators.values():
            if not coordinator._initialized:
                coordinator.initialize(dependencies)
                coordinator._initialized = True
```

#### Rollback Plan:
- Delete coordinators/ directory
- Remove imports from sprite_viewer.py

---

### Phase 2: Extract UISetupHelper
**Duration**: 45 minutes
**Risk**: Low-Medium

#### Extraction Target:
- Methods: `_setup_ui`, `_setup_menu_bar`, `_setup_toolbar`, `_setup_status_bar`, `_setup_main_content`
- Lines: 120-327

#### Steps:
1. Create UISetupHelper class
2. Move UI setup methods with minimal changes
3. Update SpriteViewer to use UISetupHelper
4. Test each UI component

#### Testing Checkpoint 2.1 - Using Existing Pytest Infrastructure:
```bash
# Test UI component creation with existing fixtures
python -m pytest tests/ui/test_sprite_canvas.py -v
python -m pytest tests/ui/test_playback_controls.py -v
python -m pytest tests/ui/test_frame_extractor.py -v

# Test menu and toolbar creation
python -m pytest tests/unit/test_menu_manager.py -v
python -m pytest tests/unit/test_action_manager.py -v

# Integration test with real_sprite_system fixture
python -m pytest tests/integration/test_component_integration.py -v

# Use real_event_helpers fixture for UI interaction testing
python -m pytest tests/ui/ -k "test_*_creation" -v

# Visual verification with signal testing
python -m pytest tests/integration/test_sprite_loading_workflow.py::test_ui_components_connected -v
```

#### Code Changes:
```python
# coordinators/ui_setup.py
from PySide6.QtWidgets import QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel
from PySide6.QtCore import Qt

class UISetupHelper(CoordinatorBase):
    """Handles UI component setup and initialization."""
    
    def initialize(self, dependencies: Dict[str, Any]):
        """Initialize with required dependencies."""
        self.menu_manager = dependencies['menu_manager']
        self.style_manager = dependencies['style_manager']
        self.config = dependencies['config']
    
    def setup_ui(self) -> Dict[str, QWidget]:
        """Set up complete UI and return component references."""
        components = {}
        
        # Window setup
        self._setup_window()
        
        # Create UI components
        components['menus'] = self._setup_menu_bar()
        components['toolbar'] = self._setup_toolbar()
        components['status_bar'] = self._setup_status_bar()
        components['central_widget'] = self._setup_main_content()
        
        return components
    
    def _setup_window(self):
        """Configure main window properties."""
        self.main_window.setWindowTitle("Python Sprite Viewer")
        self.main_window.setMinimumSize(
            self.config.UI.MIN_WINDOW_WIDTH,
            self.config.UI.MIN_WINDOW_HEIGHT
        )
        self.main_window.setAcceptDrops(True)
    
    # ... (move other setup methods here)
```

#### Testing Checkpoint 2.2 - Using Existing Pytest Infrastructure:
```bash
# Verify UI signals are properly connected using real_signal_tester
python -m pytest tests/ui/ -m "signal_test" -v

# Test with configured_sprite_model fixture
python -m pytest tests/integration/test_sprite_loading_workflow.py::test_real_sprite_system_workflow -v

# Run UI regression tests
python -m pytest -m regression tests/ui/ -v

# Full test suite with coverage to ensure no functionality lost
python run_tests.py --ui --coverage

# Performance check - UI creation should not degrade
python -m pytest -m performance tests/ui/ -v
```

#### Rollback Plan:
- Move methods back to SpriteViewer
- Remove UISetupHelper usage
- Restore original __init__ flow

---

### Phase 3: Extract ViewCoordinator
**Duration**: 1 hour
**Risk**: Medium

#### Extraction Target:
- Tab management logic
- View switching logic
- Grid/Canvas view coordination
- Methods: `_create_canvas_tab`, `_create_grid_tab`, tab change handling

#### Steps:
1. Create ViewCoordinator class
2. Extract tab creation and management
3. Move view switching logic
4. Update signal connections

#### Testing Checkpoint 3.1 - Using Existing Pytest Infrastructure:
```bash
# Test tab functionality with existing grid view tests
python -m pytest tests/ui/test_animation_grid_view.py -v

# Test view switching with real events
python -m pytest tests/integration/test_animation_splitting_workflow.py -v

# Test frame selection and preview in grid view
python -m pytest tests/ui/test_animation_grid_view.py::test_frame_selection -v
python -m pytest tests/ui/test_animation_grid_view.py::test_double_click_preview -v

# Integration test for tab coordination
python -m pytest tests/integration/test_component_integration.py::test_tab_widget_integration -v

# Use real_event_helpers to simulate tab switching
python -m pytest tests/ui/test_sprite_viewer.py::test_tab_switching -v
```

#### Code Changes:
```python
# coordinators/view_coordinator.py
class ViewCoordinator(CoordinatorBase):
    """Manages view switching and tab coordination."""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.tab_widget = None
        self.canvas = None
        self.grid_view = None
        self.current_view = "canvas"
    
    def create_tabbed_interface(self) -> QTabWidget:
        """Create and configure tab widget with views."""
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Create views
        canvas_tab = self._create_canvas_tab()
        self.tab_widget.addTab(canvas_tab, "Frame View")
        
        grid_tab = self._create_grid_tab()
        self.tab_widget.addTab(grid_tab, "Animation Splitting")
        
        return self.tab_widget
    
    def switch_to_canvas_view(self, frame_index: int = None):
        """Switch to canvas view, optionally showing specific frame."""
        self.tab_widget.setCurrentIndex(0)
        if frame_index is not None:
            self.main_window._sprite_model.set_current_frame(frame_index)
    
    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        self.current_view = "canvas" if index == 0 else "grid"
        # Notify other coordinators if needed
```

#### Testing Checkpoint 3.2 - Using Existing Pytest Infrastructure:
```bash
# Test segment synchronization between views
python -m pytest tests/integration/test_animation_splitting_workflow.py::test_segment_creation_and_sync -v

# Test view state with real_sprite_system fixture
python -m pytest tests/integration/test_end_to_end_workflows.py::test_view_state_persistence -v

# Performance test using existing markers
python -m pytest -m "performance and not slow" tests/ui/test_animation_grid_view.py -v

# Memory test with memory_intensive marker
python -m pytest -m memory_intensive tests/integration/ -v

# Full integration suite
python run_tests.py --integration --coverage
```

#### Rollback Plan:
- Move tab management back to SpriteViewer
- Restore direct tab widget creation in _setup_main_content
- Remove ViewCoordinator references

---

### Phase 4: Extract ExportCoordinator
**Duration**: 1 hour
**Risk**: Medium

#### Extraction Target:
- Export dialog management
- Export request handling
- Export type routing
- Methods: `_export_frames`, `_export_current_frame`, `_handle_unified_export_request`

#### Steps:
1. Create ExportCoordinator class
2. Move export methods
3. Centralize export dialog creation
4. Update export signal routing

#### Testing Checkpoint 4.1 - Using Existing Pytest Infrastructure:
```bash
# Test export dialog with existing comprehensive tests
python -m pytest tests/ui/test_export_dialog.py -v
python -m pytest tests/unit/test_frame_exporter.py -v

# Test export wizard workflows
python -m pytest tests/integration/test_export_wizard_workflow.py -v
python -m pytest tests/integration/test_export_wizard_realistic.py -v

# Test export settings integration
python -m pytest tests/integration/test_export_settings_integration.py -v

# Test export with temp_dir fixture for file operations
python -m pytest tests/unit/test_frame_exporter.py::test_export_to_temp_directory -v

# Signal testing for export requests
python -m pytest tests/ui/test_export_dialog.py::test_export_requested_signal -v
```

#### Code Changes:
```python
# coordinators/export_coordinator.py
from export import ExportDialog, get_frame_exporter, ExportHandler

class ExportCoordinator(CoordinatorBase):
    """Manages export operations and dialogs."""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.export_handler = None
        self.sprite_model = None
        self.segment_manager = None
    
    def initialize(self, dependencies: Dict[str, Any]):
        """Initialize with dependencies."""
        self.export_handler = dependencies['export_handler']
        self.sprite_model = dependencies['sprite_model']
        self.segment_manager = dependencies['segment_manager']
    
    def export_frames(self, current_only: bool = False):
        """Show export dialog for frames."""
        if not self._validate_frames():
            return
        
        dialog = self._create_export_dialog()
        dialog.exportRequested.connect(self._handle_export_request)
        dialog.exec()
    
    def export_segment(self, segment, parent_widget):
        """Export specific animation segment."""
        # Segment export logic
        pass
    
    def _validate_frames(self) -> bool:
        """Check if frames are available for export."""
        if not self.sprite_model.sprite_frames:
            QMessageBox.warning(
                self.main_window,
                "No Frames",
                "No frames to export."
            )
            return False
        return True
```

#### Testing Checkpoint 4.2 - Using Existing Pytest Infrastructure:
```bash
# Test export formats with real images
python -m pytest tests/unit/test_frame_exporter.py::test_export_formats -v

# Test batch operations
python -m pytest tests/integration/test_export_wizard_workflow.py::test_batch_export -v

# Test segment export functionality
python -m pytest tests/integration/test_animation_splitting_workflow.py::test_segment_export -v

# Performance test for large exports
python -m pytest -m "performance" tests/unit/test_frame_exporter.py -v

# Full export regression suite
python -m pytest -m "not slow" tests/ui/test_export* tests/unit/test_*export* -v
```

#### Rollback Plan:
- Move export methods back to SpriteViewer
- Restore direct export dialog creation
- Remove ExportCoordinator usage

---

### Phase 5: Extract AnimationCoordinator
**Duration**: 1.5 hours
**Risk**: Medium-High

#### Extraction Target:
- Animation state coordination
- Playback synchronization
- Frame navigation
- Methods: All animation-related methods and signal handling

#### Steps:
1. Create AnimationCoordinator class
2. Extract animation control methods
3. Centralize animation state management
4. Update component communication

#### Testing Checkpoint 5.1 - Using Existing Pytest Infrastructure:
```bash
# Test animation controller with existing tests
python -m pytest tests/unit/test_animation_controller.py -v

# Test playback controls integration
python -m pytest tests/ui/test_playback_controls.py -v

# Test frame navigation with real_event_helpers
python -m pytest tests/integration/test_sprite_loading_workflow.py::test_frame_navigation -v

# Test animation signals with real_signal_tester
python -m pytest tests/unit/test_animation_controller.py::test_animation_signals -v

# FPS and timing tests
python -m pytest tests/unit/test_animation_controller.py::test_fps_changes -v

# Real animation workflow test
python -m pytest tests/integration/test_end_to_end_workflows.py::test_animation_playback -v
```

#### Code Changes:
```python
# coordinators/animation_coordinator.py
class AnimationCoordinator(CoordinatorBase):
    """Coordinates animation state between components."""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.animation_controller = None
        self.sprite_model = None
        self.playback_controls = None
        self.is_playing = False
    
    def navigate_frame(self, direction: str):
        """Navigate frames in specified direction."""
        if direction == "prev":
            self.sprite_model.previous_frame()
        elif direction == "next":
            self.sprite_model.next_frame()
        elif direction == "first":
            self.sprite_model.first_frame()
        elif direction == "last":
            self.sprite_model.last_frame()
    
    def toggle_playback(self):
        """Toggle animation playback."""
        self.animation_controller.toggle_playback()
    
    def sync_playback_state(self):
        """Synchronize playback state across components."""
        # Update UI components based on animation state
        pass
```

#### Testing Checkpoint 5.2 - Using Existing Pytest Infrastructure:
```bash
# Test animation state with configured_sprite_model
python -m pytest tests/unit/test_animation_controller.py::test_animation_state_management -v

# Test loop mode and completion
python -m pytest tests/unit/test_animation_controller.py::test_loop_mode -v

# Performance benchmarks with existing markers
python -m pytest -m "performance and not slow" tests/unit/test_animation_controller.py -v

# Integration test for animation workflow
python -m pytest tests/integration/test_component_integration.py::test_animation_integration -v

# Full animation test suite
python run_tests.py --unit tests/unit/test_animation* --coverage
```

#### Rollback Plan:
- Move animation methods back to SpriteViewer
- Restore direct animation controller usage
- Remove AnimationCoordinator

---

### Phase 6: Extract EventCoordinator
**Duration**: 1.5 hours
**Risk**: High

#### Extraction Target:
- Keyboard event handling
- Drag and drop handling
- Custom event routing
- Methods: `keyPressEvent`, `dragEnterEvent`, `dropEvent`, etc.

#### Steps:
1. Create EventCoordinator class
2. Extract event handling logic
3. Create event routing system
4. Update event connections

#### Testing Checkpoint 6.1 - Using Existing Pytest Infrastructure:
```bash
# Test keyboard shortcuts with ShortcutManager
python -m pytest tests/unit/test_shortcut_manager.py -v

# Test key event handling
python -m pytest tests/ui/test_sprite_viewer.py::test_key_events -v

# Test drag and drop with real_event_helpers
python -m pytest tests/integration/test_sprite_loading_workflow.py::test_drag_drop_loading -v

# Test all keyboard shortcuts systematically
python -m pytest tests/unit/test_shortcut_manager.py::test_all_shortcuts -v

# Test file controller drag/drop validation
python -m pytest tests/unit/test_file_controller.py::test_drag_drop_validation -v

# Integration test for event routing
python -m pytest tests/integration/test_end_to_end_workflows.py::test_keyboard_navigation -v
```

#### Code Changes:
```python
# coordinators/event_coordinator.py
class EventCoordinator(CoordinatorBase):
    """Centralizes event handling and routing."""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.shortcut_manager = None
        self.file_controller = None
        self.coordinators = {}
    
    def handle_key_press(self, event):
        """Route keyboard events."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Build key sequence
        key_sequence = self._build_key_sequence(key, modifiers)
        
        # Route to appropriate handler
        if self.shortcut_manager.handle_key_press(key_sequence):
            event.accept()
            return True
        
        return False
    
    def handle_drop(self, event):
        """Handle file drops."""
        file_path = self.file_controller.extract_file_from_drop(event)
        if file_path:
            self.file_controller.load_file(file_path)
            event.acceptProposedAction()
```

#### Testing Checkpoint 6.2 - Using Existing Pytest Infrastructure:
```bash
# Test event propagation with Qt's event system
python -m pytest tests/ui/test_sprite_viewer.py::test_event_propagation -v

# Test shortcut conflicts
python -m pytest tests/unit/test_shortcut_manager.py::test_shortcut_conflicts -v

# Stress test with real_event_helpers
python -m pytest -m "performance" tests/ui/test_sprite_viewer.py::test_rapid_key_events -v

# Test event handling under load
python -m pytest -m "memory_intensive" tests/integration/test_end_to_end_workflows.py -v

# Full event handling regression suite
python -m pytest tests/unit/test_*manager.py tests/ui/test_*event* -v
```

#### Rollback Plan:
- Move event methods back to SpriteViewer
- Restore Qt event handler overrides
- Remove EventCoordinator

---

### Phase 7: Final Integration
**Duration**: 2 hours
**Risk**: High

#### Steps:
1. Update SpriteViewer to use all coordinators
2. Remove extracted methods
3. Optimize coordinator communication
4. Final cleanup and documentation

#### Testing Checkpoint 7.1 - Using Existing Pytest Infrastructure:
```bash
# Run full test suite with coverage
python run_tests.py --coverage

# Run all integration tests
python -m pytest tests/integration/ -v --tb=short

# Run specific workflow tests
python -m pytest tests/integration/test_end_to_end_workflows.py -v
python -m pytest tests/integration/test_sprite_loading_workflow.py -v
python -m pytest tests/integration/test_animation_splitting_workflow.py -v

# Performance regression testing
python -m pytest -m "performance" --benchmark-compare

# Memory leak detection
python -m pytest -m "memory_intensive" --memprof

# Critical path smoke tests
python -m pytest -m "smoke" -v

# CCL and grid detection tests
python -m pytest tests/integration/test_ccl_extraction_real_data.py -v

# Export functionality verification
python -m pytest tests/integration/test_export_wizard_workflow.py -v

# Manual testing with real sprite sheets:
python -m pytest tests/integration/test_complete_user_workflows.py -v

# Final comprehensive test
python run_tests.py --all --coverage --html-report
```

#### Final SpriteViewer Structure:
```python
class SpriteViewer(QMainWindow):
    """Main window - coordinates high-level application flow."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize coordinator registry
        self._coordinator_registry = CoordinatorRegistry()
        
        # Initialize core components
        self._init_core_components()
        
        # Initialize coordinators
        self._init_coordinators()
        
        # Set up application
        self._setup_application()
    
    def _init_coordinators(self):
        """Initialize all coordinators."""
        self._ui_helper = UISetupHelper(self)
        self._view_coord = ViewCoordinator(self)
        self._export_coord = ExportCoordinator(self)
        self._animation_coord = AnimationCoordinator(self)
        self._event_coord = EventCoordinator(self)
        
        # Register coordinators
        self._coordinator_registry.register('ui', self._ui_helper)
        self._coordinator_registry.register('view', self._view_coord)
        self._coordinator_registry.register('export', self._export_coord)
        self._coordinator_registry.register('animation', self._animation_coord)
        self._coordinator_registry.register('event', self._event_coord)
```

## Testing Strategy Using Existing Pytest Infrastructure

### Leveraging Existing Test Fixtures

#### Core Fixtures Available:
- `qapp` - Session-scoped QApplication for all Qt tests
- `sprite_model` - Fresh SpriteModel instance
- `configured_sprite_model` - Pre-configured model with test data
- `real_sprite_system` - Complete integrated sprite system
- `real_event_helpers` - Create authentic Qt events
- `real_signal_tester` - Test signal emissions with QSignalSpy
- `temp_dir` - Temporary directory for file operations

#### Using Fixtures in Coordinator Tests:
```python
# tests/unit/coordinators/test_ui_setup_helper.py
def test_ui_setup_with_fixtures(qapp, real_sprite_system):
    """Test UISetupHelper using existing fixtures."""
    viewer = real_sprite_system.viewer
    assert viewer.centralWidget() is not None
    assert viewer.menuBar() is not None

# tests/unit/coordinators/test_view_coordinator.py  
def test_tab_switching(real_sprite_system, real_event_helpers):
    """Test ViewCoordinator with real Qt events."""
    viewer = real_sprite_system.viewer
    tab_widget = viewer._tab_widget
    
    # Use real_event_helpers to simulate tab click
    real_event_helpers.click_widget(tab_widget.tabBar(), 1)
    assert tab_widget.currentIndex() == 1
```

### Test Execution Strategy

#### Phase-Specific Test Commands:
```bash
# Before any refactoring - establish baseline
python run_tests.py --all --coverage --save-baseline

# After each phase - compare with baseline
python run_tests.py --all --coverage --compare-baseline

# Quick validation during development
python -m pytest -m "smoke" -v --tb=short

# Focused testing on affected components
python -m pytest tests/ui/test_sprite_viewer.py -v
python -m pytest tests/unit/test_*manager.py -v
```

#### Continuous Testing During Refactoring:
```bash
# Watch mode for immediate feedback
python run_tests.py --watch tests/ui/ tests/unit/

# Run tests affected by changes
python -m pytest --lf  # Run last failed
python -m pytest --ff  # Run failures first
```

### Integration with Existing Test Suites

#### Reuse Existing Integration Tests:
- `test_sprite_loading_workflow.py` - Validates complete loading flow
- `test_animation_splitting_workflow.py` - Tests animation features
- `test_export_wizard_workflow.py` - Validates export functionality
- `test_end_to_end_workflows.py` - Complete user scenarios
- `test_component_integration.py` - Component interactions

#### Adapt Tests for Coordinators:
```python
# Add to existing test files
class TestWithCoordinators:
    """Test existing functionality works with new coordinator architecture."""
    
    def test_sprite_loading_with_coordinators(self, real_sprite_system):
        """Ensure sprite loading works through coordinators."""
        # Use existing test logic but verify coordinator integration
        assert hasattr(real_sprite_system.viewer, '_coordinator_registry')
        # Run existing workflow tests
```

### Performance Monitoring

#### Use Existing Performance Markers:
```bash
# Run performance tests to ensure no regression
python -m pytest -m "performance" --benchmark-autosave

# Compare with baseline after refactoring
python -m pytest -m "performance" --benchmark-compare=baseline

# Memory profiling for coordinator overhead
python -m pytest -m "memory_intensive" --memprof
```

### Signal Testing Strategy

#### Leverage real_signal_tester:
```python
def test_coordinator_signals(real_signal_tester, real_sprite_system):
    """Test signals work correctly through coordinators."""
    viewer = real_sprite_system.viewer
    model = real_sprite_system.model
    
    # Set up signal spy
    frame_spy = real_signal_tester.connect_spy(
        model.frameChanged, 'frameChanged'
    )
    
    # Trigger action through coordinator
    viewer._animation_coord.navigate_frame('next')
    
    # Verify signal emitted
    real_signal_tester.verify_signal_emitted(frame_spy, 1)
```

## Risk Mitigation

### Backup Strategy
1. Create git branch: `refactor/sprite-viewer-coordinators`
2. Commit after each successful phase
3. Tag working versions: `refactor-phase-1-complete`, etc.

### Rollback Procedures
- Each phase has specific rollback steps
- Keep original methods until phase is validated
- Use feature flags if needed for gradual rollout

### Monitoring
- Log coordinator initialization
- Track performance metrics
- Monitor memory usage
- Watch for event handling issues

## Success Criteria

### Functional
- [ ] All existing features work
- [ ] No performance degradation
- [ ] No new bugs introduced
- [ ] All tests pass

### Architectural
- [ ] SpriteViewer under 200 lines
- [ ] Clear separation of concerns
- [ ] Improved testability
- [ ] Better maintainability

### Code Quality
- [ ] Each coordinator has single responsibility
- [ ] Reduced coupling between components
- [ ] Improved cohesion within coordinators
- [ ] Clear interfaces between coordinators

## Key Test Files to Monitor During Refactoring

### Critical Test Files by Phase:

#### Phase 1-2 (Infrastructure & UI Setup):
- `tests/ui/test_sprite_viewer.py` - Main window tests
- `tests/unit/test_menu_manager.py` - Menu creation
- `tests/unit/test_action_manager.py` - Action callbacks
- `tests/integration/test_component_integration.py` - Component wiring

#### Phase 3 (View Coordination):
- `tests/ui/test_animation_grid_view.py` - Grid view functionality
- `tests/integration/test_animation_splitting_workflow.py` - Tab coordination
- `tests/ui/test_sprite_canvas.py` - Canvas view

#### Phase 4 (Export):
- `tests/ui/test_export_dialog.py` - Export UI
- `tests/unit/test_frame_exporter.py` - Export engine
- `tests/integration/test_export_wizard_workflow.py` - Export flows

#### Phase 5 (Animation):
- `tests/unit/test_animation_controller.py` - Animation logic
- `tests/ui/test_playback_controls.py` - Playback UI

#### Phase 6 (Events):
- `tests/unit/test_shortcut_manager.py` - Keyboard handling
- `tests/integration/test_sprite_loading_workflow.py` - Drag/drop

#### Phase 7 (Integration):
- `tests/integration/test_end_to_end_workflows.py` - Complete flows
- `tests/integration/test_ccl_extraction_real_data.py` - CCL functionality

### Test Coverage Commands:

```bash
# Check coverage before starting
python run_tests.py --coverage --html-report
# Open htmlcov/index.html to see baseline

# Monitor coverage during refactoring
python -m pytest --cov=sprite_viewer --cov=coordinators \
    --cov-report=html --cov-report=term-missing

# Ensure no coverage regression
python -m pytest --cov-fail-under=85
```

## Timeline

- **Phase 1**: 30 minutes
- **Phase 2**: 45 minutes  
- **Phase 3**: 1 hour
- **Phase 4**: 1 hour
- **Phase 5**: 1.5 hours
- **Phase 6**: 1.5 hours
- **Phase 7**: 2 hours

**Total**: ~8.5 hours (including testing)

## Next Steps

1. Establish test baseline: `python run_tests.py --all --coverage --save-baseline`
2. Create feature branch: `git checkout -b refactor/sprite-viewer-coordinators`
3. Begin Phase 1 implementation
4. Run phase-specific tests after each step
5. Document lessons learned and any test failures encountered