"""
Integration tests for the integrated export dialog workflow
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtTest import QTest

from export.export_dialog_wizard_integrated import ExportDialogWizardIntegrated
from export.export_presets import get_preset_manager


class TestIntegratedExportWorkflow:
    """Test the complete integrated export workflow."""
    
    @pytest.fixture
    def test_sprites(self):
        """Create test sprite pixmaps."""
        sprites = []
        for i in range(12):
            pixmap = QPixmap(48, 48)
            color = QColor.fromHsv((i * 30) % 360, 200, 200)
            pixmap.fill(color)
            sprites.append(pixmap)
        return sprites
    
    @pytest.fixture
    def export_dialog(self, test_sprites):
        """Create export dialog with test data."""
        dialog = ExportDialogWizardIntegrated(
            frame_count=len(test_sprites),
            current_frame=3,
            sprites=test_sprites
        )
        return dialog
    
    @pytest.mark.integration
    def test_dialog_creation(self, qtbot, export_dialog):
        """Test dialog is created properly."""
        qtbot.addWidget(export_dialog)
        
        # Check dialog properties
        assert export_dialog.windowTitle() == "Export Sprites"
        assert export_dialog.isModal()
        
        # Check wizard steps
        assert len(export_dialog.wizard.steps) == 2
        assert export_dialog.type_step is not None
        assert export_dialog.settings_preview_step is not None
    
    @pytest.mark.integration
    def test_type_to_settings_navigation(self, qtbot, export_dialog):
        """Test navigating from type selection to settings."""
        qtbot.addWidget(export_dialog)
        
        # Select sprite sheet type
        preset_manager = get_preset_manager()
        sheet_preset = preset_manager.get_preset("sprite_sheet")
        export_dialog.type_step._select_preset(sheet_preset)
        
        # Navigate to settings
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        # Check we're on settings step
        assert export_dialog.wizard.current_step_index == 1
        
        # Check settings were created for sprite sheet
        settings_step = export_dialog.settings_preview_step
        assert 'grid_layout' in settings_step._settings_widgets
        assert 'spacing' in settings_step._settings_widgets
    
    @pytest.mark.integration  
    def test_live_preview_updates(self, qtbot, export_dialog):
        """Test that preview updates when settings change."""
        qtbot.addWidget(export_dialog)
        
        # Navigate to sprite sheet settings
        preset_manager = get_preset_manager()
        sheet_preset = preset_manager.get_preset("sprite_sheet")
        export_dialog.type_step._select_preset(sheet_preset)
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_preview_step
        
        # Mock preview update
        settings_step._update_preview = Mock()
        
        # Change spacing
        settings_step._settings_widgets['spacing'].setValue(4)
        
        # Wait for debounced update
        qtbot.wait(200)
        
        # Preview should have updated
        assert settings_step._update_preview.called
    
    @pytest.mark.integration
    def test_export_button_triggers_wizard_finish(self, qtbot, export_dialog):
        """Test export button completes wizard."""
        qtbot.addWidget(export_dialog)
        
        # Navigate to settings
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(preset_manager.get_preset("individual_frames"))
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        # Set valid directory
        export_dialog.settings_preview_step._settings_widgets['directory'].set_directory("/tmp")
        
        # Mock wizard finish
        export_dialog.wizard._on_finish = Mock()
        
        # Click export button
        qtbot.mouseClick(export_dialog.settings_preview_step.export_button, Qt.LeftButton)
        
        # Should trigger wizard finish
        assert export_dialog.wizard._on_finish.called
    
    @pytest.mark.integration
    def test_individual_frames_workflow(self, qtbot, export_dialog):
        """Test complete workflow for individual frames."""
        qtbot.addWidget(export_dialog)
        
        # Select individual frames
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(preset_manager.get_preset("individual_frames"))
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_preview_step
        
        # Configure settings
        settings_step._settings_widgets['directory'].set_directory("/tmp/export")
        settings_step._settings_widgets['base_name'].setText("sprite")
        settings_step._settings_widgets['format'].setCurrentText("PNG")
        settings_step._settings_widgets['scale'].set_scale(2.0)
        
        # Check preview updated
        qtbot.wait(200)  # Wait for debounce
        
        # Verify preview info
        assert "Individual Frames" in settings_step.preview_info_label.text()
        assert "12 files" in settings_step.preview_info_label.text()
        
        # Check data collection
        data = settings_step.get_data()
        assert data['output_dir'] == "/tmp/export"
        assert data['base_name'] == "sprite"
        assert data['format'] == "PNG"
        assert data['scale'] == 2.0
    
    @pytest.mark.integration
    def test_sprite_sheet_workflow(self, qtbot, export_dialog):
        """Test complete workflow for sprite sheet."""
        qtbot.addWidget(export_dialog)
        
        # Select sprite sheet
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(preset_manager.get_preset("sprite_sheet"))
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_preview_step
        
        # Configure settings
        settings_step._settings_widgets['directory'].set_directory("/tmp/sheets")
        settings_step._settings_widgets['single_filename'].setText("atlas")
        settings_step._settings_widgets['spacing'].setValue(2)
        
        # Change layout mode
        grid_layout = settings_step._settings_widgets['grid_layout']
        columns_btn = grid_layout.mode_group.button(1)  # Columns mode
        qtbot.mouseClick(columns_btn, Qt.LeftButton)
        
        # Wait for preview update
        qtbot.wait(200)
        
        # Check preview shows grid info
        assert "grid" in settings_step.preview_info_label.text()
        assert "Sprite Sheet" in settings_step.preview_info_label.text()
        
        # Verify data
        data = settings_step.get_data()
        assert data['output_dir'] == "/tmp/sheets"
        assert data['single_filename'] == "atlas"
        assert data['spacing'] == 2
        assert data['layout_mode'] == "columns"
    
    @pytest.mark.integration
    def test_selected_frames_workflow(self, qtbot, export_dialog):
        """Test workflow for selected frames export."""
        qtbot.addWidget(export_dialog)
        
        # Select selected frames preset
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(preset_manager.get_preset("selected_frames"))
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_preview_step
        
        # Select specific frames
        frame_list = settings_step._settings_widgets['frame_list']
        frame_list.clearSelection()
        frame_list.item(1).setSelected(True)
        frame_list.item(3).setSelected(True)
        frame_list.item(5).setSelected(True)
        frame_list.item(7).setSelected(True)
        
        # Wait for preview
        qtbot.wait(200)
        
        # Check selection info
        assert "4 frames selected" in settings_step.selection_info.text()
        assert "Selected Frames: 4 of 12" in settings_step.preview_info_label.text()
        
        # Verify data
        data = settings_step.get_data()
        assert sorted(data['selected_indices']) == [1, 3, 5, 7]
    
    @pytest.mark.integration
    def test_format_change_updates_preview(self, qtbot, export_dialog):
        """Test changing format updates preview info."""
        qtbot.addWidget(export_dialog)
        
        # Navigate to settings
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(preset_manager.get_preset("sprite_sheet"))
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_preview_step
        
        # Change format
        settings_step._settings_widgets['format'].setCurrentText("JPG")
        qtbot.wait(200)
        
        # Check preview stats updated
        assert "JPG" in settings_step.preview_stats_label.text()
    
    @pytest.mark.integration
    def test_preview_zoom_controls(self, qtbot, export_dialog):
        """Test preview zoom functionality."""
        qtbot.addWidget(export_dialog)
        
        # Navigate to settings with content
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(preset_manager.get_preset("sprite_sheet"))
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_preview_step
        
        # Let preview generate
        qtbot.wait(200)
        
        # Test fit button (smoke test - just ensure no crashes)
        settings_step._fit_preview()
        
        # Test 100% button
        settings_step._reset_zoom()
        
        # Verify preview view exists and has content
        assert settings_step.preview_view.scene.items()
    
    @pytest.mark.integration
    def test_validation_prevents_export(self, qtbot, export_dialog):
        """Test validation prevents export with invalid settings."""
        qtbot.addWidget(export_dialog)
        
        # Navigate to settings
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(preset_manager.get_preset("individual_frames"))
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_preview_step
        
        # Clear directory to make invalid
        settings_step._settings_widgets['directory'].set_directory("")
        
        # Export button should be disabled
        assert not settings_step.export_button.isEnabled()
        
        # Set valid directory
        settings_step._settings_widgets['directory'].set_directory("/tmp")
        
        # Export button should be enabled
        assert settings_step.export_button.isEnabled()
    
    @pytest.mark.integration
    def test_export_summary_updates(self, qtbot, export_dialog):
        """Test export summary label updates."""
        qtbot.addWidget(export_dialog)
        
        # Navigate to settings
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(preset_manager.get_preset("individual_frames"))
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        settings_step = export_dialog.settings_preview_step
        
        # Initially should have default directory
        initial_text = settings_step.export_summary_label.text()
        assert "Export to:" in initial_text
        
        # Clear directory to test empty state
        settings_step._settings_widgets['directory'].set_directory("")
        qtbot.wait(200)
        assert "Select output directory" in settings_step.export_summary_label.text()
        
        # Set directory
        settings_step._settings_widgets['directory'].set_directory("/home/user/exports")
        qtbot.wait(200)
        
        # Should show directory name
        assert "exports/" in settings_step.export_summary_label.text()
    
    @pytest.mark.integration
    @patch('export.frame_exporter.get_frame_exporter')
    def test_export_completion_flow(self, mock_get_exporter, qtbot, export_dialog):
        """Test the export completion flow."""
        qtbot.addWidget(export_dialog)
        
        # Mock exporter
        mock_exporter = Mock()
        mock_get_exporter.return_value = mock_exporter
        
        # Navigate through wizard
        preset_manager = get_preset_manager()
        export_dialog.type_step._select_preset(preset_manager.get_preset("individual_frames"))
        qtbot.mouseClick(export_dialog.wizard.next_button, Qt.LeftButton)
        qtbot.wait(100)
        
        # Configure settings
        export_dialog.settings_preview_step._settings_widgets['directory'].set_directory("/tmp")
        
        # Track completion signal
        completed = []
        export_dialog.exportCompleted.connect(lambda path: completed.append(path))
        
        # Trigger export through wizard finish
        export_dialog._on_wizard_finished({
            'step_0': {'preset': preset_manager.get_preset("individual_frames")},
            'step_1': export_dialog.settings_preview_step.get_data()
        })
        
        # Verify exporter was called
        assert mock_exporter.export_individual_frames.called