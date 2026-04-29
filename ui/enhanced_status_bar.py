#!/usr/bin/env python3
"""
Enhanced Status Bar Module
==========================

Status bar with temporary message and mouse-position indicator.
"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QStatusBar, QWidget

__all__ = ["EnhancedStatusBar"]


class EnhancedStatusBar(QStatusBar):
    """Status bar with temporary message + permanent mouse-coordinates label."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._message_timer = QTimer(self)
        self._message_timer.setSingleShot(True)
        self._message_timer.timeout.connect(self.clearMessage)

        self._mouse_label = QLabel("Mouse: -")
        self._mouse_label.setToolTip("Mouse position in sprite coordinates")
        self._mouse_label.setMinimumWidth(100)

        permanent_widget = QWidget()
        permanent_layout = QHBoxLayout(permanent_widget)
        permanent_layout.setContentsMargins(5, 0, 5, 0)
        permanent_layout.setSpacing(15)
        permanent_layout.addWidget(self._mouse_label)

        self.addPermanentWidget(permanent_widget)

    def show_message(self, message: str, timeout: int = 5000) -> None:
        """Show a temporary status message (timeout in ms; 0 = permanent)."""
        super().showMessage(message)
        if timeout > 0:
            self._message_timer.start(timeout)

    def update_mouse_position(self, x: int | None, y: int | None) -> None:
        """Update the mouse position label."""
        if x is not None and y is not None:
            self._mouse_label.setText(f"Mouse: ({x}, {y})")
            self._mouse_label.setToolTip(f"Mouse position in sprite coordinates: ({x}, {y})")
        else:
            self._mouse_label.setText("Mouse: -")
            self._mouse_label.setToolTip("Mouse position not available")
