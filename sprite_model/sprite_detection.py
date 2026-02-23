#!/usr/bin/env python3
"""
Sprite Detection Module
=======================

Automatic detection algorithms for sprite sheets including:
- Margin detection (transparent borders)
- Frame size detection (multiple algorithms)
- Spacing detection (gaps between frames)
- Comprehensive auto-detection workflow

Consolidated from sprite_model/detection/ subpackage.
"""

import logging
import math
from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtGui import QImage, QPixmap

from config import Config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Confidence score constants
# ---------------------------------------------------------------------------
_CONFIDENCE_HIGH = 0.9
_CONFIDENCE_CONTENT = 0.95
_CONFIDENCE_MEDIUM = 0.7
_CONFIDENCE_FALLBACK = 0.6
_CONFIDENCE_LOW = 0.3
_CONFIDENCE_FAILED = 0.1
_CONFIDENCE_ERROR = 0.2
_CONFIDENCE_VALIDATION_OK = 0.8
_CONFIDENCE_VALIDATION_WARN = 0.4


def _confidence_label(confidence: float) -> str:
    """Return a human-readable label for a confidence score in [0.0, 1.0]."""
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.6:
        return "medium"
    if confidence > 0.0:
        return "low"
    return "failed"


@dataclass
class DetectionStepResult:
    """Result of a single detection step."""

    step_name: str  # "margins", "frame_size", "spacing", "cross_validation"
    success: bool
    confidence: float  # 0.0-1.0
    description: str
    fallback_used: bool = False

    @property
    def confidence_level(self) -> str:
        """Get human-readable confidence level."""
        return _confidence_label(self.confidence)


class DetectionResult:
    """Container for detection results."""

    def __init__(self):
        self.frame_width: int = 0
        self.frame_height: int = 0
        self.offset_x: int = 0
        self.offset_y: int = 0
        self.spacing_x: int = 0
        self.spacing_y: int = 0
        self.success: bool = False
        self._confidence: float = 0.0
        self.messages: list[str] = []
        self.step_results: list[DetectionStepResult] = []

    @property
    def confidence(self) -> float:
        """Get confidence score."""
        return self._confidence

    @confidence.setter
    def confidence(self, value: float) -> None:
        """Set confidence score, clamping to valid range [0.0, 1.0]."""
        self._confidence = max(0.0, min(1.0, float(value)))

    @property
    def confidence_level(self) -> str:
        """Get human-readable confidence level."""
        return _confidence_label(self._confidence)


# ============================================================================
# Margin Detection
# ============================================================================


def detect_margins(
    sprite_sheet: QPixmap, frame_width: int | None = None, frame_height: int | None = None
) -> tuple[bool, int, int, str]:
    """
    Detect transparent margins around sprite content from all four edges.

    Args:
        sprite_sheet: Source sprite sheet pixmap
        frame_width: Optional frame width for validation (if known)
        frame_height: Optional frame height for validation (if known)

    Returns:
        Tuple of (success, offset_x, offset_y, status_message)
    """
    if not sprite_sheet or sprite_sheet.isNull():
        return False, 0, 0, "No sprite sheet provided"

    try:
        # Convert to QImage for pixel analysis
        image = sprite_sheet.toImage()
        width = image.width()
        height = image.height()

        # Get raw margin measurements
        raw_left, raw_right, raw_top, raw_bottom = _detect_raw_margins(image)

        # Apply validation and reasonableness checks
        validated_left, validated_top, validation_msg = _validate_margins(
            raw_left, raw_right, raw_top, raw_bottom, width, height, frame_width, frame_height
        )

        # Calculate final content area
        content_width = width - validated_left - (raw_right if validated_left == raw_left else 0)
        content_height = height - validated_top - (raw_bottom if validated_top == raw_top else 0)

        status_msg = (
            f"Margins: L={raw_left}, R={raw_right}, T={raw_top}, B={raw_bottom} | "
            f"Validated: X={validated_left}, Y={validated_top} | "
            f"Content: {content_width}×{content_height}"
        )

        if validation_msg:
            status_msg += f" | {validation_msg}"

        return True, validated_left, validated_top, status_msg

    except Exception as e:
        logger.debug("Error detecting margins: %s", e, exc_info=True)
        return False, 0, 0, f"Error detecting margins: {e!s}"


