"""
Validation Widgets
Input widgets with inline validation and helpful error guidance.
Part of Phase 1: Export Dialog Redesign implementation.
"""

import os
import re
from pathlib import Path
from typing import Callable, Optional, Tuple, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QFrame, QToolTip, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QPalette, QColor

from config import Config


class ValidationState:
    """Validation state constants."""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    NEUTRAL = "neutral"


class ValidatedLineEdit(QLineEdit):
    """Line edit with inline validation feedback and helpful messages."""
    
    validationChanged = Signal(str, str)  # state, message
    
    def __init__(self, validator_func: Optional[Callable[[str], Tuple[str, str]]] = None, parent=None):
        super().__init__(parent)
        self.validator_func = validator_func
        self._current_state = ValidationState.NEUTRAL
        self._validation_timer = QTimer()
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self._validate_input)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the validated line edit UI."""
        self.setStyleSheet(self._get_style(ValidationState.NEUTRAL))
        
    def _connect_signals(self):
        """Connect internal signals."""
        self.textChanged.connect(self._on_text_changed)
    
    def _on_text_changed(self):
        """Handle text changes with debounced validation."""
        # Reset to neutral state immediately
        if self._current_state != ValidationState.NEUTRAL:
            self.set_validation_state(ValidationState.NEUTRAL, "")
        
        # Start validation timer (debounced)
        self._validation_timer.start(300)  # 300ms delay
    
    def _validate_input(self):
        """Perform validation on current input."""
        if not self.validator_func:
            return
        
        text = self.text().strip()
        state, message = self.validator_func(text)
        self.set_validation_state(state, message)
    
    def set_validation_state(self, state: str, message: str):
        """Set the validation state and update appearance."""
        self._current_state = state
        self.setStyleSheet(self._get_style(state))
        
        # Update tooltip with validation message
        if message:
            self.setToolTip(message)
        else:
            self.setToolTip("")
        
        self.validationChanged.emit(state, message)
    
    def _get_style(self, state: str) -> str:
        """Get stylesheet for validation state."""
        base_style = """
            QLineEdit {
                padding: 6px 8px;
                border-radius: 4px;
                font-size: 11px;
            }
        """
        
        if state == ValidationState.VALID:
            return base_style + """
                QLineEdit {
                    border: 2px solid #4caf50;
                    background-color: #f1f8e9;
                }
            """
        elif state == ValidationState.WARNING:
            return base_style + """
                QLineEdit {
                    border: 2px solid #ff9800;
                    background-color: #fff8e1;
                }
            """
        elif state == ValidationState.ERROR:
            return base_style + """
                QLineEdit {
                    border: 2px solid #f44336;
                    background-color: #ffebee;
                }
            """
        else:  # NEUTRAL
            return base_style + """
                QLineEdit {
                    border: 1px solid #ddd;
                    background-color: white;
                }
                QLineEdit:focus {
                    border: 2px solid #2196f3;
                }
            """
    
    def get_validation_state(self) -> str:
        """Get current validation state."""
        return self._current_state
    
    def is_valid(self) -> bool:
        """Check if current input is valid."""
        return self._current_state in [ValidationState.VALID, ValidationState.NEUTRAL]
    
    def force_validation(self):
        """Force immediate validation."""
        self._validate_input()


class ValidationMessageWidget(QFrame):
    """Widget for displaying validation messages with icons."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.hide()  # Hidden by default
    
    def _setup_ui(self):
        """Set up the validation message widget."""
        self.setFrameStyle(QFrame.NoFrame)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Icon label
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        layout.addWidget(self.icon_label)
        
        # Message label
        self.message_label = QLabel()
        message_font = QFont()
        message_font.setPointSize(9)
        self.message_label.setFont(message_font)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label, 1)
    
    def show_message(self, state: str, message: str):
        """Show a validation message with appropriate styling."""
        if not message:
            self.hide()
            return
        
        # Set icon and styling based on state
        if state == ValidationState.VALID:
            self.icon_label.setText("✅")
            self.setStyleSheet("""
                ValidationMessageWidget {
                    background-color: #e8f5e8;
                    border-left: 3px solid #4caf50;
                    border-radius: 4px;
                }
            """)
            self.message_label.setStyleSheet("color: #2e7d32;")
            
        elif state == ValidationState.WARNING:
            self.icon_label.setText("⚠️")
            self.setStyleSheet("""
                ValidationMessageWidget {
                    background-color: #fff8e1;
                    border-left: 3px solid #ff9800;
                    border-radius: 4px;
                }
            """)
            self.message_label.setStyleSheet("color: #f57c00;")
            
        elif state == ValidationState.ERROR:
            self.icon_label.setText("❌")
            self.setStyleSheet("""
                ValidationMessageWidget {
                    background-color: #ffebee;
                    border-left: 3px solid #f44336;
                    border-radius: 4px;
                }
            """)
            self.message_label.setStyleSheet("color: #c62828;")
        
        self.message_label.setText(message)
        self.show()
    
    def hide_message(self):
        """Hide the validation message."""
        self.hide()


