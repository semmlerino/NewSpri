"""
Tests for Simplified Export Wizard
Verifies the simplified export type selection is working correctly.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor

from export import ExportDialog
from export.steps.type_selection import ExportTypeStepSimple
from export.widgets.preset_widget import ExportPresetSelector


class TestSimplifiedExportWizard:
    """Test the simplified export wizard interface."""
    
    @pytest.mark.integration
    def test_simplified_type_step_is_used(self, qtbot):
        """Test that the wizard uses the simplified type step."""
        dialog = ExportDialog(frame_count=8, current_frame=0)
        qtbot.addWidget(dialog)
        
        # Check that the type step is the simplified version
        assert isinstance(dialog.type_step, ExportTypeStepSimple)
        assert dialog.type_step.__class__.__name__ == "ExportTypeStepSimple"
    
    @pytest.mark.integration
    def test_no_gif_option_available(self, qtbot):
        """Test that GIF export option is not available."""
        dialog = ExportDialog(frame_count=8, current_frame=0)
        qtbot.addWidget(dialog)
        
        # Get all preset names
        preset_names = []
        for card in dialog.type_step._cards:
            preset_names.append(card.preset.name)
        
        # Should have only 3 options: individual, sheet, selected
        assert len(preset_names) == 3
        assert "individual_frames" in preset_names
        assert "sprite_sheet" in preset_names
        assert "selected_frames" in preset_names
        assert "animation_gif" not in preset_names
    
    @pytest.mark.integration
    def test_simple_option_appearance(self, qtbot):
        """Test that export options use simple appearance."""
        dialog = ExportDialog(frame_count=8, current_frame=0)
        qtbot.addWidget(dialog)
        
        # Check that options are preset selector instances
        assert len(dialog.type_step._cards) > 0
        for card in dialog.type_step._cards:
            assert hasattr(card, 'preset')
            # Should not be overly large
            assert option.sizeHint().height() < 200  # Reasonable size for cards
    
    @pytest.mark.integration
    def test_simple_selection_flow(self, qtbot):
        """Test selecting an export type in the simplified interface."""
        dialog = ExportDialog(frame_count=8, current_frame=0)
        qtbot.addWidget(dialog)
        dialog.show()
        
        # Initially no selection
        assert dialog.type_step._selected_preset is None
        assert not dialog.wizard.next_button.isEnabled()
        
        # Click first option (individual frames)
        first_card = dialog.type_step._cards[0]
        qtbot.mouseClick(first_card, Qt.LeftButton)
        
        # Should now have selection
        assert dialog.type_step._selected_preset is not None
        assert dialog.type_step._selected_preset.name == "individual_frames"
        assert dialog.wizard.next_button.isEnabled()
        
        # First card should be selected
        assert first_card in dialog.type_step._cards
    
    @pytest.mark.integration
    def test_preset_descriptions_visible(self, qtbot):
        """Test that preset descriptions are visible in the simple interface."""
        dialog = ExportDialog(frame_count=8, current_frame=0)
        qtbot.addWidget(dialog)
        
        # Each option should display description text
        for option in dialog.type_step._cards:
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
        dialog = ExportDialog(frame_count=8, current_frame=0)
        qtbot.addWidget(dialog)
        
        # The simplified version shouldn't have a quick export bar
        # Check that there are no buttons with "Quick Export" text
        buttons = dialog.type_step.findChildren(QPushButton)
        for button in buttons:
            assert "Quick Export" not in button.text()
            # Also shouldn't have the old quick action buttons
            assert "All as PNG" not in button.text()
            assert "Animated GIF" not in button.text()


from PySide6.QtWidgets import QPushButton, QLabel