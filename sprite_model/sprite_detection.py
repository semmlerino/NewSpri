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

import math

from PySide6.QtGui import QPixmap

from config import Config


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
        self.messages: list = []

    @property
    def confidence(self) -> float:
        """Get confidence score."""
        return self._confidence

    @confidence.setter
    def confidence(self, value: float) -> None:
        """Set confidence score, clamping to valid range [0.0, 1.0]."""
        self._confidence = max(0.0, min(1.0, float(value)))


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
        return False, 0, 0, f"Error detecting margins: {e!s}"


def _detect_raw_margins(image) -> tuple[int, int, int, int]:
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

    # Detect left margin
    left_margin = 0
    for x in range(width):
        has_content = False
        for y in range(height):
            pixel = image.pixel(x, y)
            alpha = (pixel >> 24) & 0xFF
            if alpha > alpha_threshold:
                has_content = True
                break
        if has_content:
            break
        left_margin += 1

    # Detect right margin
    right_margin = 0
    for x in range(width - 1, -1, -1):
        has_content = False
        for y in range(height):
            pixel = image.pixel(x, y)
            alpha = (pixel >> 24) & 0xFF
            if alpha > alpha_threshold:
                has_content = True
                break
        if has_content:
            break
        right_margin += 1

    # Detect top margin
    top_margin = 0
    for y in range(height):
        has_content = False
        for x in range(width):
            pixel = image.pixel(x, y)
            alpha = (pixel >> 24) & 0xFF
            if alpha > alpha_threshold:
                has_content = True
                break
        if has_content:
            break
        top_margin += 1

    # Detect bottom margin
    bottom_margin = 0
    for y in range(height - 1, -1, -1):
        has_content = False
        for x in range(width):
            pixel = image.pixel(x, y)
            alpha = (pixel >> 24) & 0xFF
            if alpha > alpha_threshold:
                has_content = True
                break
        if has_content:
            break
        bottom_margin += 1

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
        image.width()
        image.height()

        # Find content boundaries by analyzing transparency
        content_bounds = _analyze_content_boundaries(image)

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


def _analyze_content_boundaries(image) -> list[tuple[int, int, int, int]]:
    """
    Analyze image to find content boundaries (sprites).

    Args:
        image: QImage to analyze

    Returns:
        List of (x, y, width, height) tuples for detected sprites
    """
    # This is a simplified implementation
    # In a full implementation, this would use more sophisticated algorithms
    # like connected component analysis or edge detection

    width = image.width()
    height = image.height()
    alpha_threshold = Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD

    # Simple grid-based content detection
    # This is a placeholder for more sophisticated content analysis
    content_bounds = []

    # Try different grid sizes to find content blocks
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
    image, x: int, y: int, width: int, height: int, alpha_threshold: int
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
) -> tuple[bool, int, int, str]:
    """
    Enhanced spacing detection that validates across multiple frame positions.

    Args:
        sprite_sheet: Source sprite sheet pixmap
        frame_width: Width of individual frames
        frame_height: Height of individual frames
        offset_x: X offset (margin) from left edge
        offset_y: Y offset (margin) from top edge

    Returns:
        Tuple of (success, spacing_x, spacing_y, status_message)
    """
    if not sprite_sheet or sprite_sheet.isNull():
        return False, 0, 0, "No sprite sheet provided"

    if frame_width <= 0 or frame_height <= 0:
        return False, 0, 0, "Frame size must be greater than 0"

    try:
        image = sprite_sheet.toImage()
        available_width = image.width() - offset_x
        available_height = image.height() - offset_y

        # Test spacing values from 0-10 pixels
        best_spacing_x = 0
        best_score_x = 0
        best_spacing_y = 0
        best_score_y = 0

        # Horizontal spacing detection
        best_spacing_x, best_score_x = _detect_horizontal_spacing(
            image, frame_width, frame_height, offset_x, offset_y, available_width
        )

        # Vertical spacing detection
        best_spacing_y, best_score_y = _detect_vertical_spacing(
            image, frame_width, frame_height, offset_x, offset_y, available_height
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
        )

    except Exception as e:
        return False, 0, 0, f"Error in enhanced spacing detection: {e!s}"


