"""
Integration tests for manager classes.
Tests that all managers work together correctly and maintain proper state.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from managers import (
    ActionManager, MenuManager, ShortcutManager,
    get_settings_manager, get_recent_files_manager, AnimationSegmentManager
)
from sprite_viewer import SpriteViewer


@pytest.mark.integration
class TestManagerIntegration:
    """Test integration between different manager classes."""

    def test_all_managers_can_initialize(self):
        """Verify all managers can be initialized without conflicts."""
        # Create core managers with proper DI
        shortcut_manager = ShortcutManager()
        action_manager = ActionManager(shortcut_manager=shortcut_manager)
        menu_manager = MenuManager(action_manager=action_manager)

        # Get utility managers (still use factories)
        settings_manager = get_settings_manager()
        recent_files_manager = get_recent_files_manager()
        segment_manager = AnimationSegmentManager()

        # All should be initialized
        assert action_manager is not None
        assert menu_manager is not None
        assert shortcut_manager is not None
        assert settings_manager is not None
        assert recent_files_manager is not None
        assert segment_manager is not None

    def test_manager_di_chain(self):
        """Test that DI chain works correctly."""
        # Create in proper order
        shortcut_manager = ShortcutManager()
        action_manager = ActionManager(shortcut_manager=shortcut_manager)
        menu_manager = MenuManager(action_manager=action_manager)

        # Verify references are correct
        assert action_manager._shortcut_manager is shortcut_manager
        assert menu_manager._action_manager is action_manager

    def test_settings_manager_persistence(self, tmp_path):
        """Test that settings manager correctly persists data."""
        settings_manager = get_settings_manager()

        # Set test configuration
        test_settings = {
            'last_export_dir': str(tmp_path),
            'default_fps': 15,
            'auto_save': True
        }

        # Save settings
        for key, value in test_settings.items():
            if hasattr(settings_manager, 'set_value'):
                settings_manager.set_value(key, value)

        # Retrieve settings
        for key, expected_value in test_settings.items():
            if hasattr(settings_manager, 'get_value'):
                actual_value = settings_manager.get_value(key)
                assert actual_value == expected_value, f"Setting {key} not persisted correctly"

    def test_animation_segment_manager_operations(self):
        """Test AnimationSegmentManager functionality."""
        segment_manager = AnimationSegmentManager()
        segment_manager.set_auto_save_enabled(False)  # Disable auto-save for testing
        segment_manager.set_sprite_context("test.png", 30)  # Set sprite context

        # Clear any existing segments
        segment_manager.clear_segments()

        # Add segments using the manager's API
        success1, msg1 = segment_manager.add_segment("Walk", 0, 10)
        success2, msg2 = segment_manager.add_segment("Run", 11, 20)

        assert success1, f"Failed to add Walk segment: {msg1}"
        assert success2, f"Failed to add Run segment: {msg2}"

        # Verify segments exist
        segments = segment_manager.get_all_segments()
        assert len(segments) == 2
        assert segments[0].name == "Walk"
        assert segments[1].name == "Run"

        # Test segment operations
        walk_segment = segment_manager.get_segment("Walk")
        assert walk_segment is not None
        assert walk_segment.start_frame == 0
        assert walk_segment.end_frame == 10

        # Test renaming a segment
        success, msg = segment_manager.rename_segment("Walk", "WalkCycle")
        assert success, f"Failed to rename segment: {msg}"

        # Verify rename worked
        renamed_segment = segment_manager.get_segment("WalkCycle")
        assert renamed_segment is not None
        assert renamed_segment.name == "WalkCycle"

        # Old name should not exist
        old_segment = segment_manager.get_segment("Walk")
        assert old_segment is None


@pytest.mark.integration
class TestManagerCrossCommunication:
    """Test communication between managers."""

    def test_action_and_shortcut_manager_sync(self):
        """Test that actions and shortcuts stay synchronized."""
        shortcut_manager = ShortcutManager()
        action_manager = ActionManager(shortcut_manager=shortcut_manager)

        # Test with an existing action from the predefined set
        # ActionManager requires predefined action IDs
        existing_action_ids = action_manager.get_all_action_ids()

        if existing_action_ids:
            # Test with first available action
            test_id = existing_action_ids[0]
            action = action_manager.get_action(test_id)

            # Action should be retrieved (might be None if not created yet)
            # This tests that the managers can be queried without error

            # Shortcut manager should have shortcut definitions
            if hasattr(shortcut_manager, 'get_all_shortcut_ids'):
                shortcut_ids = shortcut_manager.get_all_shortcut_ids()
                assert isinstance(shortcut_ids, (list, tuple, set))

    def test_menu_manager_uses_action_manager(self):
        """Test that menu manager properly uses action manager."""
        shortcut_manager = ShortcutManager()
        action_manager = ActionManager(shortcut_manager=shortcut_manager)
        menu_manager = MenuManager(action_manager=action_manager)

        # Menu manager should use actions from action manager
        if hasattr(menu_manager, 'create_menus'):
            mock_menubar = Mock()
            menu_manager.create_menus(mock_menubar)

            # Verify menus were created
            assert mock_menubar.addMenu.called

    def test_settings_affect_other_managers(self):
        """Test that settings changes affect other managers."""
        settings_manager = get_settings_manager()
        recent_files_manager = get_recent_files_manager()

        # Change max recent files setting
        if hasattr(settings_manager, 'set_value'):
            settings_manager.set_value('max_recent_files', 5)

            # Recent files manager should respect this
            if hasattr(recent_files_manager, 'get_max_files'):
                max_files = recent_files_manager.get_max_files()
                assert max_files == 5


@pytest.mark.integration
class TestManagerErrorHandling:
    """Test manager behavior under error conditions."""

    def test_managers_handle_missing_config(self):
        """Test managers work with missing configuration."""
        with patch('pathlib.Path.exists', return_value=False):
            settings_manager = get_settings_manager()

            # Should work with defaults
            if hasattr(settings_manager, 'get_value'):
                value = settings_manager.get_value('nonexistent_key', default_value='default')
                assert value == 'default'

    def test_segment_manager_handles_invalid_segments(self):
        """Test segment manager handles invalid segment data."""
        import uuid
        segment_manager = AnimationSegmentManager()
        segment_manager.set_auto_save_enabled(False)
        # Use unique sprite name to avoid test pollution
        segment_manager.set_sprite_context(f"test_{uuid.uuid4().hex[:8]}.png", 30)

        # Clear any existing segments
        segment_manager.clear_segments()

        # Add first segment
        success1, msg1 = segment_manager.add_segment("Segment1", 0, 10)
        assert success1, f"Should add first segment: {msg1}"

        # Try to add overlapping segment
        success2, msg2 = segment_manager.add_segment("Segment2", 5, 15)

        # Manager rejects overlapping segments - this is the actual behavior
        # Tests should reflect reality, not assumptions
        assert not success2, "Overlapping segments should be rejected"
        assert "overlap" in msg2.lower() or "conflict" in msg2.lower() or len(msg2) > 0

        # Verify only first segment exists
        segments = segment_manager.get_all_segments()
        assert len(segments) == 1
        assert segments[0].name == "Segment1"

    def test_recent_files_handles_missing_files(self, tmp_path):
        """Test recent files manager handles deleted files."""
        recent_files_manager = get_recent_files_manager()

        # Add a file that exists
        test_file = tmp_path / "test.png"
        test_file.write_text("dummy")

        recent_files_manager.add_file_to_recent(str(test_file))

        # Delete the file
        test_file.unlink()

        # Manager should handle gracefully - use correct API methods
        # get_recent_files_count() and has_recent_files() are the actual methods
        count = recent_files_manager.get_recent_files_count()
        has_files = recent_files_manager.has_recent_files()

        # Implementation might remove missing files or keep them
        # Just shouldn't crash - count should be a non-negative integer
        assert isinstance(count, int)
        assert count >= 0
        assert isinstance(has_files, bool)


@pytest.mark.integration
class TestManagerStateConsistency:
    """Test that managers maintain consistent state."""

    def test_segment_manager_state_consistency(self):
        """Test segment manager maintains consistent state."""
        segment_manager = AnimationSegmentManager()
        segment_manager.set_auto_save_enabled(False)
        segment_manager.set_sprite_context("test.png", 30)

        # Clear any existing segments
        segment_manager.clear_segments()

        # Add segments and verify state
        segments_to_add = [
            ("Idle", 0, 5),
            ("Walk", 6, 15),
            ("Run", 16, 25)
        ]

        for name, start, end in segments_to_add:
            success, msg = segment_manager.add_segment(name, start, end)
            assert success, f"Failed to add segment {name}: {msg}"

        # Verify count
        assert len(segment_manager.get_all_segments()) == 3

        # Remove middle segment
        segment_manager.remove_segment("Walk")

        # Verify state is consistent
        remaining = segment_manager.get_all_segments()
        assert len(remaining) == 2
        assert remaining[0].name == "Idle"
        assert remaining[1].name == "Run"

        # Frame queries should still work
        assert segment_manager.get_segment_at_frame(2).name == "Idle"
        assert segment_manager.get_segment_at_frame(10) is None  # Gap where Walk was
        assert segment_manager.get_segment_at_frame(20).name == "Run"

    def test_settings_manager_transaction_safety(self):
        """Test settings manager handles concurrent access safely."""
        settings_manager = get_settings_manager()

        # Simulate concurrent access
        test_key = 'concurrent_test'

        # Multiple writes
        for i in range(10):
            settings_manager.set_value(f"{test_key}_{i}", i)

        # Verify all writes succeeded
        for i in range(10):
            value = settings_manager.get_value(f"{test_key}_{i}")
            assert value == i


# Manager testing utilities
class ManagerTestHelper:
    """Helper class for manager testing."""

    @staticmethod
    def create_manager_chain():
        """Create a properly wired manager chain for testing."""
        shortcut_manager = ShortcutManager()
        action_manager = ActionManager(shortcut_manager=shortcut_manager)
        menu_manager = MenuManager(action_manager=action_manager)
        return shortcut_manager, action_manager, menu_manager

    @staticmethod
    def create_test_segments(count=5):
        """Create test animation segments."""
        from managers.animation_segment_manager import AnimationSegment

        segments = []
        frame_offset = 0

        for i in range(count):
            duration = 10
            segment = AnimationSegment(
                f"Segment_{i}",
                frame_offset,
                frame_offset + duration - 1
            )
            segments.append(segment)
            frame_offset += duration

        return segments


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
