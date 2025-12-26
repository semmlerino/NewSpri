"""
Action Manager - Centralized QAction creation and management
Provides structured action definitions and state management.
Part of Phase 5: Architecture refactoring for better maintainability.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget

from managers.shortcut_manager import get_shortcut_manager


class ActionCategory(Enum):
    """Categories for organizing actions."""
    FILE = "file"
    VIEW = "view"
    ANIMATION = "animation"
    HELP = "help"
    TOOLBAR = "toolbar"


@dataclass
class ActionDefinition:
    """Definition of a UI action."""
    action_id: str              # Unique identifier
    text: str                   # Display text
    category: ActionCategory    # Category for organization
    shortcut_id: str | None = None  # Associated shortcut ID
    tooltip: str = ""           # Tooltip text
    icon: str = ""             # Icon text/emoji
    callback: Callable | None = None  # Function to call
    enabled_by_default: bool = True     # Initial enabled state
    enabled_context: str | None = None  # Context requirement for enabling

    def __post_init__(self):
        """Validate action definition."""
        if not self.action_id or not self.text:
            raise ValueError("Action must have ID and text")


class ActionManager(QObject):
    """
    Centralized QAction creation and management system.

    Features:
    - Structured action definitions
    - State management (enabled/disabled)
    - Integration with ShortcutManager
    - Action lookup and grouping
    - Context-sensitive enabling
    """

    # Signal emitted when action states need updating
    actionStateChanged = Signal(str, bool)  # action_id, enabled

    # Structured action definitions
    ACTION_DEFINITIONS = {
        # File actions
        'file_open': ActionDefinition(
            "file_open", "Open...", ActionCategory.FILE,
            shortcut_id="file_open",
            tooltip="Open sprite sheet",
            icon="📁"
        ),
        'file_quit': ActionDefinition(
            "file_quit", "Quit", ActionCategory.FILE,
            shortcut_id="file_quit",
            tooltip="Quit application"
        ),
        'file_export_frames': ActionDefinition(
            "file_export_frames", "Export Frames...", ActionCategory.FILE,
            shortcut_id="file_export_frames",
            tooltip="Export frames in various formats",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),
        'file_export_current': ActionDefinition(
            "file_export_current", "Export Current Frame...", ActionCategory.FILE,
            shortcut_id="file_export_current",
            tooltip="Export only the current frame",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),

        # View actions
        'view_zoom_in': ActionDefinition(
            "view_zoom_in", "Zoom In", ActionCategory.VIEW,
            shortcut_id="view_zoom_in",
            tooltip="Zoom in",
            icon="🔍+"
        ),
        'view_zoom_out': ActionDefinition(
            "view_zoom_out", "Zoom Out", ActionCategory.VIEW,
            shortcut_id="view_zoom_out",
            tooltip="Zoom out",
            icon="🔍-"
        ),
        'view_zoom_fit': ActionDefinition(
            "view_zoom_fit", "Fit to Window", ActionCategory.VIEW,
            shortcut_id="view_zoom_fit",
            tooltip="Fit to window",
            icon="🔍⇄"
        ),
        'view_zoom_reset': ActionDefinition(
            "view_zoom_reset", "Reset Zoom", ActionCategory.VIEW,
            shortcut_id="view_zoom_reset",
            tooltip="Reset zoom (100%)",
            icon="🔍1:1"
        ),
        'view_toggle_grid': ActionDefinition(
            "view_toggle_grid", "Toggle Grid", ActionCategory.VIEW,
            shortcut_id="view_toggle_grid",
            tooltip="Toggle grid overlay"
        ),

        # Animation actions
        'animation_toggle': ActionDefinition(
            "animation_toggle", "Play/Pause", ActionCategory.ANIMATION,
            shortcut_id="animation_toggle",
            tooltip="Play/Pause animation",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),
        'animation_prev_frame': ActionDefinition(
            "animation_prev_frame", "Previous Frame", ActionCategory.ANIMATION,
            shortcut_id="animation_prev_frame",
            tooltip="Previous frame",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),
        'animation_next_frame': ActionDefinition(
            "animation_next_frame", "Next Frame", ActionCategory.ANIMATION,
            shortcut_id="animation_next_frame",
            tooltip="Next frame",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),
        'animation_first_frame': ActionDefinition(
            "animation_first_frame", "First Frame", ActionCategory.ANIMATION,
            shortcut_id="animation_first_frame",
            tooltip="First frame",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),
        'animation_last_frame': ActionDefinition(
            "animation_last_frame", "Last Frame", ActionCategory.ANIMATION,
            shortcut_id="animation_last_frame",
            tooltip="Last frame",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),
        'animation_restart': ActionDefinition(
            "animation_restart", "Restart Animation", ActionCategory.ANIMATION,
            shortcut_id="animation_restart",
            tooltip="Restart animation from first frame",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),
        'animation_speed_decrease': ActionDefinition(
            "animation_speed_decrease", "Decrease Speed", ActionCategory.ANIMATION,
            shortcut_id="animation_speed_decrease",
            tooltip="Decrease animation speed",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),
        'animation_speed_increase': ActionDefinition(
            "animation_speed_increase", "Increase Speed", ActionCategory.ANIMATION,
            shortcut_id="animation_speed_increase",
            tooltip="Increase animation speed",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),

        # Toolbar actions (special variants)
        'toolbar_export': ActionDefinition(
            "toolbar_export", "Export", ActionCategory.TOOLBAR,
            shortcut_id="file_export_frames",
            tooltip="Export frames",
            icon="💾",
            enabled_by_default=False,
            enabled_context="has_frames"
        ),

        # Help actions
        'help_shortcuts': ActionDefinition(
            "help_shortcuts", "Keyboard Shortcuts", ActionCategory.HELP,
            tooltip="Show keyboard shortcuts"
        ),
        'help_about': ActionDefinition(
            "help_about", "About", ActionCategory.HELP,
            tooltip="About Sprite Viewer"
        ),
    }

    def __init__(self, parent: QWidget | None = None):
        """
        Initialize action manager.

        Args:
            parent: Parent widget for actions
        """
        super().__init__(parent)
        self._parent_widget = parent
        self._actions: dict[str, QAction] = {}
        self._action_definitions: dict[str, ActionDefinition] = {}
        self._context_state: dict[str, Any] = {}

        # Get shortcut manager
        self._shortcut_manager = get_shortcut_manager(parent)

        # Load default actions
        self._load_default_actions()

    def _load_default_actions(self):
        """Load default action definitions."""
        for action_id, definition in self.ACTION_DEFINITIONS.items():
            self._action_definitions[action_id] = definition

    def create_action(self, action_id: str) -> QAction:
        """
        Create a QAction from definition.

        Args:
            action_id: Action identifier

        Returns:
            Created QAction

        Raises:
            ValueError: If action ID not found
        """
        if action_id not in self._action_definitions:
            raise ValueError(f"Unknown action ID: {action_id}")

        # Return existing action if already created
        if action_id in self._actions:
            return self._actions[action_id]

        definition = self._action_definitions[action_id]

        # Create action
        display_text = definition.text
        if definition.icon:
            display_text = f"{definition.icon} {definition.text}"

        action = QAction(display_text, self._parent_widget)

        # Set tooltip
        if definition.tooltip:
            full_tooltip = definition.tooltip
            if definition.shortcut_id:
                # Add shortcut to tooltip
                shortcut_def = self._shortcut_manager.get_shortcut_definition(definition.shortcut_id)
                if shortcut_def:
                    full_tooltip += f" ({shortcut_def.key})"
            action.setToolTip(full_tooltip)

        # Associate with shortcut manager
        if definition.shortcut_id:
            self._shortcut_manager.set_shortcut_action(definition.shortcut_id, action)

            # Set callback to trigger action
            if definition.callback:
                self._shortcut_manager.set_shortcut_callback(
                    definition.shortcut_id,
                    lambda: action.triggered.emit()
                )

        # Set initial enabled state
        enabled = self._should_action_be_enabled(definition)
        action.setEnabled(enabled)

        # Store action
        self._actions[action_id] = action

        return action

    def get_action(self, action_id: str) -> QAction | None:
        """
        Get existing action by ID.

        Args:
            action_id: Action identifier

        Returns:
            QAction if found, None otherwise
        """
        return self._actions.get(action_id)

    def set_action_callback(self, action_id: str, callback: Callable):
        """
        Set callback for an action.

        Args:
            action_id: Action identifier
            callback: Function to call when action is triggered
        """
        if action_id in self._action_definitions:
            self._action_definitions[action_id].callback = callback

            # Connect to existing action if created
            if action_id in self._actions:
                action = self._actions[action_id]
                action.triggered.connect(callback)

            # Update shortcut callback
            definition = self._action_definitions[action_id]
            if definition.shortcut_id:
                self._shortcut_manager.set_shortcut_callback(definition.shortcut_id, callback)

    def get_actions_by_category(self, category: ActionCategory) -> list[QAction]:
        """
        Get all actions in a specific category.

        Args:
            category: Action category

        Returns:
            List of QActions in the category
        """
        actions = []
        for action_id, definition in self._action_definitions.items():
            if definition.category == category:
                # Create action if needed
                if action_id not in self._actions:
                    self.create_action(action_id)
                actions.append(self._actions[action_id])

        return actions

    def update_context(self, **context_state):
        """
        Update context state and refresh action enabled states.

        Args:
            **context_state: Context state variables (e.g., has_frames=True)
        """
        self._context_state.update(context_state)

        # Update shortcut manager context
        self._shortcut_manager.update_context(**context_state)

        # Update action states
        self._update_action_states()

    def _update_action_states(self):
        """Update enabled states of all actions based on current context."""
        for action_id, action in self._actions.items():
            definition = self._action_definitions[action_id]
            enabled = self._should_action_be_enabled(definition)
            action.setEnabled(enabled)
            self.actionStateChanged.emit(action_id, enabled)

    def _should_action_be_enabled(self, definition: ActionDefinition) -> bool:
        """
        Check if an action should be enabled based on current context.

        Args:
            definition: Action definition to check

        Returns:
            True if action should be enabled
        """
        if not definition.enabled_by_default and not definition.enabled_context:
            return False

        if definition.enabled_context:
            return self._context_state.get(definition.enabled_context, False)

        return definition.enabled_by_default

    def create_all_actions(self) -> dict[str, QAction]:
        """
        Create all defined actions.

        Returns:
            Dictionary mapping action IDs to QActions
        """
        for action_id in self._action_definitions:
            if action_id not in self._actions:
                self.create_action(action_id)

        return self._actions.copy()

    def get_action_definition(self, action_id: str) -> ActionDefinition | None:
        """
        Get action definition by ID.

        Args:
            action_id: Action identifier

        Returns:
            ActionDefinition if found, None otherwise
        """
        return self._action_definitions.get(action_id)

    def register_action(self, action_id: str, definition: ActionDefinition) -> bool:
        """
        Register a new action definition.

        Args:
            action_id: Unique action identifier
            definition: Action definition

        Returns:
            True if successful, False if ID already exists
        """
        if action_id in self._action_definitions:
            print(f"Warning: Action ID '{action_id}' already exists")
            return False

        definition.action_id = action_id
        self._action_definitions[action_id] = definition
        return True

    def get_all_action_ids(self) -> list[str]:
        """
        Get all registered action IDs.

        Returns:
            List of action identifiers
        """
        return list(self._action_definitions.keys())

    def get_actions_requiring_context(self, context: str) -> list[str]:
        """
        Get action IDs that require a specific context.

        Args:
            context: Context requirement (e.g., "has_frames")

        Returns:
            List of action IDs requiring the context
        """
        return [
            action_id for action_id, definition in self._action_definitions.items()
            if definition.enabled_context == context
        ]


# Singleton implementation (simplified from base manager pattern)
_action_manager_instance = None

def get_actionmanager(parent: QWidget | None = None) -> ActionManager:
    """Get the global action manager instance."""
    global _action_manager_instance
    if _action_manager_instance is None:
        _action_manager_instance = ActionManager(parent)
    return _action_manager_instance

def reset_actionmanager():
    """Reset the global action manager instance (for testing)."""
    global _action_manager_instance
    _action_manager_instance = None
