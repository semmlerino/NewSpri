"""
Integration Tests for Animation Splitting Workflow - Testing the complete user workflow.
Tests the export workflow UX fixes and tab switching behavior that was recently improved.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QTabWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from sprite_viewer import SpriteViewer
from ui.animation_grid_view import AnimationSegment


class TestAnimationSplittingWorkflow:
    """Test complete animation splitting workflows that were recently fixed."""
    
    def test_complete_animation_splitting_workflow(self, qtbot):
        """Test the complete workflow: load sprite → create segments → export."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Ensure we have the animation splitting tab
        tab_widget = viewer.findChild(QTabWidget)
        assert tab_widget is not None
        
        # Find animation splitting tab
        animation_tab_index = -1
        for i in range(tab_widget.count()):
            if "Animation Splitting" in tab_widget.tabText(i):
                animation_tab_index = i
                break
        
        assert animation_tab_index >= 0, "Animation Splitting tab not found"
        
        # Switch to animation splitting tab
        tab_widget.setCurrentIndex(animation_tab_index)
        
        # Get the animation grid view
        animation_grid = viewer._grid_view
        assert animation_grid is not None
        
        # Load real frames using real image factory
        # Note: In a full integration this would come from real sprite loading
        test_frames = []
        colors = [Qt.red, Qt.green, Qt.blue, Qt.yellow, Qt.cyan, Qt.magenta] * 2
        for i in range(12):
            pixmap = QPixmap(32, 32)
            pixmap.fill(colors[i])
            test_frames.append(pixmap)
        
        animation_grid.set_frames(test_frames)
        
        # Simulate user creating animation segments
        segments_created = []
        animation_grid.segmentCreated.connect(lambda seg: segments_created.append(seg))
        
        # Create first segment (Walk cycle)
        animation_grid._selected_frames.update([0, 1, 2, 3])
        with patch('PySide6.QtWidgets.QInputDialog.getText') as mock_input:
            mock_input.return_value = ("Walk", True)
            animation_grid._create_segment_from_selection()
        
        assert len(segments_created) == 1
        assert segments_created[0].name == "Walk"
        
        # Create second segment (Attack)
        animation_grid._clear_selection()
        animation_grid._selected_frames.update([4, 5, 6, 7])
        with patch('PySide6.QtWidgets.QInputDialog.getText') as mock_input:
            mock_input.return_value = ("Attack", True)
            animation_grid._create_segment_from_selection()
        
        assert len(segments_created) == 2
        assert segments_created[1].name == "Attack"
        
        # Verify segments are in the list
        assert animation_grid._segment_list.count() == 2
        
        # Test selecting segment for export (should NOT switch tabs - key fix)
        current_tab = tab_widget.currentIndex()
        
        # Single-click segment (should select but NOT switch tabs)
        animation_grid._segment_list.setCurrentRow(0)
        animation_grid._on_segment_selected("Walk")
        
        # Tab should NOT have changed
        assert tab_widget.currentIndex() == current_tab
        
        # Export button should show segment name
        assert animation_grid._export_btn.isEnabled()
        assert "Walk" in animation_grid._export_btn.text()
    
    def test_export_workflow_tab_behavior(self, qtbot):
        """Test the fixed export workflow tab switching behavior."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        tab_widget = viewer.findChild(QTabWidget)
        animation_grid = viewer._grid_view
        
        # Add test segment
        segment = AnimationSegment("Test_Segment", 0, 3)
        animation_grid.add_segment(segment)
        
        # Find animation splitting tab
        animation_tab_index = -1
        frame_view_tab_index = -1
        for i in range(tab_widget.count()):
            tab_text = tab_widget.tabText(i)
            if "Animation Splitting" in tab_text:
                animation_tab_index = i
            elif "Frame View" in tab_text:
                frame_view_tab_index = i
        
        # Switch to animation splitting tab
        tab_widget.setCurrentIndex(animation_tab_index)
        
        # Test single-click behavior (should NOT switch tabs)
        current_tab = tab_widget.currentIndex()
        animation_grid._on_segment_selected("Test_Segment")
        
        assert tab_widget.currentIndex() == current_tab  # Should stay in Animation Splitting
        
        # Test double-click behavior (should switch to Frame View for preview)
        preview_signals = []
        animation_grid.segmentPreviewRequested.connect(lambda seg: preview_signals.append(seg))
        
        animation_grid._on_segment_double_clicked("Test_Segment")
        
        assert len(preview_signals) == 1
        assert preview_signals[0].name == "Test_Segment"
        # Note: Actual tab switching would be handled by the main viewer
    
    def test_segment_selection_and_export_button_updates(self, qtbot):
        """Test export button updates when segments are selected."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        animation_grid = viewer._grid_view
        
        # Initially export button should be disabled
        assert not animation_grid._export_btn.isEnabled()
        assert animation_grid._export_btn.text() == "Export Selected"
        
        # Add segments
        walk_segment = AnimationSegment("Walk_Cycle", 0, 7)
        attack_segment = AnimationSegment("Attack_Sequence", 8, 15)
        
        animation_grid.add_segment(walk_segment)
        animation_grid.add_segment(attack_segment)
        
        # Select first segment
        animation_grid._segment_list.setCurrentRow(0)
        animation_grid._on_segment_list_selection_changed()
        
        assert animation_grid._export_btn.isEnabled()
        assert "Walk_Cycle" in animation_grid._export_btn.text()
        
        # Select second segment
        animation_grid._segment_list.setCurrentRow(1)
        animation_grid._on_segment_list_selection_changed()
        
        assert animation_grid._export_btn.isEnabled()
        assert "Attack_Sequence" in animation_grid._export_btn.text()
        
        # Clear selection
        animation_grid._segment_list.setCurrentRow(-1)
        animation_grid._on_segment_list_selection_changed()
        
        assert not animation_grid._export_btn.isEnabled()
        assert animation_grid._export_btn.text() == "Export Selected"
    
    def test_export_signal_emission(self, qtbot):
        """Test export signal is emitted with correct segment."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        animation_grid = viewer._grid_view
        
        # Add test segment
        test_segment = AnimationSegment("Export_Test", 5, 10)
        animation_grid.add_segment(test_segment)
        
        # Set up signal spy
        export_signals = []
        animation_grid.exportRequested.connect(lambda seg: export_signals.append(seg))
        
        # Select segment and trigger export
        animation_grid._segment_list.setCurrentRow(0)
        animation_grid._export_selected_segment()
        
        assert len(export_signals) == 1
        assert export_signals[0].name == "Export_Test"
        assert export_signals[0].start_frame == 5
        assert export_signals[0].end_frame == 10
    
    def test_multi_segment_management(self, qtbot):
        """Test managing multiple animation segments."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        animation_grid = viewer._grid_view
        
        # Create multiple segments
        segments = [
            AnimationSegment("Idle", 0, 3),
            AnimationSegment("Walk", 4, 11),
            AnimationSegment("Run", 12, 19),
            AnimationSegment("Jump", 20, 27)
        ]
        
        for segment in segments:
            animation_grid.add_segment(segment)
        
        # Verify all segments are in the list
        assert animation_grid._segment_list.count() == 4
        assert len(animation_grid.get_segments()) == 4
        
        # Test segment deletion
        delete_signals = []
        animation_grid.segmentDeleted.connect(lambda name: delete_signals.append(name))
        
        animation_grid._delete_segment("Walk")
        
        assert len(delete_signals) == 1
        assert delete_signals[0] == "Walk"
        assert animation_grid._segment_list.count() == 3
        assert len(animation_grid.get_segments()) == 3
        
        # Verify Walk segment is gone
        remaining_names = [seg.name for seg in animation_grid.get_segments()]
        assert "Walk" not in remaining_names
        assert "Idle" in remaining_names
        assert "Run" in remaining_names
        assert "Jump" in remaining_names
    
    def test_segment_visualization_updates(self, qtbot):
        """Test that segment visualization updates properly."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        animation_grid = viewer._grid_view
        
        # Load frames first
        test_frames = [QPixmap(32, 32) for _ in range(16)]
        animation_grid.set_frames(test_frames)
        
        # Add segment
        segment = AnimationSegment("Visual_Test", 2, 5)
        animation_grid.add_segment(segment)
        
        # Check that thumbnails have segment markers
        for i in range(2, 6):  # Frames 2-5
            thumbnail = animation_grid._thumbnails[i]
            assert thumbnail._segment_color is not None
            
            if i == 2:  # Start frame
                assert thumbnail._is_segment_start
            elif i == 5:  # End frame
                assert thumbnail._is_segment_end
    
    def test_noncontiguous_selection_warning(self, qtbot):
        """Test warning dialog for non-contiguous frame selections."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        animation_grid = viewer._grid_view
        
        # Load frames
        test_frames = [QPixmap(32, 32) for _ in range(10)]
        animation_grid.set_frames(test_frames)
        
        # Create non-contiguous selection
        animation_grid._selected_frames.update([1, 3, 5, 7])
        
        # Mock the warning dialog to return Yes
        with patch('PySide6.QtWidgets.QMessageBox.question') as mock_question, \
             patch('PySide6.QtWidgets.QInputDialog.getText') as mock_input:
            
            mock_question.return_value = mock_question.return_value.Yes
            mock_input.return_value = ("NonContiguous_Test", True)
            
            signals_received = []
            animation_grid.segmentCreated.connect(lambda seg: signals_received.append(seg))
            
            animation_grid._create_segment_from_selection()
            
            # Should have shown warning dialog
            assert mock_question.called
            warning_call = mock_question.call_args[0]
            assert "non-contiguous" in warning_call[1].lower()
            
            # Should create segment from frame 1 to 7 (inclusive range)
            assert len(signals_received) == 1
            segment = signals_received[0]
            assert segment.start_frame == 1
            assert segment.end_frame == 7


