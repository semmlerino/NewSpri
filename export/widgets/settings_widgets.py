"""
Custom widget components for export settings.
"""

from typing import Optional, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QButtonGroup, QRadioButton, QSpinBox,
    QFileDialog, QSizePolicy, QLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import os


class SettingsCard(QFrame):
    """Card widget for grouping related settings."""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)
        
        # Title
        if title:
            title_label = QLabel(f"{icon} {title}" if icon else title)
            title_font = QFont()
            title_font.setPointSize(12)
            title_font.setBold(True)
            title_label.setFont(title_font)
            self.main_layout.addWidget(title_label)
        
        # Content layout for rows
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        self.main_layout.addLayout(self.content_layout)
    
    def add_row(self, label: str, widget: QWidget, help_text: str = "") -> QWidget:
        """Add a labeled row to the card."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(120)
        label_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row_layout.addWidget(label_widget)
        
        # Widget
        row_layout.addWidget(widget, 1)
        
        # Help text
        if help_text:
            help_label = QLabel(help_text)
            help_label.setStyleSheet("color: #6c757d; font-size: 11px;")
            row_layout.addWidget(help_label)
        
        self.content_layout.addWidget(row_widget)
        return row_widget


class SimpleDirectorySelector(QWidget):
    """Simple directory selection widget."""
    
    directoryChanged = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._directory = ""
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Directory input
        self.directory_edit = QLineEdit()
        self.directory_edit.setPlaceholderText("Select output directory...")
        self.directory_edit.setReadOnly(True)
        self.directory_edit.textChanged.connect(self._on_directory_changed)
        layout.addWidget(self.directory_edit, 1)
        
        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setMinimumWidth(80)
        self.browse_button.setFixedHeight(28)
        self.browse_button.clicked.connect(self._browse_directory)
        layout.addWidget(self.browse_button)
    
    def _browse_directory(self):
        """Open directory browser."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self._directory if self._directory else os.path.expanduser("~")
        )
        if directory:
            self.set_directory(directory)
    
    def _on_directory_changed(self):
        """Handle directory change."""
        self.directoryChanged.emit(self._directory)
    
    def set_directory(self, directory: str):
        """Set the directory."""
        self._directory = directory
        # Show abbreviated path if too long
        display_path = directory
        if len(directory) > 50:
            parts = directory.split(os.sep)
            if len(parts) > 4:
                # Show first 2 and last 2 parts
                display_path = os.sep.join(parts[:2] + ['...'] + parts[-2:])
        self.directory_edit.setText(display_path)
        self.directory_edit.setToolTip(directory)  # Full path in tooltip
        self._update_validation()
    
    def get_directory(self) -> str:
        """Get the selected directory."""
        return self._directory
    
    def is_valid(self) -> bool:
        """Check if selection is valid."""
        return bool(self._directory) and os.path.isdir(self._directory)
    
    def _update_validation(self):
        """Update validation styling."""
        if self.is_valid():
            self.directory_edit.setStyleSheet("")
        else:
            self.directory_edit.setStyleSheet("border: 1px solid #dc3545;")


class QuickScaleButtons(QWidget):
    """Quick scale selection buttons."""
    
    scaleChanged = Signal(float)
    
    def __init__(self, scales: List[float] = None, parent=None):
        super().__init__(parent)
        self.scales = scales or [1.0, 2.0, 4.0, 8.0]
        self.button_group = QButtonGroup()
        self._current_scale = 1.0
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Create scale buttons
        for i, scale in enumerate(self.scales):
            button = QRadioButton(f"{scale}x")
            button.setMinimumWidth(60)
            self.button_group.addButton(button, i)
            layout.addWidget(button)
            
            # Default selection
            if scale == 1.0:
                button.setChecked(True)
        
        # Connect signal
        self.button_group.buttonClicked.connect(self._on_button_clicked)
        
        layout.addStretch()
    
    def _on_button_clicked(self, button):
        """Handle button click."""
        button_id = self.button_group.id(button)
        self._current_scale = self.scales[button_id]
        self.scaleChanged.emit(self._current_scale)
    
    def get_scale(self) -> float:
        """Get the selected scale."""
        return self._current_scale
    
    def set_scale(self, scale: float):
        """Set the scale."""
        if scale in self.scales:
            index = self.scales.index(scale)
            button = self.button_group.button(index)
            if button:
                button.setChecked(True)
                self._current_scale = scale