def _scan_margin(
    image: QImage,
    outer_range: range,
    inner_range_fn: Callable[[int], range],
    pixel_fn: Callable[[int, int], int],
    alpha_threshold: int,
) -> int:
    """
    Scan from an edge inward, counting transparent slices until content is found.

    Args:
        image: QImage to analyze
        outer_range: Iterable of the primary axis coordinates (the axis being measured)
        inner_range_fn: Callable(outer_coord) -> iterable of secondary axis coords to sample
        pixel_fn: Callable(outer_coord, inner_coord) -> pixel value from image
        alpha_threshold: Minimum alpha to treat as content

    Returns:
        Number of empty (fully-transparent) slices counted from the edge
    """
    margin = 0
    for outer in outer_range:
        has_content = any(
            ((pixel_fn(outer, inner) >> 24) & 0xFF) > alpha_threshold
            for inner in inner_range_fn(outer)
        )
        if has_content:
            break
        margin += 1
    return margin


def _detect_raw_margins(image: QImage) -> tuple[int, int, int, int]:
    """
    Detect raw margin measurements from image edges.

    Args:
        image: QImage to analyze

    Returns:
        Tuple of (left_margin, right_margin, top_margin, bottom_margin)
    """
    width = image.width()
    height = image.height()
    alpha_threshold = Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD

    left_margin = _scan_margin(
        image,
        range(width),
        lambda x: range(height),
        lambda x, y: image.pixel(x, y),
        alpha_threshold,
    )
    right_margin = _scan_margin(
        image,
        range(width - 1, -1, -1),
        lambda x: range(height),
        lambda x, y: image.pixel(x, y),
        alpha_threshold,
    )
    top_margin = _scan_margin(
        image,
        range(height),
        lambda y: range(width),
        lambda y, x: image.pixel(x, y),
        alpha_threshold,
    )
    bottom_margin = _scan_margin(
        image,
        range(height - 1, -1, -1),
        lambda y: range(width),
        lambda y, x: image.pixel(x, y),
        alpha_threshold,
    )

    return left_margin, right_margin, top_margin, bottom_margin


def _validate_margins(
    left: int,
    right: int,
    top: int,
    bottom: int,
    width: int,
    height: int,
    frame_width: int | None = None,
    frame_height: int | None = None,
) -> tuple[int, int, str]:
    """
    Validate detected margins and apply reasonableness checks.

    Args:
        left, right, top, bottom: Raw margin measurements
        width, height: Image dimensions
        frame_width, frame_height: Optional frame dimensions for validation

    Returns:
        Tuple of (validated_left, validated_top, validation_message)
    """
    validation_msg = ""
    validated_left = left
    validated_top = top

    # Check for excessive margins (more than 25% of dimension)
    max_reasonable_x = width // 4
    max_reasonable_y = height // 4

    if left > max_reasonable_x:
        validated_left = 0
        validation_msg += f"Left margin {left}px excessive (>{max_reasonable_x}px), reset to 0; "

    if top > max_reasonable_y:
        validated_top = 0
        validation_msg += f"Top margin {top}px excessive (>{max_reasonable_y}px), reset to 0; "

    # Check for margins that would create problematic frame sizes
    if frame_width and frame_height and frame_width > 0 and frame_height > 0:
        # Check if margins make sense with current frame size
        available_after_margins = (width - validated_left, height - validated_top)

        # If margins would prevent clean division by frame size, reduce them
        if available_after_margins[0] % frame_width != 0:
            # Try reducing left margin to get clean division
            for reduced_left in range(validated_left - 1, -1, -1):
                if (width - reduced_left) % frame_width == 0:
                    validated_left = reduced_left
                    validation_msg += (
                        f"Adjusted left margin to {reduced_left} for clean frame division; "
                    )
                    break

        if available_after_margins[1] % frame_height != 0:
            # Try reducing top margin to get clean division
            for reduced_top in range(validated_top - 1, -1, -1):
                if (height - reduced_top) % frame_height == 0:
                    validated_top = reduced_top
                    validation_msg += (
                        f"Adjusted top margin to {reduced_top} for clean frame division; "
                    )
                    break

    # For horizontal strips (wide aspect ratio), minimize margins
    aspect_ratio = width / height
    if aspect_ratio > 3.0:
        # This looks like a horizontal strip - minimize margins
        if validated_left > 5:
            validated_left = min(5, validated_left)
            validation_msg += "Reduced margins for horizontal strip; "
        if validated_top > 5:
            validated_top = min(5, validated_top)
            validation_msg += "Reduced top margin for horizontal strip; "

    # If margins are very small, set to zero to avoid noise
    if validated_left <= 2:
        validated_left = 0
    if validated_top <= 2:
        validated_top = 0

    return validated_left, validated_top, validation_msg.rstrip("; ")


