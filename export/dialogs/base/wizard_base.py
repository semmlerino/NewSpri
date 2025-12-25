"""
Export Wizard Widget Framework
Provides a clean wizard interface for multi-step processes.
Part of Export Dialog Usability Improvements.
"""

from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QProgressBar
)
from PySide6.QtCore import Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont



class WizardStep(QWidget):
    """Base class for wizard steps."""
    
    # Signals
    stepValidated = Signal(bool)  # Emitted when validation state changes
    dataChanged = Signal(dict)    # Emitted when step data changes
    
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self._is_valid = True
        self._step_data = {}
        
    def validate(self) -> bool:
        """Validate the step. Override in subclasses."""
        return self._is_valid
    
    def get_data(self) -> Dict[str, Any]:
        """Get step data. Override in subclasses."""
        return self._step_data
    
    def set_data(self, data: Dict[str, Any]):
        """Set step data. Override in subclasses."""
        self._step_data = data
    
    def on_entering(self):
        """Called when entering this step. Override for setup."""
        pass
    
    def on_leaving(self):
        """Called when leaving this step. Override for cleanup."""
        pass


class WizardWidget(QWidget):
    """
    Modern wizard widget with step navigation and validation.
    Features:
    - Step-by-step navigation with Back/Next buttons
    - Visual progress indicator
    - Step validation before proceeding
    - Smooth transitions between steps
    """
    
    # Signals
    wizardFinished = Signal(dict)  # Emitted when wizard completes with all data
    wizardCancelled = Signal()     # Emitted when wizard is cancelled
    currentStepChanged = Signal(int)  # Emitted when step changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps: List[WizardStep] = []
        self.current_step_index = 0
        self._wizard_data = {}
        
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self):
        """Set up the wizard UI structure."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header section with progress
        self.header_widget = self._create_header()
        layout.addWidget(self.header_widget)
        
        # Content area (stacked widget for steps)
        self.content_stack = QStackedWidget()
        self.content_stack.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content_stack, 1)
        
        # Navigation section
        self.nav_widget = self._create_navigation()
        layout.addWidget(self.nav_widget)
    
    def _create_header(self) -> QWidget:
        """Create the header section with title and progress."""
        header = QWidget()
        header.setObjectName("wizardHeader")
        header.setStyleSheet("""
            #wizardHeader {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        
        # Step title and subtitle
        self.step_title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.step_title_label.setFont(title_font)
        layout.addWidget(self.step_title_label)
        
        self.step_subtitle_label = QLabel()
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        self.step_subtitle_label.setFont(subtitle_font)
        self.step_subtitle_label.setStyleSheet("color: #6c757d;")
        self.step_subtitle_label.setWordWrap(True)
        layout.addWidget(self.step_subtitle_label)
        
        # Progress indicator
        progress_container = QWidget()
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 8, 0, 0)
        progress_layout.setSpacing(16)
        
        self.step_indicator_label = QLabel()
        self.step_indicator_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        progress_layout.addWidget(self.step_indicator_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e9ecef;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar, 1)
        
        layout.addWidget(progress_container)
        
        return header
    
    def _create_navigation(self) -> QWidget:
        """Create the navigation section with buttons."""
        nav = QWidget()
        nav.setObjectName("wizardNav")
        nav.setStyleSheet("""
            #wizardNav {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }
        """)
        
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)
        
        # Cancel button (always visible)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
        """)
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)
        
        layout.addStretch()
        
        # Back button
        self.back_button = QPushButton("← Back")
        self.back_button.setFixedHeight(40)
        self.back_button.setMinimumWidth(100)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                color: #495057;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #adb5bd;
                border-color: #e9ecef;
            }
        """)
        self.back_button.clicked.connect(self._on_back)
        layout.addWidget(self.back_button)
        
        # Next/Finish button
        self.next_button = QPushButton("Next →")
        self.next_button.setFixedHeight(40)
        self.next_button.setMinimumWidth(120)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.next_button.clicked.connect(self._on_next)
        layout.addWidget(self.next_button)
        
        return nav
    
    def _setup_animations(self):
        """Set up animations for smooth transitions."""
        # Animation for step transitions
        self.transition_animation = QPropertyAnimation(self.content_stack, b"minimumHeight")
        self.transition_animation.setDuration(200)
        self.transition_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
    def add_step(self, step: WizardStep):
        """Add a step to the wizard."""
        self.steps.append(step)
        self.content_stack.addWidget(step)
        
        # Connect step signals
        step.stepValidated.connect(self._on_step_validated)
        step.dataChanged.connect(self._on_step_data_changed)
        
        # Update UI if this is the first step
        if len(self.steps) == 1:
            self._update_current_step()
    
    def set_current_step(self, index: int):
        """Set the current step by index."""
        if 0 <= index < len(self.steps):
            # Notify current step it's being left
            if self.current_step_index < len(self.steps):
                self.steps[self.current_step_index].on_leaving()
            
            self.current_step_index = index
            self._update_current_step()
            
            # Notify new step it's being entered
            self.steps[self.current_step_index].on_entering()
            
            self.currentStepChanged.emit(index)
    
    def _update_current_step(self):
        """Update UI to reflect current step."""
        if not self.steps:
            return
        
        current_step = self.steps[self.current_step_index]
        
        # Update header
        self.step_title_label.setText(current_step.title)
        self.step_subtitle_label.setText(current_step.subtitle)
        self.step_subtitle_label.setVisible(bool(current_step.subtitle))
        
        # Update progress
        step_text = f"Step {self.current_step_index + 1} of {len(self.steps)}"
        self.step_indicator_label.setText(step_text)
        
        progress_value = int(((self.current_step_index + 1) / len(self.steps)) * 100)
        self.progress_bar.setValue(progress_value)
        
        # Update content
        self.content_stack.setCurrentIndex(self.current_step_index)
        
        # Update navigation buttons
        self.back_button.setEnabled(self.current_step_index > 0)
        
        # Update next button text
        if self.current_step_index == len(self.steps) - 1:
            self.next_button.setText("Finish")
        else:
            self.next_button.setText("Next →")
        
        # Validate current step
        self._validate_current_step()
    
    def _validate_current_step(self):
        """Validate the current step and update navigation."""
        if self.current_step_index < len(self.steps):
            is_valid = self.steps[self.current_step_index].validate()
            self.next_button.setEnabled(is_valid)
    
    def _on_step_validated(self, is_valid: bool):
        """Handle step validation changes."""
        self.next_button.setEnabled(is_valid)
    
    def _on_step_data_changed(self, data: dict):
        """Handle step data changes."""
        # Update wizard data with step data
        step_name = f"step_{self.current_step_index}"
        self._wizard_data[step_name] = data
    
    def _on_back(self):
        """Handle back button click."""
        if self.current_step_index > 0:
            self.set_current_step(self.current_step_index - 1)
    
    def _on_next(self):
        """Handle next button click."""
        # Collect data from current step
        current_step = self.steps[self.current_step_index]
        step_data = current_step.get_data()
        step_name = f"step_{self.current_step_index}"
        self._wizard_data[step_name] = step_data
        
        if self.current_step_index < len(self.steps) - 1:
            # Go to next step
            self.set_current_step(self.current_step_index + 1)
        else:
            # Finish wizard
            self._on_finish()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.wizardCancelled.emit()
    
    def _on_finish(self):
        """Handle wizard completion."""
        # Collect all data
        all_data = {}
        for _, step in enumerate(self.steps):
            step_data = step.get_data()
            all_data.update(step_data)
        
        # Also include the accumulated wizard data
        all_data.update(self._wizard_data)
        
        self.wizardFinished.emit(all_data)
    
    def get_wizard_data(self) -> Dict[str, Any]:
        """Get all collected wizard data."""
        return self._wizard_data.copy()