class SmartDirectorySelector(QWidget):
    """Directory selector with validation, suggestions, and auto-creation."""
    
    directoryChanged = Signal(str)
    validationChanged = Signal(str, str)  # state, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_directory = ""
        self._setup_ui()
        self._setup_validation()
        self._load_suggestions()
    
    def _setup_ui(self):
        """Set up the directory selector UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Input row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # Directory input with validation
        self.directory_edit = ValidatedLineEdit(self._validate_directory)
        self.directory_edit.setPlaceholderText("Select output directory...")
        input_layout.addWidget(self.directory_edit, 1)
        
        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setFixedWidth(80)
        self.browse_button.clicked.connect(self._browse_directory)
        input_layout.addWidget(self.browse_button)
        
        layout.addLayout(input_layout)
        
        # Suggestions dropdown (initially hidden)
        self.suggestions_combo = QComboBox()
        self.suggestions_combo.setVisible(False)
        self.suggestions_combo.currentTextChanged.connect(self._on_suggestion_selected)
        layout.addWidget(self.suggestions_combo)
        
        # Validation message
        self.validation_message = ValidationMessageWidget()
        layout.addWidget(self.validation_message)
    
    def _setup_validation(self):
        """Set up validation connections."""
        self.directory_edit.validationChanged.connect(self._on_validation_changed)
        self.directory_edit.textChanged.connect(self._on_text_changed)
    
    def _load_suggestions(self):
        """Load common directory suggestions."""
        suggestions = []
        
        # User's Desktop
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            suggestions.append(str(desktop))
        
        # User's Documents
        documents = Path.home() / "Documents"
        if documents.exists():
            suggestions.append(str(documents))
        
        # Current working directory
        current_dir = Path.cwd()
        suggestions.append(str(current_dir))
        
        # Common export directories
        possible_dirs = [
            Path.home() / "Downloads",
            Path.home() / "Pictures",
            current_dir / "exports",
            current_dir / "output"
        ]
        
        for dir_path in possible_dirs:
            if dir_path.exists():
                suggestions.append(str(dir_path))
        
        # Add to suggestions combo (but keep it hidden initially)
        self.suggestions_combo.addItems(suggestions)
    
    def _validate_directory(self, path: str) -> Tuple[str, str]:
        """Validate directory path."""
        if not path.strip():
            return ValidationState.NEUTRAL, ""
        
        path_obj = Path(path)
        
        # Check if path exists
        if not path_obj.exists():
            # Check if parent exists (can create)
            parent = path_obj.parent
            if parent.exists() and os.access(parent, os.W_OK):
                return ValidationState.WARNING, f"Directory will be created: {path_obj.name}"
            else:
                return ValidationState.ERROR, "Parent directory does not exist or is not writable"
        
        # Check if it's actually a directory
        if not path_obj.is_dir():
            return ValidationState.ERROR, "Path exists but is not a directory"
        
        # Check write permissions
        if not os.access(path, os.W_OK):
            return ValidationState.ERROR, "Directory is not writable"
        
        # Check if directory is empty or has existing files
        try:
            files = list(path_obj.glob("*"))
            if files:
                return ValidationState.WARNING, f"Directory contains {len(files)} items - files may be overwritten"
        except PermissionError:
            return ValidationState.ERROR, "Cannot access directory contents"
        
        return ValidationState.VALID, "Directory is ready for export"
    
    def _on_validation_changed(self, state: str, message: str):
        """Handle validation state changes."""
        self.validation_message.show_message(state, message)
        self.validationChanged.emit(state, message)
    
    def _on_text_changed(self, text: str):
        """Handle text changes."""
        self._current_directory = text
        self.directoryChanged.emit(text)
        
        # Show suggestions if text is empty
        if not text.strip():
            self._show_suggestions()
        else:
            self._hide_suggestions()
    
    def _on_suggestion_selected(self, suggestion: str):
        """Handle suggestion selection."""
        if suggestion:
            self.directory_edit.setText(suggestion)
            self._hide_suggestions()
    
    def _show_suggestions(self):
        """Show the suggestions dropdown."""
        self.suggestions_combo.setVisible(True)
    
    def _hide_suggestions(self):
        """Hide the suggestions dropdown."""
        self.suggestions_combo.setVisible(False)
    
    def _browse_directory(self):
        """Open directory browser dialog."""
        current_dir = self.directory_edit.text() or str(Path.home())
        
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if selected_dir:
            self.directory_edit.setText(selected_dir)
    
    def get_directory(self) -> str:
        """Get the current directory."""
        return self.directory_edit.text().strip()
    
    def set_directory(self, directory: str):
        """Set the directory."""
        self.directory_edit.setText(directory)
    
    def is_valid(self) -> bool:
        """Check if current directory is valid for export (including creatable directories)."""
        # For directories, WARNING state is also acceptable (directory can be created)
        current_state = self.directory_edit._current_state
        return current_state in [ValidationState.VALID, ValidationState.NEUTRAL, ValidationState.WARNING]
    
    def create_directory_if_needed(self) -> Tuple[bool, str]:
        """Create the directory if it doesn't exist."""
        directory = self.get_directory()
        if not directory:
            return False, "No directory specified"
        
        path_obj = Path(directory)
        
        if path_obj.exists():
            return True, "Directory already exists"
        
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
            return True, "Directory created successfully"
        except Exception as e:
            return False, f"Failed to create directory: {str(e)}"


