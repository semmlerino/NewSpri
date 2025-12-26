#!/usr/bin/env python3
"""
Tests for PlaybackControls UI component.
Comprehensive testing of animation playback control widget functionality.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QPushButton, QSlider, QLabel, QCheckBox

from ui.playback_controls import PlaybackControls
from config import Config


class TestPlaybackControlsInitialization:
    """Test PlaybackControls initialization and basic setup."""
    
    def test_widget_creation(self, qapp):
        """Test widget is created successfully."""
        widget = PlaybackControls()
        assert widget is not None
        assert widget.frameStyle() != 0  # Should have styled panel frame
    
    def test_signal_definitions(self, qapp):
        """Test all required signals are defined."""
        widget = PlaybackControls()
        
        # Test signals exist
        assert hasattr(widget, 'playPauseClicked')
        assert hasattr(widget, 'frameChanged')
        assert hasattr(widget, 'fpsChanged')
        assert hasattr(widget, 'loopToggled')
    
    def test_default_state(self, qapp):
        """Test widget initializes to expected default state."""
        widget = PlaybackControls()
        
        # Play button should start as "Play"
        assert widget.play_button.text() == "Play"
        
        # Frame slider should start at minimum
        assert widget.frame_slider.value() == Config.Slider.FRAME_SLIDER_MIN
        assert widget.frame_slider.minimum() == Config.Slider.FRAME_SLIDER_MIN
        assert widget.frame_slider.maximum() == 0  # No frames loaded
        
        # FPS should be default value
        assert widget.fps_slider.value() == Config.Animation.DEFAULT_FPS
        assert widget.fps_value.text() == str(Config.Animation.DEFAULT_FPS)
        
        # Loop should be enabled by default
        assert widget.loop_checkbox.isChecked()
    
    def test_control_widgets_exist(self, qapp):
        """Test all required control widgets are created."""
        widget = PlaybackControls()
        
        # Check all key widgets exist
        assert widget.play_button is not None
        assert widget.prev_btn is not None
        assert widget.next_btn is not None
        assert widget.frame_slider is not None
        assert widget.fps_slider is not None
        assert widget.fps_value is not None
        assert widget.loop_checkbox is not None
    
    def test_slider_configurations(self, qapp):
        """Test sliders are configured correctly."""
        widget = PlaybackControls()
        
        # Frame slider
        assert widget.frame_slider.orientation() == Qt.Horizontal
        
        # FPS slider
        assert widget.fps_slider.orientation() == Qt.Horizontal
        assert widget.fps_slider.minimum() == Config.Animation.MIN_FPS
        assert widget.fps_slider.maximum() == Config.Animation.MAX_FPS
        assert widget.fps_slider.tickPosition() == QSlider.TicksBelow
        assert widget.fps_slider.tickInterval() == Config.Slider.FPS_SLIDER_TICK_INTERVAL


class TestPlaybackControlsPlaybackState:
    """Test playback state management."""
    
    def test_play_pause_toggle(self, qapp):
        """Test play/pause button state changes."""
        widget = PlaybackControls()
        
        # Start in stopped state
        assert widget.play_button.text() == "Play"
        
        # Set to playing
        widget.set_playing(True)
        assert widget.play_button.text() == "Pause"
        
        # Set back to stopped
        widget.set_playing(False)
        assert widget.play_button.text() == "Play"
    
    def test_play_pause_signals(self, qapp):
        """Test play/pause button emits signals."""
        widget = PlaybackControls()
        spy = QSignalSpy(widget.playPauseClicked)
        
        # Click play button
        widget.play_button.click()
        
        assert spy.count() == 1
    
    def test_button_state_updates(self, qapp):
        """Test navigation button state updates."""
        widget = PlaybackControls()
        
        # No frames loaded - buttons should be disabled
        widget.update_button_states(False, True, True)
        assert not widget.play_button.isEnabled()
        assert not widget.prev_btn.isEnabled()
        assert not widget.next_btn.isEnabled()
        
        # Has frames, at start
        widget.update_button_states(True, True, False)
        assert widget.play_button.isEnabled()
        assert not widget.prev_btn.isEnabled()  # At start
        assert widget.next_btn.isEnabled()
        
        # Has frames, in middle
        widget.update_button_states(True, False, False)
        assert widget.play_button.isEnabled()
        assert widget.prev_btn.isEnabled()
        assert widget.next_btn.isEnabled()
        
        # Has frames, at end
        widget.update_button_states(True, False, True)
        assert widget.play_button.isEnabled()
        assert widget.prev_btn.isEnabled()
        assert not widget.next_btn.isEnabled()  # At end


class TestPlaybackControlsFrameNavigation:
    """Test frame navigation functionality."""
    
    def test_frame_range_setting(self, qapp):
        """Test setting frame slider range."""
        widget = PlaybackControls()
        
        # Set frame range
        max_frame = 10
        widget.set_frame_range(max_frame)
        
        assert widget.frame_slider.maximum() == max_frame
        assert widget.frame_slider.minimum() == Config.Slider.FRAME_SLIDER_MIN
    
    def test_current_frame_setting(self, qapp):
        """Test setting current frame without signals."""
        widget = PlaybackControls()
        spy = QSignalSpy(widget.frameChanged)
        
        # Set frame range first
        widget.set_frame_range(10)
        
        # Set current frame (should not emit signal)
        widget.set_current_frame(5)
        
        assert widget.frame_slider.value() == 5
        assert spy.count() == 0  # No signal should be emitted
    
    def test_frame_changed_signals(self, qapp):
        """Test frame slider emits frameChanged signals."""
        widget = PlaybackControls()
        spy = QSignalSpy(widget.frameChanged)
        
        # Set frame range
        widget.set_frame_range(10)
        
        # Change frame via slider
        widget.frame_slider.setValue(3)
        
        assert spy.count() == 1
        assert spy.at(0)[0] == 3
    
    def test_frame_bounds(self, qapp):
        """Test frame slider respects bounds."""
        widget = PlaybackControls()
        
        # Set a range
        widget.set_frame_range(5)
        
        # Try to set beyond bounds
        widget.frame_slider.setValue(10)  # Beyond max
        assert widget.frame_slider.value() <= 5
        
        widget.frame_slider.setValue(-1)  # Below min
        assert widget.frame_slider.value() >= Config.Slider.FRAME_SLIDER_MIN


class TestPlaybackControlsFPSHandling:
    """Test FPS control functionality."""
    
    def test_fps_slider_range(self, qapp):
        """Test FPS slider has correct range."""
        widget = PlaybackControls()
        
        assert widget.fps_slider.minimum() == Config.Animation.MIN_FPS
        assert widget.fps_slider.maximum() == Config.Animation.MAX_FPS
    
    def test_fps_value_display(self, qapp):
        """Test FPS value label updates correctly."""
        widget = PlaybackControls()
        
        # Change FPS
        new_fps = 20
        widget.fps_slider.setValue(new_fps)
        widget._on_fps_changed(new_fps)
        
        assert widget.fps_value.text() == str(new_fps)
    
    def test_fps_changed_signals(self, qapp):
        """Test FPS slider emits fpsChanged signals."""
        widget = PlaybackControls()
        spy = QSignalSpy(widget.fpsChanged)
        
        # Change FPS
        new_fps = 15
        widget.fps_slider.setValue(new_fps)
        
        assert spy.count() == 1
        assert spy.at(0)[0] == new_fps
    
    def test_fps_bounds_validation(self, qapp):
        """Test FPS values respect configuration bounds."""
        widget = PlaybackControls()
        
        # Test minimum bound
        widget.fps_slider.setValue(Config.Animation.MIN_FPS - 1)
        assert widget.fps_slider.value() >= Config.Animation.MIN_FPS
        
        # Test maximum bound
        widget.fps_slider.setValue(Config.Animation.MAX_FPS + 1)
        assert widget.fps_slider.value() <= Config.Animation.MAX_FPS


class TestPlaybackControlsLoopHandling:
    """Test loop control functionality."""
    
    def test_loop_checkbox_default(self, qapp):
        """Test loop checkbox default state."""
        widget = PlaybackControls()
        
        # Should start checked
        assert widget.loop_checkbox.isChecked()
        assert widget.loop_checkbox.text() == "Loop animation"
    
    def test_loop_toggle_signals(self, qapp):
        """Test loop checkbox emits signals."""
        widget = PlaybackControls()
        spy = QSignalSpy(widget.loopToggled)
        
        # Toggle loop off
        widget.loop_checkbox.setChecked(False)
        
        assert spy.count() == 1
        assert spy.at(0)[0] is False
        
        # Toggle loop on
        widget.loop_checkbox.setChecked(True)
        
        assert spy.count() == 2
        assert spy.at(1)[0] is True
    
    def test_loop_state_persistence(self, qapp):
        """Test loop state can be changed and retrieved."""
        widget = PlaybackControls()
        
        # Change loop state
        widget.loop_checkbox.setChecked(False)
        assert not widget.loop_checkbox.isChecked()
        
        widget.loop_checkbox.setChecked(True)
        assert widget.loop_checkbox.isChecked()


class TestPlaybackControlsIntegration:
    """Test widget integration scenarios."""
    
    def test_complete_workflow(self, qapp):
        """Test complete playback control workflow."""
        widget = PlaybackControls()
        
        # Start with no frames
        widget.update_button_states(False, True, True)
        assert not widget.play_button.isEnabled()
        
        # Load frames
        widget.set_frame_range(10)
        widget.update_button_states(True, True, False)
        assert widget.play_button.isEnabled()
        
        # Navigate to middle frame
        widget.set_current_frame(5)
        widget.update_button_states(True, False, False)
        assert widget.prev_btn.isEnabled()
        assert widget.next_btn.isEnabled()
        
        # Start playing
        widget.set_playing(True)
        assert widget.play_button.text() == "Pause"
        
        # Stop playing
        widget.set_playing(False)
        assert widget.play_button.text() == "Play"
    
    def test_signal_connections(self, qapp):
        """Test all signals can be connected and emit properly."""
        widget = PlaybackControls()
        
        # Create spies for all signals
        play_spy = QSignalSpy(widget.playPauseClicked)
        frame_spy = QSignalSpy(widget.frameChanged)
        fps_spy = QSignalSpy(widget.fpsChanged)
        loop_spy = QSignalSpy(widget.loopToggled)
        
        # Trigger all signals
        widget.play_button.click()
        widget.set_frame_range(5)
        widget.frame_slider.setValue(2)
        widget.fps_slider.setValue(25)
        widget.loop_checkbox.setChecked(False)
        
        # Verify signals were emitted
        assert play_spy.count() == 1
        assert frame_spy.count() == 1
        assert fps_spy.count() == 1
        assert loop_spy.count() == 1
    
    def test_tooltips_and_accessibility(self, qapp):
        """Test tooltips and accessibility features."""
        widget = PlaybackControls()
        
        # Navigation buttons should have tooltips
        assert widget.prev_btn.toolTip() != ""
        assert widget.next_btn.toolTip() != ""
        assert "Prev" in widget.prev_btn.toolTip() or "←" in widget.prev_btn.toolTip()
        assert "Next" in widget.next_btn.toolTip() or "→" in widget.next_btn.toolTip()
    
    def test_widget_hierarchy(self, qapp):
        """Test widget parent-child relationships."""
        widget = PlaybackControls()
        
        # Check key child widgets exist
        buttons = widget.findChildren(QPushButton)
        assert len(buttons) == 3  # play, prev, next
        
        sliders = widget.findChildren(QSlider)
        assert len(sliders) == 2  # frame, fps
        
        labels = widget.findChildren(QLabel)
        assert len(labels) == 2  # fps label, fps value
        
        checkboxes = widget.findChildren(QCheckBox)
        assert len(checkboxes) == 1  # loop checkbox


class TestPlaybackControlsStyleAndLayout:
    """Test styling and layout functionality."""
    
    def test_minimum_dimensions(self, qapp):
        """Test widget respects minimum dimensions."""
        widget = PlaybackControls()
        
        # Play button should have minimum height
        min_height = Config.UI.PLAYBACK_BUTTON_MIN_HEIGHT
        assert widget.play_button.minimumHeight() == min_height
    
    def test_fps_value_alignment(self, qapp):
        """Test FPS value label is properly aligned."""
        widget = PlaybackControls()
        
        # FPS value should be right-aligned
        assert widget.fps_value.alignment() & Qt.AlignRight
        
        # Should have minimum width
        min_width = Config.Slider.FPS_VALUE_MIN_WIDTH
        assert widget.fps_value.minimumWidth() == min_width
    
    def test_style_sheets_applied(self, qapp):
        """Test style sheets are applied to widgets."""
        widget = PlaybackControls()
        
        # Frame should have style sheet (from Config.Styles)
        assert widget.styleSheet() != ""
        
        # Play button should have style sheet
        assert widget.play_button.styleSheet() != ""


@pytest.mark.parametrize("fps", [1, 5, 10, 15, 20, 30, 45, 60])
def test_fps_values_parametrized(qapp, fps):
    """Test various FPS values work correctly."""
    widget = PlaybackControls()
    
    if Config.Animation.MIN_FPS <= fps <= Config.Animation.MAX_FPS:
        widget.fps_slider.setValue(fps)
        widget._on_fps_changed(fps)
        assert widget.fps_value.text() == str(fps)


@pytest.mark.parametrize("frame_count", [0, 1, 5, 10, 20, 100])
def test_frame_ranges_parametrized(qapp, frame_count):
    """Test various frame counts work correctly."""
    widget = PlaybackControls()
    
    widget.set_frame_range(frame_count)
    assert widget.frame_slider.maximum() == frame_count
    
    # Test setting frame within range
    if frame_count > 0:
        mid_frame = frame_count // 2
        widget.set_current_frame(mid_frame)
        assert widget.frame_slider.value() == mid_frame


@pytest.mark.parametrize("playing", [True, False])
def test_playing_states_parametrized(qapp, playing):
    """Test both playing states work correctly."""
    widget = PlaybackControls()
    
    widget.set_playing(playing)
    
    if playing:
        assert widget.play_button.text() == "Pause"
    else:
        assert widget.play_button.text() == "Play"


class TestPlaybackControlsErrorHandling:
    """Test error handling and edge cases."""
    
    def test_negative_frame_range(self, qapp):
        """Test handling of negative frame range."""
        widget = PlaybackControls()
        
        # Setting negative range - widget may allow it, but should not crash
        try:
            widget.set_frame_range(-1)
            # Widget allows negative range, verify it's set
            assert widget.frame_slider.maximum() == -1
        except ValueError:
            # Widget rejects negative range, which is also acceptable
            pass
    
    def test_out_of_bounds_frame_setting(self, qapp):
        """Test setting frame out of slider bounds."""
        widget = PlaybackControls()
        
        # Set small range
        widget.set_frame_range(5)
        
        # Try to set beyond bounds
        widget.set_current_frame(100)
        assert widget.frame_slider.value() <= 5
        
        widget.set_current_frame(-10)
        assert widget.frame_slider.value() >= Config.Slider.FRAME_SLIDER_MIN
    
    def test_extreme_fps_values(self, qapp):
        """Test extreme but valid FPS values."""
        widget = PlaybackControls()
        
        # Test minimum FPS
        min_fps = Config.Animation.MIN_FPS
        widget.fps_slider.setValue(min_fps)
        assert widget.fps_slider.value() == min_fps
        
        # Test maximum FPS
        max_fps = Config.Animation.MAX_FPS
        widget.fps_slider.setValue(max_fps)
        assert widget.fps_slider.value() == max_fps
    
    def test_rapid_state_changes(self, qapp):
        """Test rapid state changes don't cause issues."""
        widget = PlaybackControls()
        
        # Rapidly change playing state
        for _ in range(10):
            widget.set_playing(True)
            widget.set_playing(False)
        
        # Should end in stopped state
        assert widget.play_button.text() == "Play"
        
        # Rapidly change frame
        widget.set_frame_range(10)
        for i in range(5):
            widget.set_current_frame(i)
            widget.set_current_frame(10 - i)
        
        # Should be within bounds
        assert 0 <= widget.frame_slider.value() <= 10


class TestPlaybackControlsPerformance:
    """Test performance-related scenarios."""
    
    def test_large_frame_count(self, qapp):
        """Test handling of large frame counts."""
        widget = PlaybackControls()
        
        # Test with large frame count
        large_count = 1000
        widget.set_frame_range(large_count)
        
        assert widget.frame_slider.maximum() == large_count
        
        # Should be able to navigate to middle
        mid_frame = large_count // 2
        widget.set_current_frame(mid_frame)
        assert widget.frame_slider.value() == mid_frame
    
    def test_signal_blocking_performance(self, qapp):
        """Test signal blocking prevents unnecessary emissions."""
        widget = PlaybackControls()
        spy = QSignalSpy(widget.frameChanged)
        
        widget.set_frame_range(10)
        
        # Multiple set_current_frame calls should not emit signals
        for i in range(5):
            widget.set_current_frame(i)
        
        # No signals should be emitted
        assert spy.count() == 0