# ============================================================================
# Frame Size Detection
# ============================================================================


def detect_frame_size(sprite_sheet: QPixmap) -> tuple[bool, int, int, str]:
    """
    Automatically detect optimal frame size for the sprite sheet.

    Args:
        sprite_sheet: Source sprite sheet pixmap

    Returns:
        Tuple of (success, width, height, status_message)
    """
    if not sprite_sheet or sprite_sheet.isNull():
        return False, 0, 0, "No sprite sheet provided"

    width = sprite_sheet.width()
    height = sprite_sheet.height()

    # Try common sprite sizes
    common_sizes = Config.FrameExtraction.AUTO_DETECT_SIZES

    for size in common_sizes:
        if width % size == 0 and height % size == 0:
            # Check if this produces a reasonable number of frames
            frames_x = width // size
            frames_y = height // size
            total_frames = frames_x * frames_y

            if (
                Config.FrameExtraction.MIN_REASONABLE_FRAMES
                <= total_frames
                <= Config.FrameExtraction.MAX_REASONABLE_FRAMES
            ):
                return True, size, size, f"Auto-detected frame size: {size}×{size}"

    # If no common size fits, try to find the GCD
    frame_size = math.gcd(width, height)
    if frame_size >= Config.FrameExtraction.MIN_SPRITE_SIZE:
        return True, frame_size, frame_size, f"Auto-detected frame size: {frame_size}×{frame_size}"

    return False, 0, 0, "Could not auto-detect suitable frame size"


def detect_rectangular_frames(sprite_sheet: QPixmap) -> tuple[bool, int, int, str]:
    """
    Enhanced frame size detection supporting rectangular frames and horizontal strips.
    Uses aspect ratios, scoring, and specialized detection for different sprite sheet types.

    Args:
        sprite_sheet: Source sprite sheet pixmap

    Returns:
        Tuple of (success, width, height, status_message)
    """
    if not sprite_sheet or sprite_sheet.isNull():
        return False, 0, 0, "No sprite sheet provided"

    sheet_width = sprite_sheet.width()
    sheet_height = sprite_sheet.height()

    # Common frame sizes for rectangular sprites
    base_sizes = Config.FrameExtraction.BASE_SIZES
    aspect_ratios = Config.FrameExtraction.COMMON_ASPECT_RATIOS

    candidates = []

    # Generate candidate sizes
    for base_size in base_sizes:
        for aspect_w, aspect_h in aspect_ratios:
            frame_width = base_size * aspect_w
            frame_height = base_size * aspect_h

            # Check if this frame size divides the sheet evenly
            if (
                sheet_width % frame_width == 0
                and sheet_height % frame_height == 0
                and frame_width <= sheet_width
                and frame_height <= sheet_height
            ):
                frames_x = sheet_width // frame_width
                frames_y = sheet_height // frame_height
                total_frames = frames_x * frames_y

                # Validate frame count is reasonable
                if (
                    Config.FrameExtraction.MIN_REASONABLE_FRAMES
                    <= total_frames
                    <= Config.FrameExtraction.MAX_REASONABLE_FRAMES
                ):
                    score = _score_frame_candidate(
                        frame_width, frame_height, frames_x, frames_y, total_frames
                    )
                    candidates.append(
                        (score, frame_width, frame_height, frames_x, frames_y, total_frames)
                    )

    if not candidates:
        return False, 0, 0, "No valid rectangular frame sizes found"

    # Sort by score (higher is better)
    candidates.sort(key=lambda x: x[0], reverse=True)

    # Return the best candidate
    score, frame_width, frame_height, frames_x, frames_y, total_frames = candidates[0]

    return (
        True,
        frame_width,
        frame_height,
        (
            f"Detected rectangular frames: {frame_width}×{frame_height} "
            f"({frames_x}×{frames_y} = {total_frames} frames, score: {score:.2f})"
        ),
    )


