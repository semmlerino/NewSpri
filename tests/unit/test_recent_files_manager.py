"""
Unit tests for managers.recent_files_manager.

Covers:
- Singleton accessor
- Menu population (empty + populated states)
- Display-name truncation
- File-existence handling
- Open-callback dispatch
- Add / remove / clear pass-through to settings
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QMenu

from managers.recent_files_manager import (
    RecentFilesManager,
    get_recent_files_manager,
)

pytestmark = pytest.mark.requires_qt


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset both singletons to keep tests isolated."""
    import managers.recent_files_manager as _rfm_mod
    import managers.settings_manager as _sm_mod

    _sm_mod._settings_instance = None
    _rfm_mod._recent_files_instance = None
    yield
    _sm_mod._settings_instance = None
    _rfm_mod._recent_files_instance = None


@pytest.fixture
def manager(qapp) -> RecentFilesManager:
    """Fresh RecentFilesManager backed by the global SettingsManager singleton."""
    mgr = RecentFilesManager()
    # Wipe persisted state so each test starts clean
    mgr._settings.clear_recent_files()
    return mgr


@pytest.fixture
def existing_sprite(tmp_path: Path) -> Path:
    """Create a sprite-like file on disk."""
    f = tmp_path / "real.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n")  # PNG magic bytes; enough for Path.exists()
    return f


# ============================================================================
# Singleton
# ============================================================================


class TestSingleton:
    @pytest.mark.smoke
    def test_get_recent_files_manager_returns_same_instance(self, qapp):
        first = get_recent_files_manager()
        second = get_recent_files_manager()
        assert first is second
        assert isinstance(first, RecentFilesManager)


# ============================================================================
# Menu population
# ============================================================================


class TestMenuPopulation:
    def test_empty_menu_shows_disabled_placeholder(self, manager):
        menu = QMenu()
        manager.populate_recent_files_directly(menu)

        actions = [a for a in menu.actions() if not a.isSeparator()]
        assert len(actions) == 1
        assert actions[0].text() == "No recent files"
        assert not actions[0].isEnabled()

    def test_populated_menu_lists_files_and_clear_action(self, manager, existing_sprite, tmp_path):
        # Add two real files
        manager._settings.add_recent_file(str(existing_sprite))
        second = tmp_path / "second.png"
        second.write_bytes(b"\x89PNG\r\n\x1a\n")
        manager._settings.add_recent_file(str(second))

        menu = QMenu()
        manager.populate_recent_files_directly(menu)

        named_actions = [a for a in menu.actions() if not a.isSeparator()]
        # 2 file entries + Clear Recent Files
        assert len(named_actions) == 3
        assert named_actions[-1].text() == "Clear Recent Files"

    def test_missing_file_action_is_disabled(self, manager, tmp_path):
        ghost = str(tmp_path / "missing.png")
        manager._settings.add_recent_file(ghost)

        menu = QMenu()
        manager.populate_recent_files_directly(menu)

        file_actions = [
            a for a in menu.actions() if not a.isSeparator() and "missing" in a.text().lower()
        ]
        assert len(file_actions) == 1
        assert not file_actions[0].isEnabled()
        assert "(file not found)" in file_actions[0].text()


# ============================================================================
# Display-name truncation
# ============================================================================


class TestDisplayName:
    def test_short_path_includes_index_and_filename(self, manager):
        name = manager._create_display_name("/dir/short.png", index=1)
        assert name.startswith("1. ")
        assert "short.png" in name

    def test_long_path_truncated_to_max_length(self, qapp):
        mgr = RecentFilesManager(max_display_length=30)
        long_path = "/very/long/parent/" + "x" * 100 + ".png"
        name = mgr._create_display_name(long_path, index=2)
        assert len(name) <= 30
        assert name.startswith("2. ")
        assert name.endswith("...")


# ============================================================================
# File-open dispatch
# ============================================================================


class TestOpenCallback:
    def test_existing_file_invokes_callback(self, manager, existing_sprite):
        callback = MagicMock()
        manager.set_file_open_callback(callback)
        manager._open_recent_file(str(existing_sprite))
        callback.assert_called_once_with(str(existing_sprite))

    def test_missing_file_removes_from_recent_and_skips_callback(self, manager, tmp_path):
        ghost = str(tmp_path / "vanished.png")
        manager._settings.add_recent_file(ghost)

        callback = MagicMock()
        manager.set_file_open_callback(callback)
        manager._open_recent_file(ghost)

        callback.assert_not_called()
        # Settings should no longer contain the ghost path
        assert ghost not in manager._settings.get_recent_files()


# ============================================================================
# Convenience pass-through
# ============================================================================


class TestPassThrough:
    def test_add_file_to_recent_delegates_to_settings(self, manager, existing_sprite):
        manager.add_file_to_recent(str(existing_sprite))
        recent = manager._settings.get_recent_files()
        assert len(recent) == 1
        assert Path(recent[0]).name == "real.png"

    def test_clear_recent_files_empties_list(self, manager, existing_sprite):
        manager._settings.add_recent_file(str(existing_sprite))
        manager._clear_recent_files()
        assert manager._settings.get_recent_files() == []
