"""
Frame Exporter - Export functionality for sprite frames
Handles exporting individual frames, sprite sheets, and animations.
Part of Phase 4: Frame Export System implementation.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QPixmap, QPainter, QColor

from config import Config

logger = logging.getLogger(__name__)


@dataclass
class SpriteSheetLayout:
    """Configuration for sprite sheet layout and spacing."""
    
    mode: str = Config.Export.DEFAULT_LAYOUT_MODE              # Layout calculation mode
    spacing: int = Config.Export.DEFAULT_SPRITE_SPACING        # Pixels between sprites
    padding: int = Config.Export.DEFAULT_SHEET_PADDING         # Padding around sheet
    max_columns: Optional[int] = None                           # Max columns (rows mode)
    max_rows: Optional[int] = None                              # Max rows (columns mode)
    custom_columns: Optional[int] = None                        # Custom grid columns
    custom_rows: Optional[int] = None                           # Custom grid rows
    background_mode: str = Config.Export.DEFAULT_BACKGROUND_MODE
    background_color: Tuple[int, int, int, int] = Config.Export.DEFAULT_BACKGROUND_COLOR
    
    def __post_init__(self):
        """Validate layout configuration."""
        # Validate layout mode (including custom modes)
        valid_modes = Config.Export.LAYOUT_MODES + ['segments_per_row']
        if self.mode not in valid_modes:
            raise ValueError(f"Invalid layout mode: {self.mode}")
        
        # Validate spacing
        if not (Config.Export.MIN_SPRITE_SPACING <= self.spacing <= Config.Export.MAX_SPRITE_SPACING):
            raise ValueError(f"Spacing must be between {Config.Export.MIN_SPRITE_SPACING} and {Config.Export.MAX_SPRITE_SPACING}")
        
        # Validate padding
        if not (Config.Export.MIN_SHEET_PADDING <= self.padding <= Config.Export.MAX_SHEET_PADDING):
            raise ValueError(f"Padding must be between {Config.Export.MIN_SHEET_PADDING} and {Config.Export.MAX_SHEET_PADDING}")
        
        # Validate grid constraints
        if self.max_columns is not None:
            if not (Config.Export.MIN_GRID_SIZE <= self.max_columns <= Config.Export.MAX_GRID_SIZE):
                raise ValueError(f"Max columns must be between {Config.Export.MIN_GRID_SIZE} and {Config.Export.MAX_GRID_SIZE}")
        
        if self.max_rows is not None:
            if not (Config.Export.MIN_GRID_SIZE <= self.max_rows <= Config.Export.MAX_GRID_SIZE):
                raise ValueError(f"Max rows must be between {Config.Export.MIN_GRID_SIZE} and {Config.Export.MAX_GRID_SIZE}")
        
        # Validate custom grid (for custom mode)
        if self.mode == 'custom':
            if self.custom_columns is None or self.custom_rows is None:
                raise ValueError("Custom mode requires both custom_columns and custom_rows")
            if not (Config.Export.MIN_GRID_SIZE <= self.custom_columns <= Config.Export.MAX_GRID_SIZE):
                raise ValueError(f"Custom columns must be between {Config.Export.MIN_GRID_SIZE} and {Config.Export.MAX_GRID_SIZE}")
            if not (Config.Export.MIN_GRID_SIZE <= self.custom_rows <= Config.Export.MAX_GRID_SIZE):
                raise ValueError(f"Custom rows must be between {Config.Export.MIN_GRID_SIZE} and {Config.Export.MAX_GRID_SIZE}")
        
        # Validate background mode
        if self.background_mode not in Config.Export.BACKGROUND_MODES:
            raise ValueError(f"Invalid background mode: {self.background_mode}")
        
        # Validate background color (RGBA tuple)
        if not (isinstance(self.background_color, (tuple, list)) and len(self.background_color) == 4):
            raise ValueError("Background color must be an RGBA tuple with 4 values")
        for value in self.background_color:
            if not (0 <= value <= 255):
                raise ValueError("Background color values must be between 0 and 255")
    
    def get_effective_columns(self, frame_count: int) -> Optional[int]:
        """Get effective max columns for layout calculation."""
        if self.mode == 'custom':
            return self.custom_columns
        elif self.mode == 'rows':
            return self.max_columns or Config.Export.DEFAULT_MAX_COLUMNS
        return None
    
    def get_effective_rows(self, frame_count: int) -> Optional[int]:
        """Get effective max rows for layout calculation."""
        if self.mode == 'custom':
            return self.custom_rows
        elif self.mode == 'columns':
            return self.max_rows or Config.Export.DEFAULT_MAX_ROWS
        return None
    
    def calculate_estimated_dimensions(self, frame_width: int, frame_height: int, frame_count: int) -> Tuple[int, int]:
        """Estimate sprite sheet dimensions with current layout settings."""
        import math
        
        if self.mode == 'custom':
            cols = self.custom_columns
            rows = self.custom_rows
        elif self.mode == 'rows':
            max_cols = self.max_columns or Config.Export.DEFAULT_MAX_COLUMNS
            cols = min(max_cols, frame_count)
            rows = math.ceil(frame_count / cols)
        elif self.mode == 'columns':
            max_rows = self.max_rows or Config.Export.DEFAULT_MAX_ROWS
            rows = min(max_rows, frame_count)
            cols = math.ceil(frame_count / rows)
        else:  # auto or square
            cols = math.ceil(math.sqrt(frame_count))
            rows = math.ceil(frame_count / cols)
        
        # Calculate dimensions with spacing and padding
        sheet_width = (cols * frame_width) + ((cols - 1) * self.spacing) + (2 * self.padding)
        sheet_height = (rows * frame_height) + ((rows - 1) * self.spacing) + (2 * self.padding)
        
        return sheet_width, sheet_height


class ExportFormat(Enum):
    """Supported export formats."""
    PNG = "PNG"
    JPG = "JPG"
    BMP = "BMP"
    
    @property
    def extension(self) -> str:
        """Get file extension for the format."""
        return f".{self.value.lower()}"
    
    @classmethod
    def from_string(cls, format_str: str) -> 'ExportFormat':
        """Create from string representation."""
        return cls(format_str.upper())


class ExportMode(Enum):
    """Export modes available."""
    INDIVIDUAL_FRAMES = "individual"
    SPRITE_SHEET = "sheet"


class ExportTask:
    """Represents a single export task."""
    
    def __init__(self, 
                 frames: List[QPixmap],
                 output_dir: Path,
                 base_name: str,
                 format: ExportFormat,
                 mode: ExportMode,
                 scale_factor: float = 1.0,
                 pattern: str = "{name}_{index:03d}",
                 selected_indices: Optional[List[int]] = None,
                 sprite_sheet_layout: Optional[SpriteSheetLayout] = None,
                 segment_info: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize export task.
        
        Args:
            frames: List of QPixmap frames to export
            output_dir: Output directory path
            base_name: Base name for exported files
            format: Export format
            mode: Export mode
            scale_factor: Scale factor for output (1.0 = original size)
            pattern: Naming pattern for individual frames
            selected_indices: Indices of selected frames (for filtering)
            sprite_sheet_layout: Layout configuration for sprite sheet export
            segment_info: List of segment dictionaries with 'name', 'start_frame', 'end_frame'
        """
        self.frames = frames
        self.output_dir = output_dir
        self.base_name = base_name
        self.format = format
        self.mode = mode
        self.scale_factor = scale_factor
        self.pattern = pattern
        self.selected_indices = selected_indices or []
        self.sprite_sheet_layout = sprite_sheet_layout or SpriteSheetLayout()
        self.segment_info = segment_info or []
        
        # Validate task
        if not frames:
            raise ValueError("No frames to export")
        if scale_factor <= 0:
            raise ValueError("Scale factor must be positive")
        
        # Additional validation for sprite sheet mode
        if mode == ExportMode.SPRITE_SHEET and sprite_sheet_layout is None:
            # Use default layout if none provided for sprite sheet mode
            self.sprite_sheet_layout = SpriteSheetLayout()