def detect_content_based(sprite_sheet: QPixmap) -> tuple[bool, int, int, str]:
    """
    Content-based sprite detection - finds actual sprite boundaries.
    Superior to mathematical grid detection for irregular sprites.

    Args:
        sprite_sheet: Source sprite sheet pixmap

    Returns:
        Tuple of (success, width, height, status_message)
    """
    if not sprite_sheet or sprite_sheet.isNull():
        return False, 0, 0, "No sprite sheet provided"

    try:
        # Convert to QImage for pixel analysis
        image = sprite_sheet.toImage()

        # Find content boundaries by analyzing transparency
        content_bounds = _find_nonempty_grid_cells(image)

        if not content_bounds:
            return False, 0, 0, "No content boundaries detected"

        # Calculate most common frame dimensions
        frame_dimensions = _calculate_common_dimensions(content_bounds)

        if not frame_dimensions:
            return False, 0, 0, "Could not determine consistent frame dimensions"

        # Return the most common dimensions
        frame_width, frame_height, count = frame_dimensions[0]

        return (
            True,
            frame_width,
            frame_height,
            (
                f"Content-based detection: {frame_width}×{frame_height} "
                f"(found {count} sprites with these dimensions)"
            ),
        )

    except Exception as e:
        logger.debug("Content-based detection failed: %s", e, exc_info=True)
        return False, 0, 0, f"Content-based detection failed: {e!s}"


def _score_frame_candidate(
    frame_width: int, frame_height: int, frames_x: int, frames_y: int, total_frames: int
) -> float:
    """
    Score a frame size candidate based on various criteria.

    Args:
        frame_width: Width of individual frame
        frame_height: Height of individual frame
        frames_x: Number of frames horizontally
        frames_y: Number of frames vertically
        total_frames: Total number of frames

    Returns:
        Score (higher is better)
    """
    score = 0.0

    # Prefer common frame sizes
    common_sizes = [16, 24, 32, 48, 64, 96, 128]
    if frame_width in common_sizes:
        score += 2.0
    if frame_height in common_sizes:
        score += 2.0

    # Prefer reasonable frame counts
    if 4 <= total_frames <= 16:
        score += 3.0
    elif 17 <= total_frames <= 32:
        score += 2.0
    elif 33 <= total_frames <= 64:
        score += 1.0

    # Prefer common aspect ratios
    aspect_ratio = frame_width / frame_height
    common_ratios = [1.0, 0.5, 2.0, 0.75, 1.33, 0.67, 1.5]  # 1:1, 1:2, 2:1, 3:4, 4:3, 2:3, 3:2

    for ratio in common_ratios:
        if abs(aspect_ratio - ratio) < 0.1:
            score += 1.5
            break

    # Prefer balanced grids (not too many in one dimension)
    if frames_x == frames_y:
        score += 1.0  # Square grids
    elif min(frames_x, frames_y) >= 2:
        score += 0.5  # Balanced rectangular grids

    # Slight preference for larger frames (more detail)
    frame_area = frame_width * frame_height
    if frame_area >= 1024:  # 32x32 or larger
        score += 0.5

    return score


def _find_nonempty_grid_cells(image: QImage) -> list[tuple[int, int, int, int]]:
    """
    Find non-empty grid cells by testing candidate grid sizes against image content.

    Args:
        image: QImage to analyze

    Returns:
        List of (x, y, width, height) tuples for grid cells that contain non-transparent pixels
    """
    # Grid-based approach: test candidate grid sizes, enumerate cells, keep non-empty ones.
    # Uses pixel sampling (via _has_content_in_region) rather than connected component analysis.

    width = image.width()
    height = image.height()
    alpha_threshold = Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD

    content_bounds = []

    # Subset of Config.FrameExtraction.AUTO_DETECT_SIZES used for grid-based detection
    for grid_size in [16, 24, 32, 48, 64]:
        if width % grid_size == 0 and height % grid_size == 0:
            frames_x = width // grid_size
            frames_y = height // grid_size

            for row in range(frames_y):
                for col in range(frames_x):
                    x = col * grid_size
                    y = row * grid_size

                    # Check if this grid cell has content
                    if _has_content_in_region(image, x, y, grid_size, grid_size, alpha_threshold):
                        content_bounds.append((x, y, grid_size, grid_size))

    return content_bounds


