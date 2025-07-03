"""
Realistic Unit Tests for Export Wizard Components
Tests individual components without excessive mocking.
"""

import pytest
from PySide6.QtCore import Qt, Signal, QSize, QPointF
from PySide6.QtGui import QPixmap, QColor, QPainter, QWheelEvent
from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout, QLabel
from PySide6.QtTest import QTest

from export.dialogs.base.wizard_base import WizardStep, WizardWidget
from export.steps.type_selection import ExportTypeStepSimple as ExportTypeStep
from export.steps.settings_preview import ExportSettingsPreviewStep
from export.core.frame_exporter import SpriteSheetLayout
from export.core.export_presets import ExportPreset


class TestWizardStepReal:
    """Test the base WizardStep class with real behavior."""
    
    def test_wizard_step_lifecycle_real(self, qtbot):
        """Test wizard step lifecycle with real signal emission."""
        
        class TestStep(WizardStep):
            """Custom step for testing."""
            def __init__(self):
                super().__init__("Test Step", "Testing lifecycle")
                self.enter_count = 0
                self.leave_count = 0
                self.data_changes = []
                
                # Add some real UI
                layout = QVBoxLayout(self)
                self.label = QLabel("Test content")
                layout.addWidget(self.label)
                
                # Connect to own signal
                self.dataChanged.connect(self._on_data_changed)
            
            def on_entering(self):
                self.enter_count += 1
                self._step_data['entered'] = True
                self.dataChanged.emit(self._step_data)
            
            def on_leaving(self):
                self.leave_count += 1
                self._step_data['left'] = True
                self.dataChanged.emit(self._step_data)
            
            def _on_data_changed(self, data):
                self.data_changes.append(data.copy())
        
        step = TestStep()
        qtbot.addWidget(step)
        
        # Test entering
        step.on_entering()
        assert step.enter_count == 1
        assert step.get_data()['entered'] is True
        assert len(step.data_changes) == 1
        
        # Test leaving
        step.on_leaving()
        assert step.leave_count == 1
        assert step.get_data()['left'] is True
        assert len(step.data_changes) == 2
        
        # Test validation signal
        validation_changes = []
        step.stepValidated.connect(lambda valid: validation_changes.append(valid))
        
        step._is_valid = False
        step.stepValidated.emit(False)
        assert validation_changes == [False]
        
        step._is_valid = True
        step.stepValidated.emit(True)
        assert validation_changes == [False, True]


class TestVisualPresetCardReal:
    """Test visual preset cards with real rendering."""
    
    def test_card_real_click_interaction(self, qtbot):
        """Test real mouse click interaction on card."""
        preset = EnhancedExportPreset(
            name="test_preset",
            display_name="Test Preset",
            icon="🧪",
            description="A real test preset",
            mode="individual",
            format="PNG",
            scale=1.0,
            default_pattern="{name}_{index:03d}",
            tooltip="Test tooltip",
            use_cases=["Testing"],
            short_description="For testing",
            recommended_for=["Unit tests"]
        )
        
        card = VisualPresetCard(preset)
        qtbot.addWidget(card)
        card.show()
        
        # Track click signal
        clicked_presets = []
        card.clicked.connect(lambda p: clicked_presets.append(p))
        
        # Simulate real mouse click
        qtbot.mouseClick(card, Qt.LeftButton, pos=QPoint(110, 80))  # Center of card
        
        # Verify signal was emitted
        assert len(clicked_presets) == 1
        assert clicked_presets[0] == preset
        
        # Test selection state
        assert not card._is_selected
        card.set_selected(True)
        assert card._is_selected
        
        # Verify visual state changed
        assert "3px solid" in card.styleSheet()
    
    def test_card_preview_rendering(self, qtbot):
        """Test actual preview rendering."""
        preset = EnhancedExportPreset(
            name="sprite_sheet",
            display_name="Sprite Sheet",
            icon="📋",
            description="Export as sprite sheet",
            mode="sheet",
            format="PNG",
            scale=1.0,
            default_pattern="{name}",
            tooltip="Combine all frames",
            use_cases=["Game engines"],
            short_description="Single image file",
            recommended_for=["Unity", "Godot"]
        )
        
        card = VisualPresetCard(preset)
        qtbot.addWidget(card)
        card.show()
        
        # Force a paint event
        QApplication.processEvents()
        
        # Grab the rendered widget
        pixmap = card.grab()
        assert not pixmap.isNull()
        assert pixmap.width() == 220
        assert pixmap.height() == 160
        
        # The preview should have been drawn
        assert card._preview_widget is not None