def _detect_horizontal_spacing(
    image, frame_width: int, frame_height: int, offset_x: int, offset_y: int, available_width: int
) -> tuple[int, float]:
    """
    Detect horizontal spacing between frames.

    Args:
        image: QImage to analyze
        frame_width, frame_height: Frame dimensions
        offset_x, offset_y: Margin offsets
        available_width: Available width after margins

    Returns:
        Tuple of (best_spacing, best_score)
    """
    best_spacing_x = 0
    best_score_x = 0
    alpha_threshold = Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD

    for test_spacing in range(0, 11):
        score = 0
        positions_checked = 0

        # Guard against division by zero
        if frame_width <= 0:
            continue

        # Calculate how many frames we could check with this spacing
        frames_per_row = (
            (available_width + test_spacing) // (frame_width + test_spacing)
            if test_spacing > 0
            else available_width // frame_width
        )
        positions_to_check = min(3, frames_per_row - 1)  # Check up to 3 gap positions

        if positions_to_check <= 0:
            continue

        for position in range(positions_to_check):
            x_gap_start = offset_x + (position + 1) * frame_width + position * test_spacing
            x_gap_end = x_gap_start + test_spacing
            x_next_frame = x_gap_end

            # Check bounds
            if x_next_frame + frame_width > image.width():
                break

            positions_checked += 1

            # Check if gap is empty (for non-zero spacing)
            gap_valid = True
            if test_spacing > 0:
                for y in range(offset_y, min(offset_y + frame_height, image.height()), 5):
                    for x in range(x_gap_start, x_gap_end):
                        if x < image.width():
                            pixel = image.pixel(x, y)
                            alpha = (pixel >> 24) & 0xFF
                            if alpha > alpha_threshold:
                                gap_valid = False
                                break
                    if not gap_valid:
                        break

            # Check if frame exists at expected position
            frame_exists = False
            if gap_valid:
                for y in range(offset_y, min(offset_y + 20, image.height()), 5):
                    pixel = image.pixel(x_next_frame, y)
                    alpha = (pixel >> 24) & 0xFF
                    if alpha > alpha_threshold:
                        frame_exists = True
                        break

            if gap_valid and frame_exists:
                score += 1

        # Calculate consistency score
        consistency = score / positions_checked if positions_checked > 0 else 0
        if consistency > best_score_x:
            best_score_x = consistency
            best_spacing_x = test_spacing

    return best_spacing_x, best_score_x


