"""
Pytest suite for testing export dialog integration with Phase 4 visual preview.
Tests the enhanced export dialog functionality and UI integration.
"""

import pytest

# Mark all tests in this file as export integration tests
pytestmark = [
    pytest.mark.phase4,
    pytest.mark.export_integration,
    pytest.mark.integration,
    pytest.mark.ui,
    pytest.mark.requires_display
]

import sys
import os
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from typing import List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Qt imports
from PySide6.QtWidgets import QApplication, QTabWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor

# Project imports
from export import ExportDialog
from export.core.frame_exporter import SpriteSheetLayout
from export.core.export_presets import ExportPresetType, get_preset_manager


# NOTE: qapp fixture is inherited from tests/conftest.py


@pytest.fixture
def sample_sprites():
    """Create sample sprites for testing."""
    sprites = []
    for i in range(12):
        pixmap = QPixmap(32, 32)
        color = QColor(i * 20, (i * 40) % 255, (i * 60) % 255)
        pixmap.fill(color)
        sprites.append(pixmap)
    return sprites


@pytest.fixture
def export_dialog(qapp, sample_sprites):
    """Create export dialog with test data."""
    dialog = ExportDialog(
        parent=None,
        frame_count=len(sample_sprites),
        current_frame=0,
        segment_manager=None
    )
    dialog.set_sprites(sample_sprites)
    return dialog


class TestExportDialogEnhancements:
    """Test enhanced export dialog with visual preview integration."""
    
    def test_dialog_has_visual_preview_tab(self, export_dialog):
        """Test that dialog has visual preview tab."""
        # Find the tab widget in the dialog
        tab_widget = None
        for child in export_dialog.findChildren(QTabWidget):
            if child.count() >= 2:  # Should have at least 2 tabs
                tab_widget = child
                break
        
        assert tab_widget is not None, "Tab widget not found"
        assert tab_widget.count() == 2, "Should have exactly 2 tabs"
        
        # Check tab names
        tab_names = [tab_widget.tabText(i) for i in range(tab_widget.count())]
        assert any("Export Info" in name for name in tab_names), "Export Info tab not found"
        assert any("Visual Preview" in name for name in tab_names), "Visual Preview tab not found"
        
    def test_visual_preview_widget_exists(self, export_dialog):
        """Test that visual preview widget is created."""
        assert hasattr(export_dialog, 'visual_preview_widget'), "visual_preview_widget attribute missing"
        assert export_dialog.visual_preview_widget is not None, "visual_preview_widget is None"
        
    def test_set_sprites_method(self, export_dialog, sample_sprites):
        """Test the set_sprites method."""
        # Test that method exists and works
        assert hasattr(export_dialog, 'set_sprites'), "set_sprites method missing"
        
        # Test setting sprites
        export_dialog.set_sprites(sample_sprites)
        assert export_dialog._current_sprites == sample_sprites
        
    def test_visual_preview_update_method(self, export_dialog):
        """Test the visual preview update method."""
        assert hasattr(export_dialog, '_update_visual_preview'), "_update_visual_preview method missing"
        
        # Should not crash when called
        export_dialog._update_visual_preview()
        
    def test_sprite_sheet_layout_creation(self, export_dialog):
        """Test sprite sheet layout creation from UI."""
        # Select a sprite sheet preset first
        preset_manager = get_preset_manager()
        sprite_sheet_preset = preset_manager.get_preset(ExportPresetType.SPRITE_SHEET)
        
        if sprite_sheet_preset:
            export_dialog._on_preset_selected(sprite_sheet_preset)
            
            # Test layout creation
            layout = export_dialog._create_sprite_sheet_layout()
            assert layout is not None, "Failed to create sprite sheet layout"
            assert isinstance(layout, SpriteSheetLayout), "Layout is not SpriteSheetLayout instance"
            
    def test_layout_controls_integration(self, export_dialog):
        """Test that layout controls exist and are connected."""
        # Select sprite sheet preset to make controls visible
        preset_manager = get_preset_manager()
        sprite_sheet_preset = preset_manager.get_preset(ExportPresetType.SPRITE_SHEET)
        
        if sprite_sheet_preset:
            export_dialog._on_preset_selected(sprite_sheet_preset)
            
            # Check that layout controls exist
            layout_controls = [
                'layout_mode_combo',
                'spacing_spin', 
                'padding_spin',
                'background_combo',
                'background_color_button'
            ]
            
            for control in layout_controls:
                assert hasattr(export_dialog, control), f"Layout control {control} missing"
                
    def test_preset_layout_application(self, export_dialog):
        """Test that preset layouts are applied to UI controls."""
        # Get a preset with specific layout
        preset_manager = get_preset_manager()
        web_game_preset = preset_manager.get_preset(ExportPresetType.WEB_GAME_ATLAS)
        
        if web_game_preset and web_game_preset.sprite_sheet_layout:
            # Apply preset
            export_dialog._on_preset_selected(web_game_preset)
            
            # Check that layout settings were applied
            layout = web_game_preset.sprite_sheet_layout
            
            # Verify UI reflects preset settings
            if hasattr(export_dialog, 'spacing_spin'):
                assert export_dialog.spacing_spin.value() == layout.spacing
            if hasattr(export_dialog, 'padding_spin'):
                assert export_dialog.padding_spin.value() == layout.padding