class TestAnimationSplittingErrorHandling:
    """Test error handling in animation splitting workflows."""
    
    def test_export_with_no_selection(self, qtbot):
        """Test export behavior when no segment is selected."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        animation_grid = viewer._grid_view
        
        # Add segment but don't select it
        segment = AnimationSegment("Unselected", 0, 3)
        animation_grid.add_segment(segment)
        
        # Try to export (should do nothing)
        export_signals = []
        animation_grid.exportRequested.connect(lambda seg: export_signals.append(seg))
        
        animation_grid._export_selected_segment()
        
        assert len(export_signals) == 0  # No export should happen
    
    def test_segment_creation_with_empty_selection(self, qtbot):
        """Test segment creation when no frames are selected."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        animation_grid = viewer._grid_view
        
        # Load frames
        test_frames = [QPixmap(32, 32) for _ in range(5)]
        animation_grid.set_frames(test_frames)
        
        # Try to create segment with no selection
        assert len(animation_grid._selected_frames) == 0
        
        signals_received = []
        animation_grid.segmentCreated.connect(lambda seg: signals_received.append(seg))
        
        animation_grid._create_segment_from_selection()
        
        # Should not create any segment
        assert len(signals_received) == 0
    
    def test_duplicate_segment_name_handling(self, qtbot):
        """Test handling of duplicate segment names."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        animation_grid = viewer._grid_view
        
        # Add first segment
        segment1 = AnimationSegment("Duplicate_Name", 0, 3)
        animation_grid.add_segment(segment1)
        
        # Try to rename segment to existing name
        # Note: This would typically be handled by the UI dialog,
        # but we test the underlying logic
        
        # The rename should be rejected or handled gracefully
        # (Implementation depends on specific UI behavior)
        original_count = len(animation_grid.get_segments())
        
        # Simulate renaming attempt
        animation_grid._rename_segment("Duplicate_Name", "Duplicate_Name")
        
        # Should still have same number of segments
        assert len(animation_grid.get_segments()) == original_count


class TestAnimationSplittingPerformance:
    """Test performance aspects of animation splitting."""
    
    def test_large_frame_count_handling(self, qtbot):
        """Test animation splitting with large numbers of frames."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        animation_grid = viewer._grid_view
        
        # Create a large number of frames (simulate large sprite sheet)
        large_frame_count = 200
        test_frames = [QPixmap(32, 32) for _ in range(large_frame_count)]
        
        # This should not hang or crash
        animation_grid.set_frames(test_frames)
        
        assert len(animation_grid._frames) == large_frame_count
        assert len(animation_grid._thumbnails) == large_frame_count
        
        # Test selection on large dataset
        animation_grid._selected_frames.update(range(0, 50))  # Select first 50 frames
        animation_grid._update_selection_display()
        
        # Should handle large selections without performance issues
        assert len(animation_grid._selected_frames) == 50
    
    def test_multiple_segments_performance(self, qtbot):
        """Test performance with many animation segments."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        animation_grid = viewer._grid_view
        
        # Create many segments
        segment_count = 50
        for i in range(segment_count):
            segment = AnimationSegment(f"Segment_{i:02d}", i*4, i*4+3)
            animation_grid.add_segment(segment)
        
        assert len(animation_grid.get_segments()) == segment_count
        assert animation_grid._segment_list.count() == segment_count
        
        # Test segment selection performance
        for i in range(0, segment_count, 5):  # Test every 5th segment
            animation_grid._segment_list.setCurrentRow(i)
            animation_grid._on_segment_list_selection_changed()
            
            assert animation_grid._export_btn.isEnabled()
            assert f"Segment_{i:02d}" in animation_grid._export_btn.text()


class TestRealAnimationSplittingIntegration:
    """Test real animation splitting integration with authentic component systems."""
    
    @pytest.mark.integration
    def test_real_animation_splitting_with_sprite_system(self, real_sprite_system, real_image_factory, real_signal_tester):
        """Test animation splitting workflow with real SpriteModel + AnimationController integration."""
        # Initialize real system
        success = real_sprite_system.initialize_system(frame_count=12, frame_size=(48, 48))
        assert success
        
        # Create real animation frames for splitting
        real_frames = real_image_factory.create_animation_frames(
            count=12, 
            size=(48, 48), 
            animation_type="rotate"
        )
        
        # Update sprite model with real frames
        real_sprite_system.sprite_model._sprite_frames = real_frames
        
        # Connect real signal spies for animation events
        signals = real_sprite_system.get_real_signal_connections()
        fps_spy = real_signal_tester.connect_spy(signals['fps_changed'], 'fps_changed')
        animation_spy = real_signal_tester.connect_spy(signals['animation_started'], 'animation_started')
        
        # Test animation workflow with different frame segments
        controller = real_sprite_system.animation_controller
        
        # Simulate splitting workflow: different FPS for different segments
        # Segment 1: Fast rotation (frames 0-3)
        controller.set_fps(30)  # Fast playback
        assert real_signal_tester.verify_emission('fps_changed', count=1)
        
        fps_args = real_signal_tester.get_signal_args('fps_changed', 0)
        assert fps_args[0] == 30
        
        # Start animation for first segment
        start_success = controller.start_animation()
        assert start_success
        assert real_signal_tester.verify_emission('animation_started', count=1)
        
        # Verify real animation state
        assert controller.is_playing
        assert controller.current_fps == 30
        
        controller.stop_animation()
    
    @pytest.mark.integration  
    def test_real_frame_extraction_for_splitting(self, real_sprite_system, real_image_factory):
        """Test real frame extraction workflow that feeds into animation splitting."""
        # Create real sprite sheet
        sprite_sheet = real_image_factory.create_sprite_sheet(
            frame_count=8,
            frame_size=(32, 32),
            layout="horizontal",
            spacing=2,
            margin=4
        )
        
        # Initialize system
        real_sprite_system.initialize_system(frame_count=8)
        
        # Simulate frame extraction from sprite sheet
        extracted_frames = []
        for i in range(8):
            x = 4 + i * (32 + 2)  # margin + i * (frame_width + spacing)
            y = 4  # margin
            frame = sprite_sheet.copy(x, y, 32, 32)
            extracted_frames.append(frame)
        
        # Update sprite model with extracted frames
        real_sprite_system.sprite_model._sprite_frames = extracted_frames
        
        # Verify extraction quality
        assert len(real_sprite_system.sprite_model.sprite_frames) == 8
        for frame in extracted_frames:
            assert isinstance(frame, QPixmap)
            assert frame.width() == 32
            assert frame.height() == 32
            assert not frame.isNull()
        
        # Test animation with extracted frames
        controller = real_sprite_system.animation_controller
        controller.set_fps(20)
        
        start_success = controller.start_animation()
        assert start_success
        
        assert controller.is_playing
        controller.stop_animation()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])