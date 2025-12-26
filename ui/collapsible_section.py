"""
Collapsible Section Widget
Reusable collapsible section for progressive disclosure in the UI.
Part of Phase 1: Export Dialog Redesign implementation.
"""

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class CollapsibleSection(QWidget):
    """
    Reusable collapsible section widget with smooth animations.
    Supports expanding/collapsing content with visual feedback.
    """

    expanded = Signal(bool)  # Emitted when section expands/collapses

    def __init__(self, title: str, content: QWidget, expanded: bool = True, parent=None):
        super().__init__(parent)
        self.content_widget = content
        self._is_expanded = expanded
        self._animation_duration = 200  # milliseconds

        self._setup_ui(title)
        self._setup_animations()
        self._set_expanded_state(expanded, animate=False)

    def _setup_ui(self, title: str):
        """Set up the collapsible section UI."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header section
        self.header_frame = self._create_header(title)
        self.main_layout.addWidget(self.header_frame)

        # Content container
        self.content_frame = QFrame()
        self.content_frame.setFrameStyle(QFrame.Shape.NoFrame)
        self.content_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Content layout
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(20, 8, 0, 8)  # Indent content slightly
        content_layout.addWidget(self.content_widget)

        self.main_layout.addWidget(self.content_frame)

    def _create_header(self, title: str) -> QFrame:
        """Create the clickable header section."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.NoFrame)
        header_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        header_frame.setStyleSheet("""
            QFrame:hover {
                background-color: #f5f5f5;
            }
        """)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(4, 8, 8, 8)
        header_layout.setSpacing(8)

        # Expand/collapse arrow
        self.arrow_button = QToolButton()
        self.arrow_button.setArrowType(Qt.ArrowType.DownArrow)
        self.arrow_button.setAutoRaise(True)
        self.arrow_button.setFixedSize(16, 16)
        self.arrow_button.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
                border-radius: 8px;
            }
        """)
        header_layout.addWidget(self.arrow_button)

        # Section title
        self.title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #333; margin-top: 1px;")
        header_layout.addWidget(self.title_label)

        # Stretch to push everything left
        header_layout.addStretch()

        # Optional info badge (can be set later)
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                color: #1976d2;
                border-radius: 8px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: 500;
            }
        """)
        self.info_label.hide()  # Hidden by default
        header_layout.addWidget(self.info_label)

        # Connect click events
        header_frame.mousePressEvent = self._on_header_clicked
        self.arrow_button.clicked.connect(self.toggle)

        return header_frame

    def _setup_animations(self):
        """Set up smooth expand/collapse animations."""
        # Height animation for the content frame
        self.height_animation = QPropertyAnimation(self.content_frame, b"maximumHeight")
        self.height_animation.setDuration(self._animation_duration)
        self.height_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Opacity animation for smooth visual effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.content_frame.setGraphicsEffect(self.opacity_effect)

        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(self._animation_duration)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Group animations together
        self.animation_group = QParallelAnimationGroup()
        self.animation_group.addAnimation(self.height_animation)
        self.animation_group.addAnimation(self.opacity_animation)

        # Connect animation finished signal
        self.animation_group.finished.connect(self._on_animation_finished)

    def _on_header_clicked(self, event):
        """Handle header click to toggle section."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()

    def _on_animation_finished(self):
        """Handle animation completion."""
        if not self._is_expanded:
            # Hide content completely when collapsed
            self.content_frame.hide()

        # Emit expanded signal
        self.expanded.emit(self._is_expanded)

    def toggle(self):
        """Toggle the expanded/collapsed state."""
        self.set_expanded(not self._is_expanded)

    def set_expanded(self, expanded: bool, animate: bool = True):
        """Set the expanded state of the section."""
        if self._is_expanded == expanded:
            return

        self._is_expanded = expanded
        self._set_expanded_state(expanded, animate)

    def _set_expanded_state(self, expanded: bool, animate: bool = True):
        """Internal method to set expanded state with optional animation."""
        if expanded:
            # Show content first
            self.content_frame.show()

            # Update arrow direction
            self.arrow_button.setArrowType(Qt.ArrowType.DownArrow)

            if animate:
                # Get the content height
                content_height = self.content_widget.sizeHint().height() + 16  # Add padding

                # Animate to full height
                self.height_animation.setStartValue(0)
                self.height_animation.setEndValue(content_height)

                self.opacity_animation.setStartValue(0.0)
                self.opacity_animation.setEndValue(1.0)

                self.animation_group.start()
            else:
                # Set immediately
                self.content_frame.setMaximumHeight(16777215)  # Remove height restriction
                self.opacity_effect.setOpacity(1.0)
                self.expanded.emit(True)
        else:
            # Update arrow direction
            self.arrow_button.setArrowType(Qt.ArrowType.RightArrow)

            if animate:
                # Get current height
                current_height = self.content_frame.height()

                # Animate to zero height
                self.height_animation.setStartValue(current_height)
                self.height_animation.setEndValue(0)

                self.opacity_animation.setStartValue(1.0)
                self.opacity_animation.setEndValue(0.0)

                self.animation_group.start()
            else:
                # Set immediately
                self.content_frame.setMaximumHeight(0)
                self.content_frame.hide()
                self.opacity_effect.setOpacity(0.0)
                self.expanded.emit(False)

    def is_expanded(self) -> bool:
        """Check if the section is currently expanded."""
        return self._is_expanded

    def set_title(self, title: str):
        """Set the section title."""
        self.title_label.setText(title)

    def get_title(self) -> str:
        """Get the section title."""
        return self.title_label.text()

    def set_info_badge(self, text: str, visible: bool = True):
        """Set or hide the info badge in the header."""
        if text and visible:
            self.info_label.setText(text)
            self.info_label.show()
        else:
            self.info_label.hide()

    def set_animation_duration(self, duration: int):
        """Set the animation duration in milliseconds."""
        self._animation_duration = duration
        self.height_animation.setDuration(duration)
        self.opacity_animation.setDuration(duration)

    def get_content_widget(self) -> QWidget:
        """Get the content widget."""
        return self.content_widget

    def replace_content(self, new_content: QWidget):
        """Replace the content widget with a new one."""
        # Remove old content
        layout = self.content_frame.layout()
        if layout is not None:
            layout.removeWidget(self.content_widget)
        self.content_widget.setParent(None)

        # Add new content
        self.content_widget = new_content
        layout = self.content_frame.layout()
        if layout is not None:
            layout.addWidget(self.content_widget)

        # Update layout if expanded
        if self._is_expanded:
            # Force layout update
            self.content_frame.updateGeometry()


class AdvancedCollapsibleSection(CollapsibleSection):
    """
    Enhanced collapsible section with additional features like:
    - Save/restore state
    - Custom styling
    - Progress indicators
    """

    def __init__(self, title: str, content: QWidget, section_id: str = "",
                 expanded: bool = True, parent=None):
        self.section_id = section_id
        super().__init__(title, content, expanded, parent)

    def set_progress_indicator(self, visible: bool, progress: int = 0):
        """Show/hide a progress indicator in the header."""
        # This could be enhanced to show actual progress
        if visible:
            self.set_info_badge(f"{progress}%")
        else:
            self.set_info_badge("", False)

    def set_warning_state(self, warning: bool, message: str = ""):
        """Set warning state with visual feedback."""
        if warning:
            self.title_label.setStyleSheet("color: #f57c00; font-weight: bold;")
            if message:
                self.set_info_badge("⚠️")
                self.setToolTip(message)
        else:
            self.title_label.setStyleSheet("color: #333; font-weight: bold;")
            self.set_info_badge("", False)
            self.setToolTip("")

    def save_state(self) -> dict:
        """Save the current state of the section."""
        return {
            'section_id': self.section_id,
            'expanded': self._is_expanded,
            'title': self.get_title()
        }

    def restore_state(self, state: dict):
        """Restore the section state."""
        if state.get('section_id') == self.section_id:
            expanded = state.get('expanded', True)
            self.set_expanded(expanded, animate=False)


# Convenience functions for common use cases
def create_collapsible_group(title: str, widgets: list, expanded: bool = True) -> CollapsibleSection:
    """Create a collapsible section containing multiple widgets."""
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    for widget in widgets:
        layout.addWidget(widget)

    return CollapsibleSection(title, container, expanded)

def create_advanced_section(title: str, content: QWidget, section_id: str,
                          expanded: bool = True) -> AdvancedCollapsibleSection:
    """Create an advanced collapsible section with state management."""
    return AdvancedCollapsibleSection(title, content, section_id, expanded)
