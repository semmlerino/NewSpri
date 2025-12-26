"""
UI tests for menu actions.
Tests that menu actions trigger their corresponding methods.
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QMenu


def _find_menu(viewer, menu_name: str) -> QMenu | None:
    """Helper to find a menu by name."""
    for action in viewer.menuBar().actions():
        if action.text() == menu_name:
            return action.menu()
    return None


def _find_action_in_menu(menu: QMenu, action_text: str):
    """Helper to find an action by text substring."""
    for action in menu.actions():
        try:
            if action.text() and action_text in action.text():
                return action
        except RuntimeError:
            pass
    return None


class TestMenuActionTriggers:
    """Test that menu actions trigger their corresponding methods."""

    def test_open_action_triggers_load_sprites(self, qtbot):
        """Test that Open action triggers _load_sprites method."""
        from sprite_viewer import SpriteViewer

        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        viewer._load_sprites = MagicMock()

        file_menu = _find_menu(viewer, "File")
        open_action = _find_action_in_menu(file_menu, "Open")

        assert open_action is not None
        open_action.trigger()

        viewer._load_sprites.assert_called_once()

    def test_quit_action_triggers_close(self, qtbot):
        """Test that Quit action triggers window close."""
        from sprite_viewer import SpriteViewer

        with patch.object(SpriteViewer, 'close') as mock_close:
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)

            file_menu = _find_menu(viewer, "File")
            quit_action = _find_action_in_menu(file_menu, "Quit")

            assert quit_action is not None
            quit_action.trigger()

            mock_close.assert_called_once()

    def test_grid_toggle_action_triggers_method(self, qtbot):
        """Test that Toggle Grid action triggers _toggle_grid method."""
        from sprite_viewer import SpriteViewer

        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        viewer._toggle_grid = MagicMock()

        view_menu = _find_menu(viewer, "View")
        grid_action = _find_action_in_menu(view_menu, "Toggle Grid")

        assert grid_action is not None
        grid_action.trigger()

        viewer._toggle_grid.assert_called_once()

    def test_keyboard_shortcuts_action_triggers_method(self, qtbot):
        """Test that Keyboard Shortcuts action triggers _show_shortcuts."""
        from sprite_viewer import SpriteViewer

        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        viewer._show_shortcuts = MagicMock()

        help_menu = _find_menu(viewer, "Help")
        shortcuts_action = _find_action_in_menu(help_menu, "Keyboard Shortcuts")

        assert shortcuts_action is not None
        shortcuts_action.trigger()

        viewer._show_shortcuts.assert_called_once()

    def test_about_action_triggers_method(self, qtbot):
        """Test that About action triggers _show_about."""
        from sprite_viewer import SpriteViewer

        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        viewer._show_about = MagicMock()

        help_menu = _find_menu(viewer, "Help")
        about_action = _find_action_in_menu(help_menu, "About")

        assert about_action is not None
        about_action.trigger()

        viewer._show_about.assert_called_once()


class TestMenuStructureSmoke:
    """Smoke test for menu structure."""

    def test_expected_menus_exist(self, qtbot):
        """Smoke test: all expected menus exist."""
        from sprite_viewer import SpriteViewer

        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        menu_names = [a.text() for a in viewer.menuBar().actions()]

        assert "File" in menu_names
        assert "View" in menu_names
        assert "Help" in menu_names


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
