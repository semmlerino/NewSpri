"""
Unit tests for AnimationSegmentController.

Tests segment creation, naming conflict resolution, export operations,
and grid view synchronization.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch, call
from PySide6.QtCore import QObject
from PySide6.QtGui import QColor

from core.animation_segment_controller import AnimationSegmentController
from managers import AnimationSegment, AnimationSegmentManager


class TestAnimationSegmentController(unittest.TestCase):
    """Test AnimationSegmentController functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use real AnimationSegmentManager instead of mock
        self.segment_manager = AnimationSegmentManager()

        # Create mock dependencies for UI components
        self.mock_grid_view = Mock()
        self.mock_grid_view._segments = {}  # Initialize as empty dict
        self.mock_grid_view._segment_list = Mock()
        self.mock_grid_view.has_segment.return_value = False
        self.mock_sprite_model = Mock()
        self.mock_tab_widget = Mock()

        # Create controller with all dependencies (constructor DI)
        self.controller = AnimationSegmentController(
            segment_manager=self.segment_manager,
            grid_view=self.mock_grid_view,
            sprite_model=self.mock_sprite_model,
            tab_widget=self.mock_tab_widget,
            segment_preview=None,  # Not needed for most tests
        )
    
    # ============================================================================
    # SEGMENT CREATION TESTS
    # ============================================================================
    
    def test_create_segment_success(self):
        """Test successful segment creation."""
        # Arrange - Use temp file for sprite context
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            self.segment_manager.set_sprite_context(tmp.name, 20)
        
            # Use real AnimationSegmentData
            segment = AnimationSegment(
                name="TestSegment",
                start_frame=0,
                end_frame=9,
                color_rgb=(255, 0, 0),
                description="Test segment"
            )
        
            # Act
            success, message = self.controller.create_segment(segment)
            
            # Assert
            self.assertTrue(success)
            self.assertIn("Created animation segment 'TestSegment'", message)
            self.assertIn("10 frames", message)
        
            # Verify segment was actually added to manager
            segments = self.segment_manager.get_all_segments()
            self.assertEqual(len(segments), 1)
            self.assertEqual(segments[0].name, "TestSegment")
    
    def test_create_segment_with_manager_failure(self):
        """Test segment creation with manager returning error."""
        # Arrange - use mock manager that returns error
        mock_manager = Mock()
        mock_manager.add_segment.return_value = (False, "Database error")
        self.controller._segment_manager = mock_manager

        segment = AnimationSegment("TestSegment", 0, 9)

        # Act
        success, message = self.controller.create_segment(segment)

        # Assert
        self.assertFalse(success)
        self.assertIn("Database error", message)
    
    def test_create_segment_name_conflict_resolution(self):
        """Test automatic name conflict resolution."""
        # Arrange - Set up sprite context first
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            self.segment_manager.set_sprite_context(tmp.name, 20)
            
            # First add a segment with the same name
            existing_segment = AnimationSegment(
                name="TestSegment",
                start_frame=10,
                end_frame=19
            )
            self.segment_manager.add_segment(
                existing_segment.name,
                existing_segment.start_frame,
                existing_segment.end_frame,
                QColor(255, 0, 0),
                existing_segment.description
            )
        
            # Now try to add another with same name
            new_segment = AnimationSegment(
                name="TestSegment",
                start_frame=0,
                end_frame=9
            )
            
            # Mock grid view
            self.mock_grid_view._segments = {"TestSegment": new_segment}
            self.mock_grid_view._segment_list = Mock()
            
            # Act
            with patch('time.time', return_value=1234.5678):
                success, message = self.controller.create_segment(new_segment)
            
            # Assert
            self.assertTrue(success)
            self.assertIn("renamed from 'TestSegment' to resolve conflict", message)
            
            # Verify we now have 2 segments
            segments = self.segment_manager.get_all_segments()
            self.assertEqual(len(segments), 2)
            # Note: Grid view interaction via _segment_list.remove_segment is not part of the public API
    
    def test_create_segment_max_retry_failure(self):
        """Test segment creation fails after max retries."""
        # Arrange
        segment = AnimationSegment("TestSegment", 0, 9)
        
        # Mock the segment manager for this test
        mock_segment_manager = Mock()
        mock_segment_manager.add_segment.return_value = (
            False, "Segment 'TestSegment' already exists"
        )
        self.controller._segment_manager = mock_segment_manager
        
        # Mock grid view
        self.mock_grid_view._segments = {"TestSegment": segment}
        
        # Act
        success, message = self.controller.create_segment(segment)
        
        # Assert
        self.assertFalse(success)
        self.assertIn("Please try a different name", message)
        
        # Verify max retries were attempted
        self.assertEqual(
            mock_segment_manager.add_segment.call_count,
            self.controller.MAX_NAME_RETRY_ATTEMPTS + 1
        )
    
    # ============================================================================
    # SEGMENT OPERATIONS TESTS
    # ============================================================================
    
    def test_delete_segment_success(self):
        """Test successful segment deletion."""
        # Arrange - Set up sprite context first
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            self.segment_manager.set_sprite_context(tmp.name, 20)
            
            # First add a segment
            segment = AnimationSegment("TestSegment", 0, 9)
            self.segment_manager.add_segment(
                segment.name,
                segment.start_frame,
                segment.end_frame,
                QColor(255, 0, 0),
                segment.description
            )
            
            # Act
            success, message = self.controller.delete_segment("TestSegment")
            
            # Assert
            self.assertTrue(success)
            self.assertEqual(message, "Deleted animation segment 'TestSegment'")
            
            # Verify segment was actually deleted
            segments = self.segment_manager.get_all_segments()
            self.assertEqual(len(segments), 0)
    
    def test_delete_segment_failure(self):
        """Test failed segment deletion."""
        # Arrange - Try to delete non-existent segment
        # The real manager will return False for non-existent segment
        
        # Act
        success, message = self.controller.delete_segment("NonExistentSegment")
        
        # Assert
        self.assertFalse(success)
        self.assertEqual(message, "Failed to delete segment 'NonExistentSegment'")
    
    def test_select_segment(self):
        """Test segment selection."""
        # Arrange - Use real segment data
        segment = AnimationSegment("TestSegment", 5, 15)
        signal_spy = Mock()
        self.controller.statusMessage.connect(signal_spy)
        
        # Act
        self.controller.select_segment(segment)
        
        # Assert
        signal_spy.assert_called_once()
        args = signal_spy.call_args[0]
        self.assertIn("Selected segment 'TestSegment'", args[0])
        self.assertIn("frames 5-15", args[0])
    
    def test_preview_segment(self):
        """Test segment preview."""
        # Arrange - Use real segment data
        segment = AnimationSegment("TestSegment", 10, 20)
        signal_spy = Mock()
        self.controller.statusMessage.connect(signal_spy)
        
        # Act
        self.controller.preview_segment(segment)
        
        # Assert
        self.mock_sprite_model.set_current_frame.assert_called_once_with(10)
        signal_spy.assert_called_once()
        args = signal_spy.call_args[0]
        self.assertIn("Segment 'TestSegment' selected", args[0])
    
    # ============================================================================
    # SEGMENT EXPORT TESTS
    # ============================================================================
    
    @patch('export.ExportDialog')
    @patch('core.animation_segment_controller.QMessageBox')
    def test_export_segment_success(self, mock_msgbox, mock_dialog_class):
        """Test successful segment export."""
        # Arrange
        segment = AnimationSegment("TestSegment", 0, 4)
        frames = [Mock() for _ in range(10)]
        segment_frames = frames[0:5]
        
        self.mock_sprite_model.get_all_frames.return_value = frames
        
        # Mock segment manager for this test
        mock_segment_manager = Mock()
        mock_segment_manager.extract_frames_for_segment.return_value = segment_frames
        self.controller._segment_manager = mock_segment_manager
        
        # Mock dialog
        mock_dialog = Mock()
        mock_dialog.exec.return_value = 1  # QDialog.Accepted
        mock_dialog_class.return_value = mock_dialog
        
        # Act
        self.controller.export_segment(segment, Mock())
        
        # Assert
        self.mock_sprite_model.get_all_frames.assert_called_once()
        mock_segment_manager.extract_frames_for_segment.assert_called_once_with(
            "TestSegment", frames
        )
        
        # Verify dialog creation
        mock_dialog_class.assert_called_once()
        mock_dialog.set_sprites.assert_called_once_with(segment_frames)
        mock_dialog.exportRequested.connect.assert_called_once()
    
    @patch('core.animation_segment_controller.QMessageBox')
    def test_export_segment_no_frames(self, mock_msgbox):
        """Test export with no frames available."""
        # Arrange
        segment = AnimationSegment("TestSegment", 0, 4)
        self.mock_sprite_model.get_all_frames.return_value = []
        
        # Mock segment manager for this test
        mock_segment_manager = Mock()
        mock_segment_manager.extract_frames_for_segment.return_value = []
        self.controller._segment_manager = mock_segment_manager
        
        # Act
        self.controller.export_segment(segment, Mock())
        
        # Assert
        mock_msgbox.warning.assert_called_once()
        args = mock_msgbox.warning.call_args[0]
        self.assertEqual(args[1], "Export Error")
        self.assertIn("No frames available", args[2])
    
    # ============================================================================
    # GRID VIEW SYNCHRONIZATION TESTS
    # ============================================================================
    
    def test_update_grid_view_frames_with_frames(self):
        """Test updating grid view frame thumbnails without mutating context."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            frames = [Mock() for _ in range(5)]
            self.mock_sprite_model.get_all_frames.return_value = frames
            self.mock_sprite_model.file_path = tmp.name

            # Act
            self.controller.update_grid_view_frames()

            # Assert
            self.mock_grid_view.set_frames.assert_called_once_with(frames)
            # Context changes are handled by set_sprite_context_and_sync().
            assert self.segment_manager._sprite_sheet_path == ""
    
    def test_update_grid_view_frames_no_frames(self):
        """Test updating grid view with no frames."""
        # Arrange
        self.mock_sprite_model.get_all_frames.return_value = []
        self.mock_sprite_model.file_path = ""

        # Act
        self.controller.update_grid_view_frames()

        # Assert
        self.mock_grid_view.set_frames.assert_called_once_with([])

    def test_on_tab_changed_to_animation_splitting(self):
        """Test tab change to animation splitting tab."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            self.mock_sprite_model.file_path = tmp.name
            self.mock_sprite_model.get_all_frames.return_value = [Mock()]

            # Act
            self.controller.on_tab_changed(1)  # Animation splitting tab

            # Assert
            self.mock_grid_view.set_frames.assert_called_once()
            self.mock_grid_view.sync_segments_with_manager.assert_called_once_with(
                self.segment_manager
            )

    def test_set_sprite_context_and_sync(self):
        """Test context switch and overlay sync happen atomically."""
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            self.mock_sprite_model.file_path = tmp.name

            self.controller.set_sprite_context_and_sync(tmp.name, 12)

            self.assertEqual(self.segment_manager._sprite_sheet_path, tmp.name)
            self.assertEqual(self.segment_manager._max_frames, 12)
            self.mock_grid_view.sync_segments_with_manager.assert_called_once_with(
                self.segment_manager
            )
    
    def test_on_tab_changed_to_other_tab(self):
        """Test tab change to non-animation splitting tab."""
        # Act
        self.controller.on_tab_changed(0)  # Frame view tab
        
        # Assert
        self.mock_grid_view.set_frames.assert_not_called()


if __name__ == '__main__':
    unittest.main()
