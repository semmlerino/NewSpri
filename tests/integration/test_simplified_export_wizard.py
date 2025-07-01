"""
Tests for Simplified Export Wizard
Verifies the simplified export type selection is working correctly.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor

from export.export_dialog_wizard import ExportDialogWizard
from export.export_type_step_simple import ExportTypeStepSimple, SimpleExportOption


class TestSimplifiedExportWizard:
    """Test the simplified export wizard interface."""
    
    @pytest.mark.integration
    def test_simplified_type_step_is_used(self, qtbot):
        """Test that the wizard uses the simplified type step."""
        dialog = ExportDialogWizard(frame_count=8)
        qtbot.addWidget(dialog)
        
        # Check that the type step is the simplified version
        assert isinstance(dialog.type_step, ExportTypeStepSimple)
        assert dialog.type_step.__class__.__name__ == "ExportTypeStepSimple"
    
    @pytest.mark.integration
    def test_no_gif_option_available(self, qtbot):
        """Test that GIF export option is not available."""
        dialog = ExportDialogWizard(frame_count=8)
        qtbot.addWidget(dialog)
        
        # Get all preset names
        preset_names = []
        for option in dialog.type_step._options:
            preset_names.append(option.preset.name)
        
        # Should have only 3 options: individual, sheet, selected
        assert len(preset_names) == 3
        assert "individual_frames" in preset_names
        assert "sprite_sheet" in preset_names
        assert "selected_frames" in preset_names
        assert "animation_gif" not in preset_names
    
    @pytest.mark.integration
    def test_simple_option_appearance(self, qtbot):
        """Test that export options use simple appearance."""
        dialog = ExportDialogWizard(frame_count=8)
        qtbot.addWidget(dialog)
        
        # Check that options are SimpleExportOption instances
        assert len(dialog.type_step._options) > 0
        for option in dialog.type_step._options:
            assert isinstance(option, SimpleExportOption)
            # Should have radio button
            assert option._radio_button is not None
            # Should not be overly large
            assert option.sizeHint().height() < 150  # Much smaller than old 160px cards
    
    @pytest.mark.integration
    def test_simple_selection_flow(self, qtbot):
        """Test selecting an export type in the simplified interface."""
        dialog = ExportDialogWizard(frame_count=8)
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Initially no selection
        assert dialog.type_step._selected_preset is None
        assert not dialog.wizard.next_button.isEnabled()
        
        # Click first option (individual frames)
        first_option = dialog.type_step._options[0]
        qtbot.mouseClick(first_option, Qt.LeftButton)
        
        # Should now have selection
        assert dialog.type_step._selected_preset is not None
        assert dialog.type_step._selected_preset.name == "individual_frames"
        assert dialog.wizard.next_button.isEnabled()
        
        # Radio button should be checked
        assert first_option._radio_button.isChecked()
        
        # Other options should not be checked
        for i, option in enumerate(dialog.type_step._options):
            if i == 0:
                assert option._radio_button.isChecked()
            else:
                assert not option._radio_button.isChecked()
    
    @pytest.mark.integration
    def test_preset_descriptions_visible(self, qtbot):
        """Test that preset descriptions are visible in the simple interface."""
        dialog = ExportDialogWizard(frame_count=8)
        qtbot.addWidget(dialog)
        
        # Each option should display description text
        for option in dialog.type_step._options:
            # Find description labels
            labels = option.findChildren(QLabel)
            description_found = False
            for label in labels:
                text = label.text()
                # Should contain either short description or use cases
                if (option.preset.short_description and option.preset.short_description in text) or \
                   (option.preset.description in text) or \
                   ("Best for:" in text):
                    description_found = True
                    break
            
            assert description_found, f"No description found for {option.preset.name}"
    
    @pytest.mark.integration  
    def test_no_quick_export_bar(self, qtbot):
        """Test that there's no redundant quick export bar."""
        dialog = ExportDialogWizard(frame_count=8)
        qtbot.addWidget(dialog)
        
        # The simplified version shouldn't have a quick export bar
        # Check that there are no buttons with "Quick Export" text
        buttons = dialog.type_step.findChildren(QPushButton)
        for button in buttons:
            assert "Quick Export" not in button.text()
            # Also shouldn't have the old quick action buttons
            assert "All as PNG" not in button.text()
            assert "Animated GIF" not in button.text()


# Import for type checking
from PySide6.QtWidgets import QPushButton, QLabel