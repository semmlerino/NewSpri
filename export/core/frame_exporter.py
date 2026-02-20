"""
Frame Exporter - Export functionality for sprite frames
Handles exporting individual frames, sprite sheets, and animations.
Part of Phase 4: Frame Export System implementation.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap

from config import Config

logger = logging.getLogger(__name__)


class LayoutMode(Enum):
    """Layout modes for sprite sheet export."""

    AUTO = "auto"
    ROWS = "rows"
    COLUMNS = "columns"
    SQUARE = "square"
    CUSTOM = "custom"
    SEGMENTS_PER_ROW = "segments_per_row"


class BackgroundMode(Enum):
    """Background modes for sprite sheet export."""

    TRANSPARENT = "transparent"
    SOLID = "solid"
    CHECKERBOARD = "checkerboard"


def _validate_range(name: str, value: int, min_val: int, max_val: int) -> None:
    """Raise ValueError if value is outside [min_val, max_val]."""
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name} must be between {min_val} and {max_val}")


@dataclass
class SpriteSheetLayout:
    """Configuration for sprite sheet layout and spacing."""

    mode: LayoutMode = LayoutMode.AUTO  # Layout calculation mode
    spacing: int = Config.Export.DEFAULT_SPRITE_SPACING  # Pixels between sprites
    padding: int = Config.Export.DEFAULT_SHEET_PADDING  # Padding around sheet
    max_columns: int | None = None  # Max columns (rows mode)
    max_rows: int | None = None  # Max rows (columns mode)
    custom_columns: int | None = None  # Custom grid columns
    custom_rows: int | None = None  # Custom grid rows
    background_mode: BackgroundMode = BackgroundMode.TRANSPARENT
    background_color: tuple[int, int, int, int] = Config.Export.DEFAULT_BACKGROUND_COLOR

    def __post_init__(self):
        """Validate layout configuration."""
        _validate_range(
            "Spacing",
            self.spacing,
            Config.Export.MIN_SPRITE_SPACING,
            Config.Export.MAX_SPRITE_SPACING,
        )
        _validate_range(
            "Padding",
            self.padding,
            Config.Export.MIN_SHEET_PADDING,
            Config.Export.MAX_SHEET_PADDING,
        )

        # Validate optional grid constraints
        if self.max_columns is not None:
            _validate_range(
                "Max columns",
                self.max_columns,
                Config.Export.MIN_GRID_SIZE,
                Config.Export.MAX_GRID_SIZE,
            )
        if self.max_rows is not None:
            _validate_range(
                "Max rows", self.max_rows, Config.Export.MIN_GRID_SIZE, Config.Export.MAX_GRID_SIZE
            )

        # Validate custom grid (for custom mode)
        if self.mode is LayoutMode.CUSTOM:
            if self.custom_columns is None or self.custom_rows is None:
                raise ValueError("Custom mode requires both custom_columns and custom_rows")
            _validate_range(
                "Custom columns",
                self.custom_columns,
                Config.Export.MIN_GRID_SIZE,
                Config.Export.MAX_GRID_SIZE,
            )
            _validate_range(
                "Custom rows",
                self.custom_rows,
                Config.Export.MIN_GRID_SIZE,
                Config.Export.MAX_GRID_SIZE,
            )

        # Validate background color (RGBA tuple) — isinstance is defensive for runtime callers
        if not (
            isinstance(self.background_color, (tuple, list))  # pyright: ignore[reportUnnecessaryIsInstance]
            and len(self.background_color) == 4
        ):
            raise ValueError("Background color must be an RGBA tuple with 4 values")
        for value in self.background_color:
            if not (0 <= value <= 255):
                raise ValueError("Background color values must be between 0 and 255")

    def get_effective_columns(self) -> int | None:
        """Get effective max columns for layout calculation."""
        if self.mode is LayoutMode.CUSTOM:
            return self.custom_columns
        elif self.mode is LayoutMode.ROWS:
            return self.max_columns or Config.Export.DEFAULT_MAX_COLUMNS
        return None

    def get_effective_rows(self) -> int | None:
        """Get effective max rows for layout calculation."""
        if self.mode is LayoutMode.CUSTOM:
            return self.custom_rows
        elif self.mode is LayoutMode.COLUMNS:
            return self.max_rows or Config.Export.DEFAULT_MAX_ROWS
        return None

    def calculate_estimated_dimensions(
        self, frame_width: int, frame_height: int, frame_count: int
    ) -> tuple[int, int]:
        """Estimate sprite sheet dimensions with current layout settings."""
        if frame_count <= 0:
            return (2 * self.padding, 2 * self.padding)

        if self.mode is LayoutMode.CUSTOM:
            # custom_columns and custom_rows validated in __post_init__
            assert self.custom_columns is not None
            assert self.custom_rows is not None
            cols = self.custom_columns
            rows = self.custom_rows
        elif self.mode is LayoutMode.ROWS:
            max_cols = self.max_columns or Config.Export.DEFAULT_MAX_COLUMNS
            cols = min(max_cols, frame_count)
            rows = math.ceil(frame_count / cols)
        elif self.mode is LayoutMode.COLUMNS:
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
    def from_string(cls, format_str: str) -> ExportFormat:
        """Create from string representation."""
        return cls(format_str.upper())


class ExportMode(Enum):
    """Export modes available."""

    INDIVIDUAL_FRAMES = "individual"
    SELECTED_FRAMES = "selected"
    SPRITE_SHEET = "sheet"
    SEGMENTS_SHEET = "segments_sheet"


@dataclass
class ExportConfig:
    """Typed export configuration replacing dict[str, Any] handoff."""

    output_dir: Path
    base_name: str
    format: ExportFormat
    mode: ExportMode
    scale_factor: float
    pattern: str = ""
    preset_name: str = ""
    sprite_sheet_layout: SpriteSheetLayout | None = None
    selected_indices: list[int] | None = None


class ExportTask:
    """Represents a single export task."""

    def __init__(
        self,
        frames: list[QImage],
        output_dir: Path,
        base_name: str,
        format: ExportFormat,
        mode: ExportMode,
        scale_factor: float = 1.0,
        pattern: str = "{name}_{index:03d}",
        sprite_sheet_layout: SpriteSheetLayout | None = None,
        segment_info: list[dict[str, Any]] | None = None,
    ):
        """
        Initialize export task.

        Args:
            frames: List of QImage frames to export (thread-safe)
            output_dir: Output directory path
            base_name: Base name for exported files
            format: Export format
            mode: Export mode
            scale_factor: Scale factor for output (1.0 = original size)
            pattern: Naming pattern for individual frames
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
            if self.task.mode in (ExportMode.INDIVIDUAL_FRAMES, ExportMode.SELECTED_FRAMES):
                self._export_individual_frames()
            elif self.task.mode in (ExportMode.SPRITE_SHEET, ExportMode.SEGMENTS_SHEET):
                self._export_sprite_sheet()
            else:
                raise ValueError(f"Unsupported export mode: {self.task.mode}")

        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False, f"Export failed: {e!s}")

    def cancel(self):
        """Cancel the export operation."""
        self._cancelled = True

    def _validate_segment_info(self) -> tuple[bool, str]:
        """Validate segment_info structure for segments_per_row mode.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.task.segment_info:
            return False, "No segment data for segments_per_row mode"

        required_keys = {"start_frame", "end_frame", "name"}
        for i, seg in enumerate(self.task.segment_info):
            missing = required_keys - seg.keys()
            if missing:
                return False, f"Segment {i} missing required keys: {missing}"
            if not isinstance(seg["start_frame"], int) or not isinstance(seg["end_frame"], int):
                return False, f"Segment {i} has invalid frame indices"
            if seg["end_frame"] < seg["start_frame"]:
                return False, f"Segment {i} has end_frame < start_frame"
        return True, ""

    def _export_individual_frames(self) -> None:
        """Export frames as individual files."""
        total_frames = len(self.task.frames)
        exported_count = 0
        failed_frames: list[str] = []

        for i, frame in enumerate(self.task.frames):
            if self._cancelled:
                self.finished.emit(False, "Export cancelled")
                return

            # Generate filename
            filename = (
                self.task.pattern.format(name=self.task.base_name, index=i, frame=i + 1)
                + self.task.format.extension
            )

            filepath = self.task.output_dir / filename

            # Scale if needed (frame is QImage, thread-safe)
            if self.task.scale_factor != 1.0:
                frame = self._scale_image(frame, self.task.scale_factor)

            # Save frame - Qt infers format from file extension
            if frame.save(str(filepath)):
                exported_count += 1
                self.progress.emit(i + 1, total_frames, f"Exported {filename}")
            else:
                failed_frames.append(filename)
                self.error.emit(f"Failed to export {filename}")

        # Report result — partial success if some frames exported, total failure if none
        if failed_frames:
            failed_summary = ", ".join(failed_frames[:3])
            if len(failed_frames) > 3:
                failed_summary += f" (and {len(failed_frames) - 3} more)"
            if exported_count > 0:
                self.finished.emit(
                    True,
                    f"Partial export: {exported_count} of {total_frames} frames exported; "
                    f"{len(failed_frames)} failed ({failed_summary})",
                )
            else:
                self.finished.emit(
                    False,
                    f"Export failed: {len(failed_frames)} of {total_frames} frames failed ({failed_summary})",
                )
        else:
            self.finished.emit(True, f"Successfully exported {exported_count} frames")

    def _export_sprite_sheet(self):
        """Export all frames as a single sprite sheet with enhanced layout options."""
        if not self.task.frames:
            self.finished.emit(False, "No frames to export")
            return

        self.progress.emit(0, 3, "Calculating layout...")

        # Get layout configuration
        layout = self.task.sprite_sheet_layout
        frame_count = len(self.task.frames)
        is_segments_mode = layout.mode is LayoutMode.SEGMENTS_PER_ROW and bool(
            self.task.segment_info
        )

        # Validate segment_info for segments_per_row mode
        if layout.mode is LayoutMode.SEGMENTS_PER_ROW:
            is_valid, error_msg = self._validate_segment_info()
            if not is_valid:
                self.finished.emit(False, error_msg)
                return

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
        if is_segments_mode:
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
        sprite_sheet = self._create_background_sheet(
            sheet_width, sheet_height, layout, self.task.format
        )

        # Draw frames onto sprite sheet with spacing
        if is_segments_mode:
            draw_ok = self._draw_sprites_segments_per_row(
                sprite_sheet, cols, rows, frame_width, frame_height, layout
            )
        else:
            draw_ok = self._draw_sprites_with_layout(
                sprite_sheet, cols, rows, frame_width, frame_height, layout
            )

        if not draw_ok:
            # Draw method detected cancellation; finished already emitted
            return

        self.progress.emit(2, 3, "Saving sprite sheet...")

        # Save sprite sheet
        filename = f"{self.task.base_name}_sheet{self.task.format.extension}"
        filepath = self.task.output_dir / filename

        if sprite_sheet.save(str(filepath)):
            self.progress.emit(3, 3, f"Saved {filename}")
            self.finished.emit(
                True,
                f"Successfully exported sprite sheet ({cols}x{rows}, {layout.spacing}px spacing)",
            )
        else:
            self.finished.emit(False, "Failed to save sprite sheet")

    def _calculate_grid_layout(
        self, layout: SpriteSheetLayout, frame_count: int
    ) -> tuple[int, int]:
        """Calculate optimal grid dimensions based on layout configuration."""
        if layout.mode is LayoutMode.CUSTOM:
            # Use exact user-specified dimensions (validated in __post_init__)
            effective_cols = layout.get_effective_columns()
            effective_rows = layout.get_effective_rows()
            assert effective_cols is not None
            assert effective_rows is not None
            cols = effective_cols
            rows = effective_rows

        elif layout.mode is LayoutMode.ROWS:
            # Prioritize horizontal layout with max columns constraint
            max_cols = layout.get_effective_columns() or Config.Export.DEFAULT_MAX_COLUMNS
            cols = min(max_cols, frame_count)
            rows = math.ceil(frame_count / cols)

        elif layout.mode is LayoutMode.COLUMNS:
            # Prioritize vertical layout with max rows constraint
            max_rows = layout.get_effective_rows() or Config.Export.DEFAULT_MAX_ROWS
            rows = min(max_rows, frame_count)
            cols = math.ceil(frame_count / rows)

        elif layout.mode is LayoutMode.SQUARE:
            # Force closest to square aspect ratio
            cols = math.ceil(math.sqrt(frame_count))
            rows = math.ceil(frame_count / cols)

        elif layout.mode is LayoutMode.SEGMENTS_PER_ROW:
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

    def _calculate_auto_layout(
        self, frame_count: int, layout: SpriteSheetLayout
    ) -> tuple[int, int]:
        """Calculate automatic layout using intelligent heuristics."""
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

    def _calculate_sheet_dimensions(
        self, cols: int, rows: int, frame_width: int, frame_height: int, layout: SpriteSheetLayout
    ) -> tuple[int, int]:
        """Calculate total sprite sheet dimensions including spacing and padding."""
        # Calculate total width: frames + spacing between frames + padding on both sides
        sheet_width = (cols * frame_width) + ((cols - 1) * layout.spacing) + (2 * layout.padding)

        # Calculate total height: frames + spacing between frames + padding on both sides
        sheet_height = (rows * frame_height) + ((rows - 1) * layout.spacing) + (2 * layout.padding)

        return sheet_width, sheet_height

    def _calculate_segments_sheet_dimensions(
        self, frame_width: int, frame_height: int, layout: SpriteSheetLayout
    ) -> tuple[int, int]:
        """Calculate sprite sheet dimensions for segments per row mode."""

        if not self.task.segment_info:
            return frame_width + (2 * layout.padding), frame_height + (2 * layout.padding)

        # Find the maximum width needed (longest segment)
        max_frames_in_segment = max(
            seg["end_frame"] - seg["start_frame"] + 1 for seg in self.task.segment_info
        )

        # Calculate width based on the longest segment
        sheet_width = (
            (max_frames_in_segment * frame_width)
            + ((max_frames_in_segment - 1) * layout.spacing)
            + (2 * layout.padding)
        )

        # Calculate height based on actual number of segments (rows)
        num_segments = len(self.task.segment_info)
        sheet_height = (
            (num_segments * frame_height)
            + ((num_segments - 1) * layout.spacing)
            + (2 * layout.padding)
        )

        return sheet_width, sheet_height

    def _create_background_sheet(
        self,
        width: int,
        height: int,
        layout: SpriteSheetLayout,
        export_format: ExportFormat | None = None,
    ) -> QImage:
        """Create sprite sheet with the specified background (thread-safe QImage).

        When export_format is JPG and the background would be transparent,
        white is used instead because JPG has no alpha channel.
        """
        # Use QImage instead of QPixmap for thread-safety
        sprite_sheet = QImage(width, height, QImage.Format.Format_ARGB32)

        if layout.background_mode is BackgroundMode.TRANSPARENT:
            if export_format is ExportFormat.JPG:
                # JPG cannot represent transparency; use white to avoid black output
                sprite_sheet.fill(QColor(255, 255, 255, 255))
            else:
                sprite_sheet.fill(QColor(0, 0, 0, 0))  # Fully transparent

        elif layout.background_mode is BackgroundMode.SOLID:
            r, g, b, a = layout.background_color
            sprite_sheet.fill(QColor(r, g, b, a))

        elif layout.background_mode is BackgroundMode.CHECKERBOARD:
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

    def _begin_export_painter(self, target: QImage) -> QPainter:
        """Create a QPainter for target with export render hints applied."""
        painter = QPainter(target)
        if Config.Export.ENABLE_ANTIALIASING:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        return painter

    def _draw_sprites_with_layout(
        self,
        sprite_sheet: QImage,
        cols: int,
        rows: int,
        frame_width: int,
        frame_height: int,
        layout: SpriteSheetLayout,
    ) -> bool:
        """Draw all frames onto the sprite sheet with proper spacing and layout.

        Returns True on success, False if cancelled (caller must emit finished).
        """
        painter = self._begin_export_painter(sprite_sheet)

        for i, frame in enumerate(self.task.frames):
            if self._cancelled:
                painter.end()
                self.finished.emit(False, "Export cancelled")
                return False

            # Calculate grid position
            row = i // cols
            col = i % cols

            # Calculate pixel position with spacing and padding
            x = layout.padding + (col * (frame_width + layout.spacing))
            y = layout.padding + (row * (frame_height + layout.spacing))

            self._draw_frame(painter, frame, x, y)

        painter.end()
        return True

    def _calculate_segments_per_row_layout(self) -> tuple[int, int]:
        """Calculate layout for segments per row mode."""

        if not self.task.segment_info:
            # No segments, fall back to square layout
            frame_count = len(self.task.frames)
            cols = math.ceil(math.sqrt(frame_count))
            rows = math.ceil(frame_count / cols)
            return cols, rows

        # Calculate maximum frames per segment
        max_frames_per_segment = max(
            seg["end_frame"] - seg["start_frame"] + 1 for seg in self.task.segment_info
        )

        # Rows = number of segments, cols = max frames in any segment
        rows = len(self.task.segment_info)
        cols = max_frames_per_segment

        return cols, rows

    def _draw_sprites_segments_per_row(
        self,
        sprite_sheet: QImage,
        cols: int,
        rows: int,
        frame_width: int,
        frame_height: int,
        layout: SpriteSheetLayout,
    ) -> bool:
        """Draw sprites with each segment on its own row.

        Returns True on success, False if cancelled (caller must emit finished).
        """
        painter = self._begin_export_painter(sprite_sheet)

        # Draw each segment on its own row
        for row_idx, segment in enumerate(self.task.segment_info):
            start = segment["start_frame"]
            end = segment["end_frame"]

            frames_drawn = 0
            # Draw frames for this segment
            for col_idx, frame_idx in enumerate(range(start, end + 1)):
                if frame_idx >= len(self.task.frames):
                    break

                if self._cancelled:
                    painter.end()
                    self.finished.emit(False, "Export cancelled")
                    return False

                frame = self.task.frames[frame_idx]

                # Calculate pixel position with spacing and padding
                x = layout.padding + (col_idx * (frame_width + layout.spacing))
                y = layout.padding + (row_idx * (frame_height + layout.spacing))

                self._draw_frame(painter, frame, x, y)
                frames_drawn += 1

            logger.debug("Drew %d frames for segment '%s'", frames_drawn, segment["name"])

        painter.end()
        return True

    def _draw_frame(self, painter: QPainter, frame: QImage, x: int, y: int) -> None:
        """Scale (if needed) and draw a single frame onto painter at (x, y)."""
        if self.task.scale_factor != 1.0:
            painter.drawImage(x, y, self._scale_image(frame, self.task.scale_factor))
        else:
            painter.drawImage(x, y, frame)

    def _scale_image(self, image: QImage, scale_factor: float) -> QImage:
        """Scale an image by the given factor (thread-safe)."""
        new_width = max(1, int(image.width() * scale_factor))
        new_height = max(1, int(image.height() * scale_factor))
        return image.scaled(
            new_width,
            new_height,
            aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
            mode=Qt.TransformationMode.SmoothTransformation,
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
        self._worker: ExportWorker | None = None
        self._current_task: ExportTask | None = None

    def export_frames(
        self,
        frames: list[QPixmap],
        output_dir: str,
        base_name: str = "frame",
        format: str = "PNG",
        mode: str = "individual",
        scale_factor: float = 1.0,
        pattern: str | None = None,
        selected_indices: list[int] | None = None,
        sprite_sheet_layout: SpriteSheetLayout | None = None,
        segment_info: list[dict[str, Any]] | None = None,
    ) -> bool:
        """
        Export frames with the specified settings.

        Note: If a previous export is still running, this method will wait for it
        to complete before starting the new export. This prevents thread crashes.

        Args:
            frames: List of frames to export
            output_dir: Output directory path
            base_name: Base name for exported files
            format: Export format (PNG, JPG, BMP)
            mode: Export mode (individual, sheet, selected, segments_sheet)
            scale_factor: Scale factor for output
            pattern: Naming pattern for individual frames
            selected_indices: Frame indices for selected export (unused by ExportTask; filtering done before calling)
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

        # Reject export if previous worker is still running
        if self._worker is not None and self._worker.isRunning():
            logger.debug("Export rejected: already in progress")
            self.exportError.emit("An export is already in progress")
            return False

        task = self._prepare_export(
            frames,
            output_dir,
            base_name,
            format,
            mode,
            scale_factor,
            pattern,
            sprite_sheet_layout,
            segment_info,
        )
        if task is None:
            return False

        self._current_task = task
        self._start_worker(task)
        return True

    def _prepare_export(
        self,
        frames: list[QPixmap],
        output_dir: str,
        base_name: str,
        format: str,
        mode: str,
        scale_factor: float,
        pattern: str | None,
        sprite_sheet_layout: SpriteSheetLayout | None,
        segment_info: list[dict[str, Any]] | None,
    ) -> ExportTask | None:
        """Validate inputs, parse settings, convert frames, and build an ExportTask.

        Returns None (and emits exportError) on any validation failure.
        """
        if not frames:
            logger.debug("No frames to export, emitting error")
            self.exportError.emit("No frames to export")
            return None

        # Create output directory if needed
        output_path = Path(output_dir)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.exportError.emit(f"Failed to create output directory: {e!s}")
            return None

        # Parse format and mode
        try:
            export_format = ExportFormat.from_string(format)
            logger.debug("Parsed export format: %s", export_format)

            export_mode = ExportMode(mode)
            logger.debug("Parsed export mode: %s", export_mode)
        except ValueError as e:
            self.exportError.emit(f"Invalid export settings: {e!s}")
            return None

        if pattern is None:
            pattern = Config.Export.DEFAULT_PATTERN

        # Sanitize base_name to remove characters illegal in file paths
        base_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base_name)

        # Convert QPixmap frames to QImage for thread-safe processing
        # QPixmap is NOT thread-safe; QImage IS thread-safe for worker threads
        image_frames = self._convert_frames_to_images(frames)
        if image_frames is None:
            return None

        try:
            return ExportTask(
                frames=image_frames,
                output_dir=output_path,
                base_name=base_name,
                format=export_format,
                mode=export_mode,
                scale_factor=scale_factor,
                pattern=pattern,
                sprite_sheet_layout=sprite_sheet_layout,
                segment_info=segment_info,
            )
        except ValueError as e:
            self.exportError.emit(str(e))
            return None

    def _convert_frames_to_images(self, frames: list[QPixmap]) -> list[QImage] | None:
        """Convert QPixmap frames to thread-safe QImage list.

        Returns None (and emits exportError) if any frame fails to convert.
        """
        image_frames: list[QImage] = []
        for i, frame in enumerate(frames):
            image = frame.toImage()
            if image.isNull():
                self.exportError.emit(f"Failed to convert frame {i} to image")
                return None
            image_frames.append(image)
        return image_frames

    def _start_worker(self, task: ExportTask) -> None:
        """Create, connect, and start the export worker thread."""
        self._worker = ExportWorker(task)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self.exportStarted.emit()
        self._worker.start()

    def cancel_export(self):
        """Cancel the current export operation."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            if not self._worker.wait(5000):
                self._worker.terminate()

    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress updates from worker."""
        self.exportProgress.emit(current, total, message)

    def _on_finished(self, success: bool, message: str):
        """Handle export completion."""
        if self._worker is not None:
            self._worker.wait(5000)  # Ensure thread has fully stopped before releasing reference
        self._worker = None
        self._current_task = None
        self.exportFinished.emit(success, message)

    def _on_error(self, error_message: str):
        """Handle export errors."""
        self.exportError.emit(error_message)


# Singleton instance
_exporter_instance: FrameExporter | None = None


def get_frame_exporter() -> FrameExporter:
    """Get the global frame exporter instance."""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = FrameExporter()
    return _exporter_instance


def reset_frame_exporter() -> None:
    """Reset the global frame exporter instance (for testing).

    Properly waits for any running export thread to complete before resetting.
    """
    global _exporter_instance
    if (
        _exporter_instance is not None
        and _exporter_instance._worker is not None
        and _exporter_instance._worker.isRunning()
    ):
        # Wait for any running export thread to complete
        _exporter_instance._worker.quit()
        _exporter_instance._worker.wait()
    _exporter_instance = None
