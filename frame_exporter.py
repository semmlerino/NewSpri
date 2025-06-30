"""
Frame Exporter - Export functionality for sprite frames
Handles exporting individual frames, sprite sheets, and animations.
Part of Phase 4: Frame Export System implementation.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Callable
from enum import Enum

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QPixmap, QPainter, QImage
from PySide6.QtWidgets import QMessageBox

from config import Config


class ExportFormat(Enum):
    """Supported export formats."""
    PNG = "PNG"
    JPG = "JPG"
    BMP = "BMP"
    GIF = "GIF"  # For animated exports only
    
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
    ANIMATED_GIF = "gif"
    SELECTED_FRAMES = "selected"


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
                 selected_indices: Optional[List[int]] = None):
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
            selected_indices: Indices of selected frames (for SELECTED_FRAMES mode)
        """
        self.frames = frames
        self.output_dir = output_dir
        self.base_name = base_name
        self.format = format
        self.mode = mode
        self.scale_factor = scale_factor
        self.pattern = pattern
        self.selected_indices = selected_indices or []
        
        # Validate task
        if not frames:
            raise ValueError("No frames to export")
        if scale_factor <= 0:
            raise ValueError("Scale factor must be positive")


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
            elif self.task.mode == ExportMode.SELECTED_FRAMES:
                self._export_selected_frames()
            elif self.task.mode == ExportMode.ANIMATED_GIF:
                self._export_animated_gif()
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
    
    def _export_selected_frames(self):
        """Export only selected frames."""
        if not self.task.selected_indices:
            self.error.emit("No frames selected for export")
            self.finished.emit(False, "No frames selected")
            return
        
        total_frames = len(self.task.selected_indices)
        exported_count = 0
        
        for export_index, frame_index in enumerate(self.task.selected_indices):
            if self._cancelled:
                self.finished.emit(False, "Export cancelled")
                return
            
            if 0 <= frame_index < len(self.task.frames):
                frame = self.task.frames[frame_index]
                
                # Generate filename
                filename = self.task.pattern.format(
                    name=self.task.base_name,
                    index=export_index,
                    frame=frame_index + 1
                ) + self.task.format.extension
                
                filepath = self.task.output_dir / filename
                
                # Scale if needed
                if self.task.scale_factor != 1.0:
                    frame = self._scale_pixmap(frame, self.task.scale_factor)
                
                # Save frame
                if frame.save(str(filepath), self.task.format.value):
                    exported_count += 1
                    self.progress.emit(
                        export_index + 1, 
                        total_frames, 
                        f"Exported {filename}"
                    )
                else:
                    self.error.emit(f"Failed to export {filename}")
        
        self.finished.emit(
            True, 
            f"Successfully exported {exported_count} selected frames"
        )
    
    def _export_sprite_sheet(self):
        """Export all frames as a single sprite sheet."""
        if not self.task.frames:
            self.finished.emit(False, "No frames to export")
            return
        
        self.progress.emit(0, 1, "Creating sprite sheet...")
        
        # Calculate sprite sheet dimensions
        frame_width = self.task.frames[0].width()
        frame_height = self.task.frames[0].height()
        frame_count = len(self.task.frames)
        
        # Calculate grid dimensions (prefer square-ish layout)
        import math
        cols = math.ceil(math.sqrt(frame_count))
        rows = math.ceil(frame_count / cols)
        
        # Apply scaling
        if self.task.scale_factor != 1.0:
            frame_width = int(frame_width * self.task.scale_factor)
            frame_height = int(frame_height * self.task.scale_factor)
        
        # Create sprite sheet
        sheet_width = cols * frame_width
        sheet_height = rows * frame_height
        sprite_sheet = QPixmap(sheet_width, sheet_height)
        sprite_sheet.fill(Config.Color.TRANSPARENT)
        
        # Draw frames onto sprite sheet
        painter = QPainter(sprite_sheet)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        for i, frame in enumerate(self.task.frames):
            if self._cancelled:
                painter.end()
                self.finished.emit(False, "Export cancelled")
                return
            
            row = i // cols
            col = i % cols
            x = col * frame_width
            y = row * frame_height
            
            # Scale and draw frame
            if self.task.scale_factor != 1.0:
                scaled_frame = self._scale_pixmap(frame, self.task.scale_factor)
                painter.drawPixmap(x, y, scaled_frame)
            else:
                painter.drawPixmap(x, y, frame)
        
        painter.end()
        
        # Save sprite sheet
        filename = f"{self.task.base_name}_sheet{self.task.format.extension}"
        filepath = self.task.output_dir / filename
        
        if sprite_sheet.save(str(filepath), self.task.format.value):
            self.progress.emit(1, 1, f"Saved {filename}")
            self.finished.emit(
                True, 
                f"Successfully exported sprite sheet ({cols}x{rows})"
            )
        else:
            self.finished.emit(False, f"Failed to save sprite sheet")
    
    def _export_animated_gif(self):
        """Export frames as animated GIF."""
        # This requires additional dependencies (PIL/Pillow)
        try:
            from PIL import Image
        except ImportError:
            self.error.emit("PIL/Pillow required for GIF export")
            self.finished.emit(False, "Missing required dependency")
            return
        
        self.progress.emit(0, len(self.task.frames), "Creating animated GIF...")
        
        # Convert QPixmaps to PIL Images
        pil_images = []
        for i, frame in enumerate(self.task.frames):
            if self._cancelled:
                self.finished.emit(False, "Export cancelled")
                return
            
            # Scale if needed
            if self.task.scale_factor != 1.0:
                frame = self._scale_pixmap(frame, self.task.scale_factor)
            
            # Convert to QImage then PIL
            qimage = frame.toImage()
            qimage = qimage.convertToFormat(QImage.Format_RGBA8888)
            
            width = qimage.width()
            height = qimage.height()
            ptr = qimage.bits()
            ptr.setsize(qimage.sizeInBytes())
            
            # Create PIL image
            pil_image = Image.frombytes(
                "RGBA", (width, height), ptr.asstring()
            )
            pil_images.append(pil_image)
            
            self.progress.emit(i + 1, len(self.task.frames), f"Processing frame {i + 1}")
        
        # Save as animated GIF
        filename = f"{self.task.base_name}.gif"
        filepath = self.task.output_dir / filename
        
        try:
            pil_images[0].save(
                str(filepath),
                save_all=True,
                append_images=pil_images[1:],
                duration=100,  # 100ms per frame (10 FPS)
                loop=Config.Export.GIF_DEFAULT_LOOP,
                optimize=Config.Export.GIF_OPTIMIZATION
            )
            self.finished.emit(True, f"Successfully exported animated GIF")
        except Exception as e:
            self.finished.emit(False, f"Failed to save GIF: {str(e)}")
    
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
                     selected_indices: Optional[List[int]] = None) -> bool:
        """
        Export frames with the specified settings.
        
        Args:
            frames: List of frames to export
            output_dir: Output directory path
            base_name: Base name for exported files
            format: Export format (PNG, JPG, BMP)
            mode: Export mode (individual, sheet, gif, selected)
            scale_factor: Scale factor for output
            pattern: Naming pattern for individual frames
            selected_indices: Frame indices for selected export
            
        Returns:
            True if export started successfully
        """
        # Validate inputs
        if not frames:
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
            export_mode = ExportMode(mode)
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
                selected_indices=selected_indices
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