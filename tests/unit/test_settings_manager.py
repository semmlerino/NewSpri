"""
Tests for SettingsManager functionality.

Covers:
- Singleton pattern
- Get/set value operations
- Auto-save timer behavior
- Window geometry save/restore
- Splitter state save/restore
- Extraction/display/animation settings
- Recent files management
- Signal emission
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from PySide6.QtCore import QByteArray
from PySide6.QtWidgets import QMainWindow, QSplitter

from managers.settings_manager import (
    SettingsManager,
    get_settings_manager,
    reset_settings_manager,
)

if TYPE_CHECKING:
    pass


# Mark all tests in this module as requiring Qt
pytestmark = pytest.mark.requires_qt


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global settings manager before and after each test."""
    reset_settings_manager()
    yield
    reset_settings_manager()


@pytest.fixture
def settings_manager(qapp) -> SettingsManager:
    """Create a fresh settings manager for testing."""
    manager = SettingsManager()
    # Clear any existing settings for clean tests
    manager._settings.clear()
    return manager


@pytest.fixture
def temp_settings_file(tmp_path: Path) -> Path:
    """Create a temporary settings file path."""
    return tmp_path / "settings.json"


@pytest.fixture
def sample_settings_dict() -> dict:
    """Sample settings dictionary for import/export testing."""
    return {
        'extraction/last_width': 64,
        'extraction/last_height': 48,
        'display/grid_visible': True,
        'animation/last_fps': 24,
    }


# ============================================================================
# Singleton Pattern Tests
# ============================================================================


