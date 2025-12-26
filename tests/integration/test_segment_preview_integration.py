#!/usr/bin/env python3
"""
Integration tests for animation segment preview functionality.
Tests the complete flow from segment creation to preview display.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt

from sprite_model.core import SpriteModel
from ui.animation_grid_view import AnimationGridView, AnimationSegment
from ui.animation_segment_preview import AnimationSegmentPreview
from core.animation_segment_controller import AnimationSegmentController
from managers import AnimationSegmentManager


class TestSegmentPreviewIntegration:
    """Test segment creation and preview integration."""
    
    @pytest.fixture
    def setup_components(self, qtbot):
        """Set up all components needed for testing."""
        # Create components
        sprite_model = SpriteModel()
        segment_manager = AnimationSegmentManager()
        grid_view = AnimationGridView()
        segment_preview = AnimationSegmentPreview()

        # Add widgets to qtbot
        qtbot.addWidget(grid_view)
        qtbot.addWidget(segment_preview)

        # Create controller with all dependencies (constructor DI)
        segment_controller = AnimationSegmentController(
            segment_manager=segment_manager,
            grid_view=grid_view,
            sprite_model=sprite_model,
            tab_widget=None,  # Not needed for tests
            segment_preview=segment_preview,
        )

        # Connect signals
        grid_view.segmentCreated.connect(segment_controller.create_segment)
        grid_view.segmentDeleted.connect(segment_controller.delete_segment)
        
        # Create test frames
        frames = []
        for i in range(12):
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(i * 20, 255 - i * 20, 128))
            frames.append(pixmap)
        
        # Set frames in sprite model
        sprite_model._sprite_frames = frames
        
        # Set sprite context in segment manager (needed for validation)
        segment_manager.set_sprite_context("test_sprite.png", len(frames))
        
        # Clear any existing segments that might have been loaded
        segment_manager.clear_segments()
        
        # Manually set frames in grid view and preview without syncing existing segments
        grid_view.set_frames(frames)
        segment_preview.set_frames(frames)
        
        return {
            'sprite_model': sprite_model,
            'segment_manager': segment_manager,
            'segment_controller': segment_controller,
            'grid_view': grid_view,
            'segment_preview': segment_preview,
            'frames': frames
        }
    
    def test_segment_appears_in_preview_after_creation(self, qtbot, setup_components):
        """Test that segments appear in the preview panel after creation."""
        grid_view = setup_components['grid_view']
        segment_preview = setup_components['segment_preview']
        segment_manager = setup_components['segment_manager']
        
        # Verify initial state
        assert len(segment_preview._preview_items) == 0
        assert len(segment_manager.get_all_segments()) == 0
        
        # Create a segment
        segment = AnimationSegment("TestWalk", 0, 3, QColor(255, 0, 0))
        grid_view.add_segment(segment)
        grid_view.segmentCreated.emit(segment)
        
        # Verify segment was created in all components
        assert len(segment_manager.get_all_segments()) == 1
        assert "TestWalk" in grid_view._segments
        assert "TestWalk" in segment_preview._preview_items
        
        # Verify preview item has correct properties
        preview_item = segment_preview._preview_items["TestWalk"]
        assert preview_item.segment_name == "TestWalk"
        assert len(preview_item._frames) == 4  # frames 0-3
        assert preview_item.segment_color == QColor(255, 0, 0)
    
    def test_multiple_segments_in_preview(self, qtbot, setup_components):
        """Test that multiple segments can be created and shown in preview."""
        grid_view = setup_components['grid_view']
        segment_preview = setup_components['segment_preview']
        
        # Create multiple segments
        segments_data = [
            ("Idle", 0, 2, QColor(255, 0, 0)),
            ("Walk", 3, 6, QColor(0, 255, 0)),
            ("Run", 7, 10, QColor(0, 0, 255)),
        ]
        
        for name, start, end, color in segments_data:
            segment = AnimationSegment(name, start, end, color)
            grid_view.add_segment(segment)
            grid_view.segmentCreated.emit(segment)
        
        # Verify all segments appear in preview
        assert len(segment_preview._preview_items) == 3
        assert all(name in segment_preview._preview_items for name, _, _, _ in segments_data)
        
        # Verify each preview item
        for name, start, end, color in segments_data:
            preview_item = segment_preview._preview_items[name]
            assert preview_item.segment_name == name
            assert len(preview_item._frames) == end - start + 1
            assert preview_item.segment_color == color
    
    def test_segment_preview_with_name_conflict(self, qtbot, setup_components):
        """Test that segments with name conflicts still appear in preview with renamed names."""
        grid_view = setup_components['grid_view']
        segment_preview = setup_components['segment_preview']
        segment_manager = setup_components['segment_manager']
        
        # Create first segment
        segment1 = AnimationSegment("Attack", 0, 3, QColor(255, 0, 0))
        grid_view.add_segment(segment1)
        grid_view.segmentCreated.emit(segment1)
        
        assert "Attack" in segment_preview._preview_items
        
        # Try to create segment with same name
        segment2 = AnimationSegment("Attack", 4, 7, QColor(0, 255, 0))
        grid_view.add_segment(segment2)
        grid_view.segmentCreated.emit(segment2)
        
        # Should have 2 segments now, with second one renamed
        assert len(segment_preview._preview_items) == 2
        assert "Attack" in segment_preview._preview_items
        
        # Find the renamed segment
        preview_names = list(segment_preview._preview_items.keys())
        renamed_segments = [name for name in preview_names if name.startswith("Attack_") and name != "Attack"]
        assert len(renamed_segments) == 1
        
        # Verify renamed segment has correct frames
        renamed_name = renamed_segments[0]
        preview_item = segment_preview._preview_items[renamed_name]
        assert len(preview_item._frames) == 4  # frames 4-7
    
    def test_segment_deletion_removes_from_preview(self, qtbot, setup_components):
        """Test that deleting a segment removes it from the preview panel."""
        grid_view = setup_components['grid_view']
        segment_preview = setup_components['segment_preview']
        segment_controller = setup_components['segment_controller']
        
        # Create segments
        segment1 = AnimationSegment("Segment1", 0, 3, QColor(255, 0, 0))
        segment2 = AnimationSegment("Segment2", 4, 7, QColor(0, 255, 0))
        
        grid_view.add_segment(segment1)
        grid_view.segmentCreated.emit(segment1)
        grid_view.add_segment(segment2)
        grid_view.segmentCreated.emit(segment2)
        
        assert len(segment_preview._preview_items) == 2
        
        # Delete first segment
        segment_controller.delete_segment("Segment1")
        
        # Verify removal
        assert len(segment_preview._preview_items) == 1
        assert "Segment1" not in segment_preview._preview_items
        assert "Segment2" in segment_preview._preview_items
    
    def test_preview_panel_empty_state(self, qtbot, setup_components):
        """Test that preview panel shows empty state when no segments."""
        segment_preview = setup_components['segment_preview']
        
        # Initially should show empty state
        segment_preview.show()
        qtbot.waitExposed(segment_preview)
        assert segment_preview.empty_label.isVisible()
        
        # Create a segment
        grid_view = setup_components['grid_view']
        segment = AnimationSegment("Test", 0, 3, QColor(255, 0, 0))
        grid_view.add_segment(segment)
        grid_view.segmentCreated.emit(segment)
        
        # Empty state should be hidden
        assert segment_preview.empty_label.isHidden()
        
        # Delete the segment
        segment_controller = setup_components['segment_controller']
        segment_controller.delete_segment("Test")
        
        # Empty state should be visible again
        assert segment_preview.empty_label.isVisible()
    
    def test_segment_preview_after_grid_refresh(self, qtbot, setup_components):
        """Test that segments remain in preview after grid view refresh."""
        grid_view = setup_components['grid_view']
        segment_preview = setup_components['segment_preview']
        segment_controller = setup_components['segment_controller']
        
        # Create segments
        segment = AnimationSegment("Persistent", 0, 5, QColor(128, 128, 255))
        grid_view.add_segment(segment)
        grid_view.segmentCreated.emit(segment)
        
        assert "Persistent" in segment_preview._preview_items
        initial_item = segment_preview._preview_items["Persistent"]
        
        # Refresh grid view
        segment_controller.update_grid_view_frames()
        
        # Segment should still be in preview
        assert "Persistent" in segment_preview._preview_items
        # Note: Item might be recreated during refresh, but should have same properties
        current_item = segment_preview._preview_items["Persistent"]
        assert current_item.segment_name == initial_item.segment_name
        assert len(current_item._frames) == len(initial_item._frames)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])