"""
Unit tests for integrated export settings with live preview
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QGraphicsView
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtTest import QTest

from export.steps.settings_preview import (
    ExportSettingsPreviewStep, LivePreviewWidget
)
from export.core.export_presets import ExportPreset


class TestLivePreviewWidget:
    """Test the live preview widget."""
    
    def test_preview_creation(self, qtbot):
        """Test creating preview widget."""
        widget = LivePreviewWidget()
        qtbot.addWidget(widget)
        
        assert widget.scene is not None
        assert widget.dragMode() == QGraphicsView.DragMode.ScrollHandDrag
    
    def test_preview_update(self, qtbot):
        """Test updating preview."""
        widget = LivePreviewWidget()
        qtbot.addWidget(widget)
        
        # Create test pixmap
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.red)
        
        # Update preview
        widget.update_preview(pixmap, "Test Info")
        
        # Check scene has items
        assert len(widget.scene.items()) == 2  # Pixmap + text
    
    def test_zoom_functionality(self, qtbot):
        """Test zoom with mouse wheel."""
        widget = LivePreviewWidget()
        qtbot.addWidget(widget)
        
        # Add content
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.blue)
        widget.update_preview(pixmap)
        
        # Test zoom in/out
        # Note: Testing wheel events is complex in unit tests
        # This is more of a smoke test
        widget.fit_to_view()
        assert widget.transform().m11() != 0  # Has some zoom level


class TestExportSettingsPreviewStep:
    """Test the integrated settings and preview step."""
    
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
    def individual_preset(self):
        """Create individual frames preset."""
        return ExportPreset(
            name="individual",
            display_name="Individual Frames",
            icon="📁",
            description="Export each frame",
            mode="individual",
            format="PNG",
            scale=1.0,
            default_pattern="{name}_{index:03d}",
            tooltip="Export frames",
            use_cases=["Games"]
        )
    
    @pytest.fixture
    def sheet_preset(self):
        """Create sprite sheet preset."""
        return ExportPreset(
            name="sheet",
            display_name="Sprite Sheet",
            icon="📋",
            description="Single sheet",
            mode="sheet",
            format="PNG",
            scale=1.0,
            default_pattern="sheet",
            tooltip="Export sheet",
            use_cases=["Games"]
        )
    
    def test_step_creation(self, qtbot, test_sprites):
        """Test creating the step."""
        step = ExportSettingsPreviewStep(
            frame_count=8,
            current_frame=2,
            sprites=test_sprites
        )
        qtbot.addWidget(step)
        
        assert step.frame_count == 8
        assert step.current_frame == 2
        assert len(step._sprites) == 8
        assert step.preview_view is not None
    
    def test_preset_setup(self, qtbot, test_sprites, sheet_preset):
        """Test setting up for a preset."""
        step = ExportSettingsPreviewStep(sprites=test_sprites)
        qtbot.addWidget(step)
        
        # Setup for sheet preset
        step._setup_for_preset(sheet_preset)
        
        # Check settings were created
        assert 'directory' in step._settings_widgets
        assert 'grid_layout' in step._settings_widgets
        assert 'spacing' in step._settings_widgets
        assert 'background' in step._settings_widgets
    
    def test_preview_debouncing(self, qtbot, test_sprites, sheet_preset):
        """Test preview update debouncing."""
        step = ExportSettingsPreviewStep(sprites=test_sprites)
        qtbot.addWidget(step)
        
        step._setup_for_preset(sheet_preset)
        
        # Mock the update method
        step._update_preview = Mock()
        
        # Request multiple updates quickly
        for _ in range(5):
            step._request_preview_update()
            qtbot.wait(50)
        
        # Wait for debounce timer
        qtbot.wait(200)
        
        # Should only be called once due to debouncing
        assert step._update_preview.call_count == 1
    
    def test_settings_to_preview_update(self, qtbot, test_sprites, sheet_preset):
        """Test that changing settings updates preview."""
        step = ExportSettingsPreviewStep(sprites=test_sprites)
        qtbot.addWidget(step)
        
        step._setup_for_preset(sheet_preset)
        
        # Mock preview update
        step._update_preview = Mock()
        
        # Change spacing
        if 'spacing' in step._settings_widgets:
            step._settings_widgets['spacing'].setValue(5)
            qtbot.wait(200)  # Wait for debounce
            
            assert step._update_preview.called
    
    def test_individual_preview_generation(self, qtbot, test_sprites, individual_preset):
        """Test generating preview for individual frames."""
        step = ExportSettingsPreviewStep(sprites=test_sprites)
        qtbot.addWidget(step)
        
        step._setup_for_preset(individual_preset)
        
        # Generate preview
        pixmap, info = step._generate_individual_preview()
        
        assert not pixmap.isNull()
        assert "Individual Frames" in info
        assert "8 files" in info
    
    def test_sprite_sheet_preview_generation(self, qtbot, test_sprites, sheet_preset):
        """Test generating sprite sheet preview."""
        step = ExportSettingsPreviewStep(sprites=test_sprites)
        qtbot.addWidget(step)
        
        step._setup_for_preset(sheet_preset)
        
        # Generate preview
        pixmap, info = step._generate_sprite_sheet_preview()
        
        assert not pixmap.isNull()
        assert "Sprite Sheet" in info
        assert "grid" in info
    
    def test_data_collection(self, qtbot, test_sprites, sheet_preset):
        """Test getting data from step."""
        step = ExportSettingsPreviewStep(sprites=test_sprites)
        qtbot.addWidget(step)
        
        step._setup_for_preset(sheet_preset)
        
        # Set some values
        step._settings_widgets['directory'].set_directory("/tmp")
        step._settings_widgets['spacing'].setValue(2)
        
        # Get data
        data = step.get_data()
        
        assert data['output_dir'] == "/tmp"
        assert data['spacing'] == 2
        assert 'layout_mode' in data
        assert 'format' in data
    
    def test_export_button_validation(self, qtbot, test_sprites, individual_preset):
        """Test export button enables/disables based on validation."""
        step = ExportSettingsPreviewStep(sprites=test_sprites)
        qtbot.addWidget(step)
        
        step._setup_for_preset(individual_preset)
        
        # Initially should have valid directory
        assert step.export_button.isEnabled()
        
        # Clear directory
        step._settings_widgets['directory'].set_directory("")
        step._validate_settings()
        
        assert not step.export_button.isEnabled()
        
        # Set valid directory
        step._settings_widgets['directory'].set_directory("/tmp")
        step._validate_settings()
        
        assert step.export_button.isEnabled()
    
    def test_frame_selection_preview(self, qtbot, test_sprites):
        """Test preview for selected frames."""
        selected_preset = ExportPreset(
            name="selected",
            display_name="Selected Frames",
            icon="🎯",
            description="Selected only",
            mode="selected",
            format="PNG",
            scale=1.0,
            default_pattern="{name}_{index}",
            tooltip="Export selected",
            use_cases=["Partial"]
        )
        
        step = ExportSettingsPreviewStep(
            sprites=test_sprites,
            frame_count=8,
            current_frame=2
        )
        qtbot.addWidget(step)
        
        step._setup_for_preset(selected_preset)
        
        # Select some frames
        frame_list = step._settings_widgets['frame_list']
        frame_list.item(0).setSelected(True)
        frame_list.item(2).setSelected(True)
        frame_list.item(4).setSelected(True)
        
        # Generate preview
        pixmap, info = step._generate_selected_preview()
        
        assert not pixmap.isNull()
        assert "Selected Frames: 3 of 8" in info
    
    def test_format_quality_interaction(self, qtbot, test_sprites, individual_preset):
        """Test JPG quality appears when format changes."""
        step = ExportSettingsPreviewStep(sprites=test_sprites)
        qtbot.addWidget(step)
        
        # Show the widget to ensure proper visibility hierarchy
        step.show()
        qtbot.waitExposed(step)
        
        step._setup_for_preset(individual_preset)
        
        # Get format combo from settings widgets
        format_combo = step._settings_widgets.get('format')
        quality_spin = step._settings_widgets.get('quality')
        
        assert format_combo is not None
        assert quality_spin is not None
        
        # Get the quality row widget for visibility check
        quality_row = step.quality_row if hasattr(step, 'quality_row') else None
        
        # Initially PNG - no quality visible
        assert format_combo.currentText() == "PNG"
        if quality_row:
            assert not quality_row.isVisible()
        
        # Change to JPG by index
        jpg_index = format_combo.findText("JPG")
        assert jpg_index >= 0
        format_combo.setCurrentIndex(jpg_index)
        qtbot.wait(50)  # Wait for signal processing
        QApplication.processEvents()  # Process pending events
        
        # Check visibility
        if quality_row:
            assert quality_row.isVisible()
            # Quality spin should be effectively visible when row is visible
            assert quality_spin.parent().isVisible()
        
        # Back to PNG
        png_index = format_combo.findText("PNG")
        assert png_index >= 0
        format_combo.setCurrentIndex(png_index)
        qtbot.wait(50)  # Wait for signal processing
        QApplication.processEvents()  # Process pending events
        
        if quality_row:
            assert not quality_row.isVisible()
    
    def test_preview_info_updates(self, qtbot, test_sprites, sheet_preset):
        """Test preview info labels update."""
        step = ExportSettingsPreviewStep(sprites=test_sprites)
        qtbot.addWidget(step)
        
        step._setup_for_preset(sheet_preset)
        
        # Trigger preview update
        step._update_preview()
        
        # Check info was updated
        assert step.preview_info_label.text() != "Adjust settings to see preview"
        assert step.preview_stats_label.text() != ""
        assert "PNG" in step.preview_stats_label.text()
    
    def test_layout_mode_changes(self, qtbot, test_sprites, sheet_preset):
        """Test changing sprite sheet layout modes."""
        step = ExportSettingsPreviewStep(sprites=test_sprites)
        qtbot.addWidget(step)
        
        step._setup_for_preset(sheet_preset)
        
        grid_layout = step._settings_widgets['grid_layout']
        
        # Test different modes
        for i, mode in enumerate(['auto', 'columns', 'rows', 'square']):
            grid_layout.mode_group.button(i).click()
            qtbot.wait(50)
            
            data = step.get_data()
            assert data['layout_mode'] == mode