"""
Unit tests for MenuManager functionality.
Tests the centralized menu and toolbar construction system.
"""

import pytest
from unittest.mock import MagicMock

from menu_manager import (
    MenuManager, MenuDefinition, ToolbarDefinition, 
    MenuItemDefinition, MenuItemType,
    get_menu_manager, reset_menu_manager
)


class TestMenuItemDefinition:
    """Test MenuItemDefinition class."""
    
    def test_action_item_creation(self):
        """Test creating an action menu item."""
        item = MenuItemDefinition(MenuItemType.ACTION, action_id="test_action")
        
        assert item.item_type == MenuItemType.ACTION
        assert item.action_id == "test_action"
        assert item.text is None
        assert item.items is None
    
    def test_separator_item_creation(self):
        """Test creating a separator menu item."""
        item = MenuItemDefinition(MenuItemType.SEPARATOR)
        
        assert item.item_type == MenuItemType.SEPARATOR
        assert item.action_id is None
    
    def test_submenu_item_creation(self):
        """Test creating a submenu item."""
        sub_items = [MenuItemDefinition(MenuItemType.ACTION, action_id="sub_action")]
        item = MenuItemDefinition(MenuItemType.SUBMENU, text="Submenu", items=sub_items)
        
        assert item.item_type == MenuItemType.SUBMENU
        assert item.text == "Submenu"
        assert len(item.items) == 1
    
    def test_action_item_validation(self):
        """Test validation of action items."""
        with pytest.raises(ValueError, match="ACTION items must have action_id"):
            MenuItemDefinition(MenuItemType.ACTION)
    
    def test_submenu_item_validation(self):
        """Test validation of submenu items."""
        with pytest.raises(ValueError, match="SUBMENU items must have text"):
            MenuItemDefinition(MenuItemType.SUBMENU)
        
        # Should create empty items list if not provided
        item = MenuItemDefinition(MenuItemType.SUBMENU, text="Test")
        assert item.items == []


class TestMenuDefinition:
    """Test MenuDefinition class."""
    
    def test_menu_definition_creation(self):
        """Test creating a menu definition."""
        items = [MenuItemDefinition(MenuItemType.ACTION, action_id="test_action")]
        menu_def = MenuDefinition("test_menu", "Test Menu", items)
        
        assert menu_def.menu_id == "test_menu"
        assert menu_def.text == "Test Menu"
        assert len(menu_def.items) == 1
    
    def test_menu_definition_validation(self):
        """Test menu definition validation."""
        items = [MenuItemDefinition(MenuItemType.ACTION, action_id="test_action")]
        
        # Test empty menu_id
        with pytest.raises(ValueError, match="Menu must have ID and text"):
            MenuDefinition("", "Test Menu", items)
        
        # Test empty text
        with pytest.raises(ValueError, match="Menu must have ID and text"):
            MenuDefinition("test_menu", "", items)
        
        # Should create empty items list if not provided
        menu_def = MenuDefinition("test_menu", "Test Menu", [])
        assert menu_def.items == []


class TestToolbarDefinition:
    """Test ToolbarDefinition class."""
    
    def test_toolbar_definition_creation(self):
        """Test creating a toolbar definition."""
        items = [MenuItemDefinition(MenuItemType.ACTION, action_id="test_action")]
        toolbar_def = ToolbarDefinition("test_toolbar", "Test Toolbar", items, movable=True)
        
        assert toolbar_def.toolbar_id == "test_toolbar"
        assert toolbar_def.name == "Test Toolbar"
        assert len(toolbar_def.items) == 1
        assert toolbar_def.movable is True
    
    def test_toolbar_definition_validation(self):
        """Test toolbar definition validation."""
        items = [MenuItemDefinition(MenuItemType.ACTION, action_id="test_action")]
        
        # Test empty toolbar_id
        with pytest.raises(ValueError, match="Toolbar must have ID and name"):
            ToolbarDefinition("", "Test Toolbar", items)
        
        # Test empty name
        with pytest.raises(ValueError, match="Toolbar must have ID and name"):
            ToolbarDefinition("test_toolbar", "", items)


