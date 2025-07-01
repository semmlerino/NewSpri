"""
Menu Manager - Centralized menu and toolbar construction
Provides structured menu definitions and dynamic updates.
Part of Phase 5: Architecture refactoring for better maintainability.
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QMenuBar, QMenu, QToolBar, QMainWindow
from PySide6.QtGui import QAction

from managers.action_manager import get_actionmanager, ActionManager


class MenuItemType(Enum):
    """Types of menu items."""
    ACTION = "action"           # Regular action
    SEPARATOR = "separator"     # Menu separator
    SUBMENU = "submenu"        # Submenu
    RECENT_FILES = "recent_files"  # Recent files insertion point
    CUSTOM = "custom"          # Custom widget/handler


@dataclass
class MenuItemDefinition:
    """Definition of a menu item."""
    item_type: MenuItemType
    action_id: Optional[str] = None      # Action ID for ACTION type
    text: Optional[str] = None           # Text for SUBMENU type
    items: Optional[List['MenuItemDefinition']] = None  # Items for SUBMENU type
    handler: Optional[callable] = None   # Custom handler for CUSTOM type
    
    def __post_init__(self):
        """Validate menu item definition."""
        if self.item_type == MenuItemType.ACTION and not self.action_id:
            raise ValueError("ACTION items must have action_id")
        elif self.item_type == MenuItemType.SUBMENU:
            if not self.text:
                raise ValueError("SUBMENU items must have text")
            if not self.items:
                self.items = []


@dataclass
class MenuDefinition:
    """Definition of a complete menu."""
    menu_id: str
    text: str
    items: List[MenuItemDefinition]
    
    def __post_init__(self):
        """Validate menu definition."""
        if not self.menu_id or not self.text:
            raise ValueError("Menu must have ID and text")
        if not self.items:
            self.items = []


@dataclass
class ToolbarDefinition:
    """Definition of a toolbar."""
    toolbar_id: str
    name: str
    items: List[MenuItemDefinition]
    movable: bool = False
    
    def __post_init__(self):
        """Validate toolbar definition."""
        if not self.toolbar_id or not self.name:
            raise ValueError("Toolbar must have ID and name")
        if not self.items:
            self.items = []


class MenuManager(QObject):
    """
    Centralized menu and toolbar construction system.
    
    Features:
    - Structured menu definitions
    - Integration with ActionManager
    - Recent files support
    - Dynamic menu updates
    - Context-sensitive menus
    """
    
    # Signal emitted when menus need updating
    menuUpdateRequested = Signal()
    
    # Structured menu definitions
    MENU_DEFINITIONS = {
        'file': MenuDefinition(
            menu_id='file',
            text='File',
            items=[
                MenuItemDefinition(MenuItemType.ACTION, action_id='file_open'),
                MenuItemDefinition(MenuItemType.RECENT_FILES),
                MenuItemDefinition(MenuItemType.SEPARATOR),
                MenuItemDefinition(MenuItemType.ACTION, action_id='file_export_frames'),
                MenuItemDefinition(MenuItemType.ACTION, action_id='file_export_current'),
                MenuItemDefinition(MenuItemType.SEPARATOR),
                MenuItemDefinition(MenuItemType.ACTION, action_id='file_quit'),
            ]
        ),
        
        'view': MenuDefinition(
            menu_id='view',
            text='View',
            items=[
                MenuItemDefinition(MenuItemType.ACTION, action_id='view_zoom_in'),
                MenuItemDefinition(MenuItemType.ACTION, action_id='view_zoom_out'),
                MenuItemDefinition(MenuItemType.ACTION, action_id='view_zoom_fit'),
                MenuItemDefinition(MenuItemType.ACTION, action_id='view_zoom_reset'),
                MenuItemDefinition(MenuItemType.SEPARATOR),
                MenuItemDefinition(MenuItemType.ACTION, action_id='view_toggle_grid'),
            ]
        ),
        
        'help': MenuDefinition(
            menu_id='help',
            text='Help',
            items=[
                MenuItemDefinition(MenuItemType.ACTION, action_id='help_shortcuts'),
                MenuItemDefinition(MenuItemType.SEPARATOR),
                MenuItemDefinition(MenuItemType.ACTION, action_id='help_about'),
            ]
        ),
    }
    
    # Toolbar definitions
    TOOLBAR_DEFINITIONS = {
        'main': ToolbarDefinition(
            toolbar_id='main',
            name='Main Toolbar',
            movable=False,
            items=[
                MenuItemDefinition(MenuItemType.ACTION, action_id='file_open'),
                MenuItemDefinition(MenuItemType.SEPARATOR),
                MenuItemDefinition(MenuItemType.ACTION, action_id='view_zoom_in'),
                MenuItemDefinition(MenuItemType.ACTION, action_id='view_zoom_out'),
                MenuItemDefinition(MenuItemType.ACTION, action_id='view_zoom_fit'),
                MenuItemDefinition(MenuItemType.ACTION, action_id='view_zoom_reset'),
                MenuItemDefinition(MenuItemType.SEPARATOR),
                MenuItemDefinition(MenuItemType.ACTION, action_id='toolbar_export'),
            ]
        ),
    }
    
    def __init__(self, parent: QMainWindow = None):
        """
        Initialize menu manager.
        
        Args:
            parent: Parent main window
        """
        super().__init__(parent)
        self._parent_window = parent
        self._action_manager = get_actionmanager(parent)
        self._menus: Dict[str, QMenu] = {}
        self._toolbars: Dict[str, QToolBar] = {}
        self._menu_definitions: Dict[str, MenuDefinition] = {}
        self._toolbar_definitions: Dict[str, ToolbarDefinition] = {}
        self._recent_files_handler: Optional[callable] = None
        
        # Load default definitions
        self._load_default_definitions()
        
        # Connect to action manager updates
        self._action_manager.actionStateChanged.connect(self._on_action_state_changed)
    
    def _load_default_definitions(self):
        """Load default menu and toolbar definitions."""
        self._menu_definitions.update(self.MENU_DEFINITIONS)
        self._toolbar_definitions.update(self.TOOLBAR_DEFINITIONS)
    
    def set_recent_files_handler(self, handler: callable):
        """
        Set handler for recent files menu creation.
        
        Args:
            handler: Function that takes a QMenu and adds recent files
        """
        self._recent_files_handler = handler
    
    def create_menu_bar(self, menu_bar: QMenuBar) -> Dict[str, QMenu]:
        """
        Create all menus in the menu bar.
        
        Args:
            menu_bar: QMenuBar to populate
            
        Returns:
            Dictionary mapping menu IDs to QMenu instances
        """
        menus = {}
        
        # Create menus in order
        for menu_id in ['file', 'view', 'help']:  # Specific order
            if menu_id in self._menu_definitions:
                menu = self._create_menu(menu_id, menu_bar)
                if menu:
                    menus[menu_id] = menu
                    self._menus[menu_id] = menu
        
        return menus
    
    def _create_menu(self, menu_id: str, parent) -> Optional[QMenu]:
        """
        Create a menu from definition.
        
        Args:
            menu_id: Menu identifier
            parent: Parent widget (QMenuBar or QMenu)
            
        Returns:
            Created QMenu or None if definition not found
        """
        if menu_id not in self._menu_definitions:
            return None
        
        definition = self._menu_definitions[menu_id]
        
        # Create menu
        if hasattr(parent, 'addMenu'):
            menu = parent.addMenu(definition.text)
        else:
            menu = QMenu(definition.text, parent)
        
        # Populate menu items
        self._populate_menu_items(menu, definition.items)
        
        return menu
    
    def _populate_menu_items(self, menu: QMenu, items: List[MenuItemDefinition]):
        """
        Populate menu with items from definitions.
        
        Args:
            menu: QMenu to populate
            items: List of menu item definitions
        """
        for item in items:
            if item.item_type == MenuItemType.ACTION:
                self._add_action_to_menu(menu, item.action_id)
            
            elif item.item_type == MenuItemType.SEPARATOR:
                menu.addSeparator()
            
            elif item.item_type == MenuItemType.SUBMENU:
                submenu = menu.addMenu(item.text)
                if item.items:
                    self._populate_menu_items(submenu, item.items)
            
            elif item.item_type == MenuItemType.RECENT_FILES:
                self._add_recent_files_to_menu(menu)
            
            elif item.item_type == MenuItemType.CUSTOM:
                if item.handler:
                    item.handler(menu)
    
    def _add_action_to_menu(self, menu: QMenu, action_id: str):
        """
        Add an action to a menu.
        
        Args:
            menu: QMenu to add to
            action_id: Action identifier
        """
        action = self._action_manager.get_action(action_id)
        if not action:
            # Create action if it doesn't exist
            action = self._action_manager.create_action(action_id)
        
        if action:
            menu.addAction(action)
    
    def _add_recent_files_to_menu(self, menu: QMenu):
        """
        Add recent files to a menu.
        
        Args:
            menu: QMenu to add recent files to
        """
        if self._recent_files_handler:
            self._recent_files_handler(menu)
    
    def create_toolbar(self, toolbar_id: str) -> Optional[QToolBar]:
        """
        Create a toolbar from definition.
        
        Args:
            toolbar_id: Toolbar identifier
            
        Returns:
            Created QToolBar or None if definition not found
        """
        if toolbar_id not in self._toolbar_definitions:
            return None
        
        definition = self._toolbar_definitions[toolbar_id]
        
        # Create toolbar
        toolbar = QToolBar(definition.name, self._parent_window)
        toolbar.setMovable(definition.movable)
        
        # Add to parent window if available
        if self._parent_window:
            self._parent_window.addToolBar(toolbar)
        
        # Populate toolbar items
        self._populate_toolbar_items(toolbar, definition.items)
        
        # Store toolbar
        self._toolbars[toolbar_id] = toolbar
        
        return toolbar
    
    def _populate_toolbar_items(self, toolbar: QToolBar, items: List[MenuItemDefinition]):
        """
        Populate toolbar with items from definitions.
        
        Args:
            toolbar: QToolBar to populate
            items: List of menu item definitions
        """
        for item in items:
            if item.item_type == MenuItemType.ACTION:
                self._add_action_to_toolbar(toolbar, item.action_id)
            
            elif item.item_type == MenuItemType.SEPARATOR:
                toolbar.addSeparator()
            
            elif item.item_type == MenuItemType.CUSTOM:
                if item.handler:
                    item.handler(toolbar)
    
    def _add_action_to_toolbar(self, toolbar: QToolBar, action_id: str):
        """
        Add an action to a toolbar.
        
        Args:
            toolbar: QToolBar to add to
            action_id: Action identifier
        """
        action = self._action_manager.get_action(action_id)
        if not action:
            # Create action if it doesn't exist
            action = self._action_manager.create_action(action_id)
        
        if action:
            toolbar.addAction(action)
    
    def get_menu(self, menu_id: str) -> Optional[QMenu]:
        """
        Get a created menu by ID.
        
        Args:
            menu_id: Menu identifier
            
        Returns:
            QMenu if found, None otherwise
        """
        return self._menus.get(menu_id)
    
    def get_toolbar(self, toolbar_id: str) -> Optional[QToolBar]:
        """
        Get a created toolbar by ID.
        
        Args:
            toolbar_id: Toolbar identifier
            
        Returns:
            QToolBar if found, None otherwise
        """
        return self._toolbars.get(toolbar_id)
    
    def update_menu_states(self):
        """Update menu item states based on current context."""
        # Action states are automatically updated by ActionManager
        self.menuUpdateRequested.emit()
    
    def _on_action_state_changed(self, action_id: str, enabled: bool):
        """
        Handle action state changes.
        
        Args:
            action_id: Action identifier
            enabled: New enabled state
        """
        # Actions automatically update their enabled state
        # We could add additional logic here if needed
        pass
    
    def register_menu_definition(self, menu_id: str, definition: MenuDefinition) -> bool:
        """
        Register a custom menu definition.
        
        Args:
            menu_id: Menu identifier
            definition: Menu definition
            
        Returns:
            True if successful, False if ID already exists
        """
        if menu_id in self._menu_definitions:
            print(f"Warning: Menu ID '{menu_id}' already exists")
            return False
        
        self._menu_definitions[menu_id] = definition
        return True
    
    def register_toolbar_definition(self, toolbar_id: str, definition: ToolbarDefinition) -> bool:
        """
        Register a custom toolbar definition.
        
        Args:
            toolbar_id: Toolbar identifier
            definition: Toolbar definition
            
        Returns:
            True if successful, False if ID already exists
        """
        if toolbar_id in self._toolbar_definitions:
            print(f"Warning: Toolbar ID '{toolbar_id}' already exists")
            return False
        
        self._toolbar_definitions[toolbar_id] = definition
        return True
    
    def get_menu_definition(self, menu_id: str) -> Optional[MenuDefinition]:
        """
        Get menu definition by ID.
        
        Args:
            menu_id: Menu identifier
            
        Returns:
            MenuDefinition if found, None otherwise
        """
        return self._menu_definitions.get(menu_id)
    
    def get_toolbar_definition(self, toolbar_id: str) -> Optional[ToolbarDefinition]:
        """
        Get toolbar definition by ID.
        
        Args:
            toolbar_id: Toolbar identifier
            
        Returns:
            ToolbarDefinition if found, None otherwise
        """
        return self._toolbar_definitions.get(toolbar_id)
    
    def get_all_menu_ids(self) -> List[str]:
        """
        Get all registered menu IDs.
        
        Returns:
            List of menu identifiers
        """
        return list(self._menu_definitions.keys())
    
    def get_all_toolbar_ids(self) -> List[str]:
        """
        Get all registered toolbar IDs.
        
        Returns:
            List of toolbar identifiers
        """
        return list(self._toolbar_definitions.keys())


# Singleton implementation (consolidated pattern)
_menu_manager_instance: Optional[MenuManager] = None

def get_menu_manager(parent: QMainWindow = None) -> MenuManager:
    """Get the global menu manager instance."""
    global _menu_manager_instance
    if _menu_manager_instance is None:
        _menu_manager_instance = MenuManager(parent)
    return _menu_manager_instance

def reset_menu_manager():
    """Reset the global menu manager instance (for testing)."""
    global _menu_manager_instance
    _menu_manager_instance = None