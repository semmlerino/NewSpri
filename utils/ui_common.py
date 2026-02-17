"""
Common UI components and utilities for reducing code duplication.
Part of Phase 2 refactoring: Code Deduplication.
"""

from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QPushButton


@dataclass
class AutoDetectionResult:
    """Unified result type for auto-detection operations."""

    success: bool
    confidence: str = "medium"  # 'high', 'medium', 'low', 'failed'
    message: str = ""
    value: Any | None = None
    x: int | None = None
    y: int | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


class AutoButtonManager(QObject):
    """Manages auto-detection button states and styles."""

    # Signals
    buttonStateChanged = Signal(str, str, str)  # button_type, confidence, message

    # Button types
    BUTTON_TYPES = ["frame", "margins", "spacing"]

    # Confidence styles
    CONFIDENCE_STYLES = {
        "high": {
            "color": "#2e7d32",  # Green
            "background": "#e8f5e9",
            "border": "#4caf50",
            "icon": "✓",
        },
        "medium": {
            "color": "#ef6c00",  # Orange
            "background": "#fff3e0",
            "border": "#ff9800",
            "icon": "⚠",
        },
        "low": {
            "color": "#c62828",  # Red
            "background": "#ffebee",
            "border": "#f44336",
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

        # Track state and emit signal
        self._current_states[button_type] = confidence
        self.buttonStateChanged.emit(button_type, confidence, message)

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
        self.buttonStateChanged.emit(button_type, "default", "")

    def reset_all_buttons(self):
        """Reset all managed buttons to default."""
        for button_type in self._buttons:
            self.reset_button(button_type)

    def get_button_state(self, button_type: str) -> str:
        """Get current state of a button."""
        return self._current_states.get(button_type, "default")

    def update_from_detection_result(self, button_type: str, result: AutoDetectionResult):
        """Update button from a DetectionResult object."""
        if result.success:
            self.update_confidence(button_type, result.confidence, result.message)
        else:
            self.update_confidence(button_type, "failed", result.message)

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


def parse_detection_tuple(result_tuple: tuple) -> AutoDetectionResult:
    """Convert legacy detection tuples to a typed auto-detection result."""
    if len(result_tuple) == 2:
        # Simple success/message format
        success, message = result_tuple
        return AutoDetectionResult(
            success=success, confidence="medium" if success else "failed", message=message
        )
    elif len(result_tuple) == 3:
        # Success/value/message format
        success, value, message = result_tuple
        return AutoDetectionResult(
            success=success,
            confidence="medium" if success else "failed",
            message=message,
            value=value,
            parameters={"value": value},
        )
    elif len(result_tuple) == 4:
        # Success/value1/value2/message format
        success, value1, value2, message = result_tuple
        return AutoDetectionResult(
            success=success,
            confidence="medium" if success else "failed",
            message=message,
            x=value1,
            y=value2,
            # Keep legacy keys for compatibility with older call sites.
            parameters={"x": value1, "y": value2, "value1": value1, "value2": value2},
        )
    else:
        raise ValueError(f"Unexpected detection result format: {result_tuple}")


def extract_confidence_from_message(message: str) -> str:
    """Extract confidence level from detection message."""
    message_lower = message.lower()

    # Check for explicit confidence indicators
    if "high confidence" in message_lower or "perfect" in message_lower:
        return "high"
    elif "medium confidence" in message_lower or "moderate" in message_lower:
        return "medium"
    elif "low confidence" in message_lower or "uncertain" in message_lower:
        return "low"
    elif "failed" in message_lower or "error" in message_lower:
        return "failed"

    # Check for percentage confidence
    import re

    percentage_match = re.search(r"(\d+)%", message)
    if percentage_match:
        percentage = int(percentage_match.group(1))
        if percentage >= 80:
            return "high"
        elif percentage >= 50:
            return "medium"
        else:
            return "low"

    # Default to medium if successful message
    return "medium"