def _has_content_in_region(
    image: QImage, x: int, y: int, width: int, height: int, alpha_threshold: int
) -> bool:
    """
    Check if a region contains non-transparent content.

    Args:
        image: QImage to check
        x, y: Top-left corner of region
        width, height: Size of region to check
        alpha_threshold: Minimum alpha value to consider as content

    Returns:
        True if region has content, False otherwise
    """
    # Sample pixels in the region to check for content
    sample_step = max(1, min(width, height) // 4)

    for check_y in range(y, min(y + height, image.height()), sample_step):
        for check_x in range(x, min(x + width, image.width()), sample_step):
            pixel = image.pixel(check_x, check_y)
            alpha = (pixel >> 24) & 0xFF
            if alpha > alpha_threshold:
                return True

    return False


def _calculate_common_dimensions(
    content_bounds: list[tuple[int, int, int, int]],
) -> list[tuple[int, int, int]]:
    """
    Calculate the most common frame dimensions from content boundaries.

    Args:
        content_bounds: List of (x, y, width, height) tuples

    Returns:
        List of (width, height, count) tuples sorted by frequency
    """
    if not content_bounds:
        return []

    # Count dimension frequencies
    dimension_counts = {}
    for _x, _y, width, height in content_bounds:
        key = (width, height)
        dimension_counts[key] = dimension_counts.get(key, 0) + 1

    # Sort by frequency (most common first)
    sorted_dimensions = sorted(dimension_counts.items(), key=lambda x: x[1], reverse=True)

    return [(width, height, count) for (width, height), count in sorted_dimensions]


# ============================================================================
# Spacing Detection
# ============================================================================


def detect_spacing(
    sprite_sheet: QPixmap, frame_width: int, frame_height: int, offset_x: int = 0, offset_y: int = 0
) -> tuple[bool, int, int, str, float]:
    """
    Enhanced spacing detection that validates across multiple frame positions.

    Args:
        sprite_sheet: Source sprite sheet pixmap
        frame_width: Width of individual frames
        frame_height: Height of individual frames
        offset_x: X offset (margin) from left edge
        offset_y: Y offset (margin) from top edge

    Returns:
        Tuple of (success, spacing_x, spacing_y, status_message, avg_confidence)
        where avg_confidence is a float in [0.0, 1.0] indicating detection reliability
    """
    if not sprite_sheet or sprite_sheet.isNull():
        return False, 0, 0, "No sprite sheet provided", 0.0

    if frame_width <= 0 or frame_height <= 0:
        return False, 0, 0, "Frame size must be greater than 0", 0.0

    try:
        image = sprite_sheet.toImage()
        available_width = image.width() - offset_x
        available_height = image.height() - offset_y

        # Horizontal spacing detection
        best_spacing_x, best_score_x = _detect_spacing_1d(
            image,
            frame_size=frame_width,
            frame_cross=frame_height,
            offset_main=offset_x,
            offset_cross=offset_y,
            available=available_width,
            pixel_fn=lambda main, cross: image.pixel(main, cross),
            image_main_size=image.width(),
            image_cross_size=image.height(),
        )

        # Vertical spacing detection
        best_spacing_y, best_score_y = _detect_spacing_1d(
            image,
            frame_size=frame_height,
            frame_cross=frame_width,
            offset_main=offset_y,
            offset_cross=offset_x,
            available=available_height,
            pixel_fn=lambda main, cross: image.pixel(cross, main),
            image_main_size=image.height(),
            image_cross_size=image.width(),
        )

        # Calculate confidence based on consistency scores
        avg_confidence = (best_score_x + best_score_y) / 2
        confidence_text = (
            "high" if avg_confidence >= 0.8 else "medium" if avg_confidence >= 0.5 else "low"
        )

        return (
            True,
            best_spacing_x,
            best_spacing_y,
            (
                f"Auto-detected spacing: X={best_spacing_x}, Y={best_spacing_y} "
                f"(confidence: {confidence_text}, consistency: {avg_confidence:.2f})"
            ),
            avg_confidence,
        )

    except Exception as e:
        logger.debug("Error in enhanced spacing detection: %s", e, exc_info=True)
        return False, 0, 0, f"Error in enhanced spacing detection: {e!s}", 0.0


def _detect_spacing_1d(
    image: QImage,
    frame_size: int,
    frame_cross: int,
    offset_main: int,
    offset_cross: int,
    available: int,
    pixel_fn: Callable[[int, int], int],
    image_main_size: int,
    image_cross_size: int,
) -> tuple[int, float]:
    """
    Detect spacing between frames along one axis.

    The "main" axis is the one being measured (horizontal for X, vertical for Y).
    The "cross" axis is the perpendicular one.  Callers swap the arguments to
    reuse this function for both directions.

    Args:
        image: QImage to analyze
        frame_size: Frame extent along the main axis
        frame_cross: Frame extent along the cross axis
        offset_main: Margin offset along the main axis
        offset_cross: Margin offset along the cross axis
        available: Available pixels along the main axis after the margin
        pixel_fn: Callable(main_coord, cross_coord) -> QImage pixel value
        image_main_size: Image size along the main axis
        image_cross_size: Image size along the cross axis

    Returns:
        Tuple of (best_spacing, best_score)
    """
    best_spacing = 0
    best_score = 0.0
    alpha_threshold = Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD

    for test_spacing in range(11):
        if frame_size <= 0:
            continue

        frames_per_strip = (
            (available + test_spacing) // (frame_size + test_spacing)
            if test_spacing > 0
            else available // frame_size
        )
        positions_to_check = min(3, frames_per_strip - 1)

        if positions_to_check <= 0:
            continue

        score = 0
        positions_checked = 0

        for position in range(positions_to_check):
            gap_start = offset_main + (position + 1) * frame_size + position * test_spacing
            gap_end = gap_start + test_spacing
            next_frame = gap_end

            if next_frame + frame_size > image_main_size:
                break

            positions_checked += 1

            # Check that the gap strip is empty
            gap_valid = True
            if test_spacing > 0:
                for cross in range(
                    offset_cross, min(offset_cross + frame_cross, image_cross_size), 5
                ):
                    for main in range(gap_start, gap_end):
                        if main < image_main_size:
                            alpha = (pixel_fn(main, cross) >> 24) & 0xFF
                            if alpha > alpha_threshold:
                                gap_valid = False
                                break
                    if not gap_valid:
                        break

            # Check that the next frame position contains content
            frame_exists = False
            if gap_valid:
                for cross in range(offset_cross, min(offset_cross + 20, image_cross_size), 5):
                    alpha = (pixel_fn(next_frame, cross) >> 24) & 0xFF
                    if alpha > alpha_threshold:
                        frame_exists = True
                        break

            if gap_valid and frame_exists:
                score += 1

        consistency = score / positions_checked if positions_checked > 0 else 0.0
        if consistency > best_score:
            best_score = consistency
            best_spacing = test_spacing

    return best_spacing, best_score


# ============================================================================
# Comprehensive Auto-Detection Coordinator
# ============================================================================


def _record_step(
    result: "DetectionResult",
    confidence_scores: list[float],
    step_name: str,
    success: bool,
    confidence: float,
    description: str,
    fallback_used: bool = False,
) -> None:
    """Append a DetectionStepResult and its confidence score to the accumulators."""
    confidence_scores.append(confidence)
    result.step_results.append(
        DetectionStepResult(
            step_name=step_name,
            success=success,
            confidence=confidence,
            description=description,
            fallback_used=fallback_used,
        )
    )


def comprehensive_auto_detect(
    sprite_sheet: QPixmap, sprite_sheet_path: str | None = None
) -> tuple[bool, str, DetectionResult]:
    """
    Comprehensive one-click auto-detection workflow.
    Detects margins, frame size, and spacing in optimal order with cross-validation.

    Args:
        sprite_sheet: Source sprite sheet pixmap
        sprite_sheet_path: Optional path for CCL detection integration

    Returns:
        Tuple of (success, detailed_status_message, detection_result)
    """
    if not sprite_sheet or sprite_sheet.isNull():
        return False, "No sprite sheet provided", DetectionResult()

    result = DetectionResult()
    messages: list[str] = []
    confidence_scores: list[float] = []
    overall_success = True

    try:
        # Step 1: Detect margins first (affects all other calculations)
        _run_margin_step(sprite_sheet, result, messages, confidence_scores)

        # Step 2: Detect optimal frame size with multiple fallback strategies
        frame_detected = _run_frame_size_step(sprite_sheet, result, messages, confidence_scores)
        if not frame_detected:
            overall_success = False

        # Step 3: Detect spacing (only if frame size detection succeeded)
        _run_spacing_step(sprite_sheet, result, messages, confidence_scores)

        # Step 4: Cross-validation and final verification
        _run_validation_step(sprite_sheet, result, messages, confidence_scores)

        # Step 5: Calculate overall confidence and summary
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        )
        overall_success, result.success = _summarize_detection(
            result, messages, overall_success, overall_confidence
        )

        result.confidence = overall_confidence
        result.messages = messages

        return overall_success, "\n".join(messages), result

    except Exception as e:
        logger.debug("Comprehensive auto-detection failed: %s", e, exc_info=True)
        error_msg = f"❌ Comprehensive auto-detection failed: {e!s}"
        messages.append(error_msg)
        result.messages = messages
        return False, "\n".join(messages), result


