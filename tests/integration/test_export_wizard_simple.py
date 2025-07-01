"""
Simple Integration Tests for Export Wizard
Tests wizard functionality without complex threading/export operations.
"""

import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor

from export.export_dialog_wizard import ExportDialogWizard
from config import Config


class TestExportWizardSimple:
    """Simple integration tests for export wizard."""
    
    @pytest.mark.integration
    def test_wizard_navigation_flow(self, qtbot):
        """Test basic wizard navigation flow."""
        # Create dialog with test data
        dialog = ExportDialogWizard(frame_count=8)
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Step 1: Type selection
        assert dialog.wizard.current_step_index == 0
        assert not dialog.wizard.next_button.isEnabled()  # No selection yet
        
        # Select individual frames preset
        type_step = dialog.type_step
        card = None
        for c in type_step._cards:
            if c.preset.name == "individual_frames":
                card = c
                break
        
        assert card is not None
        qtbot.mouseClick(card, Qt.LeftButton)
        
        # Should be able to proceed now
        assert dialog.wizard.next_button.isEnabled()
        
        # Go to settings
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Step 2: Settings
        assert dialog.wizard.current_step_index == 1
        assert dialog.wizard.back_button.isEnabled()
        
        # Wait for UI setup
        QApplication.processEvents()
        qtbot.wait(50)
        
        # Should have directory selector after setup
        settings_step = dialog.settings_step
        assert hasattr(settings_step, 'directory_selector')
        
        # Directory should have default value, so should be valid
        # Just verify we can set a directory
        settings_step.directory_selector.set_directory("/tmp")
        
        # Should be able to proceed
        assert dialog.wizard.next_button.isEnabled()
        
        # Go to preview
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Step 3: Preview
        assert dialog.wizard.current_step_index == 2
        assert dialog.wizard.next_button.text() == "Finish"
        
        # Check export button exists
        preview_step = dialog.preview_step
        assert preview_step.export_now_button is not None
        assert preview_step.export_now_button.isEnabled()
        
        # Test back navigation
        qtbot.mouseClick(dialog.wizard.back_button, Qt.LeftButton)
        assert dialog.wizard.current_step_index == 1
        
        qtbot.mouseClick(dialog.wizard.back_button, Qt.LeftButton)
        assert dialog.wizard.current_step_index == 0
        
        # Selection should be preserved
        assert type_step._selected_preset.name == "individual_frames"
        
        dialog.close()
    
    @pytest.mark.integration
    def test_export_settings_validation(self, qtbot, tmp_path):
        """Test export settings validation."""
        sprites = self._create_test_sprites(4)
        dialog = ExportDialogWizard(
            frame_count=len(sprites),
            sprites=sprites
        )
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Navigate to settings quickly
        type_step = dialog.type_step
        card = type_step._cards[0]  # Any card
        qtbot.mouseClick(card, Qt.LeftButton)
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Wait for UI
        QApplication.processEvents()
        qtbot.wait(50)
        
        settings_step = dialog.settings_step
        
        # Test with valid directory
        settings_step.directory_selector.set_directory(str(tmp_path))
        assert settings_step.validate()
        
        # Test we can set filenames
        if hasattr(settings_step, 'base_name_edit'):
            settings_step.base_name_edit.setText("test")
            assert settings_step.validate()
        
        dialog.close()
    
    @pytest.mark.integration
    def test_export_request_signal(self, qtbot, tmp_path):
        """Test that export request signal is emitted with correct data."""
        sprites = self._create_test_sprites(2)
        dialog = ExportDialogWizard(
            frame_count=len(sprites),
            sprites=sprites
        )
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Navigate through wizard
        type_step = dialog.type_step
        for card in type_step._cards:
            if card.preset.name == "individual_frames":
                qtbot.mouseClick(card, Qt.LeftButton)
                break
        
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        QApplication.processEvents()
        qtbot.wait(50)
        
        # Configure settings
        settings_step = dialog.settings_step
        settings_step.directory_selector.set_directory(str(tmp_path))
        settings_step.base_name_edit.setText("test_sprite")
        
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        QApplication.processEvents()
        qtbot.wait(50)
        
        # Track export request
        export_requested = False
        export_settings = None
        
        def on_export_requested(settings):
            nonlocal export_requested, export_settings
            export_requested = True
            export_settings = settings
        
        dialog.exportRequested.connect(on_export_requested)
        
        # Click export
        dialog.preview_step.export_now_button.click()
        
        # Should emit signal immediately
        assert export_requested
        assert export_settings is not None
        assert export_settings['output_dir'] == str(tmp_path)
        assert export_settings['base_name'] == "test_sprite"
        assert export_settings['mode'] == "individual"
        
        dialog.close()
    
    @pytest.mark.integration
    def test_sprite_sheet_settings(self, qtbot):
        """Test sprite sheet specific settings."""
        dialog = ExportDialogWizard(frame_count=16)
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Select sprite sheet
        type_step = dialog.type_step
        for card in type_step._cards:
            if card.preset.name == "sprite_sheet":
                qtbot.mouseClick(card, Qt.LeftButton)
                break
        
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        QApplication.processEvents()
        qtbot.wait(50)
        
        settings_step = dialog.settings_step
        
        # Should have sprite sheet specific controls
        assert hasattr(settings_step, 'layout_mode_combo')
        assert hasattr(settings_step, 'spacing_spin')
        assert hasattr(settings_step, 'padding_spin')
        
        # Test setting values
        settings_step.spacing_spin.setValue(4)
        settings_step.padding_spin.setValue(8)
        
        # Get data
        data = settings_step.get_data()
        assert data['spacing'] == 4
        assert data['padding'] == 8
        
        dialog.close()
    
    @pytest.mark.integration
    def test_selected_frames_mode(self, qtbot):
        """Test selected frames export mode."""
        dialog = ExportDialogWizard(frame_count=10, current_frame=3)
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Select "selected frames" preset
        type_step = dialog.type_step
        for card in type_step._cards:
            if card.preset.name == "selected_frames":
                qtbot.mouseClick(card, Qt.LeftButton)
                break
        
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        QApplication.processEvents()
        qtbot.wait(50)
        
        settings_step = dialog.settings_step
        
        # Should have frame list
        assert hasattr(settings_step, 'frame_list')
        assert settings_step.frame_list.count() == 10
        
        # Select some frames
        settings_step.frame_list.clearSelection()
        settings_step.frame_list.item(1).setSelected(True)
        settings_step.frame_list.item(3).setSelected(True)
        settings_step.frame_list.item(5).setSelected(True)
        
        # Get data
        data = settings_step.get_data()
        assert data['selected_indices'] == [1, 3, 5]
        
        dialog.close()
    
    @pytest.mark.integration
    def test_quick_export_buttons(self, qtbot):
        """Test quick export buttons in type selection."""
        dialog = ExportDialogWizard(frame_count=8)
        qtbot.addWidget(dialog)
        dialog.show()
        
        type_step = dialog.type_step
        
        # Find quick export buttons
        quick_buttons = []
        for button in type_step.findChildren(QPushButton):
            if "Quick Export" in button.text():
                quick_buttons.append(button)
        
        # Should have at least one quick export button
        assert len(quick_buttons) > 0
        
        # Click a quick export button
        if quick_buttons:
            qtbot.mouseClick(quick_buttons[0], Qt.LeftButton)
            
            # Should auto-advance after delay
            qtbot.wait(600)  # Wait for auto-advance timer
            
            # Should have moved to next step
            assert dialog.wizard.current_step_index > 0
        
        dialog.close()
    
    # Helper methods
    def _create_test_sprites(self, count):
        """Create test sprite pixmaps."""
        sprites = []
        for i in range(count):
            pixmap = QPixmap(32, 32)
            color = QColor.fromHsv(int(i * 360 / count), 200, 200)
            pixmap.fill(color)
            sprites.append(pixmap)
        return sprites