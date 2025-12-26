#!/usr/bin/env python3
"""
Settings Manager Module
=======================

Manages application settings persistence using QSettings.
Provides centralized access to user preferences and application state.
"""

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from PySide6.QtCore import QByteArray, QObject, QSettings, QTimer, Signal
from PySide6.QtWidgets import QMainWindow, QSplitter

from config import Config


class SettingsManager(QObject):
    """
    Centralized settings management for the Sprite Viewer application.

    Handles persistence of:
    - Window geometry and state
    - Frame extraction settings
    - Display preferences
    - Animation settings
    - Recent files list
    """

    # Signals for settings changes
    settingsChanged = Signal(str, object)  # key, value
    recentFilesChanged = Signal(list)  # updated recent files list

    def __init__(self):
        super().__init__()

        # Initialize QSettings
        self._settings = QSettings(
            Config.Settings.ORGANIZATION_NAME,
            Config.Settings.APPLICATION_NAME
        )

        # Auto-save timer for debounced saving
        self._autosave_timer = QTimer()
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.timeout.connect(self._auto_save)

        # Track pending changes for auto-save
        self._pending_changes: dict[str, Any] = {}

        # Recent files cache
        self._recent_files: list[str] = []
        self._load_recent_files()

    def get_value(self, key: str, default_value: Any = None) -> Any:
        """
        Get a setting value with fallback to configured defaults.

        Args:
            key: Settings key (e.g., 'window/geometry')
            default_value: Override default (if None, uses Config.Settings.DEFAULTS)

        Returns:
            Setting value or default
        """
        # Use provided default or configured default
        if default_value is None:
            default_value = Config.Settings.DEFAULTS.get(key)

        return self._settings.value(key, default_value)

    def set_value(self, key: str, value: Any, auto_save: bool = True) -> None:
        """
        Set a setting value with optional auto-save.

        Args:
            key: Settings key
            value: Value to store
            auto_save: Whether to trigger auto-save timer
        """
        self._settings.setValue(key, value)

        if auto_save:
            self._pending_changes[key] = value
            self._start_autosave_timer()

        # Emit change signal
        self.settingsChanged.emit(key, value)

        # Special handling for recent files
        if key == 'recent/files':
            self._recent_files = value if value else []
            self.recentFilesChanged.emit(self._recent_files)

    def _start_autosave_timer(self) -> None:
        """Start or restart the auto-save timer."""
        self._autosave_timer.start(Config.Settings.AUTOSAVE_DELAY_MS)

    def _auto_save(self) -> None:
        """Auto-save pending changes."""
        if self._pending_changes:
            self._settings.sync()
            self._pending_changes.clear()

    def sync(self) -> None:
        """Force immediate synchronization of settings to disk.

        Stops the autosave timer and flushes all pending changes.
        Should be called during application shutdown.
        """
        self._autosave_timer.stop()
        self._settings.sync()
        self._pending_changes.clear()

    # Window geometry methods
    def save_window_geometry(self, window: QMainWindow) -> None:
        """Save window geometry and state."""
        self.set_value('window/geometry', window.saveGeometry())
        self.set_value('window/state', window.saveState())

    def restore_window_geometry(self, window: QMainWindow) -> bool:
        """
        Restore window geometry and state.

        Returns:
            True if geometry was restored, False if using defaults
        """
        geometry = self.get_value('window/geometry')
        state = self.get_value('window/state')

        restored = False
        if geometry and isinstance(geometry, QByteArray):
            window.restoreGeometry(geometry)
            restored = True

        if state and isinstance(state, QByteArray):
            window.restoreState(state)
            restored = True

        return restored

    def save_splitter_state(self, splitter: QSplitter, key: str = 'window/splitter_state') -> None:
        """Save splitter state."""
        self.set_value(key, splitter.saveState())

    def restore_splitter_state(self, splitter: QSplitter, key: str = 'window/splitter_state') -> bool:
        """
        Restore splitter state.

        Returns:
            True if state was restored, False otherwise
        """
        state = self.get_value(key)
        if state and isinstance(state, QByteArray):
            return splitter.restoreState(state)
        return False

    # Frame extraction settings
    def save_extraction_settings(self, width: int, height: int, offset_x: int = 0,
                                offset_y: int = 0, spacing_x: int = 0, spacing_y: int = 0,
                                mode: str = 'grid') -> None:
        """Save last used frame extraction settings."""
        self.set_value('extraction/last_width', width)
        self.set_value('extraction/last_height', height)
        self.set_value('extraction/last_offset_x', offset_x)
        self.set_value('extraction/last_offset_y', offset_y)
        self.set_value('extraction/last_spacing_x', spacing_x)
        self.set_value('extraction/last_spacing_y', spacing_y)
        self.set_value('extraction/last_mode', mode)

    def get_extraction_settings(self) -> dict[str, Any]:
        """Get last used frame extraction settings."""
        return {
            'width': self.get_value('extraction/last_width'),
            'height': self.get_value('extraction/last_height'),
            'offset_x': self.get_value('extraction/last_offset_x'),
            'offset_y': self.get_value('extraction/last_offset_y'),
            'spacing_x': self.get_value('extraction/last_spacing_x'),
            'spacing_y': self.get_value('extraction/last_spacing_y'),
            'mode': self.get_value('extraction/last_mode')
        }

    # Display preferences
    def save_display_settings(self, grid_visible: bool, zoom: float, zoom_fit_tiny: bool) -> None:
        """Save display preferences."""
        self.set_value('display/grid_visible', grid_visible)
        self.set_value('display/last_zoom', zoom)
        self.set_value('display/zoom_fit_tiny', zoom_fit_tiny)

    def get_display_settings(self) -> dict[str, Any]:
        """Get display preferences."""
        return {
            'grid_visible': self.get_value('display/grid_visible'),
            'last_zoom': self.get_value('display/last_zoom'),
            'zoom_fit_tiny': self.get_value('display/zoom_fit_tiny')
        }

    # Animation settings
    def save_animation_settings(self, fps: int, loop_mode: bool) -> None:
        """Save animation preferences."""
        self.set_value('animation/last_fps', fps)
        self.set_value('animation/loop_mode', loop_mode)

    def get_animation_settings(self) -> dict[str, Any]:
        """Get animation preferences."""
        return {
            'fps': self.get_value('animation/last_fps'),
            'loop_mode': self.get_value('animation/loop_mode')
        }

    # Recent files management
    def add_recent_file(self, filepath: str) -> None:
        """
        Add a file to the recent files list.

        Args:
            filepath: Full path to the file to add
        """
        if not filepath:
            return

        # Convert to absolute path
        abs_path = str(Path(filepath).resolve())

        # Remove if already in list
        if abs_path in self._recent_files:
            self._recent_files.remove(abs_path)

        # Add to beginning
        self._recent_files.insert(0, abs_path)

        # Trim to max size
        max_files = self.get_value('recent/max_count', Config.Settings.MAX_RECENT_FILES)
        self._recent_files = self._recent_files[:max_files]

        # Save to settings
        self.set_value('recent/files', self._recent_files)

    def get_recent_files(self) -> list[str]:
        """Get list of recent files (most recent first)."""
        return self._recent_files.copy()

    def clear_recent_files(self) -> None:
        """Clear all recent files."""
        self._recent_files = []
        self.set_value('recent/files', [])

    def remove_recent_file(self, filepath: str) -> None:
        """Remove a specific file from recent files."""
        abs_path = str(Path(filepath).resolve())
        if abs_path in self._recent_files:
            self._recent_files.remove(abs_path)
            self.set_value('recent/files', self._recent_files)

    def cleanup_recent_files(self) -> None:
        """Remove non-existent files from recent files list."""
        valid_files = []
        for filepath in self._recent_files:
            if Path(filepath).exists():
                valid_files.append(filepath)

        if len(valid_files) != len(self._recent_files):
            self._recent_files = valid_files
            self.set_value('recent/files', self._recent_files)

    def _load_recent_files(self) -> None:
        """Load recent files from settings."""
        recent_files = self.get_value('recent/files', [])
        self._recent_files = recent_files if isinstance(recent_files, list) else []

        # Clean up non-existent files on load
        self.cleanup_recent_files()

    # Utility methods
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        self._settings.clear()
        self._recent_files = []
        self.recentFilesChanged.emit([])

    def export_settings(self, filepath: str) -> bool:
        """
        Export settings to a JSON file using atomic write.

        Args:
            filepath: Path to save the settings file

        Returns:
            True if successful, False otherwise
        """
        temp_path = None
        try:
            # Gather all settings
            settings_dict = {}
            for key in Config.Settings.DEFAULTS:
                value = self.get_value(key)
                # Convert QByteArray to base64 string for JSON serialization
                if isinstance(value, QByteArray):
                    value = bytes(value.toBase64().data()).decode('ascii')
                settings_dict[key] = value

            # Atomic write: write to temp file, then rename
            dir_path = os.path.dirname(filepath) or "."
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=dir_path,
                delete=False,
                suffix='.tmp',
                encoding='utf-8'
            ) as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)
                temp_path = f.name

            # Atomic rename (works on POSIX and Windows)
            os.replace(temp_path, filepath)
            return True
        except Exception as e:
            # Clean up temp file if it exists
            if temp_path is not None:
                with contextlib.suppress(OSError):
                    os.unlink(temp_path)
            print(f"Failed to export settings: {e}")
            return False

    def import_settings(self, filepath: str) -> bool:
        """
        Import settings from a JSON file.

        Args:
            filepath: Path to the settings file to import

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, encoding='utf-8') as f:
                settings_dict = json.load(f)

            # Apply imported settings
            for key, value in settings_dict.items():
                # Convert base64 strings back to QByteArray for geometry settings
                if (key.endswith('/geometry') or key.endswith('/state')) and isinstance(value, str):
                    value = QByteArray.fromBase64(value.encode('utf-8'))

                self.set_value(key, value, auto_save=False)

            # Force sync after import
            self.sync()
            return True
        except Exception as e:
            print(f"Failed to import settings: {e}")
            return False


# Singleton implementation (consolidated pattern)
_settings_instance: SettingsManager | None = None

def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance


def reset_settings_manager() -> None:
    """Reset the global settings manager instance (for testing)."""
    global _settings_instance
    _settings_instance = None

def initialize_settings() -> SettingsManager:
    """Initialize and return the settings manager."""
    return get_settings_manager()