class TestSingletonPattern:
    """Tests for singleton pattern implementation."""

    def test_get_settings_manager_returns_singleton(self, qapp) -> None:
        """get_settings_manager should return the same instance."""
        manager1 = get_settings_manager()
        manager2 = get_settings_manager()

        assert manager1 is manager2

    def test_reset_settings_manager_clears_singleton(self, qapp) -> None:
        """reset_settings_manager should clear the singleton."""
        manager1 = get_settings_manager()
        reset_settings_manager()
        manager2 = get_settings_manager()

        assert manager1 is not manager2

    def test_singleton_is_thread_safe(self, qapp) -> None:
        """Singleton access should be thread-safe."""
        import threading

        managers = []

        def get_manager():
            managers.append(get_settings_manager())

        threads = [threading.Thread(target=get_manager) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should be the same instance
        assert all(m is managers[0] for m in managers)


# ============================================================================
# Get/Set Value Tests
# ============================================================================


class TestGetSetValue:
    """Tests for get_value and set_value operations."""

    def test_get_value_returns_default_for_missing_key(
        self, settings_manager: SettingsManager
    ) -> None:
        """get_value should return default for missing keys."""
        value = settings_manager.get_value('nonexistent/key', 'default')

        assert value == 'default'

    def test_get_value_uses_config_defaults(
        self, settings_manager: SettingsManager
    ) -> None:
        """get_value should use Config.Settings.DEFAULTS when no default provided."""
        from config import Config

        # Clear the value first
        settings_manager._settings.remove('extraction/last_width')

        value = settings_manager.get_value('extraction/last_width')

        assert value == Config.Settings.DEFAULTS['extraction/last_width']

    def test_set_value_stores_value(
        self, settings_manager: SettingsManager
    ) -> None:
        """set_value should store the value."""
        settings_manager.set_value('test/key', 42)

        value = settings_manager.get_value('test/key')

        assert value == 42

    def test_set_value_emits_signal(
        self, settings_manager: SettingsManager, qtbot
    ) -> None:
        """set_value should emit settingsChanged signal."""
        with qtbot.waitSignal(settings_manager.settingsChanged, timeout=1000) as blocker:
            settings_manager.set_value('test/signal', 'value')

        key, value = blocker.args
        assert key == 'test/signal'
        assert value == 'value'

    def test_set_value_auto_save_triggers_timer(
        self, settings_manager: SettingsManager
    ) -> None:
        """set_value with auto_save should start the autosave timer."""
        settings_manager.set_value('test/auto', 'value', auto_save=True)

        assert settings_manager._autosave_timer.isActive()

    def test_set_value_no_auto_save_skips_timer(
        self, settings_manager: SettingsManager
    ) -> None:
        """set_value with auto_save=False should not start timer."""
        settings_manager.set_value('test/no_auto', 'value', auto_save=False)

        # Timer should not have been started for this value
        assert 'test/no_auto' not in settings_manager._pending_changes


# ============================================================================
# Auto-Save Timer Tests
# ============================================================================


class TestAutoSaveTimer:
    """Tests for auto-save timer behavior."""

    def test_auto_save_clears_pending_changes(
        self, settings_manager: SettingsManager
    ) -> None:
        """_auto_save should clear pending changes."""
        settings_manager._pending_changes['test'] = 'value'

        settings_manager._auto_save()

        assert len(settings_manager._pending_changes) == 0

    def test_sync_stops_timer_and_clears_pending(
        self, settings_manager: SettingsManager
    ) -> None:
        """sync should stop timer and clear pending changes."""
        settings_manager.set_value('test/sync', 'value')
        assert settings_manager._autosave_timer.isActive()

        settings_manager.sync()

        assert not settings_manager._autosave_timer.isActive()
        assert len(settings_manager._pending_changes) == 0


# ============================================================================
# Window Geometry Tests
# ============================================================================


class TestWindowGeometry:
    """Tests for window geometry save/restore."""

    def test_save_window_geometry(
        self, qapp, settings_manager: SettingsManager
    ) -> None:
        """save_window_geometry should save both geometry and state."""
        window = QMainWindow()
        window.resize(800, 600)

        settings_manager.save_window_geometry(window)

        geometry = settings_manager.get_value('window/geometry')
        state = settings_manager.get_value('window/state')

        assert geometry is not None
        assert state is not None
        assert isinstance(geometry, QByteArray)
        assert isinstance(state, QByteArray)

    def test_restore_window_geometry_returns_true_on_success(
        self, qapp, settings_manager: SettingsManager
    ) -> None:
        """restore_window_geometry should return True when geometry exists."""
        window = QMainWindow()
        window.resize(800, 600)

        settings_manager.save_window_geometry(window)

        new_window = QMainWindow()
        result = settings_manager.restore_window_geometry(new_window)

        assert result is True

    def test_restore_window_geometry_returns_false_without_saved(
        self, qapp, settings_manager: SettingsManager
    ) -> None:
        """restore_window_geometry should return False when no geometry saved."""
        window = QMainWindow()

        result = settings_manager.restore_window_geometry(window)

        assert result is False


# ============================================================================
# Splitter State Tests
# ============================================================================


class TestSplitterState:
    """Tests for splitter state save/restore."""

    def test_save_splitter_state(
        self, qapp, settings_manager: SettingsManager
    ) -> None:
        """save_splitter_state should save state to specified key."""
        splitter = QSplitter()

        settings_manager.save_splitter_state(splitter, 'test/splitter')

        state = settings_manager.get_value('test/splitter')
        assert state is not None
        assert isinstance(state, QByteArray)

    def test_restore_splitter_state_returns_true_on_success(
        self, qapp, settings_manager: SettingsManager
    ) -> None:
        """restore_splitter_state should return True when state exists."""
        splitter = QSplitter()
        settings_manager.save_splitter_state(splitter, 'test/splitter')

        new_splitter = QSplitter()
        result = settings_manager.restore_splitter_state(new_splitter, 'test/splitter')

        assert result is True

    def test_restore_splitter_state_returns_false_without_saved(
        self, qapp, settings_manager: SettingsManager
    ) -> None:
        """restore_splitter_state should return False when no state saved."""
        splitter = QSplitter()

        result = settings_manager.restore_splitter_state(splitter, 'nonexistent/splitter')

        assert result is False


# ============================================================================
# Settings Save Methods Tests
# ============================================================================


class TestSettingsSaveMethods:
    """Tests for specialized save methods."""

    def test_save_extraction_settings(
        self, settings_manager: SettingsManager
    ) -> None:
        """save_extraction_settings should save all extraction parameters."""
        settings_manager.save_extraction_settings(
            width=64, height=48, offset_x=4, offset_y=8,
            spacing_x=2, spacing_y=2, mode='manual'
        )

        assert settings_manager.get_value('extraction/last_width') == 64
        assert settings_manager.get_value('extraction/last_height') == 48
        assert settings_manager.get_value('extraction/last_offset_x') == 4
        assert settings_manager.get_value('extraction/last_offset_y') == 8
        assert settings_manager.get_value('extraction/last_spacing_x') == 2
        assert settings_manager.get_value('extraction/last_spacing_y') == 2
        assert settings_manager.get_value('extraction/last_mode') == 'manual'

    def test_save_display_settings(
        self, settings_manager: SettingsManager
    ) -> None:
        """save_display_settings should save display preferences."""
        settings_manager.save_display_settings(
            grid_visible=True, zoom=2.5, zoom_fit_tiny=False
        )

        assert settings_manager.get_value('display/grid_visible') is True
        assert settings_manager.get_value('display/last_zoom') == 2.5
        assert settings_manager.get_value('display/zoom_fit_tiny') is False

    def test_save_animation_settings(
        self, settings_manager: SettingsManager
    ) -> None:
        """save_animation_settings should save animation preferences."""
        settings_manager.save_animation_settings(fps=30, loop_mode=False)

        assert settings_manager.get_value('animation/last_fps') == 30
        assert settings_manager.get_value('animation/loop_mode') is False


# ============================================================================
# Recent Files Management Tests
# ============================================================================


class TestRecentFilesManagement:
    """Tests for recent files management."""

    def test_add_recent_file(
        self, settings_manager: SettingsManager, tmp_path: Path
    ) -> None:
        """add_recent_file should add file to beginning of list."""
        filepath = str(tmp_path / "test.png")

        settings_manager.add_recent_file(filepath)

        recent = settings_manager.get_recent_files()
        assert len(recent) == 1
        assert recent[0] == filepath

    def test_add_recent_file_moves_existing_to_front(
        self, settings_manager: SettingsManager, tmp_path: Path
    ) -> None:
        """Adding existing file should move it to front."""
        file1 = str(tmp_path / "file1.png")
        file2 = str(tmp_path / "file2.png")

        settings_manager.add_recent_file(file1)
        settings_manager.add_recent_file(file2)
        settings_manager.add_recent_file(file1)  # Add again

        recent = settings_manager.get_recent_files()
        assert len(recent) == 2
        assert recent[0] == file1
        assert recent[1] == file2

    def test_add_recent_file_trims_to_max(
        self, settings_manager: SettingsManager, tmp_path: Path
    ) -> None:
        """add_recent_file should trim list to max size."""
        from config import Config

        # Add more than max files
        for i in range(Config.Settings.MAX_RECENT_FILES + 5):
            settings_manager.add_recent_file(str(tmp_path / f"file{i}.png"))

        recent = settings_manager.get_recent_files()
        assert len(recent) == Config.Settings.MAX_RECENT_FILES

    def test_add_recent_file_empty_filepath_ignored(
        self, settings_manager: SettingsManager
    ) -> None:
        """Empty filepath should be ignored."""
        settings_manager.add_recent_file("")

        recent = settings_manager.get_recent_files()
        assert len(recent) == 0

    def test_add_recent_file_emits_signal(
        self, settings_manager: SettingsManager, tmp_path: Path, qtbot
    ) -> None:
        """add_recent_file should emit recentFilesChanged signal."""
        filepath = str(tmp_path / "test.png")

        with qtbot.waitSignal(settings_manager.recentFilesChanged, timeout=1000) as blocker:
            settings_manager.add_recent_file(filepath)

        assert filepath in blocker.args[0]

    def test_get_recent_files_returns_copy(
        self, settings_manager: SettingsManager, tmp_path: Path
    ) -> None:
        """get_recent_files should return a copy of the list."""
        filepath = str(tmp_path / "test.png")
        settings_manager.add_recent_file(filepath)

        recent = settings_manager.get_recent_files()
        recent.clear()  # Modify the returned list

        # Original should be unchanged
        assert len(settings_manager.get_recent_files()) == 1

    def test_clear_recent_files(
        self, settings_manager: SettingsManager, tmp_path: Path
    ) -> None:
        """clear_recent_files should remove all recent files."""
        settings_manager.add_recent_file(str(tmp_path / "test.png"))

        settings_manager.clear_recent_files()

        assert len(settings_manager.get_recent_files()) == 0

    def test_remove_recent_file(
        self, settings_manager: SettingsManager, tmp_path: Path
    ) -> None:
        """remove_recent_file should remove specific file."""
        file1 = str(tmp_path / "file1.png")
        file2 = str(tmp_path / "file2.png")

        settings_manager.add_recent_file(file1)
        settings_manager.add_recent_file(file2)
        settings_manager.remove_recent_file(file1)

        recent = settings_manager.get_recent_files()
        assert len(recent) == 1
        assert file1 not in recent
        assert file2 in recent

    def test_cleanup_recent_files_removes_nonexistent(
        self, settings_manager: SettingsManager, tmp_path: Path
    ) -> None:
        """cleanup_recent_files should remove non-existent files."""
        existing_file = tmp_path / "exists.png"
        existing_file.touch()
        nonexistent_file = tmp_path / "nonexistent.png"

        # Manually add both (bypass cleanup on add)
        settings_manager._recent_files = [str(existing_file), str(nonexistent_file)]

        settings_manager.cleanup_recent_files()

        recent = settings_manager.get_recent_files()
        assert len(recent) == 1
        assert str(existing_file) in recent


# ============================================================================
# Reset to Defaults Tests
# ============================================================================


class TestResetToDefaults:
    """Tests for reset_to_defaults functionality."""

    def test_reset_to_defaults_clears_settings(
        self, settings_manager: SettingsManager
    ) -> None:
        """reset_to_defaults should clear all settings."""
        settings_manager.set_value('test/key', 'value')

        settings_manager.reset_to_defaults()

        # Should return default now
        value = settings_manager.get_value('test/key', 'default')
        assert value == 'default'

    def test_reset_to_defaults_clears_recent_files(
        self, settings_manager: SettingsManager, tmp_path: Path
    ) -> None:
        """reset_to_defaults should clear recent files."""
        settings_manager.add_recent_file(str(tmp_path / "test.png"))

        settings_manager.reset_to_defaults()

        assert len(settings_manager.get_recent_files()) == 0

    def test_reset_to_defaults_emits_signal(
        self, settings_manager: SettingsManager, qtbot
    ) -> None:
        """reset_to_defaults should emit recentFilesChanged signal."""
        with qtbot.waitSignal(settings_manager.recentFilesChanged, timeout=1000) as blocker:
            settings_manager.reset_to_defaults()

        assert blocker.args[0] == []


# ============================================================================
# Signal Emission Tests
# ============================================================================


class TestSignalEmission:
    """Tests for proper signal emission."""

    def test_settings_changed_signal_has_key_and_value(
        self, settings_manager: SettingsManager, qtbot
    ) -> None:
        """settingsChanged signal should emit key and value."""
        received = []
        settings_manager.settingsChanged.connect(lambda k, v: received.append((k, v)))

        settings_manager.set_value('test/signal', 123)

        assert len(received) == 1
        assert received[0] == ('test/signal', 123)

    def test_recent_files_changed_on_add(
        self, settings_manager: SettingsManager, tmp_path: Path, qtbot
    ) -> None:
        """recentFilesChanged should emit on add_recent_file."""
        received = []
        settings_manager.recentFilesChanged.connect(lambda files: received.append(files))

        filepath = str(tmp_path / "test.png")
        settings_manager.add_recent_file(filepath)

        assert len(received) == 1
        assert filepath in received[0]

    def test_recent_files_changed_on_clear(
        self, settings_manager: SettingsManager, tmp_path: Path, qtbot
    ) -> None:
        """recentFilesChanged should emit on clear_recent_files."""
        settings_manager.add_recent_file(str(tmp_path / "test.png"))

        received = []
        settings_manager.recentFilesChanged.connect(lambda files: received.append(files))

        settings_manager.clear_recent_files()

        assert len(received) == 1
        assert received[0] == []


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_get_value_with_none_default_uses_config(
        self, settings_manager: SettingsManager
    ) -> None:
        """get_value with None default should use Config.Settings.DEFAULTS."""
        from config import Config

        # Ensure the value is not set
        settings_manager._settings.remove('animation/loop_mode')

        value = settings_manager.get_value('animation/loop_mode')

        assert value == Config.Settings.DEFAULTS['animation/loop_mode']

    def test_restore_geometry_with_non_qbytearray_fails_gracefully(
        self, qapp, settings_manager: SettingsManager
    ) -> None:
        """restore_window_geometry should handle non-QByteArray values."""
        # Set invalid geometry value
        settings_manager._settings.setValue('window/geometry', 'not a byte array')

        window = QMainWindow()
        result = settings_manager.restore_window_geometry(window)

        assert result is False

    def test_restore_splitter_with_non_qbytearray_fails_gracefully(
        self, qapp, settings_manager: SettingsManager
    ) -> None:
        """restore_splitter_state should handle non-QByteArray values."""
        settings_manager._settings.setValue('window/splitter', 'not a byte array')

        splitter = QSplitter()
        result = settings_manager.restore_splitter_state(splitter, 'window/splitter')

        assert result is False

    def test_load_recent_files_handles_non_list(
        self, settings_manager: SettingsManager
    ) -> None:
        """_load_recent_files should handle non-list values."""
        settings_manager._settings.setValue('recent/files', 'not a list')

        settings_manager._load_recent_files()

        # Should default to empty list
        assert settings_manager._recent_files == []

    def test_remove_nonexistent_recent_file_safe(
        self, settings_manager: SettingsManager, tmp_path: Path
    ) -> None:
        """remove_recent_file should be safe for nonexistent files."""
        settings_manager.add_recent_file(str(tmp_path / "exists.png"))

        # Should not raise
        settings_manager.remove_recent_file(str(tmp_path / "nonexistent.png"))

        # Original file should still be there
        assert len(settings_manager.get_recent_files()) == 1

    def test_multiple_sync_calls_safe(
        self, settings_manager: SettingsManager
    ) -> None:
        """Multiple sync calls should be safe."""
        settings_manager.set_value('test/key', 'value')

        # Multiple syncs should not raise
        settings_manager.sync()
        settings_manager.sync()
        settings_manager.sync()

        # Value should still be retrievable
        assert settings_manager.get_value('test/key') == 'value'
