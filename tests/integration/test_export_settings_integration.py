"""
Integration tests for simplified export settings
Tests the complete workflow with real components.
"""

import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication, QListWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor

from export.export_dialog_wizard import ExportDialogWizard
from export.export_settings_step_simple import ExportSettingsStepSimple
from export.export_presets import get_preset_manager


class TestExportSettingsIntegration:
    """Integration tests for export settings workflow."""
    
    @pytest.fixture
    def test_sprites(self):
        """Create test sprite pixmaps."""
        sprites = []
        for i in range(8):
            pixmap = QPixmap(32, 32)
            color = QColor.fromHsv((i * 45) % 360, 200, 200)
            pixmap.fill(color)
            sprites.append(pixmap)
        return sprites
    
    @pytest.fixture
    def export_dialog(self, test_sprites):
        """Create export dialog with test data."""
        dialog = ExportDialogWizard(
            frame_count=len(test_sprites),
            current_frame=2,
            sprites=test_sprites
        )
        return dialog
    
    @pytest.mark.integration
    def test_individual_frames_workflow(self, qtbot, export_dialog):
        """Test complete workflow for individual frames export."""
        qtbot.addWidget(export_dialog)
        
        # Step 1: Select individual frames preset
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(
            preset_manager.get_preset("individual_frames")
        )
        
        # Should enable next button
        assert export_dialog.wizard.next_button.isEnabled()
        
        # Go to settings step
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        # Step 2: Configure settings
        settings_step = export_dialog.settings_step
        assert isinstance(settings_step, ExportSettingsStepSimple)
        
        # Check that appropriate UI was created
        assert 'directory' in settings_step._settings_widgets
        assert 'base_name' in settings_step._settings_widgets
        assert 'format' in settings_step._settings_widgets
        assert 'scale' in settings_step._settings_widgets
        assert 'pattern_combo' in settings_step._settings_widgets
        
        # Set valid values
        settings_step._settings_widgets['directory'].set_directory("/tmp")
        settings_step._settings_widgets['base_name'].setText("test_frame")
        
        # Should be valid now
        assert settings_step.validate()
        assert export_dialog.wizard.next_button.isEnabled()
        
        # Get data
        data = settings_step.get_data()
        assert data['output_dir'] == "/tmp"
        assert data['base_name'] == "test_frame"
        assert data['format'] == "PNG"
        assert data['scale'] == 1.0
        assert data['pattern'] == "{name}_{index:03d}"
    
    @pytest.mark.integration
    def test_sprite_sheet_workflow(self, qtbot, export_dialog):
        """Test complete workflow for sprite sheet export."""
        qtbot.addWidget(export_dialog)
        
        # Step 1: Select sprite sheet preset
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(
            preset_manager.get_preset("sprite_sheet")
        )
        
        # Go to settings step
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        # Step 2: Configure sprite sheet settings
        settings_step = export_dialog.settings_step
        
        # Check sprite sheet specific UI
        assert 'single_filename' in settings_step._settings_widgets
        assert 'grid_layout' in settings_step._settings_widgets
        assert 'spacing' in settings_step._settings_widgets
        assert 'background' in settings_step._settings_widgets
        
        # Configure settings
        settings_step._settings_widgets['directory'].set_directory("/tmp")
        settings_step._settings_widgets['single_filename'].setText("my_sprites")
        settings_step._settings_widgets['spacing'].setValue(2)
        
        # Test grid layout selector
        grid_selector = settings_step._settings_widgets['grid_layout']
        mode, cols, rows = grid_selector.get_layout()
        assert mode == "auto"
        
        # Change to columns mode
        columns_btn = grid_selector.mode_group.button(1)
        qtbot.mouseClick(columns_btn, Qt.LeftButton)
        
        mode, cols, rows = grid_selector.get_layout()
        assert mode == "columns"
        
        # Get final data
        data = settings_step.get_data()
        assert data['output_dir'] == "/tmp"
        assert data['single_filename'] == "my_sprites"
        assert data['layout_mode'] == "columns"
        assert data['columns'] == 8
        assert data['spacing'] == 2
        assert data['padding'] == 0
        assert data['background_mode'] == 'transparent'
    
    @pytest.mark.integration
    def test_selected_frames_workflow(self, qtbot, export_dialog):
        """Test complete workflow for selected frames export."""
        qtbot.addWidget(export_dialog)
        
        # Step 1: Select selected frames preset
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(
            preset_manager.get_preset("selected_frames")
        )
        
        # Go to settings step
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        # Step 2: Configure selected frames
        settings_step = export_dialog.settings_step
        
        # Check frame selection UI exists
        assert 'frame_list' in settings_step._settings_widgets
        frame_list = settings_step._settings_widgets['frame_list']
        assert isinstance(frame_list, QListWidget)
        assert frame_list.count() == 8  # Number of test sprites
        
        # Current frame should be selected by default
        selected_items = frame_list.selectedItems()
        assert len(selected_items) == 1
        assert selected_items[0].data(Qt.UserRole) == 2  # current_frame
        
        # Select additional frames
        item_1 = frame_list.item(1)
        item_3 = frame_list.item(3)
        item_1.setSelected(True)
        item_3.setSelected(True)
        
        # Check selection
        selected_indices = []
        for item in frame_list.selectedItems():
            selected_indices.append(item.data(Qt.UserRole))
        assert sorted(selected_indices) == [1, 2, 3]
        
        # Validate settings
        settings_step._settings_widgets['directory'].set_directory("/tmp")
        assert settings_step.validate()
        
        # Get data
        data = settings_step.get_data()
        assert sorted(data['selected_indices']) == [1, 2, 3]
    
    @pytest.mark.integration
    def test_format_quality_interaction(self, qtbot, export_dialog):
        """Test format and quality slider interaction."""
        qtbot.addWidget(export_dialog)
        
        # Select individual frames and go to settings
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(
            preset_manager.get_preset("individual_frames")
        )
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_step
        
        # Quality should be hidden for PNG
        format_combo = settings_step._settings_widgets['format']
        quality_spin = settings_step._settings_widgets['quality']
        
        assert format_combo.currentText() == "PNG"
        
        # Change to JPG
        format_combo.setCurrentText("JPG")
        
        # Verify in data - quality should be included for JPG
        data = settings_step.get_data()
        assert data['format'] == "JPG"
        assert 'quality' in data
        assert data['quality'] == 95  # Default value
        
        # Change back to PNG
        format_combo.setCurrentText("PNG")
        
        # Quality should not affect PNG export
        data = settings_step.get_data()
        assert data['format'] == "PNG"
        # Data-based test rather than visibility test
    
    @pytest.mark.integration
    def test_scale_buttons(self, qtbot, export_dialog):
        """Test quick scale button functionality."""
        qtbot.addWidget(export_dialog)
        
        # Navigate to settings
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(
            preset_manager.get_preset("individual_frames")
        )
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_step
        scale_buttons = settings_step._settings_widgets['scale']
        
        # Default should be 1.0
        assert scale_buttons.get_scale() == 1.0
        
        # Click 2x button
        for btn in scale_buttons.button_group.buttons():
            if btn.text() == "2.0x":
                qtbot.mouseClick(btn, Qt.LeftButton)
                break
        
        assert scale_buttons.get_scale() == 2.0
        
        # Verify in data
        data = settings_step.get_data()
        assert data['scale'] == 2.0
    
    @pytest.mark.integration
    def test_validation_flow(self, qtbot, export_dialog):
        """Test validation enables/disables next button."""
        qtbot.addWidget(export_dialog)
        
        # Select preset and go to settings
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(
            preset_manager.get_preset("individual_frames")
        )
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_step
        
        # Clear directory - should invalidate
        settings_step._settings_widgets['directory'].set_directory("")
        assert not settings_step.validate()
        assert not export_dialog.wizard.next_button.isEnabled()
        
        # Set valid directory
        settings_step._settings_widgets['directory'].set_directory("/tmp")
        assert settings_step.validate()
        assert export_dialog.wizard.next_button.isEnabled()
        
        # Clear base name - should invalidate
        settings_step._settings_widgets['base_name'].setText("")
        assert not settings_step.validate()
        assert not export_dialog.wizard.next_button.isEnabled()
        
        # Restore base name
        settings_step._settings_widgets['base_name'].setText("test")
        assert settings_step.validate()
        assert export_dialog.wizard.next_button.isEnabled()
    
    @pytest.mark.integration
    def test_background_options(self, qtbot, export_dialog):
        """Test sprite sheet background options."""
        qtbot.addWidget(export_dialog)
        
        # Select sprite sheet preset
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(
            preset_manager.get_preset("sprite_sheet")
        )
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_step
        bg_combo = settings_step._settings_widgets['background']
        
        # Test different background modes
        bg_options = ["Transparent", "White", "Black", "Custom Color"]
        expected_modes = [
            ('transparent', None),
            ('solid', (255, 255, 255, 255)),
            ('solid', (0, 0, 0, 255)),
            ('solid', (128, 128, 128, 255))  # Default gray for custom
        ]
        
        for i, (option, (expected_mode, expected_color)) in enumerate(zip(bg_options, expected_modes)):
            bg_combo.setCurrentIndex(i)
            data = settings_step.get_data()
            assert data['background_mode'] == expected_mode
            if expected_color:
                assert data.get('background_color') == expected_color
    
    @pytest.mark.integration  
    def test_preset_data_preservation(self, qtbot, export_dialog):
        """Test that settings are preserved when navigating back."""
        qtbot.addWidget(export_dialog)
        
        # Configure settings for individual frames
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(
            preset_manager.get_preset("individual_frames")
        )
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_step
        
        # Set custom values
        settings_step._settings_widgets['directory'].set_directory("/custom/path")
        settings_step._settings_widgets['base_name'].setText("my_sprites")
        settings_step._settings_widgets['format'].setCurrentText("BMP")
        
        # Get initial data
        initial_data = settings_step.get_data()
        
        # Go to next step then back
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        qtbot.mouseClick(export_dialog.wizard.back_button, Qt.LeftButton)
        qtbot.wait(100)
        
        # Data should be preserved
        preserved_data = settings_step.get_data()
        assert preserved_data['output_dir'] == initial_data['output_dir']
        assert preserved_data['base_name'] == initial_data['base_name']
        assert preserved_data['format'] == initial_data['format']