def _run_margin_step(
    sprite_sheet: QPixmap,
    result: DetectionResult,
    messages: list[str],
    confidence_scores: list[float],
) -> None:
    """Step 1: Detect transparent margins around sprite content."""
    messages.append("🔍 Step 1: Detecting margins...")

    try:
        margin_success, offset_x, offset_y, margin_msg = detect_margins(sprite_sheet)
        result.offset_x = offset_x
        result.offset_y = offset_y
    except Exception as e:
        logger.debug("Error in margin detection step: %s", e, exc_info=True)
        margin_success, margin_msg = False, f"Error: {e!s}"
        result.offset_x = 0
        result.offset_y = 0

    if margin_success:
        messages.append(f"   ✓ {margin_msg}")
        margin_conf = _CONFIDENCE_HIGH
    else:
        messages.append(f"   ⚠ Margin detection failed: {margin_msg}")
        messages.append("   → Using default margins (0, 0)")
        margin_conf = _CONFIDENCE_LOW

    _record_step(result, confidence_scores, "margins", margin_success, margin_conf, margin_msg)


def _run_frame_size_step(
    sprite_sheet: QPixmap,
    result: DetectionResult,
    messages: list[str],
    confidence_scores: list[float],
) -> bool:
    """Step 2: Detect optimal frame size with multiple fallback strategies.

    Returns True if a frame size was detected, False otherwise.
    """
    messages.append("\n🔍 Step 2: Detecting frame size...")

    # Each entry: (display_name, callable, success_confidence, is_fallback)
    frame_strategies = [
        (
            "Content-based",
            lambda: detect_content_based(sprite_sheet),
            _CONFIDENCE_CONTENT,
            False,
        ),
        (
            "Rectangular",
            lambda: detect_rectangular_frames(sprite_sheet),
            _CONFIDENCE_MEDIUM,
            True,
        ),
        ("Basic square", lambda: detect_frame_size(sprite_sheet), _CONFIDENCE_FALLBACK, True),
    ]

    for strategy_name, strategy_fn, strategy_conf, is_fallback in frame_strategies:
        try:
            success, fw, fh, msg = strategy_fn()
            if success:
                result.frame_width = fw
                result.frame_height = fh
                messages.append(f"   ✓ {msg}")
                _record_step(
                    result,
                    confidence_scores,
                    "frame_size",
                    True,
                    strategy_conf,
                    msg,
                    fallback_used=is_fallback,
                )
                return True
            messages.append(f"   ⚠ {strategy_name} detection failed: {msg}")
            if is_fallback:
                messages.append("   → Trying next strategy...")
        except Exception as e:
            logger.debug(
                "Frame size detection strategy %s error: %s", strategy_name, e, exc_info=True
            )
            messages.append(f"   ✗ {strategy_name} detection error: {e!s}")

    messages.append("   ✗ All frame detection strategies exhausted")
    _record_step(
        result,
        confidence_scores,
        "frame_size",
        False,
        _CONFIDENCE_FAILED,
        "All frame detection strategies exhausted",
        fallback_used=True,
    )
    return False


