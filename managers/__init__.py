"""
Managers package - Centralized management components.

Contains all singleton manager classes that coordinate application behavior:
- Action management and QAction creation
- Menu structure and organization
- Keyboard shortcuts and hotkeys
- Application settings persistence
- Recent files tracking
- Animation segment management
"""

# Import commonly used managers for easy access
from .action_manager import get_actionmanager, ActionManager
from .menu_manager import get_menu_manager, MenuManager
from .shortcut_manager import get_shortcut_manager, ShortcutManager
from .settings_manager import get_settings_manager, SettingsManager
from .recent_files_manager import get_recent_files_manager, RecentFilesManager
from .animation_segment_manager import AnimationSegmentManager

__all__ = [
    'get_actionmanager', 'ActionManager',
    'get_menu_manager', 'MenuManager', 
    'get_shortcut_manager', 'ShortcutManager',
    'get_settings_manager', 'SettingsManager',
    'get_recent_files_manager', 'RecentFilesManager',
    'AnimationSegmentManager'
]