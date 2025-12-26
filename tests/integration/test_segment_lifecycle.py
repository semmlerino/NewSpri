"""
Integration tests for complete segment lifecycle.
Tests the end-to-end flow from segment creation through persistence and reload.
"""

import json
import pytest
from pathlib import Path
from PySide6.QtGui import QPixmap, QColor

from managers import AnimationSegmentManager


class TestSegmentLifecycleEndToEnd:
    """Test complete segment create → save → reload cycle."""

    @pytest.fixture
    def temp_sprite_path(self, tmp_path, qapp):
        """Create a temporary sprite sheet path."""
        sprite_path = tmp_path / "test_sprite.png"
        # Create a simple sprite sheet
        pixmap = QPixmap(256, 64)
        pixmap.fill(QColor(128, 128, 128))
        pixmap.save(str(sprite_path))
        return sprite_path

    @pytest.fixture
    def segment_manager(self):
        """Create a fresh segment manager for each test."""
        return AnimationSegmentManager()

    def test_segment_persists_after_reload(self, temp_sprite_path, segment_manager, tmp_path):
        """Create segment, save, simulate app restart, verify loaded."""
        # 1. Set up sprite context
        segment_manager.set_sprite_context(str(temp_sprite_path), frame_count=8)

        # 2. Create segment using correct API
        success, message = segment_manager.add_segment(
            name="WalkCycle",
            start_frame=0,
            end_frame=3,
            color=QColor(255, 0, 0)
        )
        assert success, f"Failed to add segment: {message}"

        # 3. Verify segment exists
        assert segment_manager.get_segment("WalkCycle") is not None

        # 4. Save segments explicitly
        segment_manager.save_segments_to_file()

        # 5. Verify .sprite_segments directory and file were created
        segments_dir = temp_sprite_path.parent / ".sprite_segments"
        assert segments_dir.exists(), ".sprite_segments directory should be created"

        segments_file = segments_dir / f"{temp_sprite_path.stem}_segments.json"
        assert segments_file.exists(), "Segments JSON file should be created"

        # 6. Create new manager instance (simulates app restart)
        new_manager = AnimationSegmentManager()
        new_manager.set_sprite_context(str(temp_sprite_path), frame_count=8)

        # 7. Verify segment was reloaded
        reloaded_segment = new_manager.get_segment("WalkCycle")
        assert reloaded_segment is not None, "Segment should be reloaded"
        assert reloaded_segment.start_frame == 0
        assert reloaded_segment.end_frame == 3

    def test_segment_deletion_removes_from_disk(self, temp_sprite_path, segment_manager):
        """Verify deleted segments don't persist."""
        # 1. Create and save segment
        segment_manager.set_sprite_context(str(temp_sprite_path), frame_count=8)

        segment_manager.add_segment("ToBeDeleted", 0, 2, QColor(0, 255, 0))
        segment_manager.save_segments_to_file()

        # 2. Verify it was saved
        segments_dir = temp_sprite_path.parent / ".sprite_segments"
        segments_file = segments_dir / f"{temp_sprite_path.stem}_segments.json"
        assert segments_file.exists()

        with open(segments_file) as f:
            data = json.load(f)
            assert len(data.get("segments", [])) == 1

        # 3. Delete segment
        success = segment_manager.remove_segment("ToBeDeleted")
        assert success

        # 4. Save again
        segment_manager.save_segments_to_file()

        # 5. Verify segment is removed from disk
        with open(segments_file) as f:
            data = json.load(f)
            assert len(data.get("segments", [])) == 0

        # 6. Verify new manager doesn't load deleted segment
        new_manager = AnimationSegmentManager()
        new_manager.set_sprite_context(str(temp_sprite_path), frame_count=8)
        assert new_manager.get_segment("ToBeDeleted") is None

    def test_corrupted_segment_json_recovery(self, temp_sprite_path, segment_manager):
        """Verify graceful handling of malformed .sprite_segments/ files."""
        segment_manager.set_sprite_context(str(temp_sprite_path), frame_count=8)

        # 1. Create segments directory and write corrupted JSON
        segments_dir = temp_sprite_path.parent / ".sprite_segments"
        segments_dir.mkdir(exist_ok=True)

        segments_file = segments_dir / f"{temp_sprite_path.stem}_segments.json"
        with open(segments_file, 'w') as f:
            f.write("{ invalid json content }")

        # 2. Create new manager and set context (should not crash)
        new_manager = AnimationSegmentManager()

        # This should not raise an exception
        try:
            new_manager.set_sprite_context(str(temp_sprite_path), frame_count=8)
        except json.JSONDecodeError:
            pytest.fail("Manager should handle corrupted JSON gracefully")

        # 3. Manager should have no segments (corrupted file ignored)
        assert len(new_manager.get_all_segments()) == 0

    def test_multiple_segments_persist_correctly(self, temp_sprite_path, segment_manager):
        """Test that multiple segments are all saved and loaded correctly."""
        segment_manager.set_sprite_context(str(temp_sprite_path), frame_count=16)

        # Create multiple segments
        segments_data = [
            ("Idle", 0, 3, QColor(255, 0, 0)),
            ("Walk", 4, 7, QColor(0, 255, 0)),
            ("Run", 8, 11, QColor(0, 0, 255)),
            ("Jump", 12, 15, QColor(255, 255, 0)),
        ]

        for name, start, end, color in segments_data:
            segment_manager.add_segment(name, start, end, color)

        segment_manager.save_segments_to_file()

        # Reload with new manager
        new_manager = AnimationSegmentManager()
        new_manager.set_sprite_context(str(temp_sprite_path), frame_count=16)

        # Verify all segments loaded
        assert len(new_manager.get_all_segments()) == 4

        for name, start, end, color in segments_data:
            segment = new_manager.get_segment(name)
            assert segment is not None, f"Segment {name} not found"
            assert segment.start_frame == start
            assert segment.end_frame == end


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
