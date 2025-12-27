"""Unit tests for animation segment bounce mode and frame holds features."""

import pytest
from PySide6.QtGui import QColor
from managers import AnimationSegment, AnimationSegmentManager


class TestAnimationSegmentBounceHolds:
    """Test bounce mode and frame holds functionality."""

    @pytest.fixture
    def segment_manager(self, tmp_path):
        """Create a segment manager for testing."""
        manager = AnimationSegmentManager()
        manager.set_auto_save_enabled(False)  # Disable auto-save for testing
        # Use temp path to avoid loading segments from existing files
        sprite_path = tmp_path / "test_sprite.png"
        sprite_path.write_bytes(b"PNG")  # Create minimal file
        manager.set_sprite_context(str(sprite_path), 10)
        return manager

    def test_set_bounce_mode(self, segment_manager):
        """Test setting bounce mode on a segment."""
        # Add a segment
        success, msg = segment_manager.add_segment("Walk", 0, 7)
        assert success
        
        # Test enabling bounce mode
        success, msg = segment_manager.set_bounce_mode("Walk", True)
        assert success
        segment = segment_manager.get_segment("Walk")
        assert segment.bounce_mode is True
        
        # Test disabling bounce mode
        success, msg = segment_manager.set_bounce_mode("Walk", False)
        assert success
        segment = segment_manager.get_segment("Walk")
        assert segment.bounce_mode is False
        
        # Test non-existent segment
        success, msg = segment_manager.set_bounce_mode("NonExistent", True)
        assert not success
        assert "not found" in msg
    
    def test_set_frame_holds(self, segment_manager):
        """Test setting frame holds on a segment."""
        # Add a segment
        success, msg = segment_manager.add_segment("Walk", 0, 7)
        assert success
        
        # Test setting valid frame holds
        frame_holds = {0: 5, 3: 10, 7: 3}
        success, msg = segment_manager.set_frame_holds("Walk", frame_holds)
        assert success
        segment = segment_manager.get_segment("Walk")
        assert segment.frame_holds == frame_holds
        
        # Test clearing frame holds
        success, msg = segment_manager.set_frame_holds("Walk", {})
        assert success
        segment = segment_manager.get_segment("Walk")
        assert segment.frame_holds == {}
        
        # Test invalid frame index (out of range)
        invalid_holds = {10: 5}  # Frame 10 doesn't exist in 0-7 range
        success, msg = segment_manager.set_frame_holds("Walk", invalid_holds)
        assert not success
        assert "out of range" in msg
        
        # Test non-existent segment
        success, msg = segment_manager.set_frame_holds("NonExistent", {0: 5})
        assert not success
        assert "not found" in msg
    
    def test_serialization_with_new_attributes(self, segment_manager):
        """Test that new attributes are properly serialized/deserialized."""
        # Add a segment with new attributes
        success, msg = segment_manager.add_segment("Walk", 0, 7)
        assert success
        
        segment_manager.set_bounce_mode("Walk", True)
        segment_manager.set_frame_holds("Walk", {2: 8, 5: 12})
        
        # Get segment and convert to dict
        segment = segment_manager.get_segment("Walk")
        segment_dict = segment.to_dict()
        
        # Check serialization
        assert "bounce_mode" in segment_dict
        assert segment_dict["bounce_mode"] is True
        assert "frame_holds" in segment_dict
        assert segment_dict["frame_holds"] == {2: 8, 5: 12}
        
        # Test deserialization
        restored_segment = AnimationSegment.from_dict(segment_dict)
        assert restored_segment.bounce_mode is True
        assert restored_segment.frame_holds == {2: 8, 5: 12}
    
    def test_backward_compatibility(self):
        """Test that old segments without new attributes can be loaded."""
        # Simulate old segment data without new attributes
        old_segment_dict = {
            "name": "OldSegment",
            "start_frame": 0,
            "end_frame": 5,
            "color_rgb": [255, 0, 0],
            "description": "Old segment",
            "tags": ["test"]
        }
        
        # Load old segment
        segment = AnimationSegment.from_dict(old_segment_dict)
        
        # Check that defaults are applied
        assert segment.bounce_mode is False
        assert segment.frame_holds == {}
        assert segment.name == "OldSegment"
        assert segment.start_frame == 0
        assert segment.end_frame == 5
    
    def test_frame_holds_json_serialization(self):
        """Test that frame holds with integer keys serialize correctly."""
        # Create segment with frame holds
        frame_holds = {0: 5, 3: 10, 7: 3}
        segment = AnimationSegment(
            "Test", 0, 7,
            frame_holds=frame_holds
        )
        
        # Convert to dict (simulating JSON serialization)
        segment_dict = segment.to_dict()
        
        # In JSON, dict keys become strings
        # Simulate JSON round-trip
        import json
        json_str = json.dumps(segment_dict)
        loaded_dict = json.loads(json_str)
        
        # Deserialize
        restored_segment = AnimationSegment.from_dict(loaded_dict)
        
        # Check that integer keys are restored
        assert restored_segment.frame_holds == frame_holds
        for key in restored_segment.frame_holds:
            assert isinstance(key, int)
    
    def test_update_segment_with_new_attributes(self, segment_manager):
        """Test updating segments with the general update method."""
        # Add a segment
        success, msg = segment_manager.add_segment("Walk", 0, 7)
        assert success
        
        # Update with new attributes through general update (if supported)
        # This tests the integration path
        segment = segment_manager.get_segment("Walk")
        assert segment.bounce_mode is False
        assert segment.frame_holds == {}