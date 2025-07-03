"""
File Controller - Centralized file operations management.
Handles file loading, drag/drop, recent files, and file validation.
"""

import os
from typing import Optional, Callable, List, Tuple
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QObject, Signal, QMimeData
from PySide6.QtGui import QDropEvent

from config import Config
from managers import get_recent_files_manager


class FileController(QObject):
    """
    Centralized controller for all file operations.
    
    Handles:
    - File dialog operations
    - File loading and validation
    - Drag and drop support
    - Recent files integration
    - File path management
    """
    
    # Signals
    file_loaded = Signal(str)  # Emitted when a file is successfully loaded
    file_load_failed = Signal(str)  # Emitted when file loading fails
    
    def __init__(self):
        """Initialize the file controller."""
        super().__init__()
        self._recent_files_manager = get_recent_files_manager()
        self._current_file_path = None
        self._file_loaded_callbacks = []
        self._supported_formats = Config.File.IMAGE_FILTER
        
        # Setup recent files handler
        self._setup_recent_files()
    
    def _setup_recent_files(self):
        """Setup recent files manager handler."""
        if hasattr(self._recent_files_manager, 'set_file_open_callback'):
            self._recent_files_manager.set_file_open_callback(self._on_recent_file_selected)
    
    def _on_recent_file_selected(self, file_path: str):
        """Handle recent file selection."""
        if os.path.exists(file_path):
            self.load_file(file_path)
        else:
            self.file_load_failed.emit(f"File not found: {file_path}")
            self._recent_files_manager.remove_file(file_path)
    
    # Core file operations
    def open_file_dialog(self, parent=None) -> Optional[str]:
        """
        Show file open dialog and return selected file path.
        
        Args:
            parent: Parent widget for the dialog
            
        Returns:
            Selected file path or None if cancelled
        """
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Open Sprite Sheet",
            "",
            self._supported_formats
        )
        return file_path if file_path else None
    
    def load_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Load a file with validation.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            Tuple of (success, error_message)
        """
        # Validate file
        is_valid, error_msg = self.validate_file(file_path)
        if not is_valid:
            self.file_load_failed.emit(error_msg)
            return False, error_msg
        
        # Update current file path
        self._current_file_path = file_path
        
        # Add to recent files
        self.add_to_recent_files(file_path)
        
        # Notify callbacks
        self._notify_file_loaded(file_path)
        
        # Emit signal
        self.file_loaded.emit(file_path)
        
        return True, ""
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate a file for loading.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "No file path provided"
        
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"Not a file: {file_path}"
        
        # Check if file has a supported extension
        _, ext = os.path.splitext(file_path)
        supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        if ext.lower() not in supported_extensions:
            return False, f"Unsupported file format: {ext}"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            return False, f"File too large: {file_size / (1024 * 1024):.1f}MB (max {max_size / (1024 * 1024)}MB)"
        
        return True, ""
    
    # Drag and drop support
    def is_valid_drop(self, mime_data: QMimeData) -> bool:
        """
        Check if mime data contains valid file URLs.
        
        Args:
            mime_data: QMimeData from drag event
            
        Returns:
            True if valid file drop
        """
        if not mime_data.hasUrls():
            return False
        
        urls = mime_data.urls()
        if not urls:
            return False
        
        # Check first URL is a local file
        first_url = urls[0]
        if not first_url.isLocalFile():
            return False
        
        # Validate the file
        file_path = first_url.toLocalFile()
        is_valid, _ = self.validate_file(file_path)
        return is_valid
    
    def extract_file_from_drop(self, drop_event: QDropEvent) -> Optional[str]:
        """
        Extract file path from drop event.
        
        Args:
            drop_event: QDropEvent from drop operation
            
        Returns:
            File path or None if invalid
        """
        mime_data = drop_event.mimeData()
        if not self.is_valid_drop(mime_data):
            return None
        
        urls = mime_data.urls()
        if urls:
            return urls[0].toLocalFile()
        
        return None
    
    # Recent files integration
    def add_to_recent_files(self, file_path: str):
        """Add file to recent files list."""
        if self._recent_files_manager and hasattr(self._recent_files_manager, 'add_file_to_recent'):
            self._recent_files_manager.add_file_to_recent(file_path)
    
    def setup_recent_files_handler(self, callback: Callable[[str], None]):
        """
        Setup a custom handler for recent file selection.
        
        Args:
            callback: Function to call with selected file path
        """
        self._file_loaded_callbacks.append(callback)
    
    # File info
    def get_current_file_path(self) -> Optional[str]:
        """Get the currently loaded file path."""
        return self._current_file_path
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        info = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'directory': os.path.dirname(file_path),
            'exists': os.path.exists(file_path),
            'size': 0,
            'extension': ''
        }
        
        if info['exists'] and os.path.isfile(file_path):
            info['size'] = os.path.getsize(file_path)
            _, ext = os.path.splitext(file_path)
            info['extension'] = ext
        
        return info
    
    # Callbacks
    def register_file_loaded_callback(self, callback: Callable[[str], None]):
        """
        Register a callback to be called when a file is loaded.
        
        Args:
            callback: Function to call with file path
        """
        if callback not in self._file_loaded_callbacks:
            self._file_loaded_callbacks.append(callback)
    
    def _notify_file_loaded(self, file_path: str):
        """Notify all registered callbacks that a file was loaded."""
        for callback in self._file_loaded_callbacks:
            try:
                callback(file_path)
            except Exception as e:
                print(f"Error in file loaded callback: {e}")