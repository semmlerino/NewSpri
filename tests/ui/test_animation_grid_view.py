"""
UI Tests for AnimationGridView - Missing test coverage for critical animation splitting component.
Tests the multi-frame selection behavior that was recently fixed.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QMouseEvent

from ui.animation_grid_view import AnimationGridView, FrameThumbnail, AnimationSegment


class TestFrameThumbnail:
    """Test FrameThumbnail component functionality."""
    
    def test_thumbnail_creation(self, qtbot):
        """Test basic thumbnail creation and setup."""
        pixmap = QPixmap(32, 32)
        thumbnail = FrameThumbnail(5, pixmap)
        qtbot.addWidget(thumbnail)
        
        assert thumbnail.frame_index == 5
        assert thumbnail._thumbnail_size == 80  # Default size
        assert not thumbnail._selected
        assert thumbnail._drag_threshold == 8  # Fixed value (was 3)
    
    def test_selection_state_management(self, qtbot):
        """Test selection state changes."""
        pixmap = QPixmap(32, 32)
        thumbnail = FrameThumbnail(0, pixmap)
        qtbot.addWidget(thumbnail)
        
        # Test initial state
        assert not thumbnail._selected
        
        # Test selection
        thumbnail.set_selected(True)
        assert thumbnail._selected
        
        # Test deselection
        thumbnail.set_selected(False)
        assert not thumbnail._selected
    
    def test_keyboard_modifier_conversion(self, qtbot):
        """Test safe keyboard modifier conversion across PySide6 versions."""
        pixmap = QPixmap(32, 32)
        thumbnail = FrameThumbnail(0, pixmap)
        qtbot.addWidget(thumbnail)
        
        signal_received = []
        thumbnail.clicked.connect(lambda idx, mods: signal_received.append((idx, mods)))
        
        # Test the modifier conversion logic directly by simulating the actual event handling
        # Create a real QMouseEvent (this tests the actual PySide6 behavior)
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QMouseEvent
        
        pos = QPointF(10, 10)
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            pos, pos, pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.ControlModifier  # Include Ctrl modifier
        )
        
        # This should work with the actual modifier conversion logic
        thumbnail.mousePressEvent(event)
        
        assert len(signal_received) == 1
        assert signal_received[0][0] == 0  # frame_index
        # Should have extracted the Ctrl modifier correctly
        assert signal_received[0][1] != 0  # Should not be empty
    
    def test_drag_threshold_behavior_real_events(self, qtbot, real_event_helpers):
        """Test drag detection threshold with REAL Qt events (key fix - was 3, now 8 pixels)."""
        pixmap = QPixmap(32, 32)
        thumbnail = FrameThumbnail(0, pixmap)
        qtbot.addWidget(thumbnail)
        
        drag_signals = []
        thumbnail.dragStarted.connect(lambda idx: drag_signals.append(idx))
        
        # Test 1: Movement UNDER threshold (should NOT trigger drag)
        # Create real mouse press event
        press_event = real_event_helpers.create_mouse_press(10, 10, Qt.LeftButton)
        thumbnail.mousePressEvent(press_event)
        
        # Create real mouse move event - under 8 pixel threshold
        move_event_small = real_event_helpers.create_mouse_move(13, 13, Qt.LeftButton)
        thumbnail.mouseMoveEvent(move_event_small)
        
        # Calculate distance: |13-10| + |13-10| = 6 pixels (< 8 threshold)
        distance = real_event_helpers.calculate_manhattan_distance(QPoint(10, 10), QPoint(13, 13))
        assert distance == 6  # Verify our calculation
        assert len(drag_signals) == 0  # Should NOT trigger drag
        
        # Test 2: Movement OVER threshold (SHOULD trigger drag)
        drag_signals.clear()
        
        # Reset for new test
        press_event = real_event_helpers.create_mouse_press(10, 10, Qt.LeftButton)
        thumbnail.mousePressEvent(press_event)
        
        # Create real mouse move event - over 8 pixel threshold
        move_event_large = real_event_helpers.create_mouse_move(19, 19, Qt.LeftButton)
        thumbnail.mouseMoveEvent(move_event_large)
        
        # Calculate distance: |19-10| + |19-10| = 18 pixels (> 8 threshold)
        distance = real_event_helpers.calculate_manhattan_distance(QPoint(10, 10), QPoint(19, 19))
        assert distance == 18  # Verify our calculation
        assert len(drag_signals) == 1  # SHOULD trigger drag
        assert drag_signals[0] == 0  # Correct frame_index
        
        # Test 3: Edge case - exactly at threshold boundary
        drag_signals.clear()
        
        press_event = real_event_helpers.create_mouse_press(10, 10, Qt.LeftButton)
        thumbnail.mousePressEvent(press_event)
        
        # Move exactly 8 pixels (should trigger since > threshold)
        move_event_boundary = real_event_helpers.create_mouse_move(14, 14, Qt.LeftButton)
        thumbnail.mouseMoveEvent(move_event_boundary)
        
        # Distance: |14-10| + |14-10| = 8 pixels (= threshold, should NOT trigger)
        distance = real_event_helpers.calculate_manhattan_distance(QPoint(10, 10), QPoint(14, 14))
        assert distance == 8
        assert len(drag_signals) == 0  # Should not trigger at exactly threshold
        
        # Test 4: Boundary + 1 (should trigger)
        drag_signals.clear()
        
        press_event = real_event_helpers.create_mouse_press(10, 10, Qt.LeftButton)
        thumbnail.mousePressEvent(press_event)
        
        # Move 9 pixels (should trigger since > 8 threshold)
        move_event_over = real_event_helpers.create_mouse_move(14, 15, Qt.LeftButton)
        thumbnail.mouseMoveEvent(move_event_over)
        
        distance = real_event_helpers.calculate_manhattan_distance(QPoint(10, 10), QPoint(14, 15))
        assert distance == 9
        assert len(drag_signals) == 1  # Should trigger
    
    
    def test_real_click_behavior_with_modifiers(self, qtbot, real_event_helpers, real_signal_tester):
        """Test real mouse click behavior with keyboard modifiers using real Qt events."""
        pixmap = QPixmap(32, 32)
        thumbnail = FrameThumbnail(2, pixmap)
        qtbot.addWidget(thumbnail)
        
        # Test 1: Normal click (no modifiers)
        click_spy = real_signal_tester.connect_spy(thumbnail.clicked, 'thumbnail_clicked')
        
        real_event_helpers.simulate_real_click(thumbnail, QPoint(16, 16), qtbot)
        
        # Verify real signal emission
        assert real_signal_tester.verify_emission('thumbnail_clicked', count=1)
        args = real_signal_tester.get_signal_args('thumbnail_clicked', 0)
        assert len(args) >= 1  # Should have at least frame_index
        assert args[0] == 2  # frame_index
        
        # Test 2: Ctrl+click on separate thumbnail
        pixmap2 = QPixmap(32, 32)
        thumbnail2 = FrameThumbnail(3, pixmap2)
        qtbot.addWidget(thumbnail2)
        
        ctrl_click_spy = real_signal_tester.connect_spy(thumbnail2.clicked, 'ctrl_clicked')
        
        ctrl_event = real_event_helpers.create_mouse_press(16, 16, Qt.LeftButton, Qt.ControlModifier)
        thumbnail2.mousePressEvent(ctrl_event)
        
        assert real_signal_tester.verify_emission('ctrl_clicked', count=1)
        ctrl_args = real_signal_tester.get_signal_args('ctrl_clicked', 0)
        assert len(ctrl_args) >= 1
        assert ctrl_args[0] == 3  # frame_index
        if len(ctrl_args) > 1:
            assert ctrl_args[1] != 0  # Should have Ctrl modifier
    
    def test_real_drag_sequence_complete(self, qtbot, real_event_helpers, real_signal_tester):
        """Test complete drag sequence with real Qt events."""
        pixmap = QPixmap(32, 32)
        thumbnail = FrameThumbnail(4, pixmap)
        qtbot.addWidget(thumbnail)
        
        # Connect real signal spies
        drag_spy = real_signal_tester.connect_spy(thumbnail.dragStarted, 'drag_started')
        
        # Simulate complete real drag sequence
        start_pos = QPoint(10, 10)
        end_pos = QPoint(25, 25)  # 30 pixel Manhattan distance > 8 threshold
        
        real_event_helpers.simulate_real_drag(thumbnail, start_pos, end_pos, qtbot)
        
        # Verify drag signal was emitted
        assert real_signal_tester.verify_emission('drag_started', count=1, timeout=500)
        args = real_signal_tester.get_signal_args('drag_started', 0)
        assert len(args) == 1
        assert args[0] == 4  # frame_index


class TestRealImageIntegration:
    """Test AnimationGridView with real image data instead of mock pixmaps."""
    
    def test_grid_with_real_sprite_frames(self, qtbot, real_image_factory):
        """Test grid view with real animated sprite frames."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Create real animation frames using the image factory
        real_frames = real_image_factory.create_animation_frames(
            count=8, 
            size=(48, 48), 
            animation_type="rotate"
        )
        
        # Load real frames into grid
        grid_view.set_frames(real_frames)
        
        # Verify real frames are loaded
        assert len(grid_view._frames) == 8
        assert len(grid_view._thumbnails) == 8
        
        # Verify frames are real QPixmap objects
        for frame in grid_view._frames:
            assert isinstance(frame, QPixmap)
            assert frame.width() == 48
            assert frame.height() == 48
            assert not frame.isNull()
    
    def test_segment_creation_with_real_sprite_sheet(self, qtbot, real_image_factory, real_signal_tester):
        """Test segment creation using a real sprite sheet."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Create a real sprite sheet
        sprite_sheet_frames = []
        sprite_sheet = real_image_factory.create_sprite_sheet(
            frame_count=6,
            frame_size=(32, 32),
            layout="horizontal",
            spacing=2,
            margin=1
        )
        
        # Extract frames from the sprite sheet (normally done by sprite model)
        # For this test, create individual frames 
        for i in range(6):
            frame = real_image_factory.create_numbered_frame(32, 32, i)
            sprite_sheet_frames.append(frame)
        
        grid_view.set_frames(sprite_sheet_frames)
        
        # Connect real signal spy
        segment_spy = real_signal_tester.connect_spy(grid_view.segmentCreated, 'segment_created')
        
        # Select frames for segment
        grid_view._selected_frames.update([1, 2, 3])
        
        # Create segment with real selection
        with patch('PySide6.QtWidgets.QInputDialog.getText') as mock_input:
            mock_input.return_value = ("Real_Animation", True)
            grid_view._create_segment_from_selection()
        
        # Verify real segment creation
        assert real_signal_tester.verify_emission('segment_created', count=1)
        args = real_signal_tester.get_signal_args('segment_created', 0)
        segment = args[0]
        assert segment.name == "Real_Animation"
        assert segment.start_frame == 1
        assert segment.end_frame == 3
    
    def test_ccl_test_sprite_integration(self, qtbot, real_image_factory, ark_sprite_fixture):
        """Test integration with CCL test sprite and Ark.png if available."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Test with generated CCL sprite
        ccl_sprite = real_image_factory.create_ccl_test_sprite()
        assert isinstance(ccl_sprite, QPixmap)
        assert ccl_sprite.width() == 200
        assert ccl_sprite.height() == 100
        
        # Create mock frames from CCL sprite regions (simulates CCL extraction)
        mock_ccl_frames = []
        sprite_regions = [
            (10, 10, 30, 30),   # Red sprite
            (50, 10, 25, 35),   # Green sprite  
            (85, 15, 20, 25),   # Blue sprite
            (115, 5, 35, 40),   # Yellow sprite
            (160, 20, 30, 25)   # Cyan sprite
        ]
        
        for x, y, w, h in sprite_regions:
            frame = ccl_sprite.copy(x, y, w, h)
            mock_ccl_frames.append(frame)
        
        grid_view.set_frames(mock_ccl_frames)
        
        assert len(grid_view._frames) == 5
        assert all(not frame.isNull() for frame in grid_view._frames)
        
        # Test Ark.png availability for future CCL testing
        if ark_sprite_fixture['exists']:
            # Ark.png is available for real CCL testing
            assert ark_sprite_fixture['path'] is not None
            print(f"✅ Ark.png available at: {ark_sprite_fixture['path']}")
        else:
            print("⚠️  Ark.png not found - CCL tests will use generated sprites")