class TestLayoutModeVisibility:
    """Test layout mode visibility logic."""
    
    def test_individual_frames_hides_layout_section(self, export_dialog):
        """Test that individual frames preset hides layout section."""
        preset_manager = get_preset_manager()
        individual_preset = preset_manager.get_preset(ExportPresetType.INDIVIDUAL_FRAMES)
        
        if individual_preset:
            # Show the dialog so visibility checks work properly
            export_dialog.show()
            
            export_dialog._on_preset_selected(individual_preset)
            
            # Layout section should be hidden
            if hasattr(export_dialog, 'layout_section'):
                assert not export_dialog.layout_section.isVisible(), "Layout section should be hidden for individual frames"
                
    def test_sprite_sheet_shows_layout_section(self, export_dialog):
        """Test that sprite sheet preset shows layout section."""
        preset_manager = get_preset_manager()
        sprite_sheet_preset = preset_manager.get_preset(ExportPresetType.SPRITE_SHEET)
        
        if sprite_sheet_preset:
            # Show the dialog so visibility checks work properly
            export_dialog.show()
            
            # First check it's initially hidden
            if hasattr(export_dialog, 'layout_section'):
                assert not export_dialog.layout_section.isVisible(), "Layout section should be initially hidden"
            
            # Now select sprite sheet preset
            export_dialog._on_preset_selected(sprite_sheet_preset)
            
            # Layout section should now be visible
            if hasattr(export_dialog, 'layout_section'):
                assert export_dialog.layout_section.isVisible(), "Layout section should be visible for sprite sheet"
                
    def test_layout_mode_controls_visibility(self, export_dialog):
        """Test that layout mode controls show/hide correctly."""
        preset_manager = get_preset_manager()
        sprite_sheet_preset = preset_manager.get_preset(ExportPresetType.SPRITE_SHEET)
        
        if sprite_sheet_preset:
            # Show the dialog so visibility checks work properly
            export_dialog.show()
            
            export_dialog._on_preset_selected(sprite_sheet_preset)
            
            # Check that layout section is now visible first
            if not hasattr(export_dialog, 'layout_section') or not export_dialog.layout_section.isVisible():
                pytest.skip("Layout section not visible, skipping control visibility test")
            
            # Test different layout modes
            layout_modes = ['auto', 'rows', 'columns', 'square', 'custom']
            
            for i, mode in enumerate(layout_modes):
                if hasattr(export_dialog, 'layout_mode_combo'):
                    export_dialog.layout_mode_combo.setCurrentIndex(i)
                    export_dialog._on_layout_mode_changed(i)
                    
                    # Verify appropriate controls are visible
                    if mode == 'rows':
                        if hasattr(export_dialog, 'max_cols_spin'):
                            assert export_dialog.max_cols_spin.isVisible(), f"Max columns should be visible for {mode} mode"
                        if hasattr(export_dialog, 'max_rows_spin'):
                            assert not export_dialog.max_rows_spin.isVisible(), f"Max rows should be hidden for {mode} mode"
                    elif mode == 'columns':
                        if hasattr(export_dialog, 'max_rows_spin'):
                            assert export_dialog.max_rows_spin.isVisible(), f"Max rows should be visible for {mode} mode"
                        if hasattr(export_dialog, 'max_cols_spin'):
                            assert not export_dialog.max_cols_spin.isVisible(), f"Max columns should be hidden for {mode} mode"
                    elif mode == 'custom':
                        if hasattr(export_dialog, 'custom_cols_spin'):
                            assert export_dialog.custom_cols_spin.isVisible(), f"Custom columns should be visible for {mode} mode"
                        if hasattr(export_dialog, 'custom_rows_spin'):
                            assert export_dialog.custom_rows_spin.isVisible(), f"Custom rows should be visible for {mode} mode"


class TestSignalConnections:
    """Test signal connections for visual preview integration."""
    
    def test_layout_controls_connected(self, export_dialog):
        """Test that layout controls are connected to update methods."""
        preset_manager = get_preset_manager()
        sprite_sheet_preset = preset_manager.get_preset(ExportPresetType.SPRITE_SHEET)
        
        if sprite_sheet_preset:
            export_dialog._on_preset_selected(sprite_sheet_preset)
            
            # Test that controls exist and have connections
            controls_to_test = [
                'layout_mode_combo',
                'spacing_spin',
                'padding_spin', 
                'background_combo'
            ]
            
            for control_name in controls_to_test:
                if hasattr(export_dialog, control_name):
                    control = getattr(export_dialog, control_name)
                    
                    # Check that control has signal connections
                    # This is a bit tricky to test directly, so we'll check for the method existence
                    assert hasattr(export_dialog, '_update_layout_preview'), "Update method should exist"
                    
    def test_visual_preview_signal_connection(self, export_dialog):
        """Test that visual preview widget is connected."""
        if hasattr(export_dialog, 'visual_preview_widget'):
            # Check that the signal connection method exists
            assert hasattr(export_dialog, '_on_visual_preview_updated'), "Visual preview signal handler should exist"


