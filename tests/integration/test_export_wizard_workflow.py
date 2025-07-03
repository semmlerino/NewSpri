"""
Integration Tests for Export Wizard Workflow
Tests the complete export wizard workflow from start to finish.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor

from export import ExportDialog  # Should use wizard version
from export.core.frame_exporter import get_frame_exporter
from sprite_viewer import SpriteViewer
from sprite_model import SpriteModel


class TestExportWizardIntegration:
    """Test complete export wizard integration with the application."""
    
    @pytest.mark.integration
    def test_wizard_launches_from_sprite_viewer(self, qtbot):
        """Test wizard launches correctly from main application."""
        # Create sprite viewer
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Load test sprites
        model = viewer._sprite_model
        sprites = self._create_test_sprites(8)
        for sprite in sprites:
            model.sprite_frames.append(sprite)
        model.frameChanged.emit(0, len(sprites))
        
        # Trigger export action
        with patch('export.ExportDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog_class.return_value = mock_dialog
            mock_dialog.exec.return_value = True
            
            viewer._export_frames()
            
            # Check dialog was created with correct parameters
            mock_dialog_class.assert_called_once()
            call_args = mock_dialog_class.call_args[1]
            assert call_args['frame_count'] == 8
            assert 'sprites' in call_args
    
    @pytest.mark.integration
    def test_complete_individual_frames_export(self, qtbot, tmp_path):
        """Test complete workflow for individual frames export."""
        # Create dialog with test data
        sprites = self._create_test_sprites(4)
        dialog = ExportDialog(
            frame_count=len(sprites),
            current_frame=0
        )
        dialog.set_sprites(sprites)
        qtbot.addWidget(dialog)
        
        # Step 1: Select individual frames preset
        type_step = dialog.type_step
        individual_card = self._find_preset_card(type_step, "individual_frames")
        assert individual_card is not None
        
        qtbot.mouseClick(individual_card, Qt.LeftButton)
        
        # Navigate to settings
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Step 2: Configure settings
        settings_step = dialog.settings_step
        settings_step.directory_selector.set_directory(str(tmp_path))
        settings_step.base_name_edit.setText("test_sprite")
        
        # Navigate to preview
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Step 3: Export
        with patch.object(dialog, '_exporter') as mock_exporter:
            # Mock successful export
            mock_exporter.export_frames.return_value = True
            
            # Click export
            dialog.preview_step.export_now_button.click()
            
            # Verify export was called
            mock_exporter.export_frames.assert_called_once()
            call_args = mock_exporter.export_frames.call_args[1]
            
            assert call_args['sprites'] == sprites
            assert call_args['output_dir'] == str(tmp_path)
            assert call_args['base_name'] == "test_sprite"
            assert call_args['mode'] == "individual"
    
    @pytest.mark.integration
    def test_complete_sprite_sheet_export(self, qtbot, tmp_path):
        """Test complete workflow for sprite sheet export."""
        sprites = self._create_test_sprites(16)
        dialog = ExportDialog(
            frame_count=len(sprites),
            current_frame=0
        )
        dialog.set_sprites(sprites)
        qtbot.addWidget(dialog)
        
        # Select sprite sheet preset
        type_step = dialog.type_step
        sheet_card = self._find_preset_card(type_step, "sprite_sheet")
        qtbot.mouseClick(sheet_card, Qt.LeftButton)
        
        # Navigate to settings
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Configure sprite sheet settings
        settings_step = dialog.settings_step
        settings_step.directory_selector.set_directory(str(tmp_path))
        settings_step.single_filename_edit.setText("spritesheet")
        settings_step.layout_mode_combo.setCurrentText("Square")
        settings_step.spacing_spin.setValue(2)
        settings_step.padding_spin.setValue(4)
        
        # Navigate to preview
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Verify preview shows sprite sheet
        preview_step = dialog.preview_step
        assert "Sprite Sheet" in preview_step.preview_type_label.text()
        assert preview_step.preview_view.scene.items() != []
        
        # Mock export
        with patch.object(dialog._exporter, 'export_frames') as mock_export:
            mock_export.return_value = True
            
            # Export
            dialog.preview_step.export_now_button.click()
            
            # Verify sprite sheet layout was passed
            call_args = mock_export.call_args[1]
            assert 'sprite_sheet_layout' in call_args
            layout = call_args['sprite_sheet_layout']
            assert layout.mode == 'square'
            assert layout.spacing == 2
            assert layout.padding == 4
    
    @pytest.mark.integration
    def test_animated_gif_export_workflow(self, qtbot, tmp_path):
        """Test animated GIF export workflow."""
        sprites = self._create_test_sprites(8)
        dialog = ExportDialog(frame_count=len(sprites), current_frame=0)
        dialog.set_sprites(sprites)
        qtbot.addWidget(dialog)
        
        # Use quick export for GIF
        type_step = dialog.type_step
        gif_button = None
        for button in type_step.findChildren(QPushButton):
            if "GIF" in button.text():
                gif_button = button
                break
        
        assert gif_button is not None
        qtbot.mouseClick(gif_button, Qt.LeftButton)
        
        # Should auto-advance after quick selection
        QTimer.singleShot(400, lambda: None)  # Wait for auto-advance
        qtbot.wait(500)
        
        # Configure GIF settings
        if dialog.wizard.current_step_index == 1:
            settings_step = dialog.settings_step
            settings_step.directory_selector.set_directory(str(tmp_path))
            
            # Check GIF-specific settings exist
            assert hasattr(settings_step, 'fps_spin')
            assert hasattr(settings_step, 'loop_checkbox')
            
            settings_step.fps_spin.setValue(12)
            settings_step.loop_checkbox.setChecked(True)
            
            # Navigate to preview
            qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Verify GIF preview
        assert "Animated GIF" in dialog.preview_step.preview_type_label.text()
    
    @pytest.mark.integration
    def test_selected_frames_export_workflow(self, qtbot, tmp_path):
        """Test selected frames export with frame selection."""
        sprites = self._create_test_sprites(10)
        dialog = ExportDialog(
            frame_count=len(sprites),
            current_frame=2
        )
        dialog.set_sprites(sprites)
        qtbot.addWidget(dialog)
        
        # Select "selected frames" preset
        type_step = dialog.type_step
        selected_card = self._find_preset_card(type_step, "selected_frames")
        qtbot.mouseClick(selected_card, Qt.LeftButton)
        
        # Navigate to settings
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Select specific frames
        settings_step = dialog.settings_step
        settings_step.directory_selector.set_directory(str(tmp_path))
        
        # Select frames 0, 2, 4, 6
        frame_list = settings_step.frame_list
        frame_list.clearSelection()
        for i in [0, 2, 4, 6]:
            frame_list.item(i).setSelected(True)
        
        # Verify selection info updated
        assert "4 frames selected" in settings_step.selection_info_label.text()
        
        # Navigate to preview
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Verify preview shows selected frames
        assert "Selected Frames (4 of 10)" in dialog.preview_step.preview_type_label.text()
    
    @pytest.mark.integration
    def test_validation_prevents_invalid_export(self, qtbot):
        """Test validation prevents proceeding with invalid settings."""
        dialog = ExportDialog(frame_count=4, current_frame=0)
        qtbot.addWidget(dialog)
        
        # Try to proceed without selecting preset
        assert dialog.wizard.next_button.isEnabled() is False
        
        # Select preset
        type_step = dialog.type_step
        card = type_step._cards[0] if type_step._cards else None
        qtbot.mouseClick(card, Qt.LeftButton)
        
        # Now can proceed
        assert dialog.wizard.next_button.isEnabled() is True
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Clear directory to make invalid
        dialog.settings_step.directory_selector.set_directory("")
        
        # Cannot proceed with invalid directory
        assert dialog.wizard.next_button.isEnabled() is False
    
    @pytest.mark.integration
    def test_backward_navigation_preserves_settings(self, qtbot):
        """Test going back preserves user settings."""
        dialog = ExportDialog(frame_count=8, current_frame=0)
        qtbot.addWidget(dialog)
        
        # Configure first two steps
        type_step = dialog.type_step
        card = self._find_preset_card(type_step, "sprite_sheet")
        qtbot.mouseClick(card, Qt.LeftButton)
        
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Configure settings
        settings_step = dialog.settings_step
        settings_step.directory_selector.set_directory("/custom/path")
        settings_step.spacing_spin.setValue(8)
        settings_step.padding_spin.setValue(16)
        
        # Go to preview
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Go back to settings
        qtbot.mouseClick(dialog.wizard.back_button, Qt.LeftButton)
        
        # Settings should be preserved
        assert settings_step.directory_selector.get_directory() == "/custom/path"
        assert settings_step.spacing_spin.value() == 8
        assert settings_step.padding_spin.value() == 16
        
        # Go back to type selection
        qtbot.mouseClick(dialog.wizard.back_button, Qt.LeftButton)
        
        # Selection should be preserved
        assert type_step._selected_preset.name == "sprite_sheet"
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_large_sprite_count_performance(self, qtbot, benchmark):
        """Test wizard performance with large sprite counts."""
        # Create many sprites
        sprite_count = 200
        sprites = self._create_test_sprites(sprite_count)
        
        def create_and_navigate_wizard():
            dialog = ExportDialog(
                frame_count=sprite_count,
                current_frame=0
            )
            dialog.set_sprites(sprites)
            qtbot.addWidget(dialog)
            
            # Select preset
            card = dialog.type_step._cards[0]
            qtbot.mouseClick(card, Qt.LeftButton)
            
            # Navigate through all steps
            for _ in range(2):
                qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
            
            dialog.close()
        
        # Should handle 200 sprites efficiently
        result = benchmark(create_and_navigate_wizard)
        assert result.stats['mean'] < 1.0  # Under 1 second
    
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
    
    def _find_preset_card(self, type_step, preset_name):
        """Find a preset card by name."""
        for card in type_step._cards:
            if card.preset.name == preset_name:
                return card
        return None


class TestExportWizardErrorHandling:
    """Test error handling in the export wizard."""
    
    @pytest.mark.integration
    def test_export_failure_handling(self, qtbot):
        """Test handling of export failures."""
        dialog = ExportDialog(frame_count=4, current_frame=0)
        qtbot.addWidget(dialog)
        
        # Navigate to export
        self._navigate_to_export(dialog, qtbot)
        
        # Mock export failure
        with patch.object(dialog._exporter, 'exportError') as mock_error:
            # Simulate error
            error_message = "Permission denied: Cannot write to directory"
            dialog._on_export_error(error_message)
            
            # Check UI updated appropriately
            assert dialog.wizard.isEnabled() is True
            assert dialog.preview_step.export_now_button.isEnabled() is True
            assert dialog.preview_step.export_now_button.text() == "🚀 Export Now!"
    
    @pytest.mark.integration
    def test_directory_creation_handling(self, qtbot, tmp_path):
        """Test handling of directory creation."""
        dialog = ExportDialog(frame_count=4, current_frame=0)
        qtbot.addWidget(dialog)
        
        # Navigate to settings
        self._select_preset_and_continue(dialog, qtbot, "individual_frames")
        
        # Set non-existent directory
        new_dir = tmp_path / "new_export_dir"
        assert not new_dir.exists()
        
        dialog.settings_step.directory_selector.set_directory(str(new_dir))
        
        # Continue to export
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Mock directory creation
        with patch.object(dialog.settings_step.directory_selector, 
                         'create_directory_if_needed') as mock_create:
            mock_create.return_value = (True, "Created successfully")
            
            # Attempt export
            with patch.object(dialog._exporter, 'export_frames'):
                dialog._on_export_now()
                
                # Directory creation should be attempted
                mock_create.assert_called()
    
    @pytest.mark.integration  
    def test_file_overwrite_confirmation(self, qtbot, tmp_path):
        """Test file overwrite confirmation dialog."""
        # Create existing file
        existing_file = tmp_path / "sprite_000.png"
        existing_file.write_text("existing")
        
        dialog = ExportDialog(frame_count=4, current_frame=0)
        qtbot.addWidget(dialog)
        
        # Configure to overwrite
        self._select_preset_and_continue(dialog, qtbot, "individual_frames")
        dialog.settings_step.directory_selector.set_directory(str(tmp_path))
        dialog.settings_step.base_name_edit.setText("sprite")
        
        # Continue to export
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
        
        # Mock overwrite check
        with patch.object(dialog, '_check_file_overwrite_risk', return_value=True):
            with patch('PySide6.QtWidgets.QMessageBox.question') as mock_question:
                mock_question.return_value = QApplication.DialogCode.Yes
                
                dialog._on_export_now()
                
                # Overwrite confirmation should be shown
                mock_question.assert_called_once()
                assert "overwrite" in mock_question.call_args[0][2].lower()
    
    # Helper methods
    def _navigate_to_export(self, dialog, qtbot):
        """Navigate through wizard to export step."""
        # Select first preset
        card = dialog.type_step._cards[0]
        qtbot.mouseClick(card, Qt.LeftButton)
        
        # Navigate through steps
        for _ in range(2):
            qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)
    
    def _select_preset_and_continue(self, dialog, qtbot, preset_name):
        """Select a preset and continue to next step."""
        type_step = dialog.type_step
        for card in type_step._cards:
            if card.preset.name == preset_name:
                qtbot.mouseClick(card, Qt.LeftButton)
                break
        
        qtbot.mouseClick(dialog.wizard.next_button, Qt.LeftButton)


# Test fixtures
@pytest.fixture
def mock_sprite_viewer(qtbot):
    """Create a mock sprite viewer with test data."""
    viewer = SpriteViewer()
    qtbot.addWidget(viewer)
    
    # Add test sprites
    for i in range(16):
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor.fromHsv(i * 22, 200, 200))
        viewer._sprite_model.sprite_frames.append(pixmap)
    
    return viewer