class GridLayoutSelector(QWidget):
    """Grid layout configuration widget."""
    
    layoutChanged = Signal(str, int, int)  # mode, columns, rows
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode_group = QButtonGroup()
        self._mode = "auto"
        self._columns = 8
        self._rows = 8
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        
        modes = [
            ("Auto", "auto", "Automatically calculate best layout"),
            ("Columns", "columns", "Fixed number of columns"),
            ("Rows", "rows", "Fixed number of rows"),
            ("Square", "square", "Force square grid")
        ]
        
        for i, (label, mode, tooltip) in enumerate(modes):
            button = QRadioButton(label)
            button.setToolTip(tooltip)
            self.mode_group.addButton(button, i)
            mode_layout.addWidget(button)
            
            if mode == "auto":
                button.setChecked(True)
        
        layout.addLayout(mode_layout)
        
        # Number inputs
        number_widget = QWidget()
        number_layout = QHBoxLayout(number_widget)
        number_layout.setContentsMargins(0, 0, 0, 0)
        number_layout.setSpacing(16)
        
        # Columns input
        number_layout.addWidget(QLabel("Columns:"))
        self.columns_spin = QSpinBox()
        self.columns_spin.setRange(1, 100)
        self.columns_spin.setValue(8)
        self.columns_spin.setMinimumWidth(80)
        self.columns_spin.setEnabled(False)
        self.columns_spin.valueChanged.connect(self._on_value_changed)
        number_layout.addWidget(self.columns_spin)
        
        # Rows input
        number_layout.addWidget(QLabel("Rows:"))
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 100)
        self.rows_spin.setValue(8)
        self.rows_spin.setMinimumWidth(80)
        self.rows_spin.setEnabled(False)
        self.rows_spin.valueChanged.connect(self._on_value_changed)
        number_layout.addWidget(self.rows_spin)
        
        number_layout.addStretch()
        layout.addWidget(number_widget)
        
        # Connect mode changes
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
    
    def _on_mode_changed(self, button):
        """Handle mode change."""
        button_id = self.mode_group.id(button)
        modes = ["auto", "columns", "rows", "square"]
        self._mode = modes[button_id]
        
        # Enable/disable inputs
        self.columns_spin.setEnabled(self._mode == "columns")
        self.rows_spin.setEnabled(self._mode == "rows")
        
        self._emit_change()
    
    def _on_value_changed(self):
        """Handle value change."""
        if self._mode == "columns":
            self._columns = self.columns_spin.value()
        elif self._mode == "rows":
            self._rows = self.rows_spin.value()
        
        self._emit_change()
    
    def _emit_change(self):
        """Emit layout change signal."""
        self.layoutChanged.emit(self._mode, self._columns, self._rows)
    
    def get_layout(self) -> Tuple[str, int, int]:
        """Get current layout configuration."""
        return self._mode, self._columns, self._rows
    
    def set_layout(self, mode: str, columns: int = 8, rows: int = 8):
        """Set layout configuration."""
        self._mode = mode
        self._columns = columns
        self._rows = rows
        
        # Update UI
        modes = ["auto", "columns", "rows", "square"]
        if mode in modes:
            button = self.mode_group.button(modes.index(mode))
            if button:
                button.setChecked(True)
        
        self.columns_spin.setValue(columns)
        self.rows_spin.setValue(rows)
        self.columns_spin.setEnabled(mode == "columns")
        self.rows_spin.setEnabled(mode == "rows")