def _run_spacing_step(
    sprite_sheet: QPixmap,
    result: DetectionResult,
    messages: list[str],
    confidence_scores: list[float],
) -> None:
    """Step 3: Detect spacing between frames (skipped if no valid frame size)."""
    if result.frame_width <= 0 or result.frame_height <= 0:
        messages.append("\n⚠ Step 3: Skipped spacing detection (no valid frame size)")
        _record_step(
            result,
            confidence_scores,
            "spacing",
            False,
            _CONFIDENCE_FAILED,
            "Skipped - no valid frame size",
        )
        return

    messages.append("\n🔍 Step 3: Detecting frame spacing...")

    try:
        spacing_success, spacing_x, spacing_y, spacing_msg, spacing_confidence = detect_spacing(
            sprite_sheet,
            result.frame_width,
            result.frame_height,
            result.offset_x,
            result.offset_y,
        )
    except Exception as e:
        logger.debug("Error in spacing detection step: %s", e, exc_info=True)
        messages.append(f"   ✗ Spacing detection error: {e!s}")
        messages.append("   → Using default spacing (0, 0)")
        result.spacing_x = 0
        result.spacing_y = 0
        _record_step(result, confidence_scores, "spacing", False, _CONFIDENCE_ERROR, str(e))
        return

    if spacing_success:
        result.spacing_x = spacing_x
        result.spacing_y = spacing_y
        messages.append(f"   ✓ {spacing_msg}")
        _record_step(
            result,
            confidence_scores,
            "spacing",
            True,
            spacing_confidence,
            spacing_msg,
        )
    else:
        messages.append(f"   ⚠ Spacing detection failed: {spacing_msg}")
        messages.append("   → Using default spacing (0, 0)")
        result.spacing_x = 0
        result.spacing_y = 0
        _record_step(
            result,
            confidence_scores,
            "spacing",
            False,
            _CONFIDENCE_LOW,
            spacing_msg,
        )


