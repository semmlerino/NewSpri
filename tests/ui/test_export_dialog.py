"""
UI tests for ExportDialog.
Tests the export dialog functionality and user interactions.
"""

import pytest
from unittest.mock import MagicMock, patch
import os

from PySide6.QtWidgets import QApplication, QDialogButtonBox
from PySide6.QtCore import Qt

from export.export_dialog import ExportDialog, ExportMode
from config import Config


class TestExportDialog:
    """Test ExportDialog functionality."""
    
    def test_dialog_creation(self, qtbot):
        """Test creating export dialog."""
        dialog = ExportDialog(frame_count=10, current_frame=5)
        qtbot.addWidget(dialog)
        
        assert dialog.windowTitle() == "Export Frames"
        assert dialog.isModal()
        assert dialog.frame_count == 10
        assert dialog.current_frame == 5
    
    def test_export_modes(self, qtbot):
        """Test export mode radio buttons."""
        dialog = ExportDialog(frame_count=10)
        qtbot.addWidget(dialog)
        
        # Check default mode
        assert dialog.individual_radio.isChecked()
        
        # Test mode switching
        dialog.sheet_radio.click()
        assert dialog.sheet_radio.isChecked()
        assert dialog.mode_group.checkedId() == 1
        
        dialog.selected_radio.click()
        assert dialog.selected_radio.isChecked()
        assert dialog.mode_group.checkedId() == 2
        
        dialog.gif_radio.click()
        assert dialog.gif_radio.isChecked()
        assert dialog.mode_group.checkedId() == 3
    
    def test_format_selection(self, qtbot):
        """Test format combo box."""
        dialog = ExportDialog()
        qtbot.addWidget(dialog)
        
        # Check available formats
        format_count = dialog.format_combo.count()
        assert format_count >= 3  # At least PNG, JPG, BMP
        
        # Check default format
        assert dialog.format_combo.currentText() == Config.Export.DEFAULT_FORMAT
        
        # Test format change
        dialog.format_combo.setCurrentText("JPG")
        assert dialog.format_combo.currentText() == "JPG"
    
    def test_scale_factor_controls(self, qtbot):
        """Test scale factor spin box and preset buttons."""
        dialog = ExportDialog()
        qtbot.addWidget(dialog)
        
        # Check default scale
        assert dialog.scale_spin.value() == 1.0
        
        # Test manual scale change
        dialog.scale_spin.setValue(2.5)
        assert dialog.scale_spin.value() == 2.5
        
        # Test scale limits
        assert dialog.scale_spin.minimum() == 0.1
        assert dialog.scale_spin.maximum() == 10.0
    
    def test_output_directory_selection(self, qtbot):
        """Test output directory selection."""
        dialog = ExportDialog()
        qtbot.addWidget(dialog)
        
        # Check default directory
        default_dir = os.path.join(os.getcwd(), Config.Export.DEFAULT_EXPORT_DIR)
        assert dialog.output_dir_edit.text() == default_dir
        
        # Test setting directory
        test_dir = "/test/export/dir"
        dialog.output_dir_edit.setText(test_dir)
        assert dialog.output_dir_edit.text() == test_dir
    
    def test_filename_pattern(self, qtbot):
        """Test filename pattern and preview."""
        dialog = ExportDialog()
        qtbot.addWidget(dialog)
        
        # Check default pattern
        assert dialog.pattern_edit.text() == Config.Export.DEFAULT_PATTERN
        
        # Test pattern preview
        dialog.base_name_edit.setText("sprite")
        dialog.pattern_edit.setText("{name}_{index:04d}")
        
        # Preview should update
        assert "sprite_0000.png" in dialog.preview_label.text()
    
    def test_frame_selection_list(self, qtbot):
        """Test frame selection list for selected frames mode."""
        dialog = ExportDialog(frame_count=5, current_frame=2)
        qtbot.addWidget(dialog)
        
        # Selection group should be hidden initially
        assert not dialog.selection_group.isVisible()
        
        # Switch to selected frames mode
        dialog.selected_radio.click()
        assert dialog.selection_group.isVisible()
        
        # Check frame list
        assert dialog.frame_list.count() == 5
        
        # Current frame should be selected
        assert dialog.frame_list.item(2).isSelected()
        
        # Test select all
        dialog._select_all_frames()
        for i in range(5):
            assert dialog.frame_list.item(i).isSelected()
        
        # Test select none
        dialog._select_no_frames()
        for i in range(5):
            assert not dialog.frame_list.item(i).isSelected()
    
    def test_ui_state_updates(self, qtbot):
        """Test UI state updates based on mode."""
        dialog = ExportDialog()
        qtbot.addWidget(dialog)
        
        # Individual mode - pattern enabled
        dialog.individual_radio.click()
        assert dialog.pattern_edit.isEnabled()
        assert not dialog.selection_group.isVisible()
        
        # Sheet mode - pattern disabled
        dialog.sheet_radio.click()
        assert not dialog.pattern_edit.isEnabled()
        assert not dialog.selection_group.isVisible()
        
        # Selected mode - pattern enabled, selection visible
        dialog.selected_radio.click()
        assert dialog.pattern_edit.isEnabled()
        assert dialog.selection_group.isVisible()
        
        # GIF mode - format disabled
        dialog.gif_radio.click()
        assert not dialog.format_combo.isEnabled()
    
    def test_validation(self, qtbot):
        """Test export settings validation."""
        dialog = ExportDialog(frame_count=5)
        qtbot.addWidget(dialog)
        
        # Clear required fields
        dialog.output_dir_edit.clear()
        assert not dialog._validate_settings()
        
        dialog.output_dir_edit.setText("/tmp")
        dialog.base_name_edit.clear()
        assert not dialog._validate_settings()
        
        dialog.base_name_edit.setText("test")
        dialog.pattern_edit.clear()
        assert not dialog._validate_settings()
        
        # Invalid pattern
        dialog.pattern_edit.setText("{invalid}")
        assert not dialog._validate_settings()
        
        # Valid pattern
        dialog.pattern_edit.setText("{name}_{index}")
        assert dialog._validate_settings()
        
        # Selected mode with no selection
        dialog.selected_radio.click()
        dialog._select_no_frames()
        assert not dialog._validate_settings()
    
    def test_gather_settings(self, qtbot):
        """Test gathering export settings."""
        dialog = ExportDialog(frame_count=3)
        qtbot.addWidget(dialog)
        
        # Set up test values
        dialog.output_dir_edit.setText("/test/dir")
        dialog.base_name_edit.setText("mysprite")
        dialog.format_combo.setCurrentText("PNG")
        dialog.scale_spin.setValue(2.0)
        dialog.pattern_edit.setText("{name}_{frame}")
        
        # Individual frames mode
        dialog.individual_radio.click()
        settings = dialog._gather_settings()
        
        assert settings['output_dir'] == "/test/dir"
        assert settings['base_name'] == "mysprite"
        assert settings['format'] == "PNG"
        assert settings['mode'] == "individual"
        assert settings['scale_factor'] == 2.0
        assert settings['pattern'] == "{name}_{frame}"
        
        # Selected frames mode
        dialog.selected_radio.click()
        dialog.frame_list.item(0).setSelected(True)
        dialog.frame_list.item(2).setSelected(True)
        
        settings = dialog._gather_settings()
        assert settings['mode'] == "selected"
        assert settings['selected_indices'] == [0, 2]
    
    def test_export_button_triggers_signal(self, qtbot):
        """Test that OK button triggers export signal."""
        dialog = ExportDialog(frame_count=1)
        qtbot.addWidget(dialog)
        
        # Set valid values
        dialog.output_dir_edit.setText("/tmp")
        dialog.base_name_edit.setText("test")
        
        # Connect signal spy
        signal_received = []
        dialog.exportRequested.connect(lambda s: signal_received.append(s))
        
        # Click OK
        ok_button = dialog.button_box.button(QDialogButtonBox.Ok)
        ok_button.click()
        
        # Check signal was emitted
        assert len(signal_received) == 1
        settings = signal_received[0]
        assert settings['output_dir'] == "/tmp"
        assert settings['base_name'] == "test"
    
    def test_progress_handling(self, qtbot):
        """Test progress bar updates."""
        dialog = ExportDialog()
        qtbot.addWidget(dialog)
        
        # Progress bar should be hidden initially
        assert not dialog.progress_bar.isVisible()
        
        # Simulate export start
        dialog._on_export_started()
        assert dialog.progress_bar.isVisible()
        assert not dialog.button_box.button(QDialogButtonBox.Ok).isEnabled()
        
        # Simulate progress
        dialog._on_export_progress(5, 10, "Exporting frame 5")
        assert dialog.progress_bar.value() == 5
        assert dialog.progress_bar.maximum() == 10
        assert dialog.status_label.text() == "Exporting frame 5"
        
        # Simulate completion
        dialog._on_export_finished(True, "Export complete")
        assert not dialog.progress_bar.isVisible()
        assert dialog.button_box.button(QDialogButtonBox.Ok).isEnabled()
        assert "Export complete" in dialog.status_label.text()
    
    @patch('export_dialog.QFileDialog.getExistingDirectory')
    def test_browse_directory(self, mock_dialog, qtbot):
        """Test browse directory functionality."""
        dialog = ExportDialog()
        qtbot.addWidget(dialog)
        
        # Mock directory selection
        mock_dialog.return_value = "/new/export/path"
        
        # Find and click browse button
        browse_button = None
        for widget in dialog.findChildren(type(dialog.button_box.button(QDialogButtonBox.Ok))):
            if widget.text() == "Browse...":
                browse_button = widget
                break
        
        assert browse_button is not None
        browse_button.click()
        
        # Check directory was updated
        assert dialog.output_dir_edit.text() == "/new/export/path"
    
    def test_export_current_frame_preset(self, qtbot):
        """Test export dialog preset for current frame export."""
        dialog = ExportDialog(frame_count=10, current_frame=5)
        qtbot.addWidget(dialog)
        
        # Simulate preset for current frame
        dialog.selected_radio.setChecked(True)
        dialog._update_ui_state()
        
        assert dialog.selected_radio.isChecked()
        assert dialog.selection_group.isVisible()
        
        # Current frame should be selected
        assert dialog.frame_list.item(5).isSelected()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])