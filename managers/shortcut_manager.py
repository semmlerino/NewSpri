"""
Shortcut Manager - Centralized keyboard shortcut management
Provides structured shortcut definitions, conflict detection, and auto-help generation.
Part of Phase 5: Architecture refactoring for better maintainability.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QWidget


class ShortcutContext(Enum):
    """Contexts in which shortcuts can be active."""
    GLOBAL = "global"          # Always active
    HAS_FRAMES = "has_frames"  # Only when frames are loaded
    PLAYING = "playing"        # Only during animation playback
    PAUSED = "paused"         # Only when animation is paused


@dataclass
class ShortcutDefinition:
    """Definition of a keyboard shortcut."""
    key: str                    # Key sequence (e.g., "Ctrl+O")
    description: str           # Human-readable description
    category: str              # Category for organization (e.g., "file")
    context: ShortcutContext   # When this shortcut is active
    callback: Callable | None = None  # Function to call (set during registration)
    action: QAction | None = None     # Associated QAction (if any)

    def __post_init__(self):
        """Validate shortcut definition."""
        if not self.key or not self.description:
            raise ValueError("Shortcut must have key and description")

        # Validate key sequence
        try:
            QKeySequence(self.key)
        except Exception as e:
            raise ValueError(f"Invalid key sequence '{self.key}': {e}") from e


class ShortcutManager(QObject):
    """
    Centralized keyboard shortcut management system.

    Features:
    - Structured shortcut definitions
    - Conflict detection and resolution
    - Context-sensitive shortcut handling
    - Auto-generated help documentation
    - Enable/disable shortcuts by context
    """

    # Structured shortcut definitions
    SHORTCUT_DEFINITIONS = {
        # File operations
        'file_open': ShortcutDefinition(
            "Ctrl+O", "Open sprite sheet", "file", ShortcutContext.GLOBAL
        ),
        'file_quit': ShortcutDefinition(
            "Ctrl+Q", "Quit application", "file", ShortcutContext.GLOBAL
        ),
        'file_export_frames': ShortcutDefinition(
            "Ctrl+E", "Export frames", "file", ShortcutContext.HAS_FRAMES
        ),
        'file_export_current': ShortcutDefinition(
            "Ctrl+Shift+E", "Export current frame", "file", ShortcutContext.HAS_FRAMES
        ),

        # Animation controls
        'animation_toggle': ShortcutDefinition(
            "Space", "Play/Pause animation", "animation", ShortcutContext.HAS_FRAMES
        ),
        'animation_prev_frame': ShortcutDefinition(
            "Left", "Previous frame", "animation", ShortcutContext.HAS_FRAMES
        ),
        'animation_next_frame': ShortcutDefinition(
            "Right", "Next frame", "animation", ShortcutContext.HAS_FRAMES
        ),
        'animation_first_frame': ShortcutDefinition(
            "Home", "First frame", "animation", ShortcutContext.HAS_FRAMES
        ),
        'animation_last_frame': ShortcutDefinition(
            "End", "Last frame", "animation", ShortcutContext.HAS_FRAMES
        ),
        'animation_restart': ShortcutDefinition(
            "R", "Restart animation", "animation", ShortcutContext.HAS_FRAMES
        ),
        'animation_speed_decrease': ShortcutDefinition(
            "[", "Decrease animation speed", "animation", ShortcutContext.HAS_FRAMES
        ),
        'animation_speed_increase': ShortcutDefinition(
            "]", "Increase animation speed", "animation", ShortcutContext.HAS_FRAMES
        ),

        # View controls
        'view_zoom_in': ShortcutDefinition(
            "Ctrl++", "Zoom in", "view", ShortcutContext.GLOBAL
        ),
        'view_zoom_out': ShortcutDefinition(
            "Ctrl+-", "Zoom out", "view", ShortcutContext.GLOBAL
        ),
        'view_zoom_fit': ShortcutDefinition(
            "Ctrl+0", "Fit to window", "view", ShortcutContext.GLOBAL
        ),
        'view_zoom_reset': ShortcutDefinition(
            "Ctrl+1", "Reset zoom (100%)", "view", ShortcutContext.GLOBAL
        ),
        'view_toggle_grid': ShortcutDefinition(
            "G", "Toggle grid overlay", "view", ShortcutContext.GLOBAL
        ),
    }

    def __init__(self, parent: QWidget | None = None):
        """
        Initialize shortcut manager.

        Args:
            parent: Parent widget for shortcut handling
        """
        super().__init__(parent)
        self._parent_widget = parent
        self._registered_shortcuts: dict[str, ShortcutDefinition] = {}
        self._key_to_shortcut: dict[str, str] = {}  # Key sequence -> shortcut ID
        self._current_context: ShortcutContext = ShortcutContext.GLOBAL
        self._context_state: dict[str, Any] = {}

        # Initialize with default shortcuts
        self._load_default_shortcuts()

    def _load_default_shortcuts(self):
        """Load default shortcut definitions."""
        for shortcut_id, definition in self.SHORTCUT_DEFINITIONS.items():
            self._registered_shortcuts[shortcut_id] = definition
            self._key_to_shortcut[definition.key] = shortcut_id

    def register_shortcut(self, shortcut_id: str, definition: ShortcutDefinition) -> bool:
        """
        Register a new shortcut.

        Args:
            shortcut_id: Unique identifier for the shortcut
            definition: Shortcut definition

        Returns:
            True if registration successful, False if conflict detected
        """
        # Check for conflicts
        if definition.key in self._key_to_shortcut:
            existing_id = self._key_to_shortcut[definition.key]
            if existing_id != shortcut_id:  # Allow re-registration of same shortcut
                print(f"Warning: Shortcut conflict detected! Key '{definition.key}' "
                      f"already used by '{existing_id}'")
                return False

        self._registered_shortcuts[shortcut_id] = definition
        self._key_to_shortcut[definition.key] = shortcut_id
        return True

    def unregister_shortcut(self, shortcut_id: str) -> bool:
        """
        Unregister a shortcut.

        Args:
            shortcut_id: Shortcut identifier to remove

        Returns:
            True if successful, False if shortcut not found
        """
        if shortcut_id not in self._registered_shortcuts:
            return False

        definition = self._registered_shortcuts[shortcut_id]
        del self._registered_shortcuts[shortcut_id]

        # Remove from key mapping
        if definition.key in self._key_to_shortcut:
            del self._key_to_shortcut[definition.key]

        return True

    def set_shortcut_callback(self, shortcut_id: str, callback: Callable):
        """
        Set callback function for a shortcut.

        Args:
            shortcut_id: Shortcut identifier
            callback: Function to call when shortcut is triggered
        """
        if shortcut_id in self._registered_shortcuts:
            self._registered_shortcuts[shortcut_id].callback = callback

    def set_shortcut_action(self, shortcut_id: str, action: QAction):
        """
        Associate a QAction with a shortcut.

        Args:
            shortcut_id: Shortcut identifier
            action: QAction to associate
        """
        if shortcut_id in self._registered_shortcuts:
            definition = self._registered_shortcuts[shortcut_id]
            definition.action = action
            action.setShortcut(definition.key)

    def handle_key_press(self, key_sequence: str) -> bool:
        """
        Handle a key press event.

        Args:
            key_sequence: String representation of key sequence

        Returns:
            True if shortcut was handled, False otherwise
        """
        # Find shortcut
        if key_sequence not in self._key_to_shortcut:
            return False

        shortcut_id = self._key_to_shortcut[key_sequence]
        definition = self._registered_shortcuts[shortcut_id]

        # Check if shortcut is active in current context
        if not self._is_shortcut_active(definition):
            return False

        # Execute callback if available
        if definition.callback:
            try:
                definition.callback()
                return True
            except Exception as e:
                print(f"Error executing shortcut callback for '{shortcut_id}': {e}")
                return False

        return False

    def _is_shortcut_active(self, definition: ShortcutDefinition) -> bool:
        """
        Check if a shortcut is active in the current context.

        Args:
            definition: Shortcut definition to check

        Returns:
            True if shortcut should be active
        """
        if definition.context == ShortcutContext.GLOBAL:
            return True
        elif definition.context == ShortcutContext.HAS_FRAMES:
            return self._context_state.get('has_frames', False)
        elif definition.context == ShortcutContext.PLAYING:
            return self._context_state.get('is_playing', False)
        elif definition.context == ShortcutContext.PAUSED:
            return (self._context_state.get('has_frames', False) and
                   not self._context_state.get('is_playing', False))

        return False

    def update_context(self, **context_state):
        """
        Update the current context state.

        Args:
            **context_state: Context state variables (e.g., has_frames=True)
        """
        self._context_state.update(context_state)

    def get_shortcuts_by_category(self, category: str) -> list[ShortcutDefinition]:
        """
        Get all shortcuts in a specific category.

        Args:
            category: Category name (e.g., "file", "animation", "view")

        Returns:
            List of shortcut definitions in the category
        """
        return [
            definition for definition in self._registered_shortcuts.values()
            if definition.category == category
        ]

    def get_all_categories(self) -> list[str]:
        """
        Get all available shortcut categories.

        Returns:
            List of category names
        """
        categories = {
            definition.category
            for definition in self._registered_shortcuts.values()
        }
        return sorted(categories)

    def generate_help_html(self) -> str:
        """
        Generate HTML help documentation for all shortcuts.

        Returns:
            HTML string with formatted shortcut documentation
        """
        html = ["<h3>Keyboard Shortcuts</h3>"]

        # Group by category
        for category in self.get_all_categories():
            shortcuts = self.get_shortcuts_by_category(category)
            if not shortcuts:
                continue

            # Category header
            category_title = category.replace('_', ' ').title()
            html.append(f"<h4>{category_title}</h4>")
            html.append("<table>")

            # Sort shortcuts by key sequence for consistent display
            shortcuts.sort(key=lambda s: s.key)

            for shortcut in shortcuts:
                context_info = ""
                if shortcut.context != ShortcutContext.GLOBAL:
                    context_info = f" <i>({shortcut.context.value})</i>"

                html.append(
                    f"<tr><td><b>{shortcut.key}</b></td>"
                    f"<td>{shortcut.description}{context_info}</td></tr>"
                )

            html.append("</table>")
            html.append("<br>")

        # Add mouse actions
        html.append("<h4>Mouse Actions</h4>")
        html.append("<table>")
        html.append("<tr><td><b>Mouse wheel</b></td><td>Zoom in/out</td></tr>")
        html.append("<tr><td><b>Click+drag</b></td><td>Pan view</td></tr>")
        html.append("</table>")

        return "\n".join(html)

    def detect_conflicts(self) -> list[tuple[str, str, str]]:
        """
        Detect shortcut conflicts.

        Returns:
            List of tuples: (key_sequence, shortcut_id1, shortcut_id2)
        """
        conflicts = []
        key_usage = {}

        for shortcut_id, definition in self._registered_shortcuts.items():
            key = definition.key
            if key in key_usage:
                conflicts.append((key, key_usage[key], shortcut_id))
            else:
                key_usage[key] = shortcut_id

        return conflicts

    def get_shortcut_definition(self, shortcut_id: str) -> ShortcutDefinition | None:
        """
        Get shortcut definition by ID.

        Args:
            shortcut_id: Shortcut identifier

        Returns:
            ShortcutDefinition if found, None otherwise
        """
        return self._registered_shortcuts.get(shortcut_id)

    def get_all_shortcuts(self) -> dict[str, ShortcutDefinition]:
        """
        Get all registered shortcuts.

        Returns:
            Dictionary mapping shortcut IDs to definitions
        """
        return self._registered_shortcuts.copy()


# Singleton implementation (consolidated pattern)
_shortcut_manager_instance: ShortcutManager | None = None

def get_shortcut_manager(parent: QWidget | None = None) -> ShortcutManager:
    """Get the global shortcut manager instance."""
    global _shortcut_manager_instance
    if _shortcut_manager_instance is None:
        _shortcut_manager_instance = ShortcutManager(parent)
    return _shortcut_manager_instance

def reset_shortcut_manager():
    """Reset the global shortcut manager instance (for testing)."""
    global _shortcut_manager_instance
    _shortcut_manager_instance = None