def _run_validation_step(
    sprite_sheet: QPixmap,
    result: DetectionResult,
    messages: list[str],
    confidence_scores: list[float],
) -> None:
    """Step 4: Cross-validate that all detected parameters work together."""
    messages.append("\n🔍 Step 4: Cross-validation...")
    try:
        validation_success, validation_msg = _validate_detection_consistency(sprite_sheet, result)

        if validation_success:
            messages.append(f"   ✓ {validation_msg}")
            val_conf: float = _CONFIDENCE_VALIDATION_OK
        else:
            messages.append(f"   ⚠ {validation_msg}")
            val_conf = _CONFIDENCE_VALIDATION_WARN
        _record_step(
            result,
            confidence_scores,
            "cross_validation",
            validation_success,
            val_conf,
            validation_msg,
        )
    except Exception as e:
        logger.debug("Error in validation step: %s", e, exc_info=True)
        messages.append(f"   ✗ Validation error: {e!s}")
        _record_step(
            result,
            confidence_scores,
            "cross_validation",
            False,
            _CONFIDENCE_LOW,
            str(e),
        )


def _summarize_detection(
    result: DetectionResult,
    messages: list[str],
    overall_success: bool,
    overall_confidence: float,
) -> tuple[bool, bool]:
    """Append summary messages and determine final success.

    Returns (overall_success, result_success) tuple.
    """
    confidence_text = _confidence_label(overall_confidence)

    messages.append("\n📊 Overall Result:")
    messages.append(f"   • Frame Size: {result.frame_width}×{result.frame_height}")
    messages.append(f"   • Margins: X={result.offset_x}, Y={result.offset_y}")
    messages.append(f"   • Spacing: X={result.spacing_x}, Y={result.spacing_y}")
    messages.append(f"   • Confidence: {confidence_text} ({overall_confidence:.1%})")

    if overall_success and overall_confidence >= 0.6:
        messages.append("   🎉 Auto-detection completed successfully!")
        return True, True
    elif overall_confidence >= 0.4:
        messages.append("   ⚠ Auto-detection completed with warnings")
        return overall_success, True
    else:
        messages.append("   ❌ Auto-detection completed with low confidence")
        return False, False


def _validate_detection_consistency(
    sprite_sheet: QPixmap, result: DetectionResult
) -> tuple[bool, str]:
    """
    Validate that all detected parameters work together consistently.

    Args:
        sprite_sheet: Source sprite sheet pixmap
        result: Detection result to validate

    Returns:
        Tuple of (success, status_message)
    """
    try:
        # Check basic parameter validity
        if result.frame_width <= 0 or result.frame_height <= 0:
            return False, "Invalid frame dimensions detected"

        # Check that frame fits within sheet dimensions after applying offsets
        sheet_width = sprite_sheet.width()
        sheet_height = sprite_sheet.height()

        if result.offset_x + result.frame_width > sheet_width:
            return (
                False,
                f"Frame width + margin ({result.offset_x + result.frame_width}) exceeds sheet width ({sheet_width})",
            )

        if result.offset_y + result.frame_height > sheet_height:
            return (
                False,
                f"Frame height + margin ({result.offset_y + result.frame_height}) exceeds sheet height ({sheet_height})",
            )

        # Calculate expected frame count
        available_width = sheet_width - result.offset_x
        available_height = sheet_height - result.offset_y

        if result.spacing_x > 0:
            frames_x = (available_width + result.spacing_x) // (
                result.frame_width + result.spacing_x
            )
        else:
            frames_x = available_width // result.frame_width

        if result.spacing_y > 0:
            frames_y = (available_height + result.spacing_y) // (
                result.frame_height + result.spacing_y
            )
        else:
            frames_y = available_height // result.frame_height

        expected_frames = frames_x * frames_y

        # Check if frame count is reasonable
        if expected_frames < Config.FrameExtraction.MIN_REASONABLE_FRAMES:
            return False, f"Too few frames detected ({expected_frames})"

        if expected_frames > Config.FrameExtraction.MAX_REASONABLE_FRAMES:
            return False, f"Too many frames detected ({expected_frames})"

        return True, f"Validation passed: {frames_x}×{frames_y} = {expected_frames} frames"

    except Exception as e:
        logger.debug("Detection consistency validation error: %s", e, exc_info=True)
        return False, f"Validation error: {e!s}"
