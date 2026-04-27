"""
Common UI components and utilities for reducing code duplication.
Part of Phase 2 refactoring: Code Deduplication.
"""

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QPushButton

from utils.styles import StyleManager


class AutoButtonManager(QObject):
    """Manages auto-detection button states and styles."""

    # Button types
    BUTTON_TYPES = ["frame", "margins", "spacing"]

    # Confidence styles
    CONFIDENCE_STYLES = {
        "high": {
            "color": "#2e7d32",  # Green
            "background": "#e8f5e9",
            "border": StyleManager.Colors.SUCCESS,
            "icon": "✓",
        },
        "medium": {
            "color": "#ef6c00",  # Orange
            "background": "#fff3e0",
            "border": StyleManager.Colors.WARNING,
            "icon": "⚠",
        },
        "low": {
            "color": "#c62828",  # Red
            "background": "#ffebee",
            "border": StyleManager.Colors.DANGER,
            "icon": "!",
        },
        "failed": {
            "color": "#424242",  # Gray
            "background": "#f5f5f5",
            "border": "#9e9e9e",
            "icon": "✗",
        },
    }

    # Default tooltips
    DEFAULT_TOOLTIPS = {
        "frame": "Auto-detect frame size",
        "margins": "Auto-detect margins",
        "spacing": "Auto-detect frame spacing",
    }

    def __init__(self):
        super().__init__()
        self._buttons: dict[str, QPushButton] = {}
        self._base_styles: dict[str, str] = {}
        self._current_states: dict[str, str] = {}

    def register_button(self, button_type: str, button: QPushButton):
        """Register a button to be managed."""
        if button_type not in self.BUTTON_TYPES:
            raise ValueError(f"Invalid button type: {button_type}")

        self._buttons[button_type] = button
        self._base_styles[button_type] = button.styleSheet()
        self._current_states[button_type] = "default"

    def update_confidence(self, button_type: str, confidence: str, message: str = ""):
        """Update button appearance based on confidence level."""
        button = self._buttons.get(button_type)
        if not button:
            return

        # Get style info
        style_info = self.CONFIDENCE_STYLES.get(confidence, self.CONFIDENCE_STYLES["failed"])

        # Update button style
        button.setStyleSheet(self._create_button_style(style_info))

        # Update button text with icon
        button.setText(f"{style_info['icon']} Auto")

        # Update tooltip
        self._update_tooltip(button, button_type, confidence, message)

        # Track state
        self._current_states[button_type] = confidence

    def reset_button(self, button_type: str):
        """Reset button to default appearance."""
        button = self._buttons.get(button_type)
        if not button:
            return

        # Reset style
        button.setStyleSheet(self._base_styles.get(button_type, ""))
        button.setText("Auto")
        button.setToolTip(self.DEFAULT_TOOLTIPS.get(button_type, "Auto-detect"))

        # Track state
        self._current_states[button_type] = "default"

    def reset_all_buttons(self):
        """Reset all managed buttons to default."""
        for button_type in self._buttons:
            self.reset_button(button_type)

    def get_button_state(self, button_type: str) -> str:
        """Get current state of a button."""
        return self._current_states.get(button_type, "default")

    @staticmethod
    def _create_button_style(style_info: dict[str, str]) -> str:
        """Create button stylesheet from style info."""
        return f"""
            QPushButton {{
                background-color: {style_info["background"]};
                border: 2px solid {style_info["border"]};
                color: {style_info["color"]};
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: {style_info["border"]};
                color: white;
            }}
        """

    def _update_tooltip(self, button: QPushButton, button_type: str, confidence: str, message: str):
        """Update button tooltip with confidence information."""
        base_tooltip = self.DEFAULT_TOOLTIPS.get(button_type, "Auto-detect")

        if message and confidence != "default":
            confidence_desc = {
                "high": "High confidence",
                "medium": "Medium confidence",
                "low": "Low confidence",
                "failed": "Detection failed",
            }.get(confidence, "Unknown")

            button.setToolTip(f"{base_tooltip}\n{confidence_desc}: {message}")
        else:
            button.setToolTip(base_tooltip)
