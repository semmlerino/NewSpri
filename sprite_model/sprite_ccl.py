#!/usr/bin/env python3
"""
CCL Operations Module
=====================

Connected Component Labeling (CCL) operations for sprite extraction.
Extracted from monolithic SpriteModel for better separation of concerns and testability.

Handles:
- CCL-based frame extraction from irregular sprite collections
- Background transparency processing
- CCL mode state management
- Sprite boundary management
"""

import logging
from collections.abc import Callable

import numpy as np
from PySide6.QtCore import QRect
from PySide6.QtGui import QImage, QPixmap

from sprite_model.extraction_mode import ExtractionMode
from sprite_model.sprite_extraction import CCLDetectionResult

logger = logging.getLogger(__name__)


class CCLOperations:
    """
    CCL (Connected Component Labeling) operations for sprite extraction.

    Handles extraction of individual sprites from irregular collections using
    connected component labeling algorithms, background transparency processing,
    and CCL-specific state management.
    """

    def __init__(self):
        """Initialize CCL operations with default state."""
        # CCL-specific state
        self._ccl_sprite_bounds: list[
            tuple[int, int, int, int]
        ] = []  # (x, y, w, h) for each sprite
        self._ccl_background_color: tuple[int, int, int] | None = (
            None  # RGB background color for transparency
        )
        self._ccl_color_tolerance: int = 10  # Tolerance for background color matching

        # Mode state
        self._extraction_mode: ExtractionMode = ExtractionMode.GRID

    def extract_ccl_frames(
        self,
        sprite_sheet: QPixmap | None,
        sprite_sheet_path: str,
        detect_sprites_ccl_enhanced: Callable[[str], CCLDetectionResult | None],
        detect_background_color: Callable[[str], tuple[tuple[int, int, int], int] | None],
    ) -> tuple[bool, str, int, list[QPixmap]]:
        """
        Extract frames using CCL-detected sprite boundaries (for irregular sprite collections).

        Args:
            sprite_sheet: The original sprite sheet QPixmap
            sprite_sheet_path: Path to the sprite sheet file
            detect_sprites_ccl_enhanced: Function to detect sprites using CCL
            detect_background_color: Function to detect background color

        Returns:
            Tuple of (success, error_message, frame_count, sprite_frames)
        """
        if sprite_sheet is None or sprite_sheet.isNull():
            return False, "No sprite sheet loaded", 0, []

        # If no CCL sprite bounds, try to run auto-detection first
        if not self._ccl_sprite_bounds:
            if not sprite_sheet_path:
                return False, "No sprite sheet path available for CCL detection.", 0, []

            # Try to run CCL detection automatically
            try:
                ccl_result = detect_sprites_ccl_enhanced(sprite_sheet_path)

                # Ensure we got a CCLDetectionResult
                if not isinstance(ccl_result, CCLDetectionResult):
                    return (
                        False,
                        f"CCL auto-detection returned unexpected type: {type(ccl_result)}",
                        0,
                        [],
                    )

                if ccl_result and ccl_result.success:
                    # Store CCL sprite boundaries
                    if ccl_result.ccl_sprite_bounds:
                        self._ccl_sprite_bounds = ccl_result.ccl_sprite_bounds

                        # Store background color info if available
                        bg_color_info = detect_background_color(sprite_sheet_path)
                        if bg_color_info is not None:
                            self._ccl_background_color = bg_color_info[0]
                            # Cap tolerance at 25 for CCL mode to prevent destroying sprite content
                            raw_tolerance = bg_color_info[1]
                            self._ccl_color_tolerance = min(raw_tolerance, 25)
                            if raw_tolerance > 25:
                                logger.debug(
                                    "CCL reduced background tolerance from %d to %d to preserve sprite "
                                    "content",
                                    raw_tolerance,
                                    self._ccl_color_tolerance,
                                )
                    else:
                        logger.warning("CCL detection succeeded but returned no sprite bounds")
                else:
                    return False, "CCL auto-detection failed. Cannot extract CCL frames.", 0, []
            except Exception as e:
                return False, f"CCL auto-detection error: {e!s}", 0, []

        # Check again after potential auto-detection
        if not self._ccl_sprite_bounds:
            return False, "No CCL sprite boundaries detected.", 0, []

        try:
            # Extract individual sprites using exact CCL boundaries
            sprite_frames = []
            filtered_count = 0
            null_frame_count = 0

            sheet_width = sprite_sheet.width()
            sheet_height = sprite_sheet.height()
            logger.debug("CCL sheet dimensions: %dx%d", sheet_width, sheet_height)
            logger.debug("CCL processing %d detected sprite bounds", len(self._ccl_sprite_bounds))

            for i, (x, y, width, height) in enumerate(self._ccl_sprite_bounds):
                # Ensure bounds are within sheet dimensions
                if x >= 0 and y >= 0 and x + width <= sheet_width and y + height <= sheet_height:
                    frame_rect = QRect(x, y, width, height)
                    frame = sprite_sheet.copy(frame_rect)

                    if not frame.isNull():
                        # Apply background color transparency if available
                        if self._ccl_background_color is not None:
                            frame = self._apply_background_transparency(
                                frame, self._ccl_background_color, self._ccl_color_tolerance
                            )

                        sprite_frames.append(frame)
                    else:
                        null_frame_count += 1
                        if null_frame_count <= 5:  # Only log first few
                            logger.debug(
                                "CCL sprite %d produced null frame from (%d, %d) %dx%d",
                                i + 1,
                                x,
                                y,
                                width,
                                height,
                            )
                else:
                    # Log invalid bounds but continue
                    filtered_count += 1
                    if filtered_count <= 5:  # Only log first few invalid bounds
                        logger.debug(
                            "CCL sprite %d has invalid bounds (%d, %d) %dx%d for sheet %dx%d",
                            i + 1,
                            x,
                            y,
                            width,
                            height,
                            sheet_width,
                            sheet_height,
                        )

            # Report filtering statistics
            total_detected = len(self._ccl_sprite_bounds)
            total_extracted = len(sprite_frames)
            logger.debug(
                "CCL extraction results: %d/%d sprites extracted", total_extracted, total_detected
            )
            if filtered_count > 0:
                logger.debug("CCL filtered %d sprites with invalid bounds", filtered_count)
            if null_frame_count > 0:
                logger.debug("CCL had %d null sprite frames", null_frame_count)

            # Set extraction mode
            self._extraction_mode = ExtractionMode.CCL

            return True, "", len(sprite_frames), sprite_frames

        except Exception as e:
            return False, f"Error extracting CCL frames: {e!s}", 0, []

    def set_current_mode(self, mode: object) -> bool:
        """Update the selected extraction mode without extracting frames."""
        if not isinstance(mode, ExtractionMode):
            return False
        self._extraction_mode = mode
        return True

    def get_extraction_mode(self) -> ExtractionMode:
        """Get current extraction mode."""
        return self._extraction_mode

    def get_ccl_sprite_bounds(self) -> list[tuple[int, int, int, int]]:
        """Get the CCL-detected sprite boundaries."""
        return self._ccl_sprite_bounds.copy()

    def clear_ccl_data(self) -> None:
        """Clear all CCL-related data and reset to defaults."""
        self._ccl_sprite_bounds.clear()
        self._ccl_background_color = None
        self._ccl_color_tolerance = 10
        self._extraction_mode = ExtractionMode.GRID

    def _apply_background_transparency(
        self, pixmap: QPixmap, background_color: tuple[int, int, int], tolerance: int
    ) -> QPixmap:
        """
        Apply background color transparency to a QPixmap.

        Args:
            pixmap: Source QPixmap to process
            background_color: RGB background color to make transparent
            tolerance: Color matching tolerance (0-255)

        Returns:
            QPixmap with background transparency applied
        """
        try:
            # Convert QPixmap to QImage for pixel manipulation
            image = pixmap.toImage()

            # Convert to ARGB format for transparency support
            if image.format() != QImage.Format.Format_ARGB32:
                image = image.convertToFormat(QImage.Format.Format_ARGB32)

            width = image.width()
            height = image.height()
            bytes_per_line = image.bytesPerLine()

            bg_r, bg_g, bg_b = background_color
            bg_bgr = np.array([bg_b, bg_g, bg_r], dtype=np.int16)

            image_buffer = np.frombuffer(image.bits(), dtype=np.uint8, count=image.sizeInBytes())
            scanlines = image_buffer.reshape((height, bytes_per_line))
            pixels = scanlines[:, : width * 4].reshape((height, width, 4))

            color_delta = np.abs(pixels[:, :, :3].astype(np.int16) - bg_bgr)
            background_mask = np.all(color_delta <= tolerance, axis=2)
            pixels[background_mask] = 0

            # Convert back to QPixmap
            return QPixmap.fromImage(image)

        except Exception as e:
            logger.warning("Failed to apply background transparency: %s", e)
            return pixmap  # Return original if processing fails