class SmartFilenameEdit(ValidatedLineEdit):
    """Filename input with pattern validation and preview."""
    
    def __init__(self, parent=None):
        super().__init__(self._validate_filename, parent)
        self.setPlaceholderText("Enter base filename...")
    
    def _validate_filename(self, filename: str) -> Tuple[str, str]:
        """Validate filename input."""
        if not filename.strip():
            return ValidationState.NEUTRAL, ""
        
        # Check for invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, filename):
            return ValidationState.ERROR, "Filename contains invalid characters: < > : \" / \\ | ? *"
        
        # Check for reserved names (Windows)
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        if filename.upper() in reserved_names:
            return ValidationState.ERROR, f"'{filename}' is a reserved system name"
        
        # Check length
        if len(filename) > 200:
            return ValidationState.ERROR, "Filename is too long"
        
        # Check for spaces at start/end
        if filename != filename.strip():
            return ValidationState.WARNING, "Filename has leading or trailing spaces"
        
        return ValidationState.VALID, "Filename is valid"


class PatternEdit(ValidatedLineEdit):
    """Pattern input with preview and validation."""
    
    previewChanged = Signal(str)  # Preview text
    
    def __init__(self, parent=None):
        super().__init__(self._validate_pattern, parent)
        self.setPlaceholderText("Enter naming pattern...")
        self._setup_pattern_validation()
    
    def _setup_pattern_validation(self):
        """Set up pattern-specific validation."""
        self.textChanged.connect(self._update_preview)
    
    def _validate_pattern(self, pattern: str) -> Tuple[str, str]:
        """Validate naming pattern."""
        if not pattern.strip():
            return ValidationState.NEUTRAL, ""
        
        # Test pattern with sample data
        try:
            sample = pattern.format(name="test", index=0, frame=1)
            
            # Check for invalid filename characters in result
            invalid_chars = r'[<>:"/\\|?*]'
            if re.search(invalid_chars, sample):
                return ValidationState.ERROR, "Pattern generates invalid filename characters"
            
            return ValidationState.VALID, f"Example: {sample}.png"
            
        except KeyError as e:
            missing_key = str(e).strip("'")
            return ValidationState.ERROR, f"Unknown placeholder: {{{missing_key}}}. Use {{name}}, {{index}}, or {{frame}}"
        
        except Exception as e:
            return ValidationState.ERROR, f"Invalid pattern: {str(e)}"
    
    def _update_preview(self, pattern: str):
        """Update pattern preview."""
        if not pattern.strip():
            self.previewChanged.emit("")
            return
        
        try:
            preview = pattern.format(name="frame", index=0, frame=1)
            self.previewChanged.emit(f"Example: {preview}.png")
        except:
            self.previewChanged.emit("Invalid pattern")


# Validation functions for common use cases
def create_directory_validator() -> SmartDirectorySelector:
    """Create a smart directory selector with validation."""
    return SmartDirectorySelector()

def create_filename_validator() -> SmartFilenameEdit:
    """Create a smart filename input with validation."""
    return SmartFilenameEdit()

def create_pattern_validator() -> PatternEdit:
    """Create a pattern input with validation and preview."""
    return PatternEdit()