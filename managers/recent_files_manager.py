#!/usr/bin/env python3
"""
Recent Files Manager Module
===========================

Manages the recent files menu and related UI functionality.
Provides integration between settings persistence and menu display.
"""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu

from config import Config
from managers.settings_manager import get_settings_manager


class RecentFilesManager(QObject):
    """
    Manages recent files menu and UI integration.

    Handles:
    - Recent files menu creation and updates
    - File validation and cleanup
    - Keyboard shortcuts for recent files
    - Welcome screen integration
    """

    # Signals
    fileRequested = Signal(str)  # Emitted when user selects a recent file
    menuUpdated = Signal()  # Emitted when menu is updated

    def __init__(self, max_display_length: int = 50):
        super().__init__()

        self._settings = get_settings_manager()
        self._max_display_length = max_display_length

        # Menu references
        self._recent_menu: QMenu | None = None
        self._file_actions: list[QAction] = []

        # Connect to settings changes
        self._settings.recentFilesChanged.connect(self._update_menu)

        # File open callback
        self._file_open_callback: Callable[[str], None] | None = None

    def set_file_open_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback function for opening files."""
        self._file_open_callback = callback

    def create_recent_files_menu(self, parent_menu: QMenu) -> QMenu:
        """
        Create and return the recent files submenu.

        Args:
            parent_menu: Parent menu to add the recent files submenu to

        Returns:
            The created recent files submenu
        """
        # Remove existing recent menu if it exists
        if self._recent_menu:
            try:
                parent_menu.removeAction(self._recent_menu.menuAction())
            except RuntimeError:
                # Menu was already deleted by Qt
                pass

        # Create new recent files submenu
        self._recent_menu = parent_menu.addMenu("Recent Files")
        self._recent_menu.setToolTip("Recently opened sprite sheets")

        # Initial population
        self._update_menu()

        return self._recent_menu

    def populate_recent_files_directly(self, parent_menu: QMenu) -> None:
        """
        Add recent files directly to the parent menu (without submenu).

        Args:
            parent_menu: Menu to add the recent files to
        """
        # Clear any existing file actions from our tracking
        self._file_actions.clear()

        # Get recent files from settings
        recent_files = self._settings.get_recent_files()

        if not recent_files:
            # Show "No recent files" placeholder
            no_files_action = parent_menu.addAction("No recent files")
            no_files_action.setEnabled(False)
            no_files_action.setToolTip("No sprite sheets have been opened recently")
            self._file_actions.append(no_files_action)
        else:
            # Add actions for each recent file
            for i, filepath in enumerate(recent_files):
                if i >= Config.Settings.MAX_RECENT_FILES:
                    break

                # Create action
                action = self._create_file_action(filepath, i + 1)
                parent_menu.addAction(action)
                self._file_actions.append(action)

            # Add separator and clear action
            parent_menu.addSeparator()
            clear_action = parent_menu.addAction("Clear Recent Files")
            clear_action.setToolTip("Remove all files from recent files list")
            clear_action.triggered.connect(self._clear_recent_files)
            self._file_actions.append(clear_action)

    def _update_menu(self) -> None:
        """Update the recent files menu with current files."""
        if not self._recent_menu:
            return

        # Clear existing actions
        self._recent_menu.clear()
        self._file_actions.clear()

        # Get recent files from settings
        recent_files = self._settings.get_recent_files()

        if not recent_files:
            # Show "No recent files" placeholder
            no_files_action = self._recent_menu.addAction("No recent files")
            no_files_action.setEnabled(False)
            no_files_action.setToolTip("No sprite sheets have been opened recently")
        else:
            # Add actions for each recent file
            for i, filepath in enumerate(recent_files):
                if i >= Config.Settings.MAX_RECENT_FILES:
                    break

                # Create action
                action = self._create_file_action(filepath, i + 1)
                self._recent_menu.addAction(action)
                self._file_actions.append(action)

            # Add separator and clear action
            self._recent_menu.addSeparator()
            clear_action = self._recent_menu.addAction("Clear Recent Files")
            clear_action.setToolTip("Remove all files from recent files list")
            clear_action.triggered.connect(self._clear_recent_files)

        # Emit update signal
        self.menuUpdated.emit()

    def _create_file_action(self, filepath: str, index: int) -> QAction:
        """
        Create a QAction for a recent file.

        Args:
            filepath: Full path to the file
            index: 1-based index for keyboard shortcut

        Returns:
            QAction for the file
        """
        # Create display name
        display_name = self._create_display_name(filepath, index)

        # Create action
        action = QAction(display_name)

        # Set tooltip with full path
        action.setToolTip(f"Open {filepath}")

        # Add keyboard shortcut for first 9 files
        if index <= 9:
            shortcut = QKeySequence(f"Alt+{index}")
            action.setShortcut(shortcut)
            action.setToolTip(f"Open {filepath} ({shortcut.toString()})")

        # Connect to file opening
        action.triggered.connect(lambda checked, path=filepath: self._open_recent_file(path))

        # Check if file still exists and gray out if not
        if not Path(filepath).exists():
            action.setEnabled(False)
            action.setText(f"{display_name} (file not found)")
            action.setToolTip(f"File not found: {filepath}")

        return action

    def _create_display_name(self, filepath: str, index: int) -> str:
        """
        Create a display name for a file path.

        Args:
            filepath: Full file path
            index: 1-based index for numbering

        Returns:
            Formatted display name
        """
        # Get filename and parent directory
        path_obj = Path(filepath)
        filename = path_obj.name
        parent_dir = path_obj.parent.name

        # Create base display text
        if parent_dir:
            base_text = f"{filename} ({parent_dir})"
        else:
            base_text = filename

        # Add numbering
        display_text = f"{index}. {base_text}"

        # Truncate if too long
        if len(display_text) > self._max_display_length:
            # Keep the index and truncate the rest
            available_length = self._max_display_length - len(f"{index}. ") - 3  # 3 for "..."
            truncated = base_text[:available_length] + "..."
            display_text = f"{index}. {truncated}"

        return display_text

    def _open_recent_file(self, filepath: str) -> None:
        """
        Handle opening a recent file.

        Args:
            filepath: Path to the file to open
        """
        # Check if file exists
        if not Path(filepath).exists():
            # File doesn't exist, remove from recent files
            self._settings.remove_recent_file(filepath)
            return

        # Emit signal for file opening
        self.fileRequested.emit(filepath)

        # Call callback if available
        if self._file_open_callback:
            self._file_open_callback(filepath)

    def _clear_recent_files(self) -> None:
        """Clear all recent files."""
        self._settings.clear_recent_files()

    def cleanup_recent_files(self) -> None:
        """Remove non-existent files from recent files list."""
        self._settings.cleanup_recent_files()

    def get_recent_files_for_welcome(self) -> list[dict]:
        """
        Get recent files formatted for welcome screen display.

        Returns:
            List of dicts with file info for welcome screen
        """
        recent_files = self._settings.get_recent_files()
        result = []

        for filepath in recent_files[:5]:  # Show only first 5 in welcome screen
            path_obj = Path(filepath)

            # Skip if file doesn't exist
            if not path_obj.exists():
                continue

            # Get file info
            file_info = {
                'path': filepath,
                'name': path_obj.name,
                'directory': path_obj.parent.name or path_obj.parent.as_posix(),
                'size': self._format_file_size(path_obj.stat().st_size),
                'modified': path_obj.stat().st_mtime,
                'exists': True
            }

            result.append(file_info)

        return result

    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size_bytes: File size in bytes

        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def add_file_to_recent(self, filepath: str) -> None:
        """
        Add a file to recent files (convenience method).

        Args:
            filepath: Path to add to recent files
        """
        self._settings.add_recent_file(filepath)

    def get_recent_files_count(self) -> int:
        """Get the number of recent files."""
        return len(self._settings.get_recent_files())

    def has_recent_files(self) -> bool:
        """Check if there are any recent files."""
        return self.get_recent_files_count() > 0


# Singleton implementation (consolidated pattern)
_recent_files_instance: RecentFilesManager | None = None

def get_recent_files_manager() -> RecentFilesManager:
    """Get the global recent files manager instance."""
    global _recent_files_instance
    if _recent_files_instance is None:
        _recent_files_instance = RecentFilesManager()
    return _recent_files_instance


def reset_recent_files_manager() -> None:
    """Reset the global recent files manager instance (for testing)."""
    global _recent_files_instance
    _recent_files_instance = None
