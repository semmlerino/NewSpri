"""
Event Coordinator for SpriteViewer refactoring.
Handles keyboard shortcuts, drag/drop events, and user input coordination.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QDragEnterEvent, QDropEvent

from .base import CoordinatorBase
from utils import StyleManager


class EventCoordinator(CoordinatorBase):
    """
    Coordinator responsible for event handling.
    
    Manages keyboard shortcuts, drag/drop operations, and coordinates
    between various managers and controllers for user input.
    Extracts event handling logic from SpriteViewer.
    """
    
    # Key mapping for special keys
    KEY_MAPPING = {
        Qt.Key.Key_Space: "Space",
        Qt.Key.Key_Left: "Left",
        Qt.Key.Key_Right: "Right",
        Qt.Key.Key_Home: "Home",
        Qt.Key.Key_End: "End",
        Qt.Key.Key_Plus: "+",
        Qt.Key.Key_Minus: "-",
    }
    
    def __init__(self, main_window):
        """Initialize event coordinator."""
        super().__init__(main_window)
        
        # Component references
        self.shortcut_manager = None
        self.file_controller = None
        self.canvas = None
        self.status_manager = None
        
        # Status message callback for welcome message
        self._show_welcome_message = None
    
    def initialize(self, dependencies):
        """
        Initialize coordinator with required dependencies.
        
        Args:
            dependencies: Dict containing:
                - shortcut_manager: ShortcutManager instance
                - file_controller: FileController instance
                - canvas: SpriteCanvas instance
                - status_manager: StatusBarManager instance
                - show_welcome_message: Callback for showing welcome message
        """
        self.shortcut_manager = dependencies['shortcut_manager']
        self.file_controller = dependencies['file_controller']
        self.canvas = dependencies['canvas']
        self.status_manager = dependencies.get('status_manager')
        self._show_welcome_message = dependencies.get('show_welcome_message')
        
        self._initialized = True
    
    def cleanup(self):
        """Clean up resources."""
        # No specific cleanup needed for event coordinator
        pass
    
    # ============================================================================
    # KEYBOARD EVENT HANDLING
    # ============================================================================
    
    def handle_key_press(self, key: int, modifiers) -> bool:
        """
        Handle keyboard shortcut events.
        
        Args:
            key: Qt key code
            modifiers: Qt keyboard modifiers
            
        Returns:
            bool: True if event was handled, False otherwise
        """
        if not self.shortcut_manager:
            return False
        
        # Build key sequence using Qt's built-in functionality
        q_key_sequence = QKeySequence(key | modifiers.value if hasattr(modifiers, 'value') else int(modifiers))
        key_sequence_str = q_key_sequence.toString()
        
        # For special keys not handled well by QKeySequence, use our mapping
        if key in self.KEY_MAPPING:
            # Build custom sequence for special keys
            parts = []
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                parts.append("Ctrl")
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                parts.append("Shift")
            if modifiers & Qt.KeyboardModifier.AltModifier:
                parts.append("Alt")
            parts.append(self.KEY_MAPPING[key])
            key_sequence_str = "+".join(parts)
        elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            # Handle single letter keys specially - QKeySequence may not format them correctly
            if modifiers == Qt.KeyboardModifier.NoModifier:
                # For single letters with no modifiers, use the letter directly
                key_sequence_str = chr(key)
            # else let QKeySequence handle modified letters (Ctrl+A, etc.)
        elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            # Handle single digit keys specially
            if modifiers == Qt.KeyboardModifier.NoModifier:
                # For single digits with no modifiers, use the digit directly
                key_sequence_str = chr(key)
            # else let QKeySequence handle modified digits (Alt+1, etc.)
        elif key == Qt.Key.Key_BracketLeft:
            # Handle bracket keys specially
            key_sequence_str = "["
        elif key == Qt.Key.Key_BracketRight:
            key_sequence_str = "]"
        else:
            # Let parent handle other keys
            return False
        
        # Try to handle with shortcut manager
        return self.shortcut_manager.handle_key_press(key_sequence_str)
    
    # ============================================================================
    # DRAG & DROP EVENT HANDLING
    # ============================================================================
    
    def handle_drag_enter(self, event: QDragEnterEvent):
        """
        Handle drag enter event.
        
        Args:
            event: Qt drag enter event
        """
        if not self.file_controller:
            return
            
        if self.file_controller.is_valid_drop(event.mimeData()):
            event.acceptProposedAction()
            # Update canvas style for drag hover
            if self.canvas:
                self.canvas.setStyleSheet(StyleManager.get_canvas_drag_hover())
    
    def handle_drag_leave(self, event):
        """
        Handle drag leave event.
        
        Args:
            event: Qt drag leave event
        """
        # Reset canvas style
        if self.canvas:
            self.canvas.setStyleSheet(StyleManager.get_canvas_normal())

        # Show welcome message
        if self._show_welcome_message:
            self._show_welcome_message()
    
    def handle_drop(self, event: QDropEvent):
        """
        Handle drop event.

        Args:
            event: Qt drop event
        """
        # Reset canvas style
        if self.canvas:
            self.canvas.setStyleSheet(StyleManager.get_canvas_normal())
        
        if not self.file_controller:
            return
            
        file_path = self.file_controller.extract_file_from_drop(event)
        if file_path:
            self.file_controller.load_file(file_path)
            event.acceptProposedAction()
    
    # ============================================================================
    # GRID VIEW EVENT HANDLING
    # ============================================================================
    
    def handle_grid_frame_selected(self, frame_index: int):
        """
        Handle frame selection from grid view.
        
        Args:
            frame_index: Index of selected frame
        """
        # Update status to show selected frame but don't switch tabs
        if self.status_manager:
            self.status_manager.show_message(f"Selected frame {frame_index}")
    
    def handle_grid_frame_preview(self, frame_index: int):
        """
        Handle frame preview request (double-click) from grid view.
        
        Args:
            frame_index: Index of frame to preview
        """
        # This requires access to tab widget and sprite model
        # Will be handled by main window callback
        if self.status_manager:
            self.status_manager.show_message(f"Previewing frame {frame_index}")
    
    # ============================================================================
    # STATE QUERIES
    # ============================================================================
    
    def is_shortcut_enabled(self, shortcut: str) -> bool:
        """
        Check if a shortcut is currently enabled.
        
        Args:
            shortcut: Shortcut string to check
            
        Returns:
            bool: True if shortcut is enabled
        """
        if self.shortcut_manager:
            return self.shortcut_manager.is_shortcut_enabled(shortcut)
        return False