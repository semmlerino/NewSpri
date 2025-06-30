"""
Foundation tests for existing menu system before Phase 4-5 enhancements.
Tests all current menu actions trigger correctly to prevent regressions.
"""

import pytest
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtGui import QAction


class TestFileMenuActions:
    """Test File menu actions work correctly."""
    
    def test_file_menu_exists(self, qtbot):
        """Test that File menu exists and is accessible."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            
            # Find File menu
            file_menu = None
            for action in menubar.actions():
                if action.text() == "File":
                    file_menu = action.menu()
                    break
            
            assert file_menu is not None, "File menu should exist"
            assert isinstance(file_menu, QMenu), "File menu should be QMenu instance"
    
    def test_open_action_configured_correctly(self, qtbot):
        """Test that Open action is configured with correct shortcut and tooltip."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            file_menu = None
            for action in menubar.actions():
                if action.text() == "File":
                    file_menu = action.menu()
                    break
            
            # Find Open action (looking for "Open..." with ellipsis)
            open_action = None
            for action in file_menu.actions():
                if action.text() and "Open" in action.text():
                    open_action = action
                    break
            
            assert open_action is not None, "Open action should exist"
            assert open_action.shortcut().toString() == "Ctrl+O"
            assert "Ctrl+O" in open_action.toolTip()
    
    def test_open_action_triggers_load_sprites(self, qtbot):
        """Test that Open action triggers _load_sprites method."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            # Mock the load sprites method
            viewer._load_sprites = MagicMock()
            
            menubar = viewer.menuBar()
            file_menu = None
            for action in menubar.actions():
                if action.text() == "File":
                    file_menu = action.menu()
                    break
            
            # Find and trigger Open action (looking for "Open..." with ellipsis)
            open_action = None
            for action in file_menu.actions():
                if action.text() and "Open" in action.text():
                    open_action = action
                    break
            
            assert open_action is not None
            open_action.trigger()
            
            # Verify _load_sprites was called
            viewer._load_sprites.assert_called_once()
    
    def test_recent_files_menu_exists(self, qtbot):
        """Test that Recent Files submenu exists."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            file_menu = None
            for action in menubar.actions():
                if action.text() == "File":
                    file_menu = action.menu()
                    break
            
            # Look for Recent Files submenu
            recent_menu = None
            for action in file_menu.actions():
                if action.menu():
                    # Check if this action has a submenu and its text contains "Recent"
                    try:
                        if action.text() and "Recent" in action.text():
                            recent_menu = action.menu()
                            break
                    except RuntimeError:
                        # Handle case where Qt object was deleted
                        pass
            
            assert recent_menu is not None, "Recent Files menu should exist"
    
    def test_quit_action_configured_correctly(self, qtbot):
        """Test that Quit action is configured with correct shortcut."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            file_menu = None
            for action in menubar.actions():
                if action.text() == "File":
                    file_menu = action.menu()
                    break
            
            # Find Quit action
            quit_action = None
            for action in file_menu.actions():
                try:
                    if action.text() and "Quit" in action.text():
                        quit_action = action
                        break
                except RuntimeError:
                    # Handle case where Qt object was deleted
                    pass
            
            assert quit_action is not None, "Quit action should exist"
            assert quit_action.shortcut().toString() == "Ctrl+Q"
    
    def test_quit_action_triggers_close(self, qtbot):
        """Test that Quit action triggers window close."""
        from sprite_viewer import SpriteViewer
        
        # Mock close method BEFORE creating the viewer  
        # so the connection gets the mocked version
        with patch.object(SpriteViewer, '_load_test_sprites'), \
             patch.object(SpriteViewer, 'close') as mock_close:
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            file_menu = None
            for action in menubar.actions():
                if action.text() == "File":
                    file_menu = action.menu()
                    break
            
            # Find and trigger Quit action
            quit_action = None
            for action in file_menu.actions():
                try:
                    if action.text() and "Quit" in action.text():
                        quit_action = action
                        break
                except RuntimeError:
                    # Handle case where Qt object was deleted
                    pass
            
            assert quit_action is not None
            quit_action.trigger()
            
            # Verify close was called
            mock_close.assert_called_once()


class TestViewMenuActions:
    """Test View menu actions work correctly."""
    
    def test_view_menu_exists(self, qtbot):
        """Test that View menu exists and is accessible."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            
            # Find View menu
            view_menu = None
            for action in menubar.actions():
                if action.text() == "View":
                    view_menu = action.menu()
                    break
            
            assert view_menu is not None, "View menu should exist"
            assert isinstance(view_menu, QMenu), "View menu should be QMenu instance"
    
    def test_view_menu_contains_zoom_actions(self, qtbot):
        """Test that View menu contains all zoom actions."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            view_menu = None
            for action in menubar.actions():
                if action.text() == "View":
                    view_menu = action.menu()
                    break
            
            assert view_menu is not None
            
            # Get all action texts in view menu (excluding separators)
            # Store action info immediately to avoid Qt object deletion
            action_texts = []
            view_menu_actions = view_menu.actions()
            for action in view_menu_actions:
                try:
                    if not action.isSeparator():
                        action_texts.append(action.text())
                except RuntimeError:
                    # Handle case where Qt object was deleted
                    pass
            
            # Should contain zoom actions and grid toggle
            expected_actions = ["🔍+", "🔍-", "🔍⇄", "🔍1:1", "Toggle Grid"]
            for expected in expected_actions:
                assert any(expected in text for text in action_texts), f"Missing action: {expected}"
    
    def test_grid_toggle_action_configured_correctly(self, qtbot):
        """Test that Toggle Grid action is configured correctly."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            view_menu = None
            for action in menubar.actions():
                if action.text() == "View":
                    view_menu = action.menu()
                    break
            
            # Find Toggle Grid action
            grid_action = None
            view_menu_actions = view_menu.actions()
            for action in view_menu_actions:
                try:
                    if "Toggle Grid" in action.text():
                        grid_action = action
                        break
                except RuntimeError:
                    # Handle case where Qt object was deleted
                    pass
            
            assert grid_action is not None, "Toggle Grid action should exist"
            assert grid_action.shortcut().toString() == "G"
            assert grid_action.isCheckable(), "Grid action should be checkable"
    
    def test_grid_toggle_action_triggers_method(self, qtbot):
        """Test that Toggle Grid action triggers _toggle_grid method."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            # Mock the toggle grid method
            viewer._toggle_grid = MagicMock()
            
            menubar = viewer.menuBar()
            view_menu = None
            for action in menubar.actions():
                if action.text() == "View":
                    view_menu = action.menu()
                    break
            
            # Find and trigger Toggle Grid action
            grid_action = None
            view_menu_actions = view_menu.actions()
            for action in view_menu_actions:
                try:
                    if "Toggle Grid" in action.text():
                        grid_action = action
                        break
                except RuntimeError:
                    # Handle case where Qt object was deleted
                    pass
            
            assert grid_action is not None
            grid_action.trigger()
            
            # Verify _toggle_grid was called
            viewer._toggle_grid.assert_called_once()


class TestHelpMenuActions:
    """Test Help menu actions work correctly."""
    
    def test_help_menu_exists(self, qtbot):
        """Test that Help menu exists and is accessible."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            
            # Find Help menu
            help_menu = None
            for action in menubar.actions():
                if action.text() == "Help":
                    help_menu = action.menu()
                    break
            
            assert help_menu is not None, "Help menu should exist"
            assert isinstance(help_menu, QMenu), "Help menu should be QMenu instance"
    
    def test_keyboard_shortcuts_action_exists(self, qtbot):
        """Test that Keyboard Shortcuts action exists and works."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            # Mock the show shortcuts method
            viewer._show_shortcuts = MagicMock()
            
            menubar = viewer.menuBar()
            help_menu = None
            for action in menubar.actions():
                if action.text() == "Help":
                    help_menu = action.menu()
                    break
            
            # Find and trigger Keyboard Shortcuts action
            shortcuts_action = None
            for action in help_menu.actions():
                if "Keyboard Shortcuts" in action.text():
                    shortcuts_action = action
                    break
            
            assert shortcuts_action is not None, "Keyboard Shortcuts action should exist"
            shortcuts_action.trigger()
            
            # Verify _show_shortcuts was called
            viewer._show_shortcuts.assert_called_once()
    
    def test_about_action_exists(self, qtbot):
        """Test that About action exists and works."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            # Mock the show about method
            viewer._show_about = MagicMock()
            
            menubar = viewer.menuBar()
            help_menu = None
            for action in menubar.actions():
                if action.text() == "Help":
                    help_menu = action.menu()
                    break
            
            # Find and trigger About action
            about_action = None
            for action in help_menu.actions():
                try:
                    if action.text() and "About" in action.text():
                        about_action = action
                        break
                except RuntimeError:
                    # Handle case where Qt object was deleted
                    pass
            
            assert about_action is not None, "About action should exist"
            about_action.trigger()
            
            # Verify _show_about was called
            viewer._show_about.assert_called_once()


class TestMenuStructure:
    """Test overall menu structure and organization."""
    
    def test_menu_structure_is_complete(self, qtbot):
        """Test that all expected menus exist."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            menu_names = [action.text() for action in menubar.actions()]
            
            expected_menus = ["File", "View", "Help"]
            for expected in expected_menus:
                assert expected in menu_names, f"Missing menu: {expected}"
    
    def test_menu_actions_are_accessible(self, qtbot):
        """Test that all menu actions are accessible and not None."""
        from sprite_viewer import SpriteViewer
        
        with patch.object(SpriteViewer, '_load_test_sprites'):
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            menubar = viewer.menuBar()
            
            for menu_action in menubar.actions():
                menu = menu_action.menu()
                if menu:  # Skip separators
                    assert menu is not None
                    
                    # Check that menu has actions
                    menu_actions = [a for a in menu.actions() if not a.isSeparator()]
                    assert len(menu_actions) > 0, f"Menu {menu_action.text()} should have actions"
                    
                    # Check that actions are properly configured
                    for action in menu_actions:
                        if action.menu() is None:  # Skip submenus
                            assert action.text() != "", "Action should have text"
                            # Actions should be either triggerable or checkable
                            assert hasattr(action, 'trigger'), "Action should be triggerable"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])