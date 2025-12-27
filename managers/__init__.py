"""
Managers package - Centralized management components.

Contains all singleton manager classes that coordinate application behavior:
- Application settings persistence
- Recent files tracking
- Animation segment management
"""

# Import commonly used managers for easy access
from .animation_segment_manager import (
    AnimationSegment,
    AnimationSegmentData,  # Backward compat alias
    AnimationSegmentManager,
)
from .recent_files_manager import RecentFilesManager, get_recent_files_manager
from .settings_manager import SettingsManager, get_settings_manager

__all__ = [
    'AnimationSegment',
    'AnimationSegmentData',  # Backward compat alias
    'AnimationSegmentManager',
    'RecentFilesManager',
    'SettingsManager',
    'get_recent_files_manager',
    'get_settings_manager',
]
