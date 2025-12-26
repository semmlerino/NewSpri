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
from .action_manager import ActionManager
from .animation_segment_manager import AnimationSegmentManager
from .menu_manager import MenuManager
from .recent_files_manager import RecentFilesManager, get_recent_files_manager
from .settings_manager import SettingsManager, get_settings_manager
from .shortcut_manager import ShortcutManager

__all__ = [
    'ActionManager',
    'AnimationSegmentManager',
    'MenuManager',
    'RecentFilesManager',
    'SettingsManager',
    'ShortcutManager',
    'get_recent_files_manager',
    'get_settings_manager',
]
