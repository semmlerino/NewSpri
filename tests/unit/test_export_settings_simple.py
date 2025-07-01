"""
Unit tests for simplified export settings step
"""

import pytest
from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QSpinBox
from PySide6.QtCore import Qt

from export.export_settings_step_simple import (
    ExportSettingsStepSimple, SettingsCard, SimpleDirectorySelector,
    QuickScaleButtons, GridLayoutSelector
)
from export.export_presets import ExportPreset


class TestSettingsCard:
    """Test the settings card component."""
    
    def test_card_creation(self, qtbot):
        """Test creating a settings card."""
        card = SettingsCard("Test Card", "🎨")
        qtbot.addWidget(card)
        
        # Check title is set
        labels = card.findChildren(QLabel)
        assert any("🎨 Test Card" in label.text() for label in labels)
    
    def test_add_row(self, qtbot):
        """Test adding rows to card."""
        card = SettingsCard("Test Card")
        qtbot.addWidget(card)
        
        # Add a row
        widget = QLineEdit()
        card.add_row("Test:", widget, "Help text")
        
        # Check row was added
        assert widget.parent() is not None
        labels = card.findChildren(QLabel)
        assert any("Test:" in label.text() for label in labels)
        assert any("Help text" in label.text() for label in labels)


class TestSimpleDirectorySelector:
    """Test the simplified directory selector."""
    
    def test_directory_selector(self, qtbot):
        """Test directory selector creation and validation."""
        selector = SimpleDirectorySelector()
        qtbot.addWidget(selector)
        
        # Initially invalid (no directory)
        assert not selector.is_valid()
        
        # Set directory
        selector.set_directory("/tmp")
        assert selector.get_directory() == "/tmp"
        assert selector.is_valid()
    
    def test_directory_change_signal(self, qtbot):
        """Test directory change signal."""
        selector = SimpleDirectorySelector()
        qtbot.addWidget(selector)
        
        # Connect signal
        signal_received = []
        selector.directoryChanged.connect(lambda d: signal_received.append(d))
        
        # Change directory
        selector.set_directory("/home")
        assert len(signal_received) == 1
        assert signal_received[0] == "/home"


class TestQuickScaleButtons:
    """Test quick scale selection buttons."""
    
    def test_scale_buttons(self, qtbot):
        """Test scale button creation and selection."""
        buttons = QuickScaleButtons()
        qtbot.addWidget(buttons)
        
        # Default scale
        assert buttons.get_scale() == 1.0
        
        # Check buttons exist
        button_group = buttons.button_group
        assert len(button_group.buttons()) == 4  # Default scales
    
    def test_scale_change_signal(self, qtbot):
        """Test scale change signal."""
        buttons = QuickScaleButtons([1.0, 2.0])
        qtbot.addWidget(buttons)
        
        # Connect signal
        signal_received = []
        buttons.scaleChanged.connect(lambda s: signal_received.append(s))
        
        # Click 2x button
        for btn in buttons.button_group.buttons():
            if btn.text() == "2.0x":
                qtbot.mouseClick(btn, Qt.LeftButton)
                break
        
        assert len(signal_received) == 1
        assert signal_received[0] == 2.0


class TestGridLayoutSelector:
    """Test grid layout selector."""
    
    def test_layout_modes(self, qtbot):
        """Test different layout modes."""
        selector = GridLayoutSelector()
        qtbot.addWidget(selector)
        
        # Default is auto
        mode, cols, rows = selector.get_layout()
        assert mode == "auto"
        
        # Check mode buttons exist
        assert len(selector.mode_group.buttons()) == 4
    
    def test_layout_change_signal(self, qtbot):
        """Test layout change signal."""
        selector = GridLayoutSelector()
        qtbot.addWidget(selector)
        
        # Connect signal
        signal_received = []
        selector.layoutChanged.connect(
            lambda m, c, r: signal_received.append((m, c, r))
        )
        
        # Click columns mode button
        columns_btn = selector.mode_group.button(1)  # Second button
        qtbot.mouseClick(columns_btn, Qt.LeftButton)
        
        assert len(signal_received) == 1
        assert signal_received[0][0] == "columns"