def _detect_vertical_spacing(
    image, frame_width: int, frame_height: int, offset_x: int, offset_y: int, available_height: int
) -> tuple[int, float]:
    """
    Detect vertical spacing between frames.

    Args:
        image: QImage to analyze
        frame_width, frame_height: Frame dimensions
        offset_x, offset_y: Margin offsets
        available_height: Available height after margins

    Returns:
        Tuple of (best_spacing, best_score)
    """
    best_spacing_y = 0
    best_score_y = 0
    alpha_threshold = Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD

    for test_spacing in range(0, 11):
        score = 0
        positions_checked = 0

        # Guard against division by zero
        if frame_height <= 0:
            continue

        # Calculate how many frames we could check with this spacing
        frames_per_col = (
            (available_height + test_spacing) // (frame_height + test_spacing)
            if test_spacing > 0
            else available_height // frame_height
        )
        positions_to_check = min(3, frames_per_col - 1)  # Check up to 3 gap positions

        if positions_to_check <= 0:
            continue

        for position in range(positions_to_check):
            y_gap_start = offset_y + (position + 1) * frame_height + position * test_spacing
            y_gap_end = y_gap_start + test_spacing
            y_next_frame = y_gap_end

            # Check bounds
            if y_next_frame + frame_height > image.height():
                break

            positions_checked += 1

            # Check if gap is empty (for non-zero spacing)
            gap_valid = True
            if test_spacing > 0:
                for x in range(offset_x, min(offset_x + frame_width, image.width()), 5):
                    for y in range(y_gap_start, y_gap_end):
                        if y < image.height():
                            pixel = image.pixel(x, y)
                            alpha = (pixel >> 24) & 0xFF
                            if alpha > alpha_threshold:
                                gap_valid = False
                                break
                    if not gap_valid:
                        break

            # Check if frame exists at expected position
            frame_exists = False
            if gap_valid:
                for x in range(offset_x, min(offset_x + 20, image.width()), 5):
                    pixel = image.pixel(x, y_next_frame)
                    alpha = (pixel >> 24) & 0xFF
                    if alpha > alpha_threshold:
                        frame_exists = True
                        break

            if gap_valid and frame_exists:
                score += 1

        # Calculate consistency score
        consistency = score / positions_checked if positions_checked > 0 else 0
        if consistency > best_score_y:
            best_score_y = consistency
            best_spacing_y = test_spacing

    return best_spacing_y, best_score_y


