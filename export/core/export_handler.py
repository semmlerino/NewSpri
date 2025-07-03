"""
Export Handler - Centralized export request handling
Part of Phase 1 refactoring to extract export handlers from sprite_viewer.py.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from PySide6.QtWidgets import QMessageBox

from .frame_exporter import get_frame_exporter


class ExportHandler:
    """Handles export requests from dialogs and UI components."""
    
    def __init__(self, parent_widget=None):
        """
        Initialize export handler.
        
        Args:
            parent_widget: Parent widget for message boxes
        """
        self.parent = parent_widget
        self._exporter = get_frame_exporter()
    
    def handle_unified_export_request(self, settings: Dict[str, Any], sprite_model=None, segment_manager=None):
        """
        Handle unified export request from dialog (handles both frames and segments).
        
        Args:
            settings: Export settings dictionary
            sprite_model: Sprite model for accessing frames
            segment_manager: Animation segment manager for segment exports
        """
        # Check if this is a segment export
        if settings.get('mode') == 'segments' and 'selected_segments' in settings:
            self.handle_segment_export_request(settings, sprite_model, segment_manager)
        elif settings.get('mode') == 'segments_sheet':
            self.handle_segments_per_row_export(settings, sprite_model, segment_manager)
        else:
            self.handle_frame_export_request(settings, sprite_model)
    
    def handle_frame_export_request(self, settings: Dict[str, Any], sprite_model=None):
        """
        Handle standard frame export request.
        
        Args:
            settings: Export settings dictionary
            sprite_model: Sprite model for accessing frames
        """
        try:
            # Validate required settings
            required_keys = ['output_dir', 'base_name', 'format', 'mode', 'scale_factor']
            for key in required_keys:
                if key not in settings:
                    self._show_error(f"Missing required setting: {key}")
                    return
            
            # Get frames from sprite model
            if not sprite_model or not sprite_model.sprite_frames:
                self._show_warning("No frames available to export.")
                return
            
            all_frames = sprite_model.sprite_frames
            frames_to_export = all_frames
            export_mode = settings['mode']
            selected_indices = None
            
            # Handle frame selection
            selected_indices = settings.get('selected_indices', [])
            if selected_indices:
                # Validate selected indices
                valid_indices = [i for i in selected_indices if 0 <= i < len(all_frames)]
                if not valid_indices:
                    self._show_warning("No valid frames selected for export.")
                    return
                
                frames_to_export = [all_frames[i] for i in valid_indices]
                export_mode = 'individual'  # Force individual mode for selected frames
                
                if len(valid_indices) != len(selected_indices):
                    # Some indices were invalid, warn user
                    invalid_count = len(selected_indices) - len(valid_indices)
                    self._show_info(
                        f"Exported {len(valid_indices)} frames. "
                        f"{invalid_count} invalid frame selection(s) were skipped."
                    )
            
            # Start export
            success = self._exporter.export_frames(
                frames=frames_to_export,
                output_dir=settings['output_dir'],
                base_name=settings['base_name'],
                format=settings['format'],
                mode=export_mode,
                scale_factor=settings['scale_factor'],
                pattern=settings.get('pattern', None),
                selected_indices=selected_indices,
                sprite_sheet_layout=settings.get('sprite_sheet_layout')
            )
            
            if not success:
                self._show_error("Failed to start export.")
                
        except Exception as e:
            self._show_error(f"Unexpected error during export: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def handle_segments_per_row_export(self, settings: Dict[str, Any], sprite_model=None, segment_manager=None):
        """
        Handle segments per row sprite sheet export.
        
        Args:
            settings: Export settings dictionary
            sprite_model: Sprite model for accessing frames
            segment_manager: Animation segment manager
        """
        if not sprite_model or not sprite_model.sprite_frames:
            self._show_warning("No frames available to export.")
            return
        
        if not segment_manager:
            self._show_error("Segment manager not available.")
            return
        
        # Get all segments
        segments = segment_manager.get_all_segments()
        if not segments:
            self._show_warning("No animation segments defined. Please create segments first.")
            return
        
        # Prepare segment info for exporter
        segment_info = []
        for segment in segments:
            segment_info.append({
                'name': segment.name,
                'start_frame': segment.start_frame,
                'end_frame': segment.end_frame
            })
        
        # Sort segments by start frame for logical ordering
        segment_info.sort(key=lambda s: s['start_frame'])
        
        # Start export with segment info
        success = self._exporter.export_frames(
            frames=sprite_model.sprite_frames,
            output_dir=settings['output_dir'],
            base_name=settings['base_name'],
            format=settings['format'],
            mode='segments_sheet',
            scale_factor=settings['scale_factor'],
            sprite_sheet_layout=settings.get('sprite_sheet_layout'),
            segment_info=segment_info
        )
        
        if not success:
            self._show_error("Failed to start segments per row export.")
    
    def handle_segment_export_request(self, settings: Dict[str, Any], sprite_model=None, segment_manager=None):
        """
        Handle animation segment export request.
        
        Args:
            settings: Export settings dictionary
            sprite_model: Sprite model for accessing frames
            segment_manager: Animation segment manager
        """
        selected_segments = settings.get('selected_segments', [])
        
        if not selected_segments:
            self._show_warning("No animation segments selected for export.")
            return
        
        if not sprite_model or not sprite_model.sprite_frames:
            self._show_warning("No frames available to export.")
            return
        
        if not segment_manager:
            self._show_error("Segment manager not available.")
            return
        
        all_frames = sprite_model.sprite_frames
        
        for segment_name in selected_segments:
            segment = segment_manager.get_segment(segment_name)
            if not segment:
                continue
            
            # Extract frames for this segment
            segment_frames = segment_manager.extract_frames_for_segment(
                segment_name, all_frames
            )
            
            if not segment_frames:
                continue
            
            # Determine output directory and naming
            base_output_dir = settings['output_dir']
            segment_output_dir = Path(base_output_dir) / segment_name
            segment_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Export based on mode
            mode_index = settings.get('mode_index', 0)
            
            if mode_index == 0:  # Individual segments (separate folders)
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(segment_output_dir),
                    base_name=settings.get('base_name', segment_name),
                    format=settings['format'],
                    mode='individual',
                    scale_factor=settings['scale_factor']
                )
            elif mode_index == 1:  # Combined sprite sheet
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(segment_output_dir),
                    base_name=f"{segment_name}_sheet",
                    format=settings['format'],
                    mode='sheet',
                    scale_factor=settings['scale_factor']
                )
            elif mode_index == 2:  # Animated GIF per segment
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(segment_output_dir),
                    base_name=segment_name,
                    format='GIF',
                    mode='gif',
                    scale_factor=settings['scale_factor'],
                    fps=settings.get('fps', 10),
                    loop=settings.get('loop', True)
                )
            else:  # Individual frames (all segments)
                success = self._exporter.export_frames(
                    frames=segment_frames,
                    output_dir=str(base_output_dir),
                    base_name=f"{settings.get('base_name', 'frame')}_{segment_name}",
                    format=settings['format'],
                    mode='individual',
                    scale_factor=settings['scale_factor']
                )
            
            if not success:
                self._show_error(f"Failed to export segment '{segment_name}'.")
    
    def handle_segment_specific_export(
        self, 
        settings: Dict[str, Any], 
        segment_frames: List, 
        segment_name: str
    ):
        """
        Handle export request for a specific animation segment.
        
        Args:
            settings: Export settings dictionary
            segment_frames: Frames belonging to the segment
            segment_name: Name of the segment
        """
        try:
            # Validate required settings
            required_keys = ['output_dir', 'base_name', 'format', 'mode', 'scale_factor']
            for key in required_keys:
                if key not in settings:
                    self._show_error(f"Missing required setting: {key}")
                    return
            
            if not segment_frames:
                self._show_warning(f"No frames available for segment '{segment_name}'.")
                return
            
            frames_to_export = segment_frames
            export_mode = settings['mode']
            selected_indices = None
            
            # Handle frame selection within segment
            selected_indices = settings.get('selected_indices', [])
            if selected_indices:
                # Validate selected indices against segment frame count
                valid_indices = [i for i in selected_indices if 0 <= i < len(segment_frames)]
                if not valid_indices:
                    self._show_warning("No valid frames selected for export.")
                    return
                
                frames_to_export = [segment_frames[i] for i in valid_indices]
                export_mode = 'individual'
                
                if len(valid_indices) != len(selected_indices):
                    invalid_count = len(selected_indices) - len(valid_indices)
                    self._show_info(
                        f"Exported {len(valid_indices)} frames from segment '{segment_name}'. "
                        f"{invalid_count} invalid frame selection(s) were skipped."
                    )
            
            # Update base name to include segment name
            base_name = f"{settings['base_name']}_{segment_name}"
            
            success = self._exporter.export_frames(
                frames=frames_to_export,
                output_dir=settings['output_dir'],
                base_name=base_name,
                format=settings['format'],
                mode=export_mode,
                scale_factor=settings['scale_factor'],
                pattern=settings.get('pattern', None),
                selected_indices=selected_indices,
                sprite_sheet_layout=settings.get('sprite_sheet_layout')
            )
            
            if not success:
                self._show_error(f"Failed to start export for segment '{segment_name}'.")
                
        except Exception as e:
            self._show_error(f"Unexpected error during segment export: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _show_error(self, message: str):
        """Show error message box."""
        if self.parent:
            QMessageBox.critical(self.parent, "Export Error", message)
        else:
            print(f"Export Error: {message}")
    
    def _show_warning(self, message: str):
        """Show warning message box."""
        if self.parent:
            QMessageBox.warning(self.parent, "Export Warning", message)
        else:
            print(f"Export Warning: {message}")
    
    def _show_info(self, message: str):
        """Show information message box."""
        if self.parent:
            QMessageBox.information(self.parent, "Export Info", message)
        else:
            print(f"Export Info: {message}")