class TestExportSettingsReal:
    """Test export settings with real UI interactions."""
    
    def test_directory_selector_real_interaction(self, qtbot, tmp_path):
        """Test real directory selector interaction."""
        step = ExportSettingsStep(frame_count=10)
        qtbot.addWidget(step)
        step.show()
        
        # Set up for a preset
        preset = EnhancedExportPreset(
            name="individual_frames",
            display_name="Individual Frames",
            icon="📁",
            description="Export each frame",
            mode="individual",
            format="PNG",
            scale=1.0,
            default_pattern="{name}_{index:03d}",
            tooltip="One file per frame",
            use_cases=["Frame by frame editing"],
            short_description="Separate files",
            recommended_for=["Photoshop", "GIMP"]
        )
        step._setup_for_preset(preset)
        
        # Test validation with empty directory
        assert not step.validate()
        
        # Set real directory
        step.directory_selector.set_directory(str(tmp_path))
        assert step.validate()
        
        # Test base name validation
        step.base_name_edit.setText("")
        assert not step.validate()
        
        step.base_name_edit.setText("test_sprite")
        assert step.validate()
        
        # Get real data
        data = step.get_data()
        assert data['output_dir'] == str(tmp_path)
        assert data['base_name'] == "test_sprite"
        assert data['format'] == "PNG"
    
    def test_frame_selection_real_ui(self, qtbot):
        """Test real frame selection UI."""
        step = ExportSettingsStep(frame_count=10, current_frame=3)
        qtbot.addWidget(step)
        step.show()
        
        # Set up for selected frames
        preset = EnhancedExportPreset(
            name="selected_frames",
            display_name="Selected Frames",
            icon="✅",
            description="Export selected frames",
            mode="selected",
            format="PNG",
            scale=1.0,
            default_pattern="{name}_{index:03d}",
            tooltip="Choose specific frames",
            use_cases=["Partial export"],
            short_description="Custom selection",
            recommended_for=["Any workflow"]
        )
        step._setup_for_preset(preset)
        
        # Frame list should exist
        assert hasattr(step, 'frame_list')
        assert step.frame_list.count() == 10
        
        # Select some frames
        step.frame_list.clearSelection()
        step.frame_list.item(1).setSelected(True)
        step.frame_list.item(3).setSelected(True)  # Current frame
        step.frame_list.item(5).setSelected(True)
        step.frame_list.item(7).setSelected(True)
        
        # Verify selection
        selected_indices = [item.row() for item in step.frame_list.selectedItems()]
        assert sorted(selected_indices) == [1, 3, 5, 7]
        
        # Check selection info
        assert "4 frames selected" in step.selection_info_label.text()
        
        # Validation should pass
        assert step.validate()
        
        # Get data
        data = step.get_data()
        assert data['selected_indices'] == [1, 3, 5, 7]
    
    def test_sprite_sheet_settings_real(self, qtbot):
        """Test sprite sheet specific settings."""
        step = ExportSettingsStep(frame_count=16)
        qtbot.addWidget(step)
        step.show()
        
        preset = EnhancedExportPreset(
            name="sprite_sheet",
            display_name="Sprite Sheet",
            icon="📋",
            description="Export as sprite sheet",
            mode="sheet",
            format="PNG",
            scale=1.0,
            default_pattern="{name}",
            tooltip="Single image file",
            use_cases=["Game engines"],
            short_description="Combined frames",
            recommended_for=["Unity", "Godot"]
        )
        step._setup_for_preset(preset)
        
        # Should have sprite sheet controls
        assert hasattr(step, 'layout_mode_combo')
        assert hasattr(step, 'spacing_spin')
        assert hasattr(step, 'padding_spin')
        assert hasattr(step, 'single_filename_edit')
        
        # Set values
        step.single_filename_edit.setText("my_spritesheet")
        step.layout_mode_combo.setCurrentText("Square (Auto)")
        step.spacing_spin.setValue(4)
        step.padding_spin.setValue(8)
        
        # Get data
        data = step.get_data()
        assert data['single_filename'] == "my_spritesheet"
        assert data['layout_mode'] == "auto"
        assert data['spacing'] == 4
        assert data['padding'] == 8


