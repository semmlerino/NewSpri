"""
Export Coordinator for SpriteViewer refactoring.
Handles export dialog creation, configuration, and coordination between components.
"""

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Signal, QObject

from export import ExportDialog


class ExportCoordinator(QObject):
    """
    Coordinator responsible for export operations.
    
    Manages export dialog creation, frame/segment export handling,
    and coordination between sprite model, segment manager, and export handler.
    Extracts export logic from SpriteViewer.
    """
    
    # Signals
    exportRequested = Signal(dict)  # Emitted when export is requested with config
    
    def __init__(self, main_window):
        """Initialize export coordinator."""
        super().__init__()
        self.main_window = main_window
        self._initialized = False
        
        # Component references
        self.sprite_model = None
        self.segment_manager = None
        self.export_handler = None
    
    def initialize(self, dependencies):
        """
        Initialize coordinator with required dependencies.
        
        Args:
            dependencies: Dict containing:
                - sprite_model: SpriteModel instance
                - segment_manager: AnimationSegmentManager instance
                - export_handler: ExportHandler instance
        """
        self.sprite_model = dependencies['sprite_model']
        self.segment_manager = dependencies['segment_manager']
        self.export_handler = dependencies['export_handler']
        
        self._initialized = True
    
    def cleanup(self):
        """Clean up resources."""
        # No specific cleanup needed for export coordinator
        pass
    
    # ============================================================================
    # EXPORT OPERATIONS
    # ============================================================================
    
    def export_frames(self):
        """Show enhanced export dialog for exporting frames and animation segments."""
        if not self._validate_export():
            return
        
        # Emit signal to notify export has been requested
        self.exportRequested.emit({'mode': 'all_frames'})
        
        dialog = self._create_export_dialog()
        
        # Set sprites for visual preview (Phase 4 enhancement)
        dialog.set_sprites(self.sprite_model.sprite_frames)
        
        dialog.exportRequested.connect(self._handle_export_request)
        dialog.exec()
    
    def export_current_frame(self):
        """Export only the current frame."""
        if not self._validate_export():
            return
        
        # Emit signal to notify export has been requested
        self.exportRequested.emit({'mode': 'current_frame'})
        
        dialog = self._create_export_dialog()
        
        # Set sprites for visual preview (Phase 4 enhancement)
        dialog.set_sprites(self.sprite_model.sprite_frames)
        
        # The new dialog will automatically handle single frame export via presets
        dialog.exportRequested.connect(self._handle_export_request)
        dialog.exec()
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _validate_export(self) -> bool:
        """
        Validate that export can proceed.
        
        Returns:
            bool: True if export can proceed, False otherwise
        """
        if not self.sprite_model or not self.sprite_model.sprite_frames:
            QMessageBox.warning(
                self.main_window, 
                "No Frames", 
                "No frames to export."
            )
            return False
        return True
    
    def _create_export_dialog(self) -> ExportDialog:
        """
        Create and configure export dialog.
        
        Returns:
            ExportDialog: Configured export dialog
        """
        return ExportDialog(
            self.main_window,
            frame_count=len(self.sprite_model.sprite_frames),
            current_frame=self.sprite_model.current_frame,
            segment_manager=self.segment_manager
        )
    
    def _handle_export_request(self, settings: dict):
        """
        Handle unified export request from dialog.
        
        Args:
            settings: Export settings dictionary
        """
        if self.export_handler:
            self.export_handler.handle_unified_export_request(
                settings, 
                self.sprite_model, 
                self.segment_manager
            )
    
    # ============================================================================
    # STATE QUERIES
    # ============================================================================
    
    def has_frames(self) -> bool:
        """Check if there are frames available for export."""
        return bool(self.sprite_model and self.sprite_model.sprite_frames)
    
    def get_frame_count(self) -> int:
        """Get the total number of frames."""
        if self.sprite_model and self.sprite_model.sprite_frames:
            return len(self.sprite_model.sprite_frames)
        return 0
    
    def get_current_frame_index(self) -> int:
        """Get the current frame index."""
        if self.sprite_model:
            return self.sprite_model.current_frame
        return 0