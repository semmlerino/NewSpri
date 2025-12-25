"""
Export Dialog Base - Foundation classes and utilities for export dialogs
Part of Phase 1 refactoring to split export_dialog.py into smaller modules.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QWidget, QApplication, QMessageBox,
    QProgressBar, QLabel, QPushButton, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QTimer

from config import Config


class ExportDialogBase(QDialog):
    """Base class for export dialogs with common functionality."""
    
    # Common signals
    exportRequested = Signal(dict)
    exportCancelled = Signal()
    
    def __init__(self, parent=None, frame_count: int = 0, current_frame: int = 0):
        """
        Initialize base export dialog.
        
        Args:
            parent: Parent widget
            frame_count: Total number of frames available
            current_frame: Currently selected frame index
        """
        super().__init__(parent)
        self.frame_count = frame_count
        self.current_frame = current_frame
        self._current_settings: Dict[str, Any] = {}
        
        # Export state
        self._is_exporting = False
        self._export_cancelled = False
        
        # UI components to be created by subclasses
        self.progress_bar: Optional[QProgressBar] = None
        self.progress_label: Optional[QLabel] = None
        self.export_button: Optional[QPushButton] = None
        self.cancel_button: Optional[QPushButton] = None
    
    def setup_smart_sizing(self):
        """Set up smart dialog sizing based on screen dimensions."""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        max_width = min(900, int(screen_geometry.width() * 0.6))
        max_height = min(700, int(screen_geometry.height() * 0.8))
        
        self.setMinimumSize(650, 500)
        self.setMaximumSize(max_width, max_height)
        self.resize(700, 600)  # Reasonable default size
    
    def get_default_export_directory(self) -> Path:
        """Get a reliable default export directory with fallback logic."""
        # Try Desktop first (most user-friendly)
        desktop = Path.home() / "Desktop"
        if desktop.exists() and os.access(desktop, os.W_OK):
            return desktop / "sprite_exports"
        
        # Try Documents as fallback
        documents = Path.home() / "Documents"
        if documents.exists() and os.access(documents, os.W_OK):
            return documents / "sprite_exports"
        
        # Try Downloads as second fallback
        downloads = Path.home() / "Downloads"
        if downloads.exists() and os.access(downloads, os.W_OK):
            return downloads / "sprite_exports"
        
        # Try current working directory as final fallback
        cwd = Path.cwd()
        if os.access(cwd, os.W_OK):
            return cwd / "sprite_exports"
        
        # Last resort: home directory
        return Path.home() / "sprite_exports"
    
    def create_progress_section(self) -> QWidget:
        """Create the progress feedback section."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.progress_label)
        
        return container
    
    def create_action_buttons(self) -> QWidget:
        """Create the action buttons section."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Button box
        button_box = QDialogButtonBox(Qt.Orientation.Horizontal)
        
        # Export button
        self.export_button = QPushButton("Export Frames")
        self.export_button.setDefault(True)
        self.export_button.setMinimumHeight(Config.UI.PLAYBACK_BUTTON_MIN_HEIGHT)
        button_box.addButton(self.export_button, QDialogButtonBox.ButtonRole.AcceptRole)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(Config.UI.PLAYBACK_BUTTON_MIN_HEIGHT)
        button_box.addButton(self.cancel_button, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(button_box)
        return container
    
    def validate_export_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Validate export settings before export.
        
        Args:
            settings: Export settings dictionary
            
        Returns:
            True if settings are valid, False otherwise
        """
        required_keys = ['output_dir', 'base_name', 'format', 'mode', 'scale_factor']
        
        for key in required_keys:
            if key not in settings:
                QMessageBox.critical(self, "Export Error", f"Missing required setting: {key}")
                return False
        
        # Validate output directory
        output_dir = Path(settings['output_dir'])
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to create output directory: {str(e)}")
                return False
        
        # Validate base name
        if not settings['base_name'].strip():
            QMessageBox.critical(self, "Export Error", "Base name cannot be empty")
            return False
        
        return True
    
    def on_export_started(self):
        """Handle export start."""
        self._is_exporting = True
        self._export_cancelled = False
        
        if self.export_button:
            self.export_button.setEnabled(False)
            self.export_button.setText("Exporting...")
        
        if self.cancel_button:
            self.cancel_button.setText("Cancel Export")
            self.cancel_button.setEnabled(True)
        
        if self.progress_bar:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
        
        if self.progress_label:
            self.progress_label.setVisible(True)
            self.progress_label.setText("Starting export...")
    
    def on_export_progress(self, current: int, total: int, message: str):
        """Handle export progress update."""
        if self._export_cancelled:
            return
        
        if self.progress_bar:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
        
        if self.progress_label:
            self.progress_label.setText(message)
    
    def on_export_finished(self, success: bool, message: str):
        """Handle export completion."""
        self._is_exporting = False
        
        if self.progress_bar:
            self.progress_bar.setVisible(False)
        
        if self.progress_label:
            self.progress_label.setVisible(False)
        
        if self.export_button:
            self.export_button.setEnabled(True)
            self.export_button.setText("Export Frames")
        
        if self.cancel_button:
            self.cancel_button.setText("Cancel")
            self.cancel_button.setEnabled(True)
        
        if success and not self._export_cancelled:
            # Show success and close dialog
            QMessageBox.information(self, "Export Complete", message)
            QTimer.singleShot(100, self.accept)
        elif not self._export_cancelled:
            # Show error but keep dialog open
            QMessageBox.warning(self, "Export Incomplete", message)
    
    def on_export_error(self, error_message: str):
        """Handle export error."""
        self._is_exporting = False
        
        if self.progress_bar:
            self.progress_bar.setVisible(False)
        
        if self.progress_label:
            self.progress_label.setVisible(False)
        
        if self.export_button:
            self.export_button.setEnabled(True)
            self.export_button.setText("Export Frames")
        
        if self.cancel_button:
            self.cancel_button.setText("Cancel")
            self.cancel_button.setEnabled(True)
        
        QMessageBox.critical(self, "Export Error", error_message)
    
    def on_cancel_clicked(self):
        """Handle cancel button click."""
        if self._is_exporting:
            # Cancel ongoing export
            self._export_cancelled = True
            self.exportCancelled.emit()
            
            if self.cancel_button:
                self.cancel_button.setEnabled(False)
                self.cancel_button.setText("Cancelling...")
        else:
            # Close dialog
            self.reject()