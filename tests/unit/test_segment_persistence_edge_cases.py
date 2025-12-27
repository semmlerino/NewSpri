"""
Tests for segment persistence edge cases in AnimationSegmentManager.

Covers:
- Atomic write patterns (success, disk full, permission errors)
- JSON load edge cases (truncated, missing fields, partial success)
- Overlap detection boundary conditions
- Frame holds validation
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch, mock_open

import pytest

from PySide6.QtGui import QColor

from managers.animation_segment_manager import AnimationSegmentManager, AnimationSegmentData

if TYPE_CHECKING:
    from pathlib import Path as PathType


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def segment_manager() -> AnimationSegmentManager:
    """Create a fresh AnimationSegmentManager instance."""
    return AnimationSegmentManager()


@pytest.fixture
def configured_manager(segment_manager: AnimationSegmentManager, tmp_path: Path) -> AnimationSegmentManager:
    """Create a manager with sprite context set."""
    sprite_path = tmp_path / "test_sprite.png"
    sprite_path.touch()  # Create empty file
    segment_manager.set_sprite_context(str(sprite_path), frame_count=10)
    return segment_manager


@pytest.fixture
def manager_with_segments(configured_manager: AnimationSegmentManager) -> AnimationSegmentManager:
    """Create a manager with some pre-existing segments."""
    configured_manager.add_segment("Walk", 0, 3, QColor(255, 0, 0))
    configured_manager.add_segment("Run", 4, 7, QColor(0, 255, 0))
    return configured_manager


# ============================================================================
# Atomic Write Tests
# ============================================================================


class TestSaveSegmentsAtomicWrite:
    """Tests for atomic write behavior in save_segments_to_file."""

    def test_save_segments_atomic_write_success(
        self, manager_with_segments: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Verify save creates temp file then renames atomically."""
        file_path = tmp_path / "segments.json"

        success, error = manager_with_segments.save_segments_to_file(str(file_path))

        assert success is True
        assert error == ""
        assert file_path.exists()

        # Verify content is valid JSON
        with open(file_path) as f:
            data = json.load(f)
        assert "segments" in data
        assert len(data["segments"]) == 2

    def test_save_segments_disk_full_during_write(
        self, manager_with_segments: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Mock disk full during json.dump - verify graceful failure."""
        file_path = tmp_path / "segments.json"

        with patch("json.dump", side_effect=IOError("No space left on device")):
            success, error = manager_with_segments.save_segments_to_file(str(file_path))

        assert success is False
        assert "Failed to save segments" in error
        assert "No space left on device" in error
        # Original file should not exist (never created)
        assert not file_path.exists()

    def test_save_segments_permission_denied_on_replace(
        self, manager_with_segments: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Mock permission error on os.replace - verify temp file cleanup."""
        file_path = tmp_path / "segments.json"

        with patch("os.replace", side_effect=PermissionError("Access denied")):
            success, error = manager_with_segments.save_segments_to_file(str(file_path))

        assert success is False
        assert "Failed to save segments" in error
        assert "Access denied" in error

        # Temp files should be cleaned up (check no .tmp files remain)
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0, f"Temp files not cleaned up: {tmp_files}"

    def test_save_segments_windows_locked_file(
        self, manager_with_segments: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Mock Windows file lock error on os.replace."""
        file_path = tmp_path / "segments.json"

        # Windows-style error when file is locked
        with patch("os.replace", side_effect=OSError(13, "The process cannot access the file")):
            success, error = manager_with_segments.save_segments_to_file(str(file_path))

        assert success is False
        assert "Failed to save segments" in error

    def test_save_segments_no_sprite_sheet_loaded(
        self, segment_manager: AnimationSegmentManager
    ) -> None:
        """Verify proper error when no sprite sheet context is set."""
        success, error = segment_manager.save_segments_to_file()

        assert success is False
        assert error == "No sprite sheet loaded"

    def test_save_segments_creates_directory(
        self, configured_manager: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Verify .sprite_segments directory is created automatically."""
        # The configured_manager already has a sprite context
        success, error = configured_manager.save_segments_to_file()

        assert success is True
        segments_dir = tmp_path / ".sprite_segments"
        assert segments_dir.exists()


# ============================================================================
# JSON Load Edge Cases
# ============================================================================


class TestLoadSegmentsEdgeCases:
    """Tests for JSON loading edge cases."""

    def test_load_segments_truncated_json(
        self, configured_manager: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Truncated JSON file should fail with clear error."""
        file_path = tmp_path / "truncated.json"
        file_path.write_text('{"segments": [{"name": "Walk", ')  # Incomplete JSON

        success, error = configured_manager.load_segments_from_file(str(file_path))

        assert success is False
        assert "Failed to load segments" in error

    def test_load_segments_missing_segments_key(
        self, configured_manager: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """JSON without 'segments' key should handle gracefully."""
        file_path = tmp_path / "missing_key.json"
        file_path.write_text('{"other_key": "value"}')

        success, error = configured_manager.load_segments_from_file(str(file_path))

        # Should succeed but load no segments (segments key defaults to empty list)
        assert success is True
        assert len(configured_manager.get_all_segments()) == 0

    def test_load_segments_invalid_segment_data(
        self, configured_manager: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Segment with negative frame indices should be skipped."""
        file_path = tmp_path / "invalid_segment.json"
        data = {
            "segments": [
                {"name": "Valid", "start_frame": 0, "end_frame": 3, "color_rgb": [255, 0, 0]},
                {"name": "Invalid", "start_frame": -1, "end_frame": 3, "color_rgb": [0, 255, 0]},
            ]
        }
        file_path.write_text(json.dumps(data))

        success, error = configured_manager.load_segments_from_file(str(file_path))

        # Should succeed with partial load
        assert success is True
        segments = configured_manager.get_all_segments()
        assert len(segments) == 1
        assert segments[0].name == "Valid"
        assert "Skipped 1" in error

    def test_load_segments_partial_success_reporting(
        self, configured_manager: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Mix of valid and invalid segments should report skipped ones."""
        file_path = tmp_path / "mixed.json"
        data = {
            "segments": [
                {"name": "Good1", "start_frame": 0, "end_frame": 2, "color_rgb": [255, 0, 0]},
                {"name": "Bad1", "start_frame": 100, "end_frame": 105, "color_rgb": [0, 255, 0]},  # Beyond max
                {"name": "Bad2", "start_frame": 5, "end_frame": 3, "color_rgb": [0, 0, 255]},  # End < start
                {"name": "Good2", "start_frame": 3, "end_frame": 5, "color_rgb": [255, 255, 0]},
                {"name": "Bad3", "start_frame": -1, "end_frame": 2, "color_rgb": [255, 0, 255]},  # Negative start
            ]
        }
        file_path.write_text(json.dumps(data))

        success, error = configured_manager.load_segments_from_file(str(file_path))

        assert success is True
        segments = configured_manager.get_all_segments()
        assert len(segments) == 2
        assert "Loaded 2 segments" in error
        assert "Skipped 3" in error
        # First 3 skipped names should be listed
        assert "Bad1" in error or "Bad2" in error or "Bad3" in error

    def test_load_segments_empty_segments_array(
        self, configured_manager: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Empty segments array should succeed with no segments loaded."""
        file_path = tmp_path / "empty.json"
        data = {"segments": []}
        file_path.write_text(json.dumps(data))

        success, error = configured_manager.load_segments_from_file(str(file_path))

        assert success is True
        assert error == ""
        assert len(configured_manager.get_all_segments()) == 0

    def test_load_segments_file_not_found(
        self, configured_manager: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Non-existent file should fail with clear error."""
        file_path = tmp_path / "nonexistent.json"

        success, error = configured_manager.load_segments_from_file(str(file_path))

        assert success is False
        assert "Failed to load segments" in error

    def test_load_segments_clears_existing(
        self, manager_with_segments: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Loading should clear existing segments first."""
        # Manager already has Walk and Run segments
        assert len(manager_with_segments.get_all_segments()) == 2

        file_path = tmp_path / "new_segments.json"
        data = {
            "segments": [
                {"name": "Jump", "start_frame": 0, "end_frame": 2, "color_rgb": [255, 0, 0]},
            ]
        }
        file_path.write_text(json.dumps(data))

        success, error = manager_with_segments.load_segments_from_file(str(file_path))

        assert success is True
        segments = manager_with_segments.get_all_segments()
        assert len(segments) == 1
        assert segments[0].name == "Jump"


# ============================================================================
# Overlap Detection Tests
# ============================================================================


class TestFindOverlappingSegment:
    """Tests for _find_overlapping_segment boundary conditions."""

    def test_adjacent_frames_do_not_overlap(
        self, configured_manager: AnimationSegmentManager
    ) -> None:
        """Segments [0-3] and [4-7] should NOT be considered overlapping."""
        configured_manager.add_segment("First", 0, 3, QColor(255, 0, 0))

        # Check if [4-7] overlaps - it should NOT
        overlap = configured_manager._find_overlapping_segment(4, 7)

        assert overlap is None, "Adjacent segments incorrectly detected as overlapping"

    def test_touching_at_boundary_does_overlap(
        self, configured_manager: AnimationSegmentManager
    ) -> None:
        """Segments [0-5] and [5-10] SHOULD overlap at frame 5 (inclusive boundaries)."""
        configured_manager.add_segment("First", 0, 5, QColor(255, 0, 0))

        # Check if [5-10] overlaps - it SHOULD (both include frame 5)
        overlap = configured_manager._find_overlapping_segment(5, 9)

        assert overlap == "First", "Touching segments should be detected as overlapping"

    def test_single_frame_segment_overlap(
        self, configured_manager: AnimationSegmentManager
    ) -> None:
        """Single-frame segment [5-5] overlap detection."""
        configured_manager.add_segment("Single", 5, 5, QColor(255, 0, 0))

        # [4-6] should overlap with [5-5]
        assert configured_manager._find_overlapping_segment(4, 6) == "Single"

        # [5-5] should overlap with [5-5]
        assert configured_manager._find_overlapping_segment(5, 5) == "Single"

        # [6-7] should NOT overlap with [5-5]
        assert configured_manager._find_overlapping_segment(6, 7) is None

        # [3-4] should NOT overlap with [5-5]
        assert configured_manager._find_overlapping_segment(3, 4) is None

    def test_no_segments_no_overlap(
        self, configured_manager: AnimationSegmentManager
    ) -> None:
        """Empty segments list should return None."""
        overlap = configured_manager._find_overlapping_segment(0, 5)

        assert overlap is None

    def test_completely_contained_overlap(
        self, configured_manager: AnimationSegmentManager
    ) -> None:
        """Segment fully contained within another should overlap."""
        configured_manager.add_segment("Outer", 0, 9, QColor(255, 0, 0))

        # [2-5] is fully contained within [0-9]
        overlap = configured_manager._find_overlapping_segment(2, 5)

        assert overlap == "Outer"

    def test_partial_overlap_from_start(
        self, configured_manager: AnimationSegmentManager
    ) -> None:
        """Partial overlap starting before existing segment."""
        configured_manager.add_segment("Middle", 3, 7, QColor(255, 0, 0))

        # [0-4] overlaps with [3-7] at frames 3-4
        overlap = configured_manager._find_overlapping_segment(0, 4)

        assert overlap == "Middle"

    def test_partial_overlap_from_end(
        self, configured_manager: AnimationSegmentManager
    ) -> None:
        """Partial overlap extending beyond existing segment."""
        configured_manager.add_segment("Middle", 3, 7, QColor(255, 0, 0))

        # [6-9] overlaps with [3-7] at frames 6-7
        overlap = configured_manager._find_overlapping_segment(6, 9)

        assert overlap == "Middle"


# ============================================================================
# Frame Holds Validation Tests
# ============================================================================


class TestSetFrameHoldsValidation:
    """Tests for set_frame_holds boundary validation."""

    def test_valid_frame_holds_at_boundaries(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Valid holds at segment boundaries should succeed."""
        # Walk segment is [0-3], so valid indices are 0, 1, 2, 3 (4 frames)
        success, error = manager_with_segments.set_frame_holds("Walk", {0: 2, 3: 3})

        assert success is True
        assert error == ""
        segment = manager_with_segments.get_segment("Walk")
        assert segment is not None
        assert segment.frame_holds == {0: 2, 3: 3}

    def test_frame_hold_at_last_valid_index(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Hold at last valid index (frame_count - 1) should succeed."""
        # Walk is [0-3], frame_count=4, so index 3 is valid
        success, error = manager_with_segments.set_frame_holds("Walk", {3: 5})

        assert success is True
        assert error == ""

    def test_frame_hold_one_past_end(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Hold at frame_count (one past last valid) should fail."""
        # Walk is [0-3], frame_count=4, so index 4 is invalid
        success, error = manager_with_segments.set_frame_holds("Walk", {4: 2})

        assert success is False
        assert "Frame index 4 is out of range" in error

    def test_frame_hold_out_of_bounds_index(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Hold at index well beyond frame_count should fail."""
        # Walk is [0-3], frame_count=4, so index 10 is definitely invalid
        success, error = manager_with_segments.set_frame_holds("Walk", {10: 2})

        assert success is False
        assert "Frame index 10 is out of range" in error

    def test_frame_hold_negative_index(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Negative frame index should fail validation."""
        success, error = manager_with_segments.set_frame_holds("Walk", {-1: 2})

        assert success is False
        assert "Frame index -1 is out of range" in error

    def test_frame_hold_zero_duration(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Zero duration hold - document current behavior (accepted)."""
        success, error = manager_with_segments.set_frame_holds("Walk", {0: 0})

        # Current implementation accepts zero duration
        assert success is True
        segment = manager_with_segments.get_segment("Walk")
        assert segment is not None
        assert segment.frame_holds == {0: 0}

    def test_frame_hold_negative_duration(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Negative duration hold - document current behavior (accepted)."""
        success, error = manager_with_segments.set_frame_holds("Walk", {0: -1})

        # Current implementation accepts negative duration (no validation)
        assert success is True
        segment = manager_with_segments.get_segment("Walk")
        assert segment is not None
        assert segment.frame_holds == {0: -1}

    def test_frame_hold_large_duration(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Large duration value should be accepted (no upper limit)."""
        success, error = manager_with_segments.set_frame_holds("Walk", {0: 1000})

        assert success is True

    def test_frame_holds_on_nonexistent_segment(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Setting holds on non-existent segment should fail."""
        success, error = manager_with_segments.set_frame_holds("NoSuchSegment", {0: 2})

        assert success is False
        assert "Segment 'NoSuchSegment' not found" in error

    def test_frame_holds_empty_dict(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Empty frame_holds dict should succeed and clear holds."""
        # First set some holds
        manager_with_segments.set_frame_holds("Walk", {0: 2, 1: 3})

        # Then clear with empty dict
        success, error = manager_with_segments.set_frame_holds("Walk", {})

        assert success is True
        assert error == ""
        segment = manager_with_segments.get_segment("Walk")
        assert segment is not None
        assert segment.frame_holds == {}

    def test_frame_holds_triggers_auto_save(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Verify auto_save is called after successful set_frame_holds."""
        with patch.object(manager_with_segments, "_auto_save") as mock_auto_save:
            manager_with_segments.set_frame_holds("Walk", {0: 2})

            mock_auto_save.assert_called_once()

    def test_frame_holds_no_auto_save_on_failure(
        self, manager_with_segments: AnimationSegmentManager
    ) -> None:
        """Verify auto_save is NOT called when set_frame_holds fails."""
        with patch.object(manager_with_segments, "_auto_save") as mock_auto_save:
            manager_with_segments.set_frame_holds("Walk", {10: 2})  # Invalid index

            mock_auto_save.assert_not_called()


# ============================================================================
# Save/Load Round-Trip Tests
# ============================================================================


class TestSaveLoadRoundTrip:
    """Tests for complete save/load cycles."""

    def test_save_load_preserves_all_data(
        self, manager_with_segments: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Save then load should preserve all segment data."""
        # Add frame holds to test preservation
        manager_with_segments.set_frame_holds("Walk", {0: 2, 2: 3})
        manager_with_segments.set_bounce_mode("Run", True)

        file_path = tmp_path / "roundtrip.json"
        manager_with_segments.save_segments_to_file(str(file_path))

        # Create new manager and load
        new_manager = AnimationSegmentManager()
        new_manager.set_sprite_context(
            manager_with_segments._sprite_sheet_path,
            frame_count=10
        )
        success, error = new_manager.load_segments_from_file(str(file_path))

        assert success is True
        assert len(new_manager.get_all_segments()) == 2

        walk = new_manager.get_segment("Walk")
        assert walk is not None
        assert walk.start_frame == 0
        assert walk.end_frame == 3
        assert walk.frame_holds == {0: 2, 2: 3}

        run = new_manager.get_segment("Run")
        assert run is not None
        assert run.bounce_mode is True

    def test_save_load_with_unicode_names(
        self, configured_manager: AnimationSegmentManager, tmp_path: Path
    ) -> None:
        """Segment names with unicode characters should round-trip correctly."""
        configured_manager.add_segment("走路", 0, 3, QColor(255, 0, 0))  # Chinese for "walk"
        configured_manager.add_segment("ジャンプ", 4, 7, QColor(0, 255, 0))  # Japanese for "jump"

        file_path = tmp_path / "unicode.json"
        configured_manager.save_segments_to_file(str(file_path))

        # Load into new manager
        new_manager = AnimationSegmentManager()
        new_manager.set_sprite_context(str(tmp_path / "test_sprite.png"), frame_count=10)
        success, error = new_manager.load_segments_from_file(str(file_path))

        assert success is True
        assert new_manager.get_segment("走路") is not None
        assert new_manager.get_segment("ジャンプ") is not None