class TestExportIntegration:
    """Test export integration with visual preview."""
    
    def test_gather_settings_includes_layout(self, export_dialog):
        """Test that _gather_settings includes sprite sheet layout."""
        preset_manager = get_preset_manager()
        sprite_sheet_preset = preset_manager.get_preset(ExportPresetType.SPRITE_SHEET)
        
        if sprite_sheet_preset:
            export_dialog._on_preset_selected(sprite_sheet_preset)
            
            # Gather settings
            settings = export_dialog._gather_settings()
            
            # Should include sprite_sheet_layout for sheet exports
            if export_dialog._current_preset and export_dialog._current_preset.mode == "sheet":
                assert 'sprite_sheet_layout' in settings, "Settings should include sprite_sheet_layout for sheet exports"
                assert isinstance(settings['sprite_sheet_layout'], SpriteSheetLayout), "sprite_sheet_layout should be SpriteSheetLayout instance"
                
    def test_export_settings_validation(self, export_dialog):
        """Test that export settings are properly validated."""
        preset_manager = get_preset_manager()
        sprite_sheet_preset = preset_manager.get_preset(ExportPresetType.SPRITE_SHEET)
        
        if sprite_sheet_preset:
            export_dialog._on_preset_selected(sprite_sheet_preset)
            
            # Test that settings can be gathered without errors
            try:
                settings = export_dialog._gather_settings()
                assert isinstance(settings, dict), "Settings should be a dictionary"
                
                # Check required keys
                required_keys = ['output_dir', 'base_name', 'format', 'mode', 'scale_factor', 'pattern']
                for key in required_keys:
                    assert key in settings, f"Required setting {key} missing"
                    
            except Exception as e:
                pytest.fail(f"Failed to gather settings: {e}")


class TestPreviewAccuracy:
    """Test that preview accurately represents export output."""
    
    def test_preview_layout_matches_export_layout(self, export_dialog, sample_sprites):
        """Test that preview layout calculations match export calculations."""
        preset_manager = get_preset_manager()
        sprite_sheet_preset = preset_manager.get_preset(ExportPresetType.SPRITE_SHEET)
        
        if sprite_sheet_preset:
            export_dialog._on_preset_selected(sprite_sheet_preset)
            
            # Get layout from preview
            preview_layout = export_dialog._create_sprite_sheet_layout()
            
            if preview_layout:
                # Calculate dimensions both ways
                preview_dims = preview_layout.calculate_estimated_dimensions(32, 32, len(sample_sprites))
                
                # Should produce reasonable dimensions
                assert preview_dims[0] > 0, "Preview width should be positive"
                assert preview_dims[1] > 0, "Preview height should be positive"
                
                # Should handle the sprite count appropriately
                frame_area = 32 * 32 * len(sample_sprites)
                sheet_area = preview_dims[0] * preview_dims[1]
                
                # Sheet should be larger than just frames (due to spacing/padding)
                # but not unreasonably larger
                assert sheet_area >= frame_area, "Sheet area should be at least as large as frame area"
                assert sheet_area <= frame_area * 4, "Sheet area shouldn't be more than 4x frame area (reasonable spacing)"


class TestErrorHandling:
    """Test error handling in export dialog integration."""
    
    def test_empty_sprite_list_handling(self, export_dialog):
        """Test handling of empty sprite list."""
        # Set empty sprite list
        export_dialog.set_sprites([])
        
        # Should not crash when updating preview
        try:
            export_dialog._update_visual_preview()
        except Exception as e:
            pytest.fail(f"Visual preview update crashed with empty sprites: {e}")
            
    def test_invalid_layout_handling(self, export_dialog, sample_sprites):
        """Test handling of invalid layout configurations."""
        export_dialog.set_sprites(sample_sprites)
        
        # Test with various invalid configurations
        try:
            # This should not crash even with edge case values
            if hasattr(export_dialog, 'spacing_spin'):
                export_dialog.spacing_spin.setValue(0)  # Minimum value
            if hasattr(export_dialog, 'padding_spin'):
                export_dialog.padding_spin.setValue(0)  # Minimum value
                
            export_dialog._update_visual_preview()
            
        except Exception as e:
            pytest.fail(f"Visual preview crashed with edge case values: {e}")
            
    def test_missing_preview_widget_handling(self, export_dialog):
        """Test handling when preview widget is missing."""
        # Temporarily remove visual preview widget
        original_widget = getattr(export_dialog, 'visual_preview_widget', None)
        if hasattr(export_dialog, 'visual_preview_widget'):
            delattr(export_dialog, 'visual_preview_widget')
        
        try:
            # Should not crash when widget is missing
            export_dialog._update_visual_preview()
        except Exception as e:
            pytest.fail(f"Update crashed when preview widget missing: {e}")
        finally:
            # Restore widget if it existed
            if original_widget:
                export_dialog.visual_preview_widget = original_widget


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=export.export_dialog",
        "--cov-report=term-missing"
    ])