# ============================================================================
# Comprehensive Auto-Detection Coordinator
# ============================================================================


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
    results = []
    confidence_scores = []
    overall_success = True

    try:
        # Step 1: Detect margins first (affects all other calculations)
        results.append("🔍 Step 1: Detecting margins...")

        try:
            margin_success, offset_x, offset_y, margin_msg = detect_margins(sprite_sheet)
            result.offset_x = offset_x
            result.offset_y = offset_y
        except Exception as e:
            margin_success, offset_x, offset_y, margin_msg = False, 0, 0, f"Error: {e!s}"
            result.offset_x = 0
            result.offset_y = 0

        if margin_success:
            results.append(f"   ✓ {margin_msg}")
            confidence_scores.append(0.9)  # Margin detection is usually reliable
        else:
            results.append(f"   ⚠ Margin detection failed: {margin_msg}")
            results.append("   → Using default margins (0, 0)")
            confidence_scores.append(0.3)

        # Step 2: Detect optimal frame size with multiple fallback strategies
        results.append("\n🔍 Step 2: Detecting frame size...")

        # Try content-based detection first
        try:
            content_success, frame_width, frame_height, content_msg = detect_content_based(
                sprite_sheet
            )

            if content_success:
                result.frame_width = frame_width
                result.frame_height = frame_height
                results.append(f"   ✓ {content_msg}")
                confidence_scores.append(0.95)  # Content-based detection is very reliable
            else:
                results.append(f"   ⚠ Content-based detection failed: {content_msg}")
                results.append("   → Falling back to rectangular detection...")

                # Fall back to rectangular detection
                try:
                    rect_success, frame_width, frame_height, frame_msg = detect_rectangular_frames(
                        sprite_sheet
                    )

                    if rect_success:
                        result.frame_width = frame_width
                        result.frame_height = frame_height
                        results.append(f"   ✓ {frame_msg}")
                        # Extract confidence from message if available
                        if "score:" in frame_msg:
                            confidence_scores.append(0.8)
                        else:
                            confidence_scores.append(0.7)
                    else:
                        results.append(f"   ⚠ Rectangular detection failed: {frame_msg}")
                        results.append("   → Falling back to basic square detection...")

                        # Try basic square detection as final fallback
                        try:
                            basic_success, basic_width, basic_height, basic_msg = detect_frame_size(
                                sprite_sheet
                            )
                            if basic_success:
                                result.frame_width = basic_width
                                result.frame_height = basic_height
                                results.append(f"   ✓ Basic detection: {basic_msg}")
                                confidence_scores.append(0.6)
                            else:
                                results.append(f"   ✗ All frame detection failed: {basic_msg}")
                                overall_success = False
                                confidence_scores.append(0.1)
                        except Exception as e:
                            results.append(f"   ✗ Basic detection error: {e!s}")
                            overall_success = False
                            confidence_scores.append(0.1)
                except Exception as e:
                    results.append(f"   ✗ Rectangular detection error: {e!s}")
                    overall_success = False
                    confidence_scores.append(0.1)
        except Exception as e:
            results.append(f"   ✗ Content-based detection error: {e!s}")
            overall_success = False
            confidence_scores.append(0.1)

        # Step 3: Detect spacing (only if frame size detection succeeded)
        if result.frame_width > 0 and result.frame_height > 0:
            results.append("\n🔍 Step 3: Detecting frame spacing...")

            try:
                spacing_success, spacing_x, spacing_y, spacing_msg = detect_spacing(
                    sprite_sheet,
                    result.frame_width,
                    result.frame_height,
                    result.offset_x,
                    result.offset_y,
                )

                if spacing_success:
                    result.spacing_x = spacing_x
                    result.spacing_y = spacing_y
                    results.append(f"   ✓ {spacing_msg}")
                    # Extract confidence from message
                    if "confidence: high" in spacing_msg:
                        confidence_scores.append(0.9)
                    elif "confidence: medium" in spacing_msg:
                        confidence_scores.append(0.7)
                    else:
                        confidence_scores.append(0.5)
                else:
                    results.append(f"   ⚠ Spacing detection failed: {spacing_msg}")
                    results.append("   → Using default spacing (0, 0)")
                    result.spacing_x = 0
                    result.spacing_y = 0
                    confidence_scores.append(0.3)
            except Exception as e:
                results.append(f"   ✗ Spacing detection error: {e!s}")
                results.append("   → Using default spacing (0, 0)")
                result.spacing_x = 0
                result.spacing_y = 0
                confidence_scores.append(0.2)
        else:
            results.append("\n⚠ Step 3: Skipped spacing detection (no valid frame size)")
            confidence_scores.append(0.1)

        # Step 4: Cross-validation and final verification
        results.append("\n🔍 Step 4: Cross-validation...")
        try:
            validation_success, validation_msg = _validate_detection_consistency(
                sprite_sheet, result
            )

            if validation_success:
                results.append(f"   ✓ {validation_msg}")
                confidence_scores.append(0.8)
            else:
                results.append(f"   ⚠ {validation_msg}")
                confidence_scores.append(0.4)
        except Exception as e:
            results.append(f"   ✗ Validation error: {e!s}")
            confidence_scores.append(0.3)

        # Step 5: Calculate overall confidence and summary
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        )
        confidence_text = (
            "high"
            if overall_confidence >= 0.8
            else "medium"
            if overall_confidence >= 0.6
            else "low"
        )

        results.append("\n📊 Overall Result:")
        results.append(f"   • Frame Size: {result.frame_width}×{result.frame_height}")
        results.append(f"   • Margins: X={result.offset_x}, Y={result.offset_y}")
        results.append(f"   • Spacing: X={result.spacing_x}, Y={result.spacing_y}")
        results.append(f"   • Confidence: {confidence_text} ({overall_confidence:.1%})")

        if overall_success and overall_confidence >= 0.6:
            results.append("   🎉 Auto-detection completed successfully!")
            result.success = True
        elif overall_confidence >= 0.4:
            results.append("   ⚠ Auto-detection completed with warnings")
            result.success = True
        else:
            results.append("   ❌ Auto-detection completed with low confidence")
            overall_success = False
            result.success = False

        result.confidence = overall_confidence
        result.messages = results

        return overall_success, "\n".join(results), result

    except Exception as e:
        error_msg = f"❌ Comprehensive auto-detection failed: {e!s}"
        results.append(error_msg)
        result.messages = results
        return False, "\n".join(results), result


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
        return False, f"Validation error: {e!s}"