class TestSpriteSheetPreviewReal:
    """Test sprite sheet preview with real rendering."""
    
    def test_preview_zoom_real_interaction(self, qtbot):
        """Test real zoom interaction with mouse wheel."""
        view = SpriteSheetPreviewView()
        qtbot.addWidget(view)
        view.resize(400, 300)
        view.show()
        
        # Add content
        pixmap = QPixmap(200, 200)
        pixmap.fill(Qt.blue)
        view.scene.addPixmap(pixmap)
        
        initial_zoom = view._zoom_level
        
        # Create real wheel event for zoom in
        wheel_event = QWheelEvent(
            QPointF(200, 150),  # position in widget
            QPointF(200, 150),  # global position
            QPointF(0, 0),      # pixel delta
            QPointF(0, 120),    # angle delta (positive = zoom in)
            Qt.NoButton,
            Qt.ControlModifier,  # Ctrl for zoom
            Qt.ScrollBegin,
            False
        )
        
        # Send wheel event
        view.wheelEvent(wheel_event)
        
        # Verify zoom changed
        assert view._zoom_level > initial_zoom
        
        # Test zoom out
        wheel_event_out = QWheelEvent(
            QPointF(200, 150),
            QPointF(200, 150),
            QPointF(0, 0),
            QPointF(0, -120),   # negative = zoom out
            Qt.NoButton,
            Qt.ControlModifier,
            Qt.ScrollBegin,
            False
        )
        
        view.wheelEvent(wheel_event_out)
        assert view._zoom_level == initial_zoom
    
    def test_preview_generation_with_real_sprites(self, qtbot):
        """Test preview generation with real sprite data."""
        # Create real sprites
        sprites = []
        for i in range(9):
            pixmap = QPixmap(32, 32)
            color = QColor.fromHsv(i * 40, 255, 200)
            pixmap.fill(color)
            sprites.append(pixmap)
        
        # Create preview step
        step = ExportPreviewStep(sprites=sprites)
        qtbot.addWidget(step)
        step.show()
        
        # Set up for sprite sheet
        step._current_preset = EnhancedExportPreset(
            name="sprite_sheet",
            display_name="Sprite Sheet",
            icon="📋",
            description="Sprite sheet",
            mode="sheet",
            format="PNG",
            scale=1.0,
            default_pattern="{name}",
            tooltip="",
            use_cases=[],
            short_description="",
            recommended_for=[]
        )
        
        step._export_settings = {
            'layout_mode': 'auto',
            'spacing': 2,
            'padding': 4
        }
        
        # Generate preview
        step._generate_sprite_sheet_preview()
        
        # Verify preview was created
        assert step.preview_view is not None
        items = step.preview_view.scene.items()
        assert len(items) > 0
        
        # The scene should contain the sprite sheet preview
        pixmap_items = [item for item in items if hasattr(item, 'pixmap')]
        assert len(pixmap_items) > 0


class TestWizardIntegrationReal:
    """Test wizard widget integration with real steps."""
    
    def test_wizard_with_real_steps(self, qtbot):
        """Test wizard with real step navigation."""
        wizard = WizardWidget()
        qtbot.addWidget(wizard)
        wizard.show()
        
        # Create real steps
        step1 = WizardStep("Step 1", "First step")
        step2 = WizardStep("Step 2", "Second step")
        step3 = WizardStep("Step 3", "Final step")
        
        # Track step changes
        step_changes = []
        wizard.currentStepChanged.connect(lambda idx: step_changes.append(idx))
        
        # Add steps
        wizard.add_step(step1)
        wizard.add_step(step2)
        wizard.add_step(step3)
        
        # Initial state
        assert wizard.current_step_index == 0
        assert wizard.step_title_label.text() == "Step 1"
        assert wizard.back_button.isEnabled() is False
        assert wizard.next_button.isEnabled() is True
        assert wizard.next_button.text() == "Next →"
        
        # Navigate forward
        qtbot.mouseClick(wizard.next_button, Qt.LeftButton)
        assert wizard.current_step_index == 1
        assert wizard.step_title_label.text() == "Step 2"
        assert wizard.back_button.isEnabled() is True
        assert step_changes == [1]
        
        # Navigate to last step
        qtbot.mouseClick(wizard.next_button, Qt.LeftButton)
        assert wizard.current_step_index == 2
        assert wizard.step_title_label.text() == "Step 3"
        assert wizard.next_button.text() == "Finish"
        assert step_changes == [1, 2]
        
        # Navigate back
        qtbot.mouseClick(wizard.back_button, Qt.LeftButton)
        assert wizard.current_step_index == 1
        assert step_changes == [1, 2, 1]
        
        # Test finish
        finished_data = None
        wizard.wizardFinished.connect(lambda data: setattr(locals(), 'finished_data', data))
        
        # Set some data
        step1._step_data = {'key1': 'value1'}
        step2._step_data = {'key2': 'value2'}
        step3._step_data = {'key3': 'value3'}
        
        # Navigate to end and finish
        wizard.set_current_step(2)
        qtbot.mouseClick(wizard.next_button, Qt.LeftButton)
        
        # Wizard should have emitted finished signal
        # (Note: signal handling in test might need processEvents)
        QApplication.processEvents()


class TestRealFileExport:
    """Test with real file export operations."""
    
    @pytest.mark.integration
    def test_export_type_step_real_presets(self, qtbot):
        """Test export type step with real preset data."""
        step = ExportTypeStep(frame_count=16)
        qtbot.addWidget(step)
        step.show()
        
        # Should have real preset cards
        assert len(step._cards) > 0
        
        # Find individual frames preset
        individual_card = None
        for card in step._cards:
            if card.preset.name == "individual_frames":
                individual_card = card
                break
        
        assert individual_card is not None
        
        # Click the card
        clicked_presets = []
        step.presetSelected.connect(lambda p: clicked_presets.append(p))
        
        qtbot.mouseClick(individual_card, Qt.LeftButton)
        
        # Verify selection
        assert step._selected_preset.name == "individual_frames"
        assert len(clicked_presets) == 1
        assert step.validate() is True
        
        # Get data
        data = step.get_data()
        assert data['preset'].name == "individual_frames"
        assert data['export_mode'] == "individual"