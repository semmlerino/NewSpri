"""Preview pixmap rendering for export settings."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap

from export.core.frame_exporter import (
    BackgroundMode,
    ExportMode,
    LayoutMode,
    SpriteSheetLayout,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from managers.animation_segment_manager import AnimationSegment

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExportPreviewRequest:
    """Explicit input state needed to render an export preview."""

    mode: ExportMode
    sprites: Sequence[QPixmap]
    layout_mode: LayoutMode = LayoutMode.AUTO
    columns: int = 8
    rows: int = 8
    spacing: int = 0
    background_mode: BackgroundMode = BackgroundMode.TRANSPARENT
    background_color: tuple[int, int, int, int] | None = None
    selected_indices: Sequence[int] = ()
    segments: Sequence[AnimationSegment] = ()
    segments_available: bool = True


@dataclass(frozen=True)
class ExportPreviewResult:
    """Rendered preview pixmap and optional display metadata."""

    pixmap: QPixmap
    info_text: str | None = None


class ExportPreviewRenderer:
    """Render export preview pixmaps from explicit request data."""

    _MAX_SEGMENT_PREVIEW_WIDTH = 800
    _MAX_SEGMENT_PREVIEW_HEIGHT = 600

    def render(self, request: ExportPreviewRequest) -> ExportPreviewResult:
        """Render a preview for the requested export mode."""
        if not request.sprites:
            return ExportPreviewResult(QPixmap())

        if request.mode in (ExportMode.SPRITE_SHEET, ExportMode.SEGMENTS_SHEET):
            return self._render_sheet_preview(request)

        return self._render_frames_preview(request)

    def _render_sheet_preview(self, request: ExportPreviewRequest) -> ExportPreviewResult:
        """Render sprite sheet or segments-per-row previews."""
        if request.mode is ExportMode.SEGMENTS_SHEET:
            try:
                return self._render_segments_preview(request)
            except Exception as e:
                logger.debug("Failed to render segments preview: %s", e, exc_info=True)
                logger.debug("Falling back to regular sheet preview")

        return self._render_sprite_sheet_preview(request)

    def _render_sprite_sheet_preview(self, request: ExportPreviewRequest) -> ExportPreviewResult:
        sprite_count = len(request.sprites)
        cols, rows = self._calculate_grid(request.layout_mode, sprite_count, request)
        spacing = request.spacing
        fw, fh = self._frame_dimensions(request)
        sheet_w, sheet_h = self._sheet_dimensions(cols, rows, fw, fh, spacing)

        pixmap = QPixmap(sheet_w, sheet_h)
        self._fill_background(pixmap, request)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i, sprite in enumerate(request.sprites):
            if i >= cols * rows:
                break
            row = i // cols
            col = i % cols
            x = col * (fw + spacing)
            y = row * (fh + spacing)
            painter.drawPixmap(x, y, sprite)
        painter.end()

        return ExportPreviewResult(
            pixmap,
            f"Sprite Sheet: {cols}x{rows} grid, {sheet_w}x{sheet_h}px",
        )

    def _render_segments_preview(self, request: ExportPreviewRequest) -> ExportPreviewResult:
        if not request.segments:
            if not request.segments_available:
                return self._placeholder_pixmap(
                    "No animation segments available",
                    "Segments Per Row: No segments defined",
                )
            return self._placeholder_pixmap(
                "No animation segments defined",
                "Segments Per Row: No segments",
            )

        try:
            max_frames_in_segment = max(
                1,
                max(seg.end_frame - seg.start_frame + 1 for seg in request.segments),
            )
        except (ValueError, AttributeError) as e:
            logger.debug("Invalid segment data: %s", e)
            max_frames_in_segment = 1

        rows = len(request.segments)
        spacing = request.spacing
        fw, fh = self._frame_dimensions(request)
        sheet_w, sheet_h = self._sheet_dimensions(
            max_frames_in_segment,
            rows,
            fw,
            fh,
            spacing,
        )

        scale = min(
            1.0,
            self._MAX_SEGMENT_PREVIEW_WIDTH / sheet_w if sheet_w > 0 else 1.0,
        )
        if sheet_h * scale > self._MAX_SEGMENT_PREVIEW_HEIGHT and sheet_h > 0:
            scale = self._MAX_SEGMENT_PREVIEW_HEIGHT / sheet_h

        if scale < 1.0:
            fw = max(1, int(fw * scale))
            fh = max(1, int(fh * scale))
            spacing = int(spacing * scale)
            sheet_w, sheet_h = self._sheet_dimensions(
                max_frames_in_segment,
                rows,
                fw,
                fh,
                spacing,
            )

        pixmap = QPixmap(sheet_w, sheet_h)
        self._fill_background(pixmap, request)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for row_idx, segment in enumerate(request.segments):
            for frame_idx in range(segment.start_frame, segment.end_frame + 1):
                if 0 <= frame_idx < len(request.sprites):
                    col_idx = frame_idx - segment.start_frame
                    x = col_idx * (fw + spacing)
                    y = row_idx * (fh + spacing)

                    if scale < 1.0:
                        scaled_sprite = request.sprites[frame_idx].scaled(
                            fw,
                            fh,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        painter.drawPixmap(x, y, scaled_sprite)
                    else:
                        painter.drawPixmap(x, y, request.sprites[frame_idx])
        painter.end()

        info = f"Segments Per Row: {rows} segments"
        if scale < 1.0:
            info += f" (preview scaled {int(scale * 100)}%)"

        return ExportPreviewResult(pixmap, info)

    def _render_frames_preview(self, request: ExportPreviewRequest) -> ExportPreviewResult:
        display_count = min(len(request.sprites), 6)
        cols = min(3, display_count)
        rows = math.ceil(display_count / cols)
        fw = min(request.sprites[0].width(), 100)
        fh = min(request.sprites[0].height(), 100)
        spacing = 10
        width = cols * fw + (cols - 1) * spacing
        height = rows * fh + (rows - 1) * spacing

        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if request.mode is ExportMode.SELECTED_FRAMES:
            selected_indices = list(request.selected_indices)
        else:
            selected_indices = list(range(len(request.sprites)))

        for i in range(min(display_count, len(selected_indices))):
            frame_idx = selected_indices[i]
            if 0 <= frame_idx < len(request.sprites):
                row = i // cols
                col = i % cols
                x = col * (fw + spacing)
                y = row * (fh + spacing)

                scaled = request.sprites[frame_idx].scaled(
                    fw,
                    fh,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                painter.drawPixmap(x, y, scaled)
        painter.end()

        if request.mode is ExportMode.SELECTED_FRAMES:
            info = f"Selected: {len(selected_indices)} frames"
        else:
            info = f"Individual: {len(request.sprites)} frames"

        if len(selected_indices) > display_count:
            info += f" (showing {display_count})"

        return ExportPreviewResult(pixmap, info)

    def _fill_background(self, pixmap: QPixmap, request: ExportPreviewRequest) -> None:
        """Fill pixmap background from explicit preview request settings."""
        if request.background_mode is BackgroundMode.SOLID and request.background_color is not None:
            pixmap.fill(QColor(*request.background_color))
        else:
            pixmap.fill(Qt.GlobalColor.transparent)

    def _placeholder_pixmap(self, text: str, info: str) -> ExportPreviewResult:
        """Create a placeholder preview pixmap."""
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.GlobalColor.white)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(QFont("Segoe UI", 12))
        painter.setPen(QColor(108, 117, 125))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()

        return ExportPreviewResult(pixmap, info)

    def _frame_dimensions(self, request: ExportPreviewRequest) -> tuple[int, int]:
        """Return frame dimensions using the first sprite as the preview source."""
        if request.sprites:
            return request.sprites[0].width(), request.sprites[0].height()
        return 32, 32

    def _sheet_dimensions(
        self,
        cols: int,
        rows: int,
        frame_width: int,
        frame_height: int,
        spacing: int,
    ) -> tuple[int, int]:
        """Calculate sheet dimensions using the core layout helper."""
        layout = SpriteSheetLayout(spacing=spacing)
        return layout.dimensions_for(cols, rows, frame_width, frame_height)

    def _calculate_grid(
        self,
        layout_mode: LayoutMode,
        sprite_count: int,
        request: ExportPreviewRequest,
    ) -> tuple[int, int]:
        """Calculate (columns, rows) for the requested sheet layout."""
        if layout_mode is LayoutMode.COLUMNS:
            cols = max(1, request.columns)
            rows = math.ceil(sprite_count / cols)
        elif layout_mode is LayoutMode.ROWS:
            rows = max(1, request.rows)
            cols = math.ceil(sprite_count / rows)
        elif layout_mode is LayoutMode.SQUARE:
            side = math.ceil(math.sqrt(sprite_count))
            cols = rows = side
        else:
            cols = math.ceil(math.sqrt(sprite_count))
            rows = math.ceil(sprite_count / cols)
        return cols, rows
