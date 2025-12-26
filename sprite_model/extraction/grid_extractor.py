#!/usr/bin/env python3
"""
Grid-Based Frame Extraction Module
==================================

Independent grid-based frame extraction functionality for sprite sheets.
Handles regular grids with support for margins, spacing, and validation.

This module is completely independent and can be used standalone or
integrated into larger sprite processing systems.
"""

from typing import NamedTuple

from PySide6.QtCore import QRect
from PySide6.QtGui import QPixmap

from config import Config


class GridConfig(NamedTuple):
    """Configuration for grid-based frame extraction."""
    width: int
    height: int
    offset_x: int = 0
    offset_y: int = 0
    spacing_x: int = 0
    spacing_y: int = 0


class GridLayout(NamedTuple):
    """Layout information for extracted grid."""
    frames_per_row: int
    frames_per_col: int
    total_frames: int
    available_width: int
    available_height: int


class GridExtractor:
    """
    Standalone grid-based frame extraction engine.

    Provides methods for extracting frames from sprite sheets arranged in
    regular grids, with support for margins, spacing, and comprehensive validation.
    """

    def __init__(self):
        """Initialize the grid extractor."""
        pass

    def extract_frames(self, sprite_sheet: QPixmap, config: GridConfig) -> tuple[bool, str, list[QPixmap]]:
        """
        Extract frames from sprite sheet using grid-based extraction.

        Args:
            sprite_sheet: Source sprite sheet pixmap
            config: Grid configuration (frame size, offsets, spacing)

        Returns:
            Tuple of (success, error_message, frame_list)
        """
        if not sprite_sheet or sprite_sheet.isNull():
            return False, "No sprite sheet provided", []

        # Validate frame settings
        valid, error_msg = self.validate_frame_settings(sprite_sheet, config)
        if not valid:
            return False, error_msg, []

        try:
            sheet_width = sprite_sheet.width()
            sheet_height = sprite_sheet.height()

            # Calculate available area after margins
            available_width = sheet_width - config.offset_x
            available_height = sheet_height - config.offset_y

            # Calculate grid layout
            layout = self._calculate_grid_layout(available_width, available_height, config)

            # Extract individual frames with spacing
            frames = []
            for row in range(layout.frames_per_col):
                for col in range(layout.frames_per_row):
                    x = config.offset_x + (col * (config.width + config.spacing_x))
                    y = config.offset_y + (row * (config.height + config.spacing_y))

                    # Ensure we don't exceed sheet boundaries
                    if x + config.width <= sheet_width and y + config.height <= sheet_height:
                        frame_rect = QRect(x, y, config.width, config.height)
                        frame = sprite_sheet.copy(frame_rect)

                        if not frame.isNull():
                            frames.append(frame)

            return True, "", frames

        except Exception as e:
            return False, f"Error extracting frames: {e!s}", []

    def validate_frame_settings(self, sprite_sheet: QPixmap, config: GridConfig) -> tuple[bool, str]:
        """
        Validate frame extraction parameters including offsets and spacing.

        Args:
            sprite_sheet: Source sprite sheet for size validation
            config: Grid configuration to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic dimension validation
        if config.width <= 0:
            return False, "Frame width must be greater than 0"
        if config.height <= 0:
            return False, "Frame height must be greater than 0"
        if config.width > Config.FrameExtraction.MAX_FRAME_SIZE:
            return False, f"Frame width cannot exceed {Config.FrameExtraction.MAX_FRAME_SIZE}"
        if config.height > Config.FrameExtraction.MAX_FRAME_SIZE:
            return False, f"Frame height cannot exceed {Config.FrameExtraction.MAX_FRAME_SIZE}"

        # Validate offsets
        if config.offset_x < 0:
            return False, "X offset cannot be negative"
        if config.offset_y < 0:
            return False, "Y offset cannot be negative"
        if config.offset_x > Config.FrameExtraction.MAX_OFFSET:
            return False, f"X offset cannot exceed {Config.FrameExtraction.MAX_OFFSET}"
        if config.offset_y > Config.FrameExtraction.MAX_OFFSET:
            return False, f"Y offset cannot exceed {Config.FrameExtraction.MAX_OFFSET}"

        # Validate spacing
        if config.spacing_x < 0:
            return False, "X spacing cannot be negative"
        if config.spacing_y < 0:
            return False, "Y spacing cannot be negative"
        if config.spacing_x > Config.FrameExtraction.MAX_SPACING:
            return False, f"X spacing cannot exceed {Config.FrameExtraction.MAX_SPACING}"
        if config.spacing_y > Config.FrameExtraction.MAX_SPACING:
            return False, f"Y spacing cannot exceed {Config.FrameExtraction.MAX_SPACING}"

        # Check if frame size is reasonable for the sprite sheet
        if sprite_sheet and not sprite_sheet.isNull():
            sheet_width = sprite_sheet.width()
            sheet_height = sprite_sheet.height()

            # At minimum, one frame must fit after applying offset
            if config.offset_x + config.width > sheet_width:
                return False, f"Frame width + X offset ({config.offset_x + config.width}) exceeds sheet width ({sheet_width})"
            if config.offset_y + config.height > sheet_height:
                return False, f"Frame height + Y offset ({config.offset_y + config.height}) exceeds sheet height ({sheet_height})"

        return True, ""

    def calculate_grid_layout(self, sprite_sheet: QPixmap, config: GridConfig) -> GridLayout | None:
        """
        Calculate the grid layout for the given sprite sheet and configuration.

        Args:
            sprite_sheet: Source sprite sheet
            config: Grid configuration

        Returns:
            GridLayout object with layout information, or None if invalid
        """
        if not sprite_sheet or sprite_sheet.isNull():
            return None

        # Validate settings first
        valid, _ = self.validate_frame_settings(sprite_sheet, config)
        if not valid:
            return None

        available_width = sprite_sheet.width() - config.offset_x
        available_height = sprite_sheet.height() - config.offset_y

        return self._calculate_grid_layout(available_width, available_height, config)

    def _calculate_grid_layout(self, available_width: int, available_height: int, config: GridConfig) -> GridLayout:
        """
        Calculate grid layout from available dimensions and configuration.

        Args:
            available_width: Width available for frames after margins
            available_height: Height available for frames after margins
            config: Grid configuration

        Returns:
            GridLayout with calculated dimensions
        """
        # Calculate how many frames fit (accounting for spacing)
        # For N frames, we have N-1 gaps between them
        if config.spacing_x > 0:
            frames_per_row = (available_width + config.spacing_x) // (config.width + config.spacing_x)
        else:
            frames_per_row = available_width // config.width if config.width > 0 else 0

        if config.spacing_y > 0:
            frames_per_col = (available_height + config.spacing_y) // (config.height + config.spacing_y)
        else:
            frames_per_col = available_height // config.height if config.height > 0 else 0

        total_frames = frames_per_row * frames_per_col

        return GridLayout(
            frames_per_row=frames_per_row,
            frames_per_col=frames_per_col,
            total_frames=total_frames,
            available_width=available_width,
            available_height=available_height
        )

    def create_frame_info_string(self, layout: GridLayout, config: GridConfig) -> str:
        """
        Create a formatted info string describing the grid extraction.

        Args:
            layout: Grid layout information
            config: Grid configuration used

        Returns:
            Formatted string with frame extraction details
        """
        if layout.total_frames > 0:
            return (
                f"<br><b>Frames:</b> {layout.total_frames} "
                f"({layout.frames_per_row}×{layout.frames_per_col})<br>"
                f"<b>Frame size:</b> {config.width}×{config.height} px"
            )
        else:
            return "<br><b>Frames:</b> 0"
