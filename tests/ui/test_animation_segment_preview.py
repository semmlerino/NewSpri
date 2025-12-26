"""
Tests for Animation Segment Preview Widget
Tests the visual preview panel for animation segments with individual playback controls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSpinBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor

from ui.animation_segment_preview import AnimationSegmentPreview, SegmentPreviewItem


class TestSegmentPreviewItem:
    """Test the individual segment preview item."""
    
    def test_segment_preview_item_creation(self, qtbot):
        """Test basic creation of segment preview item."""
        # Create test frames
        frames = [QPixmap(32, 32) for _ in range(5)]
        for i, frame in enumerate(frames):
            frame.fill(Qt.blue)
        
        # Create preview item
        item = SegmentPreviewItem("TestSegment", QColor(255, 0, 0), frames)
        qtbot.addWidget(item)
        
        # Verify basic properties
        assert item.segment_name == "TestSegment"
        assert item.segment_color == QColor(255, 0, 0)
        assert len(item._frames) == 5
        assert item._current_frame == 0
        assert item._is_playing == False
        assert item._fps == 10  # Default FPS
        
    def test_fps_spinner_default_value(self, qtbot):
        """Test FPS spinner has correct default value of 10."""
        frames = [QPixmap(32, 32) for _ in range(3)]
        item = SegmentPreviewItem("Test", QColor(0, 255, 0), frames)
        qtbot.addWidget(item)
        
        # Find FPS spinner
        fps_spinner = item.findChild(QSpinBox)
        assert fps_spinner is not None
        assert fps_spinner.value() == 10
        assert fps_spinner.minimum() == 1
        assert fps_spinner.maximum() == 60
        
    def test_fps_spinner_functionality(self, qtbot):
        """Test FPS spinner changes timer interval."""
        frames = [QPixmap(32, 32) for _ in range(3)]
        item = SegmentPreviewItem("Test", QColor(0, 0, 255), frames)
        qtbot.addWidget(item)
        
        # Test FPS change
        item.fps_spinner.setValue(30)
        assert item._fps == 30
        assert item._timer.interval() == 1000 // 30  # ~33ms
        
        # Test edge cases
        item.fps_spinner.setValue(1)
        assert item._fps == 1
        assert item._timer.interval() == 1000  # 1000ms
        
        item.fps_spinner.setValue(60)
        assert item._fps == 60
        assert item._timer.interval() == 1000 // 60  # ~16ms
        
    def test_play_pause_toggle(self, qtbot):
        """Test play/pause button functionality."""
        frames = [QPixmap(32, 32) for _ in range(4)]
        item = SegmentPreviewItem("Test", QColor(255, 255, 0), frames)
        qtbot.addWidget(item)
        
        # Create signal spy
        play_spy = []  
        item.playToggled.connect(lambda name, playing: play_spy.append([name, playing]))
        
        # Initially not playing
        assert item._is_playing == False
        assert item.play_button.text() == "▶"
        
        # Click play
        qtbot.mouseClick(item.play_button, Qt.LeftButton)
        
        assert item._is_playing == True
        assert item.play_button.text() == "⏸"
        assert len(play_spy) == 1
        assert play_spy[0] == ["Test", True]
        
        # Click pause
        qtbot.mouseClick(item.play_button, Qt.LeftButton)
        
        assert item._is_playing == False
        assert item.play_button.text() == "▶"
        assert len(play_spy) == 2
        assert play_spy[1] == ["Test", False]
        
    def test_frame_animation_update(self, qtbot):
        """Test frame updates during animation."""
        frames = [QPixmap(32, 32) for _ in range(3)]
        for i, frame in enumerate(frames):
            # Fill with different colors to distinguish
            frame.fill([Qt.red, Qt.green, Qt.blue][i])
        
        item = SegmentPreviewItem("Test", QColor(128, 128, 128), frames)
        qtbot.addWidget(item)
        
        # Check initial frame
        assert item._current_frame == 0
        assert item.frame_counter.text() == "1 / 3"
        
        # Manually trigger frame update
        item._update_frame()
        assert item._current_frame == 1
        assert item.frame_counter.text() == "2 / 3"
        
        item._update_frame()
        assert item._current_frame == 2
        assert item.frame_counter.text() == "3 / 3"
        
        # Test wrap around
        item._update_frame()
        assert item._current_frame == 0
        assert item.frame_counter.text() == "1 / 3"
        
    def test_remove_button_signal(self, qtbot):
        """Test remove button emits correct signal."""
        frames = [QPixmap(32, 32) for _ in range(2)]
        item = SegmentPreviewItem("RemoveTest", QColor(0, 128, 255), frames)
        qtbot.addWidget(item)
        
        # Create signal spy
        remove_spy = []  
        item.removeRequested.connect(lambda name: remove_spy.append([name]))
        
        # Find and click remove button (it's a QToolButton, not QPushButton)
        from PySide6.QtWidgets import QToolButton
        remove_button = None
        for button in item.findChildren(QToolButton):
            if button.text() == "×":
                remove_button = button
                break
        
        assert remove_button is not None, "Remove button not found"
        qtbot.mouseClick(remove_button, Qt.LeftButton)
        
        assert len(remove_spy) == 1
        assert remove_spy[0] == ["RemoveTest"]
        
    def test_stop_playback(self, qtbot):
        """Test stop playback functionality."""
        frames = [QPixmap(32, 32) for _ in range(4)]
        item = SegmentPreviewItem("Test", QColor(255, 128, 0), frames)
        qtbot.addWidget(item)
        
        # Start playing and advance frames
        item.set_playing(True)
        item._current_frame = 2
        
        # Stop playback
        item.stop_playback()
        
        assert item._is_playing == False
        assert item._current_frame == 0
        assert item.frame_counter.text() == "1 / 4"


class TestAnimationSegmentPreview:
    """Test the main animation segment preview widget."""
    
    def test_widget_creation(self, qtbot):
        """Test basic widget creation."""
        widget = AnimationSegmentPreview()
        qtbot.addWidget(widget)
        
        assert widget._preview_items == {}
        assert widget._all_frames == []
        # Empty label should be visible when no segments
        # Note: Widget needs to be shown for visibility to work properly
        widget.show()
        qtbot.waitExposed(widget)
        assert widget.empty_label.isVisible()
        
    def test_add_segment(self, qtbot):
        """Test adding segments to preview."""
        widget = AnimationSegmentPreview()
        qtbot.addWidget(widget)
        
        # Set frames first
        frames = [QPixmap(32, 32) for _ in range(10)]
        widget.set_frames(frames)
        
        # Add a segment
        widget.add_segment("Walk", 0, 3, QColor(255, 0, 0))
        
        assert "Walk" in widget._preview_items
        assert len(widget._preview_items) == 1
        assert widget.empty_label.isHidden()
        
        # Add another segment
        widget.add_segment("Run", 4, 7, QColor(0, 255, 0))
        
        assert "Run" in widget._preview_items
        assert len(widget._preview_items) == 2
        
    def test_remove_segment(self, qtbot):
        """Test removing segments from preview."""
        widget = AnimationSegmentPreview()
        qtbot.addWidget(widget)
        
        # Setup
        frames = [QPixmap(32, 32) for _ in range(10)]
        widget.set_frames(frames)
        widget.add_segment("Segment1", 0, 2, QColor(255, 0, 0))
        widget.add_segment("Segment2", 3, 5, QColor(0, 255, 0))
        
        # Create signal spy
        remove_spy = []  
        # Signal connection will be added below
        
        # Remove segment
        widget.remove_segment("Segment1")
        
        assert "Segment1" not in widget._preview_items
        assert "Segment2" in widget._preview_items
        assert len(widget._preview_items) == 1
        
        # Remove last segment
        widget.remove_segment("Segment2")
        
        assert len(widget._preview_items) == 0
        # Widget needs to be shown for visibility check
        widget.show()
        qtbot.waitExposed(widget)
        assert widget.empty_label.isVisible()
        
    def test_play_all_functionality(self, qtbot):
        """Test play all button functionality."""
        widget = AnimationSegmentPreview()
        qtbot.addWidget(widget)
        
        # Setup segments
        frames = [QPixmap(32, 32) for _ in range(8)]
        widget.set_frames(frames)
        widget.add_segment("Seg1", 0, 2, QColor(255, 0, 0))
        widget.add_segment("Seg2", 3, 5, QColor(0, 255, 0))
        
        # Initially not playing
        assert all(not item._is_playing for item in widget._preview_items.values())
        
        # Click play all
        qtbot.mouseClick(widget.play_all_button, Qt.LeftButton)
        
        # All should be playing
        assert all(item._is_playing for item in widget._preview_items.values())
        assert widget.play_all_button.text() == "Pause All"
        
        # Click again to pause all
        qtbot.mouseClick(widget.play_all_button, Qt.LeftButton)
        
        assert all(not item._is_playing for item in widget._preview_items.values())
        assert widget.play_all_button.text() == "Play All"
        
    def test_stop_all_functionality(self, qtbot):
        """Test stop all button functionality."""
        widget = AnimationSegmentPreview()
        qtbot.addWidget(widget)
        
        # Setup segments
        frames = [QPixmap(32, 32) for _ in range(8)]
        widget.set_frames(frames)
        widget.add_segment("Seg1", 0, 2, QColor(255, 0, 0))
        widget.add_segment("Seg2", 3, 5, QColor(0, 255, 0))
        
        # Start playing all
        widget._toggle_all_playback()
        
        # Advance some frames
        widget._preview_items["Seg1"]._current_frame = 2
        widget._preview_items["Seg2"]._current_frame = 1
        
        # Click stop all
        qtbot.mouseClick(widget.stop_all_button, Qt.LeftButton)
        
        # All should be stopped and reset
        assert all(not item._is_playing for item in widget._preview_items.values())
        assert all(item._current_frame == 0 for item in widget._preview_items.values())
        assert widget.play_all_button.text() == "Play All"
        
    def test_segment_remove_signal_propagation(self, qtbot):
        """Test that remove requests from items are propagated."""
        widget = AnimationSegmentPreview()
        qtbot.addWidget(widget)
        
        # Setup
        frames = [QPixmap(32, 32) for _ in range(5)]
        widget.set_frames(frames)
        widget.add_segment("TestSeg", 0, 4, QColor(128, 128, 128))
        
        # Create signal spy for widget's remove signal
        remove_spy = []  
        widget.segmentRemoved.connect(lambda name: remove_spy.append([name]))
        
        # Trigger remove from the preview item
        preview_item = widget._preview_items["TestSeg"]
        preview_item.removeRequested.emit("TestSeg")
        
        assert len(remove_spy) == 1
        assert remove_spy[0] == ["TestSeg"]
        
    def test_clear_segments(self, qtbot):
        """Test clearing all segments."""
        widget = AnimationSegmentPreview()
        qtbot.addWidget(widget)
        
        # Add multiple segments
        frames = [QPixmap(32, 32) for _ in range(12)]
        widget.set_frames(frames)
        widget.add_segment("Seg1", 0, 3, QColor(255, 0, 0))
        widget.add_segment("Seg2", 4, 7, QColor(0, 255, 0))
        widget.add_segment("Seg3", 8, 11, QColor(0, 0, 255))
        
        assert len(widget._preview_items) == 3
        
        # Clear all
        widget.clear_segments()
        
        assert len(widget._preview_items) == 0
        # Widget needs to be shown for visibility check
        widget.show()
        qtbot.waitExposed(widget)
        assert widget.empty_label.isVisible()


class TestAnimationSegmentPreviewIntegration:
    """Integration tests for animation segment preview."""
    
    @pytest.mark.integration
    def test_segment_preview_with_real_frames(self, qtbot):
        """Test segment preview with realistic frame data."""
        widget = AnimationSegmentPreview()
        qtbot.addWidget(widget)
        
        # Create colored frames to simulate real sprite frames
        frames = []
        colors = [Qt.red, Qt.green, Qt.blue, Qt.yellow, Qt.cyan, Qt.magenta]
        for i in range(12):
            pixmap = QPixmap(64, 64)
            pixmap.fill(colors[i % len(colors)])
            frames.append(pixmap)
        
        widget.set_frames(frames)
        
        # Add realistic segments
        widget.add_segment("Idle", 0, 3, QColor(255, 0, 0))
        widget.add_segment("Walk", 4, 7, QColor(0, 255, 0))
        widget.add_segment("Attack", 8, 11, QColor(0, 0, 255))
        
        # Verify segments were created correctly
        assert len(widget._preview_items) == 3
        
        # Test playback of one segment
        walk_item = widget._preview_items["Walk"]
        walk_item.set_playing(True)
        
        # Simulate a few timer ticks
        for _ in range(3):
            walk_item._update_frame()
        
        # Should have advanced through frames
        assert walk_item._current_frame == 3  # Started at 0, advanced 3 times


if __name__ == '__main__':
    pytest.main([__file__, '-v'])