class TestExportSettingsStepSimple:
    """Test the simplified export settings step."""
    
    @pytest.fixture
    def individual_preset(self):
        """Create individual frames preset."""
        return ExportPreset(
            name="individual_frames",
            display_name="Individual Frames",
            icon="📁",
            description="Export each frame as a separate file",
            mode="individual",
            format="PNG",
            scale=1.0,
            default_pattern="{name}_{index:03d}",
            tooltip="Export each frame as an individual image file",
            use_cases=["Game sprites", "Animation frames", "Icon sets"]
        )
    
    @pytest.fixture
    def sheet_preset(self):
        """Create sprite sheet preset."""
        return ExportPreset(
            name="sprite_sheet",
            display_name="Sprite Sheet",
            icon="📋",
            description="Combine all frames into a single image",
            mode="sheet",
            format="PNG",
            scale=1.0,
            default_pattern="spritesheet",
            tooltip="Export all frames as a single sprite sheet",
            use_cases=["Game atlases", "Web sprites", "Texture packing"]
        )
    
    @pytest.fixture
    def selected_preset(self):
        """Create selected frames preset."""
        return ExportPreset(
            name="selected_frames",
            display_name="Selected Frames",
            icon="🎯",
            description="Export only specific frames",
            mode="selected",
            format="PNG",
            scale=1.0,
            default_pattern="{name}_{index:03d}",
            tooltip="Export only the frames you select",
            use_cases=["Partial exports", "Key frames", "Testing"]
        )
    
    def test_step_creation(self, qtbot):
        """Test creating the settings step."""
        step = ExportSettingsStepSimple(frame_count=10, current_frame=2)
        qtbot.addWidget(step)
        
        assert step.frame_count == 10
        assert step.current_frame == 2
        # Title is passed to parent constructor, not set as window title
        assert hasattr(step, 'title')
        assert step.title == "Configure Export Settings"
    
    def test_individual_frames_ui(self, qtbot, individual_preset):
        """Test UI for individual frames export."""
        step = ExportSettingsStepSimple(frame_count=10)
        qtbot.addWidget(step)
        
        # Setup for preset
        step._setup_for_preset(individual_preset)
        
        # Check cards were created
        cards = step.findChildren(SettingsCard)
        assert len(cards) >= 2  # Location and Format cards
        
        # Check widgets exist
        assert 'directory' in step._settings_widgets
        assert 'base_name' in step._settings_widgets
        assert 'format' in step._settings_widgets
        assert 'scale' in step._settings_widgets
    
    def test_sprite_sheet_ui(self, qtbot, sheet_preset):
        """Test UI for sprite sheet export."""
        step = ExportSettingsStepSimple(frame_count=10)
        qtbot.addWidget(step)
        
        # Setup for preset
        step._setup_for_preset(sheet_preset)
        
        # Check specific widgets for sprite sheet
        assert 'single_filename' in step._settings_widgets
        assert 'grid_layout' in step._settings_widgets
        assert 'spacing' in step._settings_widgets
        assert 'background' in step._settings_widgets
    
    def test_selected_frames_ui(self, qtbot, selected_preset):
        """Test UI for selected frames export."""
        step = ExportSettingsStepSimple(frame_count=10, current_frame=3)
        qtbot.addWidget(step)
        
        # Setup for preset
        step._setup_for_preset(selected_preset)
        
        # Check frame list exists
        assert 'frame_list' in step._settings_widgets
        frame_list = step._settings_widgets['frame_list']
        
        # Check frames populated
        assert frame_list.count() == 10
        
        # Check current frame selected
        selected_items = frame_list.selectedItems()
        assert len(selected_items) == 1
        assert selected_items[0].data(Qt.UserRole) == 3
    
    def test_validation(self, qtbot, individual_preset):
        """Test settings validation."""
        step = ExportSettingsStepSimple()
        qtbot.addWidget(step)
        
        step._setup_for_preset(individual_preset)
        
        # Clear the default directory to test invalid state
        step._settings_widgets['directory'].set_directory("")
        
        # Should be invalid (no directory)
        assert not step.validate()
        
        # Set valid directory
        step._settings_widgets['directory'].set_directory("/tmp")
        
        # Still invalid - no base name
        step._settings_widgets['base_name'].setText("")
        assert not step.validate()
        
        # Set base name
        step._settings_widgets['base_name'].setText("test")
        
        # Should now be valid
        assert step.validate()
    
    def test_get_data(self, qtbot, sheet_preset):
        """Test getting settings data."""
        step = ExportSettingsStepSimple()
        qtbot.addWidget(step)
        
        step._setup_for_preset(sheet_preset)
        
        # Set some values
        step._settings_widgets['directory'].set_directory("/export")
        step._settings_widgets['single_filename'].setText("sheet")
        
        # Get data
        data = step.get_data()
        
        assert data['output_dir'] == "/export"
        assert data['single_filename'] == "sheet"
        assert 'format' in data
        assert 'scale' in data


# Import for type checking
from PySide6.QtWidgets import QLabel