class ExportWorker(QThread):
    """Worker thread for export operations."""
    
    # Signals
    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(bool, str)  # success, message
    error = Signal(str)  # error message
    
    def __init__(self, task: ExportTask):
        super().__init__()
        self.task = task
        self._cancelled = False
    
    def run(self):
        """Execute the export task."""
        try:
            if self.task.mode == ExportMode.INDIVIDUAL_FRAMES:
                self._export_individual_frames()
            elif self.task.mode == ExportMode.SPRITE_SHEET:
                self._export_sprite_sheet()
            else:
                raise ValueError(f"Unsupported export mode: {self.task.mode}")
                
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False, f"Export failed: {str(e)}")
    
    def cancel(self):
        """Cancel the export operation."""
        self._cancelled = True
    
    def _export_individual_frames(self):
        """Export frames as individual files."""
        total_frames = len(self.task.frames)
        exported_count = 0
        
        for i, frame in enumerate(self.task.frames):
            if self._cancelled:
                self.finished.emit(False, "Export cancelled")
                return
            
            # Generate filename
            filename = self.task.pattern.format(
                name=self.task.base_name,
                index=i,
                frame=i + 1
            ) + self.task.format.extension
            
            filepath = self.task.output_dir / filename
            
            # Scale if needed
            if self.task.scale_factor != 1.0:
                frame = self._scale_pixmap(frame, self.task.scale_factor)
            
            # Save frame
            if frame.save(str(filepath), self.task.format.value):
                exported_count += 1
                self.progress.emit(i + 1, total_frames, f"Exported {filename}")
            else:
                self.error.emit(f"Failed to export {filename}")
        
        self.finished.emit(
            True, 
            f"Successfully exported {exported_count} frames"
        )
    
    
    def _export_sprite_sheet(self):
        """Export all frames as a single sprite sheet with enhanced layout options."""
        if not self.task.frames:
            self.finished.emit(False, "No frames to export")
            return
        
        self.progress.emit(0, 3, "Calculating layout...")
        
        # Get layout configuration
        layout = self.task.sprite_sheet_layout
        frame_count = len(self.task.frames)
        
        # Get original frame dimensions
        original_frame_width = self.task.frames[0].width()
        original_frame_height = self.task.frames[0].height()
        
        # Apply scaling to frame dimensions
        if self.task.scale_factor != 1.0:
            frame_width = int(original_frame_width * self.task.scale_factor)
            frame_height = int(original_frame_height * self.task.scale_factor)
        else:
            frame_width = original_frame_width
            frame_height = original_frame_height
        
        # Calculate grid dimensions using layout configuration
        cols, rows = self._calculate_grid_layout(layout, frame_count)
        
        self.progress.emit(1, 3, f"Creating sprite sheet ({cols}x{rows})...")
        
        # Calculate sprite sheet dimensions with spacing and padding
        if layout.mode == 'segments_per_row' and self.task.segment_info:
            # For segments per row, calculate dimensions based on actual segment layouts
            sheet_width, sheet_height = self._calculate_segments_sheet_dimensions(
                frame_width, frame_height, layout
            )
        else:
            # Use regular grid-based calculation
            sheet_width, sheet_height = self._calculate_sheet_dimensions(
                cols, rows, frame_width, frame_height, layout
            )
        
        # Create sprite sheet with background
        sprite_sheet = self._create_background_sheet(sheet_width, sheet_height, layout)
        
        # Draw frames onto sprite sheet with spacing
        if layout.mode == 'segments_per_row' and self.task.segment_info:
            self._draw_sprites_segments_per_row(
                sprite_sheet, cols, rows, frame_width, frame_height, layout
            )
        else:
            self._draw_sprites_with_layout(
                sprite_sheet, cols, rows, frame_width, frame_height, layout
            )
        
        self.progress.emit(2, 3, "Saving sprite sheet...")
        
        # Save sprite sheet
        filename = f"{self.task.base_name}_sheet{self.task.format.extension}"
        filepath = self.task.output_dir / filename
        
        if sprite_sheet.save(str(filepath), self.task.format.value):
            self.progress.emit(3, 3, f"Saved {filename}")
            self.finished.emit(
                True, 
                f"Successfully exported sprite sheet ({cols}x{rows}, {layout.spacing}px spacing)"
            )
        else:
            self.finished.emit(False, "Failed to save sprite sheet")
    
    def _calculate_grid_layout(self, layout: SpriteSheetLayout, frame_count: int) -> Tuple[int, int]:
        """Calculate optimal grid dimensions based on layout configuration."""
        import math
        
        if layout.mode == 'custom':
            # Use exact user-specified dimensions
            cols = layout.custom_columns
            rows = layout.custom_rows
            
        elif layout.mode == 'rows':
            # Prioritize horizontal layout with max columns constraint
            max_cols = layout.max_columns or Config.Export.DEFAULT_MAX_COLUMNS
            cols = min(max_cols, frame_count)
            rows = math.ceil(frame_count / cols)
            
        elif layout.mode == 'columns':
            # Prioritize vertical layout with max rows constraint
            max_rows = layout.max_rows or Config.Export.DEFAULT_MAX_ROWS
            rows = min(max_rows, frame_count)
            cols = math.ceil(frame_count / rows)
            
        elif layout.mode == 'square':
            # Force closest to square aspect ratio
            cols = math.ceil(math.sqrt(frame_count))
            rows = math.ceil(frame_count / cols)
            
        elif layout.mode == 'segments_per_row':
            # Calculate layout based on segments
            cols, rows = self._calculate_segments_per_row_layout()
            
        else:  # 'auto' mode
            # Intelligent layout selection based on frame count and preferences
            cols, rows = self._calculate_auto_layout(frame_count, layout)
        
        # Ensure we have at least enough cells for all frames
        while cols * rows < frame_count:
            if cols <= rows:
                cols += 1
            else:
                rows += 1
        
        return cols, rows
    
    def _calculate_auto_layout(self, frame_count: int, layout: SpriteSheetLayout) -> Tuple[int, int]:
        """Calculate automatic layout using intelligent heuristics."""
        import math
        
        if frame_count <= 1:
            return 1, 1
        
        # Start with square root as base
        sqrt_frames = math.sqrt(frame_count)
        base_cols = math.ceil(sqrt_frames)
        base_rows = math.ceil(frame_count / base_cols)
        
        # Consider different aspect ratios and choose the best one
        candidates = []
        
        # Try square-ish layouts
        for cols_offset in range(-2, 3):
            cols = max(1, base_cols + cols_offset)
            rows = math.ceil(frame_count / cols)
            
            if cols * rows >= frame_count:
                aspect_ratio = cols / rows
                wasted_cells = (cols * rows) - frame_count
                
                # Score based on aspect ratio preference and efficiency
                if Config.Export.PREFER_HORIZONTAL:
                    aspect_score = aspect_ratio  # Prefer wider layouts
                else:
                    aspect_score = 1.0 / aspect_ratio  # Prefer taller layouts
                
                efficiency_score = 1.0 - (wasted_cells / (cols * rows))
                combined_score = efficiency_score * 0.7 + (aspect_score / 3.0) * 0.3
                
                candidates.append((combined_score, cols, rows))
        
        # Choose the best candidate
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1], candidates[0][2]
        else:
            return base_cols, base_rows
    
    def _calculate_sheet_dimensions(self, cols: int, rows: int, frame_width: int, 
                                  frame_height: int, layout: SpriteSheetLayout) -> Tuple[int, int]:
        """Calculate total sprite sheet dimensions including spacing and padding."""
        # Calculate total width: frames + spacing between frames + padding on both sides
        sheet_width = (cols * frame_width) + ((cols - 1) * layout.spacing) + (2 * layout.padding)
        
        # Calculate total height: frames + spacing between frames + padding on both sides
        sheet_height = (rows * frame_height) + ((rows - 1) * layout.spacing) + (2 * layout.padding)
        
        return sheet_width, sheet_height
    
    def _calculate_segments_sheet_dimensions(self, frame_width: int, frame_height: int, 
                                           layout: SpriteSheetLayout) -> Tuple[int, int]:
        """Calculate sprite sheet dimensions for segments per row mode."""
        
        if not self.task.segment_info:
            return frame_width + (2 * layout.padding), frame_height + (2 * layout.padding)
        
        # Find the maximum width needed (longest segment)
        max_frames_in_segment = max(
            seg['end_frame'] - seg['start_frame'] + 1 
            for seg in self.task.segment_info
        )
        
        # Calculate width based on the longest segment
        sheet_width = (max_frames_in_segment * frame_width) + \
                     ((max_frames_in_segment - 1) * layout.spacing) + \
                     (2 * layout.padding)
        
        # Calculate height based on actual number of segments (rows)
        num_segments = len(self.task.segment_info)
        sheet_height = (num_segments * frame_height) + \
                      ((num_segments - 1) * layout.spacing) + \
                      (2 * layout.padding)
        
        
        return sheet_width, sheet_height
    
    def _create_background_sheet(self, width: int, height: int, 
                               layout: SpriteSheetLayout) -> QPixmap:
        """Create sprite sheet with the specified background."""
        sprite_sheet = QPixmap(width, height)
        
        if layout.background_mode == 'transparent':
            sprite_sheet.fill(QColor(0, 0, 0, 0))  # Fully transparent
            
        elif layout.background_mode == 'solid':
            r, g, b, a = layout.background_color
            sprite_sheet.fill(QColor(r, g, b, a))
            
        elif layout.background_mode == 'checkerboard':
            # Create checkerboard pattern
            sprite_sheet.fill(QColor(0, 0, 0, 0))  # Start transparent
            
            painter = QPainter(sprite_sheet)
            
            tile_size = Config.Export.CHECKERBOARD_TILE_SIZE
            light_color = QColor(*Config.Export.CHECKERBOARD_LIGHT_COLOR)
            dark_color = QColor(*Config.Export.CHECKERBOARD_DARK_COLOR)
            
            # Draw checkerboard pattern
            for y in range(0, height, tile_size):
                for x in range(0, width, tile_size):
                    # Determine if this tile should be light or dark
                    tile_x = x // tile_size
                    tile_y = y // tile_size
                    is_light = (tile_x + tile_y) % 2 == 0
                    
                    color = light_color if is_light else dark_color
                    painter.fillRect(x, y, tile_size, tile_size, color)
            
            painter.end()
        
        return sprite_sheet
    
    def _draw_sprites_with_layout(self, sprite_sheet: QPixmap, cols: int, rows: int,
                                frame_width: int, frame_height: int, 
                                layout: SpriteSheetLayout):
        """Draw all frames onto the sprite sheet with proper spacing and layout."""
        painter = QPainter(sprite_sheet)
        
        # Enable high-quality rendering if configured
        if Config.Export.ENABLE_ANTIALIASING:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

        for i, frame in enumerate(self.task.frames):
            if self._cancelled:
                painter.end()
                self.finished.emit(False, "Export cancelled")
                return
            
            # Calculate grid position
            row = i // cols
            col = i % cols
            
            # Calculate pixel position with spacing and padding
            x = layout.padding + (col * (frame_width + layout.spacing))
            y = layout.padding + (row * (frame_height + layout.spacing))
            
            # Scale and draw frame
            if self.task.scale_factor != 1.0:
                scaled_frame = self._scale_pixmap(frame, self.task.scale_factor)
                painter.drawPixmap(x, y, scaled_frame)
            else:
                painter.drawPixmap(x, y, frame)
        
        painter.end()
    
    def _calculate_segments_per_row_layout(self) -> Tuple[int, int]:
        """Calculate layout for segments per row mode."""
        
        if not self.task.segment_info:
            # No segments, fall back to square layout
            import math
            frame_count = len(self.task.frames)
            cols = math.ceil(math.sqrt(frame_count))
            rows = math.ceil(frame_count / cols)
            return cols, rows
        
        
        # Calculate maximum frames per segment
        max_frames_per_segment = max(
            seg['end_frame'] - seg['start_frame'] + 1 
            for seg in self.task.segment_info
        )
        
        # Rows = number of segments, cols = max frames in any segment
        rows = len(self.task.segment_info)
        cols = max_frames_per_segment
        
        
        return cols, rows
    
    def _draw_sprites_segments_per_row(self, sprite_sheet: QPixmap, cols: int, rows: int,
                                     frame_width: int, frame_height: int,
                                     layout: SpriteSheetLayout):
        """Draw sprites with each segment on its own row."""
        
        painter = QPainter(sprite_sheet)
        
        # Enable high-quality rendering if configured
        if Config.Export.ENABLE_ANTIALIASING:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Draw each segment on its own row
        for row_idx, segment in enumerate(self.task.segment_info):
            start = segment['start_frame']
            end = segment['end_frame']
            
            
            frames_drawn = 0
            # Draw frames for this segment
            for col_idx, frame_idx in enumerate(range(start, end + 1)):
                if frame_idx >= len(self.task.frames):
                    break
                    
                if self._cancelled:
                    painter.end()
                    self.finished.emit(False, "Export cancelled")
                    return
                
                frame = self.task.frames[frame_idx]
                
                # Calculate pixel position with spacing and padding
                x = layout.padding + (col_idx * (frame_width + layout.spacing))
                y = layout.padding + (row_idx * (frame_height + layout.spacing))
                
                
                # Scale and draw frame
                if self.task.scale_factor != 1.0:
                    scaled_frame = self._scale_pixmap(frame, self.task.scale_factor)
                    painter.drawPixmap(x, y, scaled_frame)
                else:
                    painter.drawPixmap(x, y, frame)
                
                frames_drawn += 1

            logger.debug("Drew %d frames for segment '%s'", frames_drawn, segment['name'])
        
        painter.end()
    
    def _scale_pixmap(self, pixmap: QPixmap, scale_factor: float) -> QPixmap:
        """Scale a pixmap by the given factor."""
        new_width = int(pixmap.width() * scale_factor)
        new_height = int(pixmap.height() * scale_factor)
        return pixmap.scaled(
            new_width, 
            new_height, 
            aspectMode=1,  # KeepAspectRatio
            mode=1  # SmoothTransformation
        )