class TestAnimationGridView:
    """Test AnimationGridView main component functionality."""
    
    def test_grid_view_creation(self, qtbot):
        """Test basic grid view creation."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        assert grid_view._grid_columns == 8  # Default columns
        assert grid_view._thumbnail_size == 80  # Default thumbnail size
        assert len(grid_view._selected_frames) == 0  # No initial selection
    
    def test_frame_loading(self, qtbot):
        """Test loading frames into the grid."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Create test frames
        test_frames = [QPixmap(32, 32) for _ in range(6)]
        
        grid_view.set_frames(test_frames)
        
        assert len(grid_view._frames) == 6
        assert len(grid_view._thumbnails) == 6
    
    def test_selection_modes(self, qtbot):
        """Test different selection modes that were recently fixed."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load test frames
        test_frames = [QPixmap(32, 32) for _ in range(8)]
        grid_view.set_frames(test_frames)
        
        # Test normal click selection
        grid_view._on_frame_clicked(3, 0)  # No modifiers
        assert 3 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 1
        
        # Test Ctrl+click toggle (add to selection)
        grid_view._on_frame_clicked(5, Qt.ControlModifier.value)
        assert 3 in grid_view._selected_frames
        assert 5 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 2
        
        # Test Ctrl+click toggle (remove from selection)
        grid_view._on_frame_clicked(3, Qt.ControlModifier.value)
        assert 3 not in grid_view._selected_frames
        assert 5 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 1
        
        # Test Shift+click range selection
        grid_view._last_clicked_frame = 5
        grid_view._on_frame_clicked(7, Qt.ShiftModifier.value)
        assert 5 in grid_view._selected_frames
        assert 6 in grid_view._selected_frames
        assert 7 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 3
    
    def test_drag_selection_state_preservation(self, qtbot):
        """Test drag selection preserves existing selections (key fix)."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load test frames
        test_frames = [QPixmap(32, 32) for _ in range(10)]
        grid_view.set_frames(test_frames)
        
        # Establish initial selection
        grid_view._selected_frames.update([1, 3, 8])
        grid_view._update_selection_display()
        
        # Start drag from selected frame (should preserve selection)
        grid_view._on_drag_started(3)
        assert hasattr(grid_view, '_pre_drag_selection')
        assert 1 in grid_view._pre_drag_selection
        assert 3 in grid_view._pre_drag_selection
        assert 8 in grid_view._pre_drag_selection
        
        # Update drag selection
        grid_view._update_drag_selection(3, 5)
        
        # Should have pre-drag selection plus drag range
        expected_frames = {1, 3, 4, 5, 8}  # Pre-drag {1,3,8} + drag range {3,4,5}
        assert grid_view._selected_frames == expected_frames
    
    def test_segment_creation(self, qtbot):
        """Test creating animation segments from selection."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load test frames
        test_frames = [QPixmap(32, 32) for _ in range(8)]
        grid_view.set_frames(test_frames)
        
        # Select range of frames
        grid_view._selected_frames.update([2, 3, 4, 5])
        
        # Mock input dialog for segment name
        with patch('PySide6.QtWidgets.QInputDialog.getText') as mock_input:
            mock_input.return_value = ("Walk_Cycle", True)
            
            signals_received = []
            grid_view.segmentCreated.connect(lambda seg: signals_received.append(seg))
            
            grid_view._create_segment_from_selection()
            
            assert len(signals_received) == 1
            segment = signals_received[0]
            assert segment.name == "Walk_Cycle"
            assert segment.start_frame == 2
            assert segment.end_frame == 5
            assert segment.frame_count == 4
    
    def test_export_button_state_management(self, qtbot):
        """Test export button shows segment names (recent fix)."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Initially export button should be disabled
        assert not grid_view._export_btn.isEnabled()
        assert grid_view._export_btn.text() == "Export Selected"
        
        # Add a segment
        segment = AnimationSegment("Attack", 0, 3)
        grid_view.add_segment(segment)
        
        # Simulate selecting the segment in the list
        grid_view._segment_list.addItem("Attack")
        grid_view._segment_list.setCurrentRow(0)
        grid_view._on_segment_list_selection_changed()
        
        # Export button should now be enabled and show segment name
        assert grid_view._export_btn.isEnabled()
        assert "Attack" in grid_view._export_btn.text()
    
    def test_contiguous_vs_noncontiguous_selection(self, qtbot):
        """Test handling of contiguous vs non-contiguous selections."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Test contiguous selection
        contiguous_frames = [2, 3, 4, 5]
        assert grid_view._is_contiguous_selection(contiguous_frames)
        
        # Test non-contiguous selection
        noncontiguous_frames = [1, 3, 5, 7]
        assert not grid_view._is_contiguous_selection(noncontiguous_frames)
        
        # Test single frame
        single_frame = [4]
        assert grid_view._is_contiguous_selection(single_frame)
        
        # Test empty selection
        assert not grid_view._is_contiguous_selection([])


class TestAnimationSegment:
    """Test AnimationSegment data class."""
    
    def test_segment_creation(self):
        """Test creating animation segments."""
        segment = AnimationSegment("Walk", 0, 7)
        
        assert segment.name == "Walk"
        assert segment.start_frame == 0
        assert segment.end_frame == 7
        assert segment.frame_count == 8
        assert segment.color is not None  # Should auto-generate color
    
    def test_segment_frame_count_calculation(self):
        """Test frame count calculation."""
        # Single frame
        single = AnimationSegment("Idle", 5, 5)
        assert single.frame_count == 1
        
        # Multiple frames
        multi = AnimationSegment("Run", 10, 17)
        assert multi.frame_count == 8


class TestSelectionUIInteraction:
    """Test UI interaction patterns for selection (integration tests)."""
    
    def test_selection_control_button_states(self, qtbot):
        """Test selection control buttons enable/disable properly."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load frames
        test_frames = [QPixmap(32, 32) for _ in range(5)]
        grid_view.set_frames(test_frames)
        
        # Initially no selection - buttons disabled
        assert not grid_view._create_segment_btn.isEnabled()
        assert not grid_view._clear_selection_btn.isEnabled()
        
        # Make selection - buttons should enable
        grid_view._selected_frames.add(2)
        grid_view._update_selection_controls()
        
        assert grid_view._create_segment_btn.isEnabled()
        assert grid_view._clear_selection_btn.isEnabled()
        assert "1 frame" in grid_view._create_segment_btn.text()
        
        # Add more frames - button text should update
        grid_view._selected_frames.update([2, 3, 4])
        grid_view._update_selection_controls()
        
        assert "frames 2-4" in grid_view._create_segment_btn.text()
    
    def test_clear_selection_cleanup(self, qtbot):
        """Test selection clearing cleans up all state properly."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Set up state
        grid_view._selected_frames.update([1, 2, 3])
        grid_view._last_clicked_frame = 2
        grid_view._is_dragging = True
        grid_view._pre_drag_selection = {1, 2}
        
        # Clear selection
        grid_view._clear_selection()
        
        # Verify complete cleanup
        assert len(grid_view._selected_frames) == 0
        assert grid_view._last_clicked_frame is None
        assert not grid_view._is_dragging
        assert not hasattr(grid_view, '_pre_drag_selection')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])