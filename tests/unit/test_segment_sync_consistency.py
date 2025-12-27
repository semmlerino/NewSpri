"""
Tests for segment synchronization between AnimationGridView and AnimationSegmentManager.

Covers:
- Sync after loading segments from file
- Sync after creating segments
- Sync after deleting segments
- Sync after renaming segments
- Sync after updating segment properties (bounce mode, frame holds)
- Bidirectional consistency between manager and grid view
- Concurrent modification scenarios
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from PySide6.QtGui import QColor

from managers.animation_segment_manager import AnimationSegmentManager, AnimationSegmentData
from ui.animation_grid_view import AnimationGridView, AnimationSegment

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


# Mark all tests in this module as requiring Qt
pytestmark = pytest.mark.requires_qt


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def segment_manager(tmp_path: Path) -> AnimationSegmentManager:
    """Create a segment manager with auto-save disabled for testing."""
    manager = AnimationSegmentManager()
    manager.set_auto_save_enabled(False)
    # Set sprite context to allow segment validation (need max_frames > 0)
    # Use a fake path that doesn't exist (auto-save is disabled anyway)
    manager._sprite_sheet_path = str(tmp_path / "test_sprite.png")
    manager._max_frames = 16  # Match grid_view frame count
    return manager


@pytest.fixture
def grid_view(qapp) -> AnimationGridView:
    """Create a grid view for testing."""
    view = AnimationGridView()
    # Create mock frames
    mock_frames = [MagicMock() for _ in range(16)]
    view.set_frames(mock_frames)
    return view


@pytest.fixture
def sample_segments() -> list[dict]:
    """Sample segment data for testing."""
    return [
        {"name": "Walk", "start": 0, "end": 3, "color": QColor(255, 0, 0)},
        {"name": "Run", "start": 4, "end": 7, "color": QColor(0, 255, 0)},
        {"name": "Jump", "start": 8, "end": 11, "color": QColor(0, 0, 255)},
        {"name": "Idle", "start": 12, "end": 15, "color": QColor(255, 255, 0)},
    ]


# ============================================================================
# Sync After Load Tests
# ============================================================================


class TestSyncAfterLoad:
    """Tests for sync_segments_with_manager after loading segments."""

    def test_sync_empty_manager_clears_grid(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Syncing with empty manager should clear grid view segments."""
        # Add a segment directly to grid view
        grid_view._segments["Test"] = AnimationSegment("Test", 0, 3, QColor(255, 0, 0))

        # Sync with empty manager
        grid_view.sync_segments_with_manager(segment_manager)

        # Grid view should be empty
        assert len(grid_view._segments) == 0

    def test_sync_populates_grid_from_manager(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView,
        sample_segments: list[dict]
    ) -> None:
        """Syncing should populate grid view with all manager segments."""
        # Add segments to manager
        for seg in sample_segments:
            segment_manager.add_segment(seg["name"], seg["start"], seg["end"], seg["color"])

        # Sync
        grid_view.sync_segments_with_manager(segment_manager)

        # Grid should have all segments
        assert len(grid_view._segments) == len(sample_segments)
        for seg in sample_segments:
            assert seg["name"] in grid_view._segments
            grid_seg = grid_view._segments[seg["name"]]
            assert grid_seg.start_frame == seg["start"]
            assert grid_seg.end_frame == seg["end"]

    def test_sync_overwrites_existing_grid_segments(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Syncing should overwrite any existing grid segments with manager state."""
        # Add segment to grid with old data
        grid_view._segments["Walk"] = AnimationSegment("Walk", 0, 3, QColor(255, 0, 0))

        # Add same segment to manager with different range
        segment_manager.add_segment("Walk", 0, 7, QColor(0, 255, 0))

        # Sync
        grid_view.sync_segments_with_manager(segment_manager)

        # Grid should have manager's version
        assert "Walk" in grid_view._segments
        assert grid_view._segments["Walk"].end_frame == 7

    def test_sync_preserves_bounce_mode_and_frame_holds(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Syncing should preserve bounce mode and frame holds from manager."""
        # Add segment with bounce and frame holds
        segment_manager.add_segment("Walk", 0, 3, QColor(255, 0, 0))
        segment_manager.set_bounce_mode("Walk", True)
        segment_manager.set_frame_holds("Walk", {1: 5, 2: 3})

        # Sync
        grid_view.sync_segments_with_manager(segment_manager)

        # Check preserved properties
        grid_seg = grid_view._segments["Walk"]
        assert grid_seg.bounce_mode is True
        assert grid_seg.frame_holds == {1: 5, 2: 3}


# ============================================================================
# Sync After Create Tests
# ============================================================================


class TestSyncAfterCreate:
    """Tests for consistency after creating segments."""

    def test_create_in_manager_then_sync(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Creating segment in manager then syncing should reflect in grid."""
        # Create segment in manager
        success, _ = segment_manager.add_segment("NewSeg", 0, 5, QColor(100, 100, 100))
        assert success

        # Sync
        grid_view.sync_segments_with_manager(segment_manager)

        # Should be in grid
        assert "NewSeg" in grid_view._segments
        assert grid_view._segments["NewSeg"].start_frame == 0
        assert grid_view._segments["NewSeg"].end_frame == 5

    def test_multiple_creates_then_single_sync(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Multiple segment creations followed by sync should all appear in grid."""
        # Create several segments
        segment_manager.add_segment("Seg1", 0, 3, QColor(255, 0, 0))
        segment_manager.add_segment("Seg2", 4, 7, QColor(0, 255, 0))
        segment_manager.add_segment("Seg3", 8, 11, QColor(0, 0, 255))

        # Single sync
        grid_view.sync_segments_with_manager(segment_manager)

        # All should be present
        assert len(grid_view._segments) == 3
        assert "Seg1" in grid_view._segments
        assert "Seg2" in grid_view._segments
        assert "Seg3" in grid_view._segments


# ============================================================================
# Sync After Delete Tests
# ============================================================================


class TestSyncAfterDelete:
    """Tests for consistency after deleting segments."""

    def test_delete_from_manager_then_sync(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Deleting segment from manager then syncing should remove from grid."""
        # Create and sync
        segment_manager.add_segment("ToDelete", 0, 3, QColor(255, 0, 0))
        grid_view.sync_segments_with_manager(segment_manager)
        assert "ToDelete" in grid_view._segments

        # Delete from manager
        success = segment_manager.remove_segment("ToDelete")
        assert success

        # Sync again
        grid_view.sync_segments_with_manager(segment_manager)

        # Should be gone from grid
        assert "ToDelete" not in grid_view._segments

    def test_delete_multiple_then_sync(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView,
        sample_segments: list[dict]
    ) -> None:
        """Deleting multiple segments then syncing should remove all from grid."""
        # Add all segments
        for seg in sample_segments:
            segment_manager.add_segment(seg["name"], seg["start"], seg["end"], seg["color"])
        grid_view.sync_segments_with_manager(segment_manager)
        assert len(grid_view._segments) == 4

        # Delete two segments
        segment_manager.remove_segment("Walk")
        segment_manager.remove_segment("Jump")

        # Sync
        grid_view.sync_segments_with_manager(segment_manager)

        # Only two should remain
        assert len(grid_view._segments) == 2
        assert "Walk" not in grid_view._segments
        assert "Jump" not in grid_view._segments
        assert "Run" in grid_view._segments
        assert "Idle" in grid_view._segments

    def test_clear_manager_then_sync(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView,
        sample_segments: list[dict]
    ) -> None:
        """Clearing all segments from manager then syncing should empty grid."""
        # Add all segments
        for seg in sample_segments:
            segment_manager.add_segment(seg["name"], seg["start"], seg["end"], seg["color"])
        grid_view.sync_segments_with_manager(segment_manager)
        assert len(grid_view._segments) == 4

        # Clear manager
        segment_manager.clear_segments()

        # Sync
        grid_view.sync_segments_with_manager(segment_manager)

        # Grid should be empty
        assert len(grid_view._segments) == 0


# ============================================================================
# Sync After Rename Tests
# ============================================================================


class TestSyncAfterRename:
    """Tests for consistency after renaming segments."""

    def test_rename_in_manager_then_sync(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Renaming segment in manager then syncing should update grid."""
        # Create and sync
        segment_manager.add_segment("OldName", 0, 3, QColor(255, 0, 0))
        grid_view.sync_segments_with_manager(segment_manager)
        assert "OldName" in grid_view._segments

        # Rename in manager
        success = segment_manager.rename_segment("OldName", "NewName")
        assert success

        # Sync
        grid_view.sync_segments_with_manager(segment_manager)

        # Old name gone, new name present
        assert "OldName" not in grid_view._segments
        assert "NewName" in grid_view._segments

    def test_rename_preserves_segment_properties(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Renaming should preserve all segment properties after sync."""
        # Create segment with properties (frames 2-6 = 5 frames, indices 0-4)
        segment_manager.add_segment("Original", 2, 6, QColor(100, 150, 200))
        segment_manager.set_bounce_mode("Original", True)
        # Frame holds use relative indices within segment (0-4), not absolute
        segment_manager.set_frame_holds("Original", {1: 2, 3: 4})
        grid_view.sync_segments_with_manager(segment_manager)

        # Rename
        segment_manager.rename_segment("Original", "Renamed")
        grid_view.sync_segments_with_manager(segment_manager)

        # Properties preserved
        seg = grid_view._segments["Renamed"]
        assert seg.start_frame == 2
        assert seg.end_frame == 6
        assert seg.bounce_mode is True
        assert seg.frame_holds == {1: 2, 3: 4}


# ============================================================================
# Sync After Property Update Tests
# ============================================================================


class TestSyncAfterPropertyUpdate:
    """Tests for consistency after updating segment properties."""

    def test_update_bounce_mode_in_manager(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Updating bounce mode in manager then syncing should update grid."""
        # Create and sync
        segment_manager.add_segment("Bounce", 0, 3, QColor(255, 0, 0))
        grid_view.sync_segments_with_manager(segment_manager)
        assert grid_view._segments["Bounce"].bounce_mode is False

        # Update bounce mode
        segment_manager.set_bounce_mode("Bounce", True)

        # Sync
        grid_view.sync_segments_with_manager(segment_manager)

        # Should be updated
        assert grid_view._segments["Bounce"].bounce_mode is True

    def test_update_frame_holds_in_manager(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Updating frame holds in manager then syncing should update grid."""
        # Create and sync
        segment_manager.add_segment("Holds", 0, 5, QColor(255, 0, 0))
        grid_view.sync_segments_with_manager(segment_manager)
        assert grid_view._segments["Holds"].frame_holds == {}

        # Update frame holds
        segment_manager.set_frame_holds("Holds", {1: 3, 3: 5})

        # Sync
        grid_view.sync_segments_with_manager(segment_manager)

        # Should be updated
        assert grid_view._segments["Holds"].frame_holds == {1: 3, 3: 5}

    def test_update_segment_range_in_manager(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Updating segment range in manager then syncing should update grid."""
        # Create and sync
        segment_manager.add_segment("Range", 0, 3, QColor(255, 0, 0))
        grid_view.sync_segments_with_manager(segment_manager)
        assert grid_view._segments["Range"].end_frame == 3

        # Update range
        segment_manager.update_segment("Range", 0, 7)

        # Sync
        grid_view.sync_segments_with_manager(segment_manager)

        # Should be updated
        assert grid_view._segments["Range"].start_frame == 0
        assert grid_view._segments["Range"].end_frame == 7


# ============================================================================
# Bidirectional Consistency Tests
# ============================================================================


class TestBidirectionalConsistency:
    """Tests for consistency in both directions."""

    def test_manager_is_source_of_truth(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Manager should be the source of truth after sync."""
        # Add different segments to each
        segment_manager.add_segment("ManagerSeg", 0, 3, QColor(255, 0, 0))
        grid_view._segments["GridSeg"] = AnimationSegment("GridSeg", 4, 7, QColor(0, 255, 0))

        # Sync (manager -> grid)
        grid_view.sync_segments_with_manager(segment_manager)

        # Grid should have manager's segment, not its own
        assert "ManagerSeg" in grid_view._segments
        assert "GridSeg" not in grid_view._segments

    def test_sync_with_none_manager_is_safe(
        self, grid_view: AnimationGridView
    ) -> None:
        """Syncing with None manager should be safe no-op."""
        # Add segment to grid
        grid_view._segments["Test"] = AnimationSegment("Test", 0, 3, QColor(255, 0, 0))

        # Sync with None (should not crash or change anything)
        grid_view.sync_segments_with_manager(None)

        # Grid unchanged
        assert "Test" in grid_view._segments

    def test_segment_data_independence_after_sync(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Grid segments should be independent copies after sync."""
        # Create and sync
        segment_manager.add_segment("Independent", 0, 3, QColor(255, 0, 0))
        segment_manager.set_frame_holds("Independent", {1: 2})
        grid_view.sync_segments_with_manager(segment_manager)

        # Modify grid segment's frame_holds directly
        grid_view._segments["Independent"].frame_holds[2] = 5

        # Manager should NOT be affected
        manager_seg = segment_manager.get_segment("Independent")
        assert manager_seg is not None
        assert 2 not in manager_seg.frame_holds


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases in segment sync."""

    def test_sync_single_frame_segment(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Single-frame segments should sync correctly."""
        # Create single-frame segment
        segment_manager.add_segment("Single", 5, 5, QColor(255, 0, 0))
        grid_view.sync_segments_with_manager(segment_manager)

        # Check synced
        assert "Single" in grid_view._segments
        seg = grid_view._segments["Single"]
        assert seg.start_frame == 5
        assert seg.end_frame == 5
        assert seg.frame_count == 1

    def test_sync_segment_with_special_characters_in_name(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Segments with special characters in name should sync."""
        special_names = ["Walk_Left", "Run-Fast", "Jump (high)", "Idle.1"]
        for i, name in enumerate(special_names):
            segment_manager.add_segment(name, i * 4, i * 4 + 3, QColor(100, 100, 100))

        grid_view.sync_segments_with_manager(segment_manager)

        for name in special_names:
            assert name in grid_view._segments

    def test_sync_maximum_segments(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Syncing many segments should work correctly."""
        # Create 50 segments (stress test)
        # Update manager to support 200 frames
        segment_manager._max_frames = 200
        mock_frames = [MagicMock() for _ in range(200)]
        grid_view.set_frames(mock_frames)

        for i in range(50):
            segment_manager.add_segment(f"Seg_{i}", i * 4, i * 4 + 3, QColor(i * 5, 100, 100))

        grid_view.sync_segments_with_manager(segment_manager)

        # All should sync
        assert len(grid_view._segments) == 50
        for i in range(50):
            assert f"Seg_{i}" in grid_view._segments

    def test_repeated_sync_is_idempotent(
        self, segment_manager: AnimationSegmentManager, grid_view: AnimationGridView
    ) -> None:
        """Multiple syncs without changes should produce same result."""
        # Create segment
        segment_manager.add_segment("Stable", 0, 3, QColor(255, 0, 0))

        # Sync multiple times
        for _ in range(5):
            grid_view.sync_segments_with_manager(segment_manager)

        # Still correct
        assert len(grid_view._segments) == 1
        assert "Stable" in grid_view._segments
        assert grid_view._segments["Stable"].start_frame == 0
        assert grid_view._segments["Stable"].end_frame == 3
