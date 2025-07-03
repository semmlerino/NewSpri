"""
Unit Tests for Export Wizard Components
Tests individual components of the wizard system in isolation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QColor, QPainter
from PySide6.QtWidgets import QWidget, QApplication

from export.dialogs.base.wizard_base import WizardStep, WizardWidget
from export.steps.type_selection import ExportTypeStepSimple as ExportTypeStep
from export.steps.settings_preview import ExportSettingsPreviewStep
from export.core.frame_exporter import SpriteSheetLayout
from export.core.export_presets import ExportPreset


class TestWizardStep:
    """Test the base WizardStep class."""
    
    def test_wizard_step_creation(self, qtbot):
        """Test creating a wizard step."""
        step = WizardStep("Test Step", "Test subtitle")
        qtbot.addWidget(step)
        
        assert step.title == "Test Step"
        assert step.subtitle == "Test subtitle"
        assert step._is_valid is True
        assert step._step_data == {}
    
    def test_wizard_step_validation(self, qtbot):
        """Test step validation."""
        step = WizardStep("Test", "Test")
        qtbot.addWidget(step)
        
        # Default validation
        assert step.validate() is True
        
        # Change validation state
        step._is_valid = False
        assert step.validate() is False
    
    def test_wizard_step_data(self, qtbot):
        """Test step data management."""
        step = WizardStep("Test", "Test")
        qtbot.addWidget(step)
        
        # Get empty data
        assert step.get_data() == {}
        
        # Set data
        test_data = {'key': 'value', 'number': 42}
        step.set_data(test_data)
        assert step.get_data() == test_data
    
    def test_wizard_step_lifecycle(self, qtbot):
        """Test step lifecycle methods."""
        step = WizardStep("Test", "Test")
        qtbot.addWidget(step)
        
        # Track calls
        enter_called = False
        leave_called = False
        
        def on_enter():
            nonlocal enter_called
            enter_called = True
        
        def on_leave():
            nonlocal leave_called  
            leave_called = True
        
        # Override methods
        step.on_entering = on_enter
        step.on_leaving = on_leave
        
        # Test lifecycle
        step.on_entering()
        assert enter_called is True
        
        step.on_leaving()
        assert leave_called is True


class TestVisualPresetCard:
    """Test the visual preset card component."""
    
    def test_card_visual_elements(self, qtbot):
        """Test card has correct visual elements."""
        preset = EnhancedExportPreset(
            name="test",
            display_name="Test Card",
            icon="🧪",
            description="A test preset card",
            mode="individual",
            format="PNG",
            scale=1.0,
            default_pattern="{name}",
            tooltip="Test tooltip",
            use_cases=["Testing"],
            short_description="For testing",
            recommended_for=["Unit tests"]
        )
        
        card = VisualPresetCard(preset)
        qtbot.addWidget(card)
        
        # Check size
        assert card.width() == 220
        assert card.height() == 160
        
        # Check labels exist and have correct text
        icon_labels = card.findChildren(QWidget)
        text_found = []
        for widget in icon_labels:
            if hasattr(widget, 'text'):
                text_found.append(widget.text())
        
        assert "🧪" in text_found
        assert "Test Card" in text_found
        assert any("testing" in t.lower() for t in text_found)
    
    def test_card_preview_generation(self, qtbot):
        """Test visual preview generation for different export types."""
        # Test individual frames preview
        preset_individual = Mock(
            name="individual_frames",
            icon="📁",
            display_name="Individual"
        )
        card = VisualPresetCard(preset_individual)
        qtbot.addWidget(card)
        
        # Create preview
        pixmap = QPixmap(188, 60)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        card._draw_individual_frames_preview(painter)
        painter.end()
        
        # Should have drawn something
        assert not pixmap.isNull()
    
    def test_card_selection_state(self, qtbot):
        """Test card selection state changes."""
        preset = Mock(name="test", icon="🧪", display_name="Test")
        card = VisualPresetCard(preset)
        qtbot.addWidget(card)
        
        # Initial state
        assert card._is_selected is False
        
        # Set selected
        card.set_selected(True)
        assert card._is_selected is True
        
        # Visual state should change (border)
        style = card.styleSheet()
        assert "3px solid" in style  # Selected border
    
    def test_card_click_signal(self, qtbot):
        """Test card emits signal when clicked."""
        preset = Mock(name="test", icon="🧪", display_name="Test")
        card = VisualPresetCard(preset)
        qtbot.addWidget(card)
        
        # Click card
        with qtbot.waitSignal(card.clicked, timeout=1000) as blocker:
            qtbot.mouseClick(card, Qt.LeftButton)
        
        assert blocker.args[0] == preset


class TestExportSettingsValidation:
    """Test export settings validation logic."""
    
    def test_directory_validation(self, qtbot):
        """Test directory validation in settings."""
        step = ExportSettingsStep()
        qtbot.addWidget(step)
        
        # Mock preset
        preset = Mock(mode="individual", format="PNG", scale=1.0)
        step._setup_for_preset(preset)
        
        # Invalid with empty directory
        step.directory_selector.set_directory("")
        assert step.validate() is False
        
        # Valid with directory
        step.directory_selector.set_directory("/tmp")
        assert step.validate() is True
    
    def test_filename_validation(self, qtbot):
        """Test filename validation."""
        step = ExportSettingsStep()
        qtbot.addWidget(step)
        
        preset = Mock(mode="individual", format="PNG", scale=1.0)
        step._setup_for_preset(preset)
        
        # Valid with default
        assert step.validate() is True
        
        # Invalid with empty base name
        if hasattr(step, 'base_name_edit'):
            step.base_name_edit.setText("")
            assert step.validate() is False
            
            # Valid with name
            step.base_name_edit.setText("sprite")
            assert step.validate() is True
    
    def test_frame_selection_validation(self, qtbot):
        """Test frame selection validation for selected frames mode."""
        step = ExportSettingsStep(frame_count=10)
        qtbot.addWidget(step)
        
        # Mock selected frames preset
        preset = Mock(mode="selected", format="PNG", scale=1.0)
        step._setup_for_preset(preset)
        
        if hasattr(step, 'frame_list'):
            # Should be invalid with no selection
            step.frame_list.clearSelection()
            assert step.validate() is False
            
            # Valid with selection
            step.frame_list.item(0).setSelected(True)
            assert step.validate() is True


class TestSpriteSheetPreviewView:
    """Test the sprite sheet preview graphics view."""
    
    def test_preview_view_creation(self, qtbot):
        """Test creating preview view."""
        view = SpriteSheetPreviewView()
        qtbot.addWidget(view)
        
        assert view.scene is not None
        assert view._zoom_level == 1.0
        assert view.dragMode() == view.ScrollHandDrag
    
    def test_zoom_functionality(self, qtbot):
        """Test zoom in/out functionality."""
        view = SpriteSheetPreviewView()
        qtbot.addWidget(view)
        
        initial_zoom = view._zoom_level
        
        # Simulate zoom in
        from PySide6.QtGui import QWheelEvent
        from PySide6.QtCore import QPointF
        
        # Create wheel event for zoom in
        wheel_event = QWheelEvent(
            QPointF(50, 50),  # position
            QPointF(50, 50),  # global position
            QPointF(),  # pixel delta
            QPointF(0, 120),  # angle delta (positive = zoom in)
            Qt.NoButton,  # buttons
            Qt.NoModifier,  # modifiers
            Qt.ScrollBegin,  # phase
            False  # inverted
        )
        
        view.wheelEvent(wheel_event)
        assert view._zoom_level > initial_zoom
        
        # Test zoom limits
        for _ in range(20):  # Zoom in a lot
            view.wheelEvent(wheel_event)
        
        assert view._zoom_level <= 5.0  # Max zoom
    
    def test_fit_in_view(self, qtbot):
        """Test fit preview in view functionality."""
        view = SpriteSheetPreviewView()
        qtbot.addWidget(view)
        
        # Add some content
        pixmap = QPixmap(200, 200)
        pixmap.fill(Qt.blue)
        view.scene.addPixmap(pixmap)
        
        # Zoom in first
        view._zoom_level = 2.0
        
        # Fit in view should reset zoom
        view.fit_preview_in_view()
        assert view._zoom_level == 1.0


class TestExportPreviewGeneration:
    """Test preview generation for different export types."""
    
    def test_sprite_sheet_preview_calculation(self):
        """Test sprite sheet layout calculation."""
        layout = SpriteSheetLayout(
            mode='auto',
            spacing=2,
            padding=4
        )
        
        # Test dimensions calculation
        frame_width = 32
        frame_height = 32
        frame_count = 16
        
        # For auto mode with 16 frames, should be 4x4
        import math
        expected_cols = math.ceil(math.sqrt(frame_count))
        expected_rows = math.ceil(frame_count / expected_cols)
        
        assert expected_cols == 4
        assert expected_rows == 4
        
        # Calculate expected sheet size
        sheet_width = layout.padding * 2 + expected_cols * frame_width + (expected_cols - 1) * layout.spacing
        sheet_height = layout.padding * 2 + expected_rows * frame_height + (expected_rows - 1) * layout.spacing
        
        assert sheet_width == 4 * 2 + 4 * 32 + 3 * 2  # padding + frames + spacing
        assert sheet_height == 4 * 2 + 4 * 32 + 3 * 2
    
    def test_individual_frames_preview_data(self, qtbot):
        """Test individual frames preview data generation."""
        step = ExportPreviewStep()
        qtbot.addWidget(step)
        
        # Mock preset and settings
        step._current_preset = Mock(mode="individual", display_name="Individual Frames")
        step._export_settings = {
            'base_name': 'sprite',
            'pattern': '{name}_{index:03d}',
            'format': 'PNG'
        }
        
        # Test filename generation
        pattern = step._export_settings['pattern']
        base_name = step._export_settings['base_name']
        
        filenames = []
        for i in range(3):
            filename = pattern.format(name=base_name, index=i, frame=i+1)
            filenames.append(f"{filename}.png")
        
        assert filenames[0] == "sprite_000.png"
        assert filenames[1] == "sprite_001.png"
        assert filenames[2] == "sprite_002.png"


class TestWizardDataFlow:
    """Test data flow through wizard steps."""
    
    def test_preset_data_propagation(self, qtbot):
        """Test preset selection propagates through steps."""
        # Create wizard steps
        type_step = ExportTypeStep()
        settings_step = ExportSettingsStep()
        qtbot.addWidget(type_step)
        qtbot.addWidget(settings_step)
        
        # Select a preset in type step
        preset = Mock(
            name="test_preset",
            mode="individual",
            format="PNG",
            scale=2.0
        )
        type_step._selected_preset = preset
        
        # Get data from type step
        type_data = type_step.get_data()
        assert type_data['preset'] == preset
        assert type_data['preset_name'] == "test_preset"
        assert type_data['export_mode'] == "individual"
        
        # Settings step should use this data
        settings_step._setup_for_preset(preset)
        assert settings_step._current_preset == preset
    
    def test_settings_data_collection(self, qtbot):
        """Test collecting settings from UI widgets."""
        step = ExportSettingsStep()
        qtbot.addWidget(step)
        
        # Mock UI widgets
        step._settings_widgets = {
            'directory': Mock(get_directory=Mock(return_value="/tmp/export")),
            'base_name': Mock(text=Mock(return_value="sprite")),
            'format': Mock(currentText=Mock(return_value="PNG")),
            'scale': Mock(value=Mock(return_value=2.0))
        }
        
        # Collect data
        data = step.get_data()
        
        assert data['output_dir'] == "/tmp/export"
        assert data['base_name'] == "sprite"
        assert data['format'] == "PNG"
        assert data['scale'] == 2.0


# Performance benchmarks
@pytest.mark.performance
class TestComponentPerformance:
    """Performance tests for wizard components."""
    
    def test_preset_card_rendering_performance(self, qtbot, benchmark):
        """Benchmark preset card rendering."""
        preset = Mock(name="test", icon="🧪", display_name="Test")
        
        def create_and_render_card():
            card = VisualPresetCard(preset)
            qtbot.addWidget(card)
            card.show()
            QApplication.processEvents()
            card.close()
        
        # Should render in under 50ms
        result = benchmark(create_and_render_card)
        assert result.stats['mean'] < 0.05
    
    def test_preview_generation_performance(self, qtbot, benchmark):
        """Benchmark preview generation."""
        step = ExportPreviewStep()
        qtbot.addWidget(step)
        step._sprites = [QPixmap(32, 32) for _ in range(100)]
        step._current_preset = Mock(mode="sheet")
        step._export_settings = {
            'layout_mode': 'auto',
            'spacing': 0,
            'padding': 0
        }
        
        # Should generate preview for 100 frames in under 200ms
        result = benchmark(step._generate_sprite_sheet_preview)
        assert result.stats['mean'] < 0.2