class TestMenuManager:
    """Test MenuManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_menu_manager()
        self.manager = MenuManager()
    
    def test_manager_initialization(self):
        """Test menu manager initialization."""
        assert isinstance(self.manager, MenuManager)
        
        # Check that default menus are loaded
        menu_ids = self.manager.get_all_menu_ids()
        assert "file" in menu_ids
        assert "view" in menu_ids
        assert "help" in menu_ids
        
        # Check that default toolbars are loaded
        toolbar_ids = self.manager.get_all_toolbar_ids()
        assert "main" in toolbar_ids
    
    def test_menu_definition_retrieval(self):
        """Test retrieving menu definitions."""
        # Test existing menu
        file_menu = self.manager.get_menu_definition("file")
        assert file_menu is not None
        assert file_menu.text == "File"
        assert len(file_menu.items) >= 5  # Should have several items
        
        # Test non-existent menu
        non_existent = self.manager.get_menu_definition("non_existent")
        assert non_existent is None
    
    def test_toolbar_definition_retrieval(self):
        """Test retrieving toolbar definitions."""
        # Test existing toolbar
        main_toolbar = self.manager.get_toolbar_definition("main")
        assert main_toolbar is not None
        assert main_toolbar.name == "Main Toolbar"
        assert len(main_toolbar.items) >= 5  # Should have several items
        
        # Test non-existent toolbar
        non_existent = self.manager.get_toolbar_definition("non_existent")
        assert non_existent is None
    
    def test_menu_definition_registration(self):
        """Test registering custom menu definitions."""
        items = [MenuItemDefinition(MenuItemType.ACTION, action_id="custom_action")]
        custom_menu = MenuDefinition("custom_menu", "Custom Menu", items)
        
        # Register menu
        success = self.manager.register_menu_definition("custom_menu", custom_menu)
        assert success
        
        # Verify registration
        retrieved = self.manager.get_menu_definition("custom_menu")
        assert retrieved is not None
        assert retrieved.text == "Custom Menu"
        
        # Test duplicate registration
        duplicate_success = self.manager.register_menu_definition("custom_menu", custom_menu)
        assert not duplicate_success
    
    def test_toolbar_definition_registration(self):
        """Test registering custom toolbar definitions."""
        items = [MenuItemDefinition(MenuItemType.ACTION, action_id="custom_action")]
        custom_toolbar = ToolbarDefinition("custom_toolbar", "Custom Toolbar", items)
        
        # Register toolbar
        success = self.manager.register_toolbar_definition("custom_toolbar", custom_toolbar)
        assert success
        
        # Verify registration
        retrieved = self.manager.get_toolbar_definition("custom_toolbar")
        assert retrieved is not None
        assert retrieved.name == "Custom Toolbar"
        
        # Test duplicate registration
        duplicate_success = self.manager.register_toolbar_definition("custom_toolbar", custom_toolbar)
        assert not duplicate_success
    
    def test_recent_files_handler(self):
        """Test recent files handler management."""
        handler_called = []
        
        def mock_handler(menu):
            handler_called.append(menu)
        
        # Set handler
        self.manager.set_recent_files_handler(mock_handler)
        
        # Verify handler is stored (we can't easily test the actual call without creating QMenus)
        assert self.manager._recent_files_handler == mock_handler
    
    def test_menu_structure_validation(self):
        """Test that default menu structures are valid."""
        for menu_id in self.manager.get_all_menu_ids():
            menu_def = self.manager.get_menu_definition(menu_id)
            
            # Check that menu has items
            assert len(menu_def.items) > 0
            
            # Check that action items have valid action IDs
            for item in menu_def.items:
                if item.item_type == MenuItemType.ACTION:
                    assert item.action_id is not None
                    assert item.action_id != ""
    
    def test_toolbar_structure_validation(self):
        """Test that default toolbar structures are valid."""
        for toolbar_id in self.manager.get_all_toolbar_ids():
            toolbar_def = self.manager.get_toolbar_definition(toolbar_id)
            
            # Check that toolbar has items
            assert len(toolbar_def.items) > 0
            
            # Check that action items have valid action IDs
            for item in toolbar_def.items:
                if item.item_type == MenuItemType.ACTION:
                    assert item.action_id is not None
                    assert item.action_id != ""
    
    def test_singleton_instance(self):
        """Test singleton instance functionality."""
        manager1 = get_menu_manager()
        manager2 = get_menu_manager()
        
        assert manager1 is manager2  # Should be same instance
        
        # Reset and test again
        reset_menu_manager()
        manager3 = get_menu_manager()
        
        assert manager3 is not manager1  # Should be new instance after reset


class TestMenuItemTypes:
    """Test MenuItemType enum."""
    
    def test_menu_item_type_values(self):
        """Test menu item type enum values."""
        assert MenuItemType.ACTION.value == "action"
        assert MenuItemType.SEPARATOR.value == "separator"
        assert MenuItemType.SUBMENU.value == "submenu"
        assert MenuItemType.RECENT_FILES.value == "recent_files"
        assert MenuItemType.CUSTOM.value == "custom"


class TestMenuIntegration:
    """Test integration scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_menu_manager()
        self.manager = MenuManager()
    
    def test_file_menu_structure(self):
        """Test file menu structure completeness."""
        file_menu = self.manager.get_menu_definition("file")
        
        # Should have open action
        has_open = any(item.action_id == "file_open" for item in file_menu.items 
                      if item.item_type == MenuItemType.ACTION)
        assert has_open
        
        # Should have recent files
        has_recent = any(item.item_type == MenuItemType.RECENT_FILES for item in file_menu.items)
        assert has_recent
        
        # Should have export actions
        has_export = any(item.action_id and "export" in item.action_id for item in file_menu.items 
                        if item.item_type == MenuItemType.ACTION)
        assert has_export
        
        # Should have separators
        has_separator = any(item.item_type == MenuItemType.SEPARATOR for item in file_menu.items)
        assert has_separator
    
    def test_view_menu_structure(self):
        """Test view menu structure completeness."""
        view_menu = self.manager.get_menu_definition("view")
        
        # Should have zoom actions
        zoom_actions = [item.action_id for item in view_menu.items 
                       if item.item_type == MenuItemType.ACTION and item.action_id and "zoom" in item.action_id]
        assert len(zoom_actions) >= 3  # Should have zoom in, out, fit, reset
        
        # Should have grid toggle
        has_grid = any(item.action_id == "view_toggle_grid" for item in view_menu.items 
                      if item.item_type == MenuItemType.ACTION)
        assert has_grid
    
    def test_main_toolbar_structure(self):
        """Test main toolbar structure completeness."""
        main_toolbar = self.manager.get_toolbar_definition("main")
        
        # Should have file open
        has_open = any(item.action_id == "file_open" for item in main_toolbar.items 
                      if item.item_type == MenuItemType.ACTION)
        assert has_open
        
        # Should have zoom actions
        zoom_actions = [item.action_id for item in main_toolbar.items 
                       if item.item_type == MenuItemType.ACTION and item.action_id and "zoom" in item.action_id]
        assert len(zoom_actions) >= 3
        
        # Should have export action
        has_export = any(item.action_id == "toolbar_export" for item in main_toolbar.items 
                        if item.item_type == MenuItemType.ACTION)
        assert has_export
        
        # Should have separators
        has_separator = any(item.item_type == MenuItemType.SEPARATOR for item in main_toolbar.items)
        assert has_separator


if __name__ == '__main__':
    pytest.main([__file__, '-v'])