class FrameExporter(QObject):
    """
    Main frame exporter class.
    Manages export operations and provides a clean API.
    """
    
    # Signals
    exportStarted = Signal()
    exportProgress = Signal(int, int, str)  # current, total, message
    exportFinished = Signal(bool, str)  # success, message
    exportError = Signal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self._worker: Optional[ExportWorker] = None
        self._current_task: Optional[ExportTask] = None
    
    def export_frames(self,
                     frames: List[QPixmap],
                     output_dir: str,
                     base_name: str = "frame",
                     format: str = "PNG",
                     mode: str = "individual",
                     scale_factor: float = 1.0,
                     pattern: Optional[str] = None,
                     selected_indices: Optional[List[int]] = None,
                     sprite_sheet_layout: Optional[SpriteSheetLayout] = None,
                     segment_info: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Export frames with the specified settings.
        
        Args:
            frames: List of frames to export
            output_dir: Output directory path
            base_name: Base name for exported files
            format: Export format (PNG, JPG, BMP)
            mode: Export mode (individual, sheet, selected, segments_sheet)
            scale_factor: Scale factor for output
            pattern: Naming pattern for individual frames
            selected_indices: Frame indices for selected export
            sprite_sheet_layout: Layout configuration for sprite sheet export
            segment_info: List of segment dictionaries with 'name', 'start_frame', 'end_frame'
            
        Returns:
            True if export started successfully
        """
        logger.debug("FrameExporter.export_frames called")
        logger.debug("Mode: %s, Format: %s, Frame count: %d", mode, format, len(frames))
        logger.debug("Base name: %s, Scale factor: %s", base_name, scale_factor)
        logger.debug("Segment info provided: %s", segment_info is not None)
        if segment_info:
            logger.debug("Segment count: %d", len(segment_info))
            for i, seg in enumerate(segment_info):
                logger.debug("  Segment %d: %s", i, seg)

        # Validate inputs
        if not frames:
            logger.debug("No frames to export, emitting error")
            self.exportError.emit("No frames to export")
            return False
        
        # Create output directory if needed
        output_path = Path(output_dir)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.exportError.emit(f"Failed to create output directory: {str(e)}")
            return False
        
        # Parse format and mode
        try:
            export_format = ExportFormat.from_string(format)
            logger.debug("Parsed export format: %s", export_format)

            # Handle special mode for segments_sheet
            if mode == 'segments_sheet':
                logger.debug("Converting segments_sheet mode to SPRITE_SHEET")
                export_mode = ExportMode.SPRITE_SHEET
            else:
                export_mode = ExportMode(mode)
            logger.debug("Parsed export mode: %s", export_mode)
        except ValueError as e:
            self.exportError.emit(f"Invalid export settings: {str(e)}")
            return False
        
        # Use default pattern if not provided
        if pattern is None:
            pattern = Config.Export.DEFAULT_PATTERN
        
        # Create export task
        try:
            self._current_task = ExportTask(
                frames=frames,
                output_dir=output_path,
                base_name=base_name,
                format=export_format,
                mode=export_mode,
                scale_factor=scale_factor,
                pattern=pattern,
                selected_indices=selected_indices,
                sprite_sheet_layout=sprite_sheet_layout,
                segment_info=segment_info
            )
        except ValueError as e:
            self.exportError.emit(str(e))
            return False
        
        # Create and start worker
        self._worker = ExportWorker(self._current_task)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        
        self.exportStarted.emit()
        self._worker.start()
        
        return True
    
    def cancel_export(self):
        """Cancel the current export operation."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.quit()
            self._worker.wait()
    
    def is_exporting(self) -> bool:
        """Check if export is in progress."""
        return self._worker is not None and self._worker.isRunning()
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return [fmt.value for fmt in ExportFormat]
    
    def get_supported_modes(self) -> List[str]:
        """Get list of supported export modes."""
        return [mode.value for mode in ExportMode]
    
    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress updates from worker."""
        self.exportProgress.emit(current, total, message)
    
    def _on_finished(self, success: bool, message: str):
        """Handle export completion."""
        self._worker = None
        self._current_task = None
        self.exportFinished.emit(success, message)
    
    def _on_error(self, error_message: str):
        """Handle export errors."""
        self.exportError.emit(error_message)


# Singleton instance
_exporter_instance: Optional[FrameExporter] = None


def get_frame_exporter() -> FrameExporter:
    """Get the global frame exporter instance."""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = FrameExporter()
    return _exporter_instance