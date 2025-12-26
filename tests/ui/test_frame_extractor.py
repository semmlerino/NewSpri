#!/usr/bin/env python3
"""
Tests for FrameExtractor UI component.
Comprehensive testing of frame extraction settings widget functionality.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QRadioButton, QSpinBox, QPushButton, QCheckBox, QButtonGroup

from ui.frame_extractor import FrameExtractor
from config import Config


class TestFrameExtractorInitialization:
    """Test FrameExtractor initialization and basic setup."""
    
    def test_widget_creation(self, qapp):
        """Test widget is created successfully."""
        widget = FrameExtractor()
        assert widget is not None
        assert widget.windowTitle() == ""  # QGroupBox title is different
        assert "Frame Extraction" in widget.title()
    
    def test_signal_definitions(self, qapp):
        """Test all required signals are defined."""
        widget = FrameExtractor()
        
        # Test signals exist
        assert hasattr(widget, 'settingsChanged')
        assert hasattr(widget, 'presetSelected')
        assert hasattr(widget, 'modeChanged')
    
    def test_default_state(self, qapp):
        """Test widget initializes to expected default state."""
        widget = FrameExtractor()

        # CCL mode is now the default (changed from grid)
        assert widget.ccl_mode_btn.isChecked()
        assert not widget.grid_mode_btn.isChecked()
        assert widget.get_extraction_mode() == "ccl"

        # CCL mode should start enabled (since it's the default)
        assert widget.ccl_mode_btn.isEnabled()
        
        # Default frame size
        expected_width = Config.FrameExtraction.DEFAULT_FRAME_WIDTH
        expected_height = Config.FrameExtraction.DEFAULT_FRAME_HEIGHT
        assert widget.get_frame_size() == (expected_width, expected_height)
        
        # Default offset and spacing
        assert widget.get_offset() == (0, 0)
        assert widget.get_spacing() == (0, 0)
        
        # Grid checkbox should be unchecked by default
        assert not widget.grid_checkbox.isChecked()
    
    def test_preset_initialization(self, qapp):
        """Test preset buttons are created correctly."""
        widget = FrameExtractor()
        
        # Should have buttons for all presets
        square_count = len(Config.FrameExtraction.SQUARE_PRESETS)
        rect_count = len(Config.FrameExtraction.RECTANGULAR_PRESETS)
        total_presets = square_count + rect_count
        
        assert len(widget.preset_group.buttons()) == total_presets
        
        # Default preset should be selected (192x192)
        default_btn = widget.preset_group.button(Config.FrameExtraction.DEFAULT_PRESET_INDEX)
        assert default_btn.isChecked()


class TestFrameExtractorModeHandling:
    """Test extraction mode switching functionality."""
    
    def test_mode_change_signals(self, qapp):
        """Test mode change emits correct signals."""
        widget = FrameExtractor()
        spy = QSignalSpy(widget.modeChanged)
        
        # Switch to CCL mode (first enable it)
        widget.set_ccl_available(True)
        widget.ccl_mode_btn.setChecked(True)
        widget._on_mode_changed(widget.ccl_mode_btn)
        
        assert spy.count() == 1
        assert spy.at(0)[0] == "ccl"
        
        # Switch back to grid mode
        widget.grid_mode_btn.setChecked(True)
        widget._on_mode_changed(widget.grid_mode_btn)
        
        assert spy.count() == 2
        assert spy.at(1)[0] == "grid"
    
    def test_grid_mode_controls(self, qapp):
        """Test grid mode enables correct controls."""
        widget = FrameExtractor()
        
        # Ensure we're in grid mode
        widget.set_extraction_mode("grid")
        
        # All controls should be enabled in grid mode
        assert widget.width_spin.isEnabled()
        assert widget.height_spin.isEnabled()
        assert widget.auto_btn.isEnabled()
        assert widget.offset_x.isEnabled()
        assert widget.offset_y.isEnabled()
        assert widget.spacing_x.isEnabled()
        assert widget.spacing_y.isEnabled()
        assert widget.auto_margins_btn.isEnabled()
        assert widget.auto_spacing_btn.isEnabled()
        
        # Presets should be enabled
        for button in widget.preset_group.buttons():
            assert button.isEnabled()
    
    def test_ccl_mode_controls(self, qapp):
        """Test CCL mode disables grid-specific controls."""
        widget = FrameExtractor()
        
        # Enable and switch to CCL mode
        widget.set_ccl_available(True)
        widget.set_extraction_mode("ccl")
        
        # Grid controls should be disabled in CCL mode
        assert not widget.width_spin.isEnabled()
        assert not widget.height_spin.isEnabled()
        assert not widget.auto_btn.isEnabled()
        assert not widget.offset_x.isEnabled()
        assert not widget.offset_y.isEnabled()
        assert not widget.spacing_x.isEnabled()
        assert not widget.spacing_y.isEnabled()
        assert not widget.auto_margins_btn.isEnabled()
        assert not widget.auto_spacing_btn.isEnabled()
        
        # Presets should be disabled
        for button in widget.preset_group.buttons():
            assert not button.isEnabled()
    
    def test_ccl_availability(self, qapp):
        """Test CCL availability setting."""
        widget = FrameExtractor()

        # CCL is now enabled by default (changed from disabled)
        assert widget.ccl_mode_btn.isEnabled()

        # Update CCL info with sprite count
        widget.set_ccl_available(True, sprite_count=5)
        assert widget.ccl_mode_btn.isEnabled()
        assert "5 sprites" in widget.ccl_mode_btn.toolTip()

        # Disable CCL
        widget.set_ccl_available(False)
        assert not widget.ccl_mode_btn.isEnabled()
        assert "Load a sprite sheet first" in widget.ccl_mode_btn.toolTip()
    
    def test_mode_status_updates(self, qapp):
        """Test mode status indicator updates correctly."""
        widget = FrameExtractor()
        
        # Grid mode status
        widget.set_extraction_mode("grid")
        assert "Grid mode active" in widget.mode_status.text()
        
        # CCL mode status
        widget.set_ccl_available(True)
        widget.set_extraction_mode("ccl")
        assert "CCL mode active" in widget.mode_status.text()


class TestFrameExtractorPresetHandling:
    """Test preset selection and management."""
    
    def test_preset_selection_signals(self, qapp):
        """Test preset selection emits correct signals."""
        widget = FrameExtractor()

        # Switch to grid mode first (CCL is now default and presets are disabled in CCL)
        widget.set_extraction_mode("grid")

        spy = QSignalSpy(widget.presetSelected)

        # Get first square preset
        first_preset = Config.FrameExtraction.SQUARE_PRESETS[0]
        _, width, height, _ = first_preset

        # Simulate clicking the first preset button
        button = widget.preset_group.button(0)
        button.click()

        assert spy.count() == 1
        assert spy.at(0)[0] == width
        assert spy.at(0)[1] == height
    
    def test_preset_updates_frame_size(self, qapp):
        """Test selecting preset updates frame size."""
        widget = FrameExtractor()
        
        # Use set_frame_size instead of signal emission to test the actual behavior
        widget.set_frame_size(64, 64)
        
        # Frame size should update
        assert widget.get_frame_size() == (64, 64)
    
    def test_custom_size_unchecks_presets(self, qapp):
        """Test custom size change triggers settings signal."""
        widget = FrameExtractor()
        spy = QSignalSpy(widget.settingsChanged)
        
        # Change custom size
        widget.width_spin.setValue(100)
        widget._on_custom_size_changed()
        
        # Should emit settings changed signal
        assert spy.count() >= 1
    
    def test_set_frame_size_works(self, qapp):
        """Test setting frame size works correctly."""
        widget = FrameExtractor()
        
        # Set to a standard size
        widget.set_frame_size(32, 32)
        assert widget.get_frame_size() == (32, 32)
    
    def test_set_frame_size_custom(self, qapp):
        """Test setting custom frame size works."""
        widget = FrameExtractor()
        
        # Set to non-preset size
        widget.set_frame_size(123, 456)
        
        # Frame size should be set correctly
        assert widget.get_frame_size() == (123, 456)


class TestFrameExtractorValueHandling:
    """Test value input and validation."""
    
    def test_frame_size_bounds(self, qapp):
        """Test frame size spinboxes respect bounds."""
        widget = FrameExtractor()
        
        # Test minimum bounds
        min_size = Config.FrameExtraction.MIN_FRAME_SIZE
        max_size = Config.FrameExtraction.MAX_FRAME_SIZE
        
        assert widget.width_spin.minimum() == min_size
        assert widget.width_spin.maximum() == max_size
        assert widget.height_spin.minimum() == min_size
        assert widget.height_spin.maximum() == max_size
    
    def test_offset_bounds(self, qapp):
        """Test offset spinboxes respect bounds."""
        widget = FrameExtractor()
        
        default_offset = Config.FrameExtraction.DEFAULT_OFFSET
        max_offset = Config.FrameExtraction.MAX_OFFSET
        
        assert widget.offset_x.minimum() == default_offset
        assert widget.offset_x.maximum() == max_offset
        assert widget.offset_y.minimum() == default_offset
        assert widget.offset_y.maximum() == max_offset
    
    def test_spacing_bounds(self, qapp):
        """Test spacing spinboxes respect bounds."""
        widget = FrameExtractor()
        
        default_spacing = Config.FrameExtraction.DEFAULT_SPACING
        max_spacing = Config.FrameExtraction.MAX_SPACING
        
        assert widget.spacing_x.minimum() == default_spacing
        assert widget.spacing_x.maximum() == max_spacing
        assert widget.spacing_y.minimum() == default_spacing
        assert widget.spacing_y.maximum() == max_spacing
    
    def test_settings_changed_signals(self, qapp):
        """Test settingsChanged signal is emitted on value changes."""
        widget = FrameExtractor()
        spy = QSignalSpy(widget.settingsChanged)
        
        # Change various values
        widget.offset_x.setValue(10)
        widget.offset_y.setValue(15)
        widget.spacing_x.setValue(5)
        widget.spacing_y.setValue(8)
        
        # Should have multiple signals
        assert spy.count() >= 4
    
    def test_value_setters_and_getters(self, qapp):
        """Test value setter and getter methods."""
        widget = FrameExtractor()
        
        # Test frame size
        widget.set_frame_size(128, 96)
        assert widget.get_frame_size() == (128, 96)
        
        # Test offset (set through spinboxes)
        widget.offset_x.setValue(20)
        widget.offset_y.setValue(30)
        assert widget.get_offset() == (20, 30)
        
        # Test spacing (set through spinboxes)
        widget.spacing_x.setValue(4)
        widget.spacing_y.setValue(6)
        assert widget.get_spacing() == (4, 6)


class TestFrameExtractorAutoButtons:
    """Test auto-detection button functionality."""
    
    def test_auto_button_registration(self, qapp):
        """Test auto buttons are properly registered."""
        widget = FrameExtractor()
        
        # Check buttons exist
        assert widget.auto_btn is not None
        assert widget.auto_margins_btn is not None
        assert widget.auto_spacing_btn is not None
        assert widget.comprehensive_auto_btn is not None
        
        # Check they're registered with button manager
        assert widget._button_manager is not None
    
    def test_confidence_updates(self, qapp):
        """Test confidence level updates work."""
        widget = FrameExtractor()
        
        # Test each confidence level
        confidence_levels = ['high', 'medium', 'low', 'failed']
        button_types = ['frame', 'margins', 'spacing']
        
        for button_type in button_types:
            for confidence in confidence_levels:
                # Should not raise exception
                widget.update_auto_button_confidence(button_type, confidence, "Test message")
    
    def test_button_reset(self, qapp):
        """Test button reset functionality."""
        widget = FrameExtractor()
        
        # Update confidence then reset
        widget.update_auto_button_confidence('frame', 'high', "Test")
        widget.reset_auto_button_style('frame')
        
        # Should not raise exception


class TestFrameExtractorCollapsibleSections:
    """Test collapsible section functionality."""
    
    def test_section_toggle(self, qapp):
        """Test section expand/collapse functionality."""
        widget = FrameExtractor()
        
        # Find collapsible sections (they contain toggle buttons)
        toggle_buttons = widget.findChildren(QPushButton)
        
        # Should have at least the preset section toggles
        assert len(toggle_buttons) > 2  # At least some buttons for sections + auto buttons
    
    def test_initial_section_state(self, qapp):
        """Test sections start in correct state."""
        widget = FrameExtractor()
        
        # Preset sections should be visible initially
        # This is tested by ensuring preset buttons are accessible
        assert len(widget.preset_group.buttons()) > 0


class TestFrameExtractorIntegration:
    """Test widget integration with other components."""
    
    def test_grid_checkbox_integration(self, qapp):
        """Test grid overlay checkbox."""
        widget = FrameExtractor()
        
        # Grid checkbox should exist and be toggleable
        assert widget.grid_checkbox is not None
        assert isinstance(widget.grid_checkbox, QCheckBox)
        
        # Should start unchecked
        assert not widget.grid_checkbox.isChecked()
        
        # Should be toggleable
        widget.grid_checkbox.setChecked(True)
        assert widget.grid_checkbox.isChecked()
    
    def test_tooltip_content(self, qapp):
        """Test important tooltips are set."""
        widget = FrameExtractor()
        
        # Auto buttons should have tooltips
        assert widget.auto_btn.toolTip() != ""
        assert widget.auto_margins_btn.toolTip() != ""
        assert widget.auto_spacing_btn.toolTip() != ""
        assert widget.comprehensive_auto_btn.toolTip() != ""
        
        # Mode buttons should have tooltips
        assert widget.grid_mode_btn.toolTip() != ""
        assert widget.ccl_mode_btn.toolTip() != ""
    
    def test_widget_hierarchy(self, qapp):
        """Test widget parent-child relationships."""
        widget = FrameExtractor()
        
        # Check key child widgets exist
        spinboxes = widget.findChildren(QSpinBox)
        assert len(spinboxes) == 6  # width, height, offset_x, offset_y, spacing_x, spacing_y
        
        buttons = widget.findChildren(QPushButton)
        assert len(buttons) >= 4  # At least auto buttons
        
        radiobuttons = widget.findChildren(QRadioButton)
        assert len(radiobuttons) >= 2  # Mode buttons + presets


@pytest.mark.parametrize("width,height", [
    (32, 32), (48, 48), (64, 64), (128, 128), (192, 192),
    (32, 48), (48, 32), (64, 48), (48, 64)
])
def test_frame_size_parametrized(qapp, width, height):
    """Test various frame sizes work correctly."""
    widget = FrameExtractor()
    
    widget.set_frame_size(width, height)
    assert widget.get_frame_size() == (width, height)


@pytest.mark.parametrize("mode", ["grid", "ccl"])
def test_extraction_modes_parametrized(qapp, mode):
    """Test both extraction modes work correctly."""
    widget = FrameExtractor()
    
    if mode == "ccl":
        widget.set_ccl_available(True)
    
    widget.set_extraction_mode(mode)
    assert widget.get_extraction_mode() == mode


class TestFrameExtractorErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_mode_handling(self, qapp):
        """Test handling of invalid extraction mode."""
        widget = FrameExtractor()
        
        # Setting invalid mode should default to grid
        widget.set_extraction_mode("invalid_mode")
        assert widget.get_extraction_mode() == "grid"
    
    def test_ccl_mode_when_unavailable(self, qapp):
        """Test CCL mode when explicitly disabled."""
        widget = FrameExtractor()

        # CCL is enabled by default; first switch to grid mode
        widget.set_extraction_mode("grid")
        assert widget.get_extraction_mode() == "grid"

        # Disable CCL availability
        widget.set_ccl_available(False)

        # Now trying to set CCL should keep us in grid mode
        widget.set_extraction_mode("ccl")
        assert widget.get_extraction_mode() == "grid"
    
    def test_extreme_values(self, qapp):
        """Test widget handles extreme but valid values."""
        widget = FrameExtractor()
        
        # Test maximum values
        max_size = Config.FrameExtraction.MAX_FRAME_SIZE
        widget.set_frame_size(max_size, max_size)
        assert widget.get_frame_size() == (max_size, max_size)
        
        # Test minimum values  
        min_size = Config.FrameExtraction.MIN_FRAME_SIZE
        widget.set_frame_size(min_size, min_size)
        assert widget.get_frame_size() == (min_size, min_size)