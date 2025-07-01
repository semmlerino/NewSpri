"""
Dialog Coordinator for SpriteViewer refactoring.
Handles help dialogs and other informational dialogs.
"""

from PySide6.QtWidgets import QMessageBox
from .base import CoordinatorBase


class DialogCoordinator(CoordinatorBase):
    """
    Coordinator responsible for showing dialogs.
    
    Manages help dialogs, about dialogs, and other informational dialogs.
    Extracts dialog logic from SpriteViewer.
    """
    
    def __init__(self, main_window):
        """Initialize dialog coordinator."""
        super().__init__(main_window)
        
        # Component references
        self.shortcut_manager = None
    
    def initialize(self, dependencies):
        """
        Initialize coordinator with required dependencies.
        
        Args:
            dependencies: Dict containing:
                - shortcut_manager: ShortcutManager instance (optional)
        """
        self.shortcut_manager = dependencies.get('shortcut_manager')
        self._initialized = True
    
    def cleanup(self):
        """Clean up resources."""
        # No specific cleanup needed for dialog coordinator
        pass
    
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog using ShortcutManager."""
        if self.shortcut_manager:
            help_html = self.shortcut_manager.generate_help_html()
            QMessageBox.information(self.main_window, "Keyboard Shortcuts", help_html)
        else:
            QMessageBox.warning(self.main_window, "Error", "Shortcut manager not available")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
<h3>Python Sprite Viewer</h3>
<p>Version 2.0 (Refactored)</p>
<p>A modern sprite sheet animation viewer with improved usability and architecture.</p>
<p>Features:</p>
<ul>
<li>Automatic frame extraction</li>
<li>Smooth animation playback</li>
<li>Intuitive controls</li>
<li>Smart size detection</li>
<li>Frame export (PNG, JPG, BMP, GIF)</li>
<li>Sprite sheet generation</li>
<li>Centralized manager architecture</li>
</ul>
        """
        QMessageBox.about(self.main_window, "About Sprite Viewer", about_text)
    
    def show_error(self, title: str, message: str):
        """
        Show error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        QMessageBox.critical(self.main_window, title, message)
    
    def show_warning(self, title: str, message: str):
        """
        Show warning dialog.
        
        Args:
            title: Dialog title
            message: Warning message
        """
        QMessageBox.warning(self.main_window, title, message)
    
    def show_info(self, title: str, message: str):
        """
        Show information dialog.
        
        Args:
            title: Dialog title
            message: Information message
        """
        QMessageBox.information(self.main_window, title, message)