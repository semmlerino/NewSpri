"""
Frame Extraction Module
======================

Handles different methods of extracting frames from sprite sheets:
- Grid-based extraction: Regular grid patterns with margins and spacing
- CCL extraction: Connected-component labeling for irregular sprites
- Background detection: Color key detection for transparency

This module provides both class-based and function-based interfaces for extraction.
All grid extraction methods are now module-level functions.
"""

import logging
from dataclasses import dataclass, field
from typing import NamedTuple, cast

import numpy as np
from PIL import Image
from PySide6.QtCore import QRect
from PySide6.QtGui import QPixmap
from scipy import ndimage

from config import Config

logger = logging.getLogger(__name__)

__all__ = [
    "CCLDetectionResult",
    "GridConfig",
    "GridLayout",
    "extract_grid_frames",
    "validate_frame_settings",
]


@dataclass
class CCLDetectionResult:
    """Result from CCL-based sprite detection."""

    success: bool
    method: str = "ccl_enhanced"
    # Frame settings (only meaningful when success=True)
    frame_width: int = 0
    frame_height: int = 0
    offset_x: int = 0
    offset_y: int = 0
    spacing_x: int = 0
    spacing_y: int = 0
    sprite_count: int = 0
    confidence: str = ""
    ccl_sprite_bounds: list[tuple[int, int, int, int]] = field(default_factory=list)
    irregular_collection: bool = False
    # Optional fields (only present in some paths)
    note: str = ""
    size_alternatives: dict = field(default_factory=dict)
    # Debug/error info (only on failure)
    debug_log: list[str] = field(default_factory=list)
    error: str = ""


# Method name constants used in detection result dicts
_METHOD_BEST_EFFORT = "best_effort"
_METHOD_FALLBACK = "fallback"
_METHOD_MODE = "mode"
_METHOD_MEDIAN = "median"

_ALPHA_OPAQUE_THRESHOLD = 128  # Pixels with alpha > this are considered opaque
_SOLID_IMAGE_OPAQUE_PCT = 95  # Images with >95% opaque pixels need color-key detection
_MIN_SPRITE_COMPONENT_SIZE = 8  # Components smaller than 8x8 treated as noise
_DEFAULT_FALLBACK_FRAME_SIZE = 48  # Fallback when distribution is too thin to estimate
_CCL_MERGE_DISTANCE = 15  # Max center-to-center px for merging multi-part sprites
_CCL_POSITION_GROUP_TOLERANCE = 15  # Max px gap for grouping positions into same row/column

# ============================================================================
# Data Structures
# ============================================================================


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


# ============================================================================
# Grid Extraction Functions
# ============================================================================


def extract_grid_frames(
    sprite_sheet: QPixmap, config: GridConfig
) -> tuple[bool, str, list[QPixmap], int]:
    """
    Extract frames from sprite sheet using grid-based extraction.

    Args:
        sprite_sheet: Source sprite sheet pixmap
        config: Grid configuration (frame size, offsets, spacing)

    Returns:
        Tuple of (success, error_message, frame_list, skipped_count)
        skipped_count indicates frames that couldn't fit within sheet boundaries
    """
    if not sprite_sheet or sprite_sheet.isNull():
        return False, "No sprite sheet provided", [], 0

    # Validate frame settings
    valid, error_msg = validate_frame_settings(sprite_sheet, config)
    if not valid:
        return False, error_msg, [], 0

    try:
        sheet_width = sprite_sheet.width()
        sheet_height = sprite_sheet.height()

        # Calculate available area after margins
        available_width = sheet_width - config.offset_x
        available_height = sheet_height - config.offset_y

        # Calculate grid layout
        layout = _calculate_grid_layout(available_width, available_height, config)

        # Extract individual frames with spacing, tracking skipped frames
        frames = []
        skipped_count = 0
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
                    else:
                        skipped_count += 1
                else:
                    skipped_count += 1

        return True, "", frames, skipped_count

    except Exception as e:
        logger.debug("Error extracting frames: %s", e, exc_info=True)
        return False, f"Error extracting frames: {e!s}", [], 0


def validate_frame_settings(sprite_sheet: QPixmap, config: GridConfig) -> tuple[bool, str]:
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
            return (
                False,
                f"Frame width + X offset ({config.offset_x + config.width}) exceeds sheet width ({sheet_width})",
            )
        if config.offset_y + config.height > sheet_height:
            return (
                False,
                f"Frame height + Y offset ({config.offset_y + config.height}) exceeds sheet height ({sheet_height})",
            )

    return True, ""


def _calculate_grid_layout(
    available_width: int, available_height: int, config: GridConfig
) -> GridLayout:
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

    return GridLayout(
        frames_per_row=frames_per_row,
        frames_per_col=frames_per_col,
    )


# ============================================================================
# Background Detection Functions
# ============================================================================


def detect_background_color(image_path: str) -> tuple[tuple[int, int, int], int] | None:
    """
    Detect background color for transparency application.
    Independent function focused solely on background color detection.

    Args:
        image_path: Path to the sprite sheet image

    Returns:
        Tuple of (rgb_color, tolerance) or None if no background color detected

    Example:
        >>> bg_info = detect_background_color("sprites.png")
        >>> if bg_info:
        ...     rgb_color, tolerance = bg_info
        ...     print(f"Background: RGB{rgb_color}, tolerance: {tolerance}")
    """
    try:
        # Load image as RGBA numpy array - use context manager to ensure file handle is closed
        with Image.open(image_path) as img:
            img_array = np.array(img.convert("RGBA"))

        # Check if image is mostly opaque (needs color key detection)
        alpha_channel = img_array[:, :, 3]
        binary_mask = (alpha_channel > _ALPHA_OPAQUE_THRESHOLD).astype(np.uint8)
        opaque_pixels = np.sum(binary_mask)
        total_pixels = binary_mask.size
        opaque_pixel_pct = 100 * opaque_pixels / total_pixels

        if opaque_pixel_pct > _SOLID_IMAGE_OPAQUE_PCT:  # Less than 5% alpha transparency
            # Try to detect background color (color key)
            color_key_result = _detect_color_key_mask(img_array, [])
            if color_key_result is not None:
                _color_key_mask, background_color, color_tolerance = color_key_result
                # Convert numpy types to Python ints
                rgb_tuple = (
                    int(background_color[0]),
                    int(background_color[1]),
                    int(background_color[2]),
                )
                return (rgb_tuple, int(color_tolerance))

        return None  # No background color detected (transparent image)

    except Exception as e:
        logger.debug("Background color detection failed: %s", e, exc_info=True)
        return None


def _detect_color_key_mask(
    img_array: np.ndarray, debug_log: list[str]
) -> tuple[np.ndarray, np.ndarray, int] | None:
    """
    Detect background color by analyzing corner pixels and testing tolerances.

    Args:
        img_array: RGBA image array
        debug_log: List to append debug messages to

    Returns:
        Tuple of (binary_mask, background_color, tolerance) or None if detection fails
    """
    try:
        _height, _width = img_array.shape[:2]

        # Sample corner pixels to find potential background color
        corner_samples = [
            img_array[0, 0, :3],  # Top-left
            img_array[0, -1, :3],  # Top-right
            img_array[-1, 0, :3],  # Bottom-left
            img_array[-1, -1, :3],  # Bottom-right
        ]

        # Find most common corner color
        corner_colors = [tuple(sample) for sample in corner_samples]
        color_counts = {}
        for color in corner_colors:
            color_counts[color] = color_counts.get(color, 0) + 1

        # Use most frequent corner color as potential background
        if color_counts:
            background_color = max(color_counts.items(), key=lambda x: x[1])[0]
            background_color = np.array(background_color, dtype=np.uint8)
        else:
            return None

        # Progressively looser tolerances: start strict to find clean backgrounds,
        # fall back to more permissive matching for noisy or compressed images.
        tolerance_levels = [15, 25, 35, 50]
        best_result = None
        best_score = 0

        for tolerance in tolerance_levels:
            result = _test_color_key_background(img_array, background_color, tolerance, debug_log)
            if result is not None:
                mask, score = result
                if score > best_score:
                    best_score = score
                    best_result = (mask, background_color, tolerance)

        if best_result is not None:
            mask, bg_color, tolerance = best_result
            debug_log.append(f"   [OK] Selected color key: {bg_color} with tolerance {tolerance}")
            logger.debug("Selected color key %s with tolerance %d", bg_color, tolerance)
            return best_result

        return None

    except Exception as e:
        logger.debug("Color key detection error: %s", e, exc_info=True)
        debug_log.append(f"   [ERROR] Color key detection error: {e}")
        return None


def _test_color_key_background(
    img_array: np.ndarray, background_color: np.ndarray, tolerance: int, debug_log: list[str]
) -> tuple[np.ndarray, float] | None:
    """
    Test a specific background color and tolerance combination.

    Args:
        img_array: RGBA image array
        background_color: RGB color to test as background
        tolerance: Color matching tolerance
        debug_log: List to append debug messages to

    Returns:
        Tuple of (binary_mask, quality_score) or None if test fails
    """
    try:
        height, width = img_array.shape[:2]

        # Create mask for non-background pixels (sprite pixels)
        rgb_array = img_array[:, :, :3]
        color_diff = np.abs(rgb_array.astype(int) - background_color.astype(int))
        sprite_mask = np.any(color_diff > tolerance, axis=2)

        # Calculate statistics
        sprite_pixels = np.sum(sprite_mask)
        total_pixels = height * width
        background_percentage = 100 * (total_pixels - sprite_pixels) / total_pixels

        # Use connected components to count separate sprites
        labeled_result = ndimage.label(sprite_mask.astype(np.uint8))
        _labeled_array, num_components = cast("tuple[np.ndarray, int]", labeled_result)

        # Calculate quality score based on background percentage and component count
        # Good background detection should have high background % and reasonable component count
        if (
            background_percentage > 50 and num_components > 0
        ):  # Majority background → likely a valid color key
            # Score: higher background % and lower tolerance both indicate a cleaner match.
            # Divide by 10 to keep score in 0-10 range; cap at 50 to prevent runaway scores.
            component_bonus = min(num_components / 10, 50)  # Cap bonus at 50
            score = background_percentage + component_bonus

            debug_log.append(
                f"   [TEST] Testing {background_color} (tol={tolerance}): {background_percentage:.1f}% bg, {num_components} comp, score: {score:.1f}"
            )
            logger.debug(
                "Testing color key %s (tol=%d): %.1f%% bg, %d comp, score: %.1f",
                background_color,
                tolerance,
                background_percentage,
                num_components,
                score,
            )

            return sprite_mask.astype(np.uint8), score

        return None

    except Exception as e:
        logger.debug("Color key test error: %s", e, exc_info=True)
        debug_log.append(f"   [ERROR] Color key test error: {e}")
        return None


# ============================================================================
# CCL Extraction Functions
# ============================================================================


def detect_sprites_ccl_enhanced(image_path: str) -> CCLDetectionResult | None:
    """
    Enhanced CCL detection for sprite boundary detection.
    Returns sprite boundaries only - background color detection is handled separately.

    Args:
        image_path: Path to the sprite sheet image

    Returns:
        CCLDetectionResult with detection results, or None on unexpected error.

    Example:
        >>> result = detect_sprites_ccl_enhanced("sprite_atlas.png")
        >>> if result and result['success']:
        ...     bounds = result['ccl_sprite_bounds']
        ...     print(f"Detected {len(bounds)} sprites")
    """
    debug_log: list[str] = []
    try:
        debug_log.append(f"CCL Detection starting on: {image_path}")

        # Stage 1: Load image and create sprite/background binary mask
        img_array, binary_mask = _load_sprite_mask(image_path, debug_log)

        # Stage 2: Label connected components and extract bounding boxes
        sprite_bounds = _extract_sprite_bounds(binary_mask, debug_log)
        if not sprite_bounds:
            return CCLDetectionResult(success=False, debug_log=debug_log)

        # Stage 3: Decide whether to merge nearby components
        skip_merging = _should_skip_merging(sprite_bounds, debug_log)

        if skip_merging:
            debug_log.append("Irregular collection - disabling sprite merging")
            merged_bounds = sprite_bounds
        else:
            debug_log.append("Regular sprite sheet - merging nearby components")
            merged_bounds = _merge_nearby_components(sprite_bounds, _CCL_MERGE_DISTANCE, debug_log)

        debug_log.append(f"After merging: {len(merged_bounds)} sprites")

        # Stage 4: Analyze results and suggest frame settings
        analysis_result = _analyze_ccl_results(
            merged_bounds, img_array.shape[1], img_array.shape[0], debug_log
        )
        if analysis_result.get("success", False):
            return CCLDetectionResult(**analysis_result)

        debug_log.append("CCL Failed: layout too irregular or insufficient sprites")
        return CCLDetectionResult(success=False, debug_log=debug_log)

    except Exception as e:
        logger.debug("CCL Detection error: %s", e, exc_info=True)
        debug_log.append(f"CCL Detection Error: {e!s}")
        return CCLDetectionResult(success=False, error=str(e), debug_log=debug_log)


def _load_sprite_mask(image_path: str, debug_log: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Load an image and produce a binary mask separating sprites from background.

    Uses alpha channel by default. Falls back to color-key detection for mostly-opaque
    images (>95% opaque pixels).

    Args:
        image_path: Path to the sprite sheet image
        debug_log: List to append debug messages to

    Returns:
        Tuple of (img_array as RGBA, binary_mask as uint8)
    """
    with Image.open(image_path) as img:
        img_array = np.array(img.convert("RGBA"))
    debug_log.append(f"Loaded image: {img_array.shape} (height, width, channels)")

    alpha_channel = img_array[:, :, 3]
    binary_mask = (alpha_channel > _ALPHA_OPAQUE_THRESHOLD).astype(np.uint8)
    opaque_pixels = np.sum(binary_mask)
    total_pixels = binary_mask.size
    opaque_pixel_pct = 100 * opaque_pixels / total_pixels
    debug_log.append(f"Alpha mask: {opaque_pixels}/{total_pixels} opaque ({opaque_pixel_pct:.1f}%)")
    debug_log.append("Using alpha channel for sprite boundary detection")

    # For mostly-opaque images, try color key detection instead
    if opaque_pixel_pct > _SOLID_IMAGE_OPAQUE_PCT:
        debug_log.append(f"Solid image detected ({opaque_pixel_pct:.1f}% opaque)")
        color_key_result = _detect_color_key_mask(img_array, debug_log)
        if color_key_result is not None:
            color_key_mask, _background_color, _color_tolerance = color_key_result
            binary_mask = color_key_mask
            opaque_pixels = np.sum(binary_mask)
            debug_log.append(f"Color key boundaries: {opaque_pixels}/{total_pixels} sprite pixels")
        else:
            debug_log.append("No suitable color key found, using alpha channel")

    return img_array, binary_mask


def _extract_sprite_bounds(
    binary_mask: np.ndarray, debug_log: list[str]
) -> list[tuple[int, int, int, int]]:
    """Label connected components and extract bounding boxes, filtering tiny ones.

    Args:
        binary_mask: Binary mask (uint8) where 1 = sprite pixel
        debug_log: List to append debug messages to

    Returns:
        List of (x, y, width, height) tuples for components >= 8x8
    """
    label_result = ndimage.label(binary_mask)
    labeled_array, num_features = cast("tuple[np.ndarray, int]", label_result)
    debug_log.append(f"Found {num_features} connected components")

    if num_features == 0:
        debug_log.append("No connected components found")
        return []

    objects = ndimage.find_objects(labeled_array)
    sprite_bounds = []

    for obj in objects:
        if obj is None:
            continue

        y_slice, x_slice = obj
        x_start, x_end = x_slice.start, x_slice.stop
        y_start, y_end = y_slice.start, y_slice.stop
        width, height = x_end - x_start, y_end - y_start

        if width >= _MIN_SPRITE_COMPONENT_SIZE and height >= _MIN_SPRITE_COMPONENT_SIZE:
            sprite_bounds.append((x_start, y_start, width, height))

    debug_log.append(f"Valid components: {len(sprite_bounds)}")
    return sprite_bounds


def _should_skip_merging(
    sprite_bounds: list[tuple[int, int, int, int]], debug_log: list[str]
) -> bool:
    """Decide whether to skip merging based on sprite size diversity.

    Large collections with high size variation are treated as irregular -- merging
    would combine unrelated sprites.

    Args:
        sprite_bounds: List of (x, y, width, height) tuples
        debug_log: List to append debug messages to

    Returns:
        True if merging should be skipped (irregular collection)
    """
    widths = [w for _x, _y, w, _h in sprite_bounds]
    heights = [h for _x, _y, _w, h in sprite_bounds]
    width_std = float(np.std(widths))
    height_std = float(np.std(heights))

    size_range_w = max(widths) - min(widths)
    size_range_h = max(heights) - min(heights)
    avg_size_std = (width_std + height_std) / 2

    small_sprites_count = sum(1 for w, h in zip(widths, heights, strict=False) if w < 24 or h < 24)

    # Skip merging when sprites are numerous AND either highly varied or atlas-like.
    # High variance suggests distinct sprites that shouldn't be merged; large atlas
    # counts make O(n²) merging too expensive with unreliable results.
    is_high_variance = (
        avg_size_std > 10
        or size_range_w > min(widths) * 3
        or size_range_h > min(heights) * 3
        or small_sprites_count > 20
    )
    is_large_atlas = len(sprite_bounds) > 200
    skip = len(sprite_bounds) > 50 and (is_high_variance or is_large_atlas)

    debug_log.append(
        f"Analysis: {len(sprite_bounds)} sprites, diversity={avg_size_std:.1f}, irregular={skip}"
    )
    return skip


class _UnionFind:
    """Disjoint-set / union-find with path compression (halving) and union by assignment."""

    __slots__ = ("_parent",)

    def __init__(self, n: int) -> None:
        self._parent = list(range(n))

    def find(self, i: int) -> int:
        while self._parent[i] != i:
            self._parent[i] = self._parent[self._parent[i]]
            i = self._parent[i]
        return i

    def union(self, i: int, j: int) -> None:
        ri, rj = self.find(i), self.find(j)
        if ri != rj:
            self._parent[ri] = rj


def _merge_nearby_components(
    sprite_bounds: list[tuple[int, int, int, int]],
    threshold: int,
    debug_log: list[str] | None = None,
) -> list[tuple[int, int, int, int]]:
    """
    Merge sprite components whose centers are within *threshold* px of each other (multi-part sprites).

    Proximity is measured as center-to-center Euclidean distance. Uses union-find for
    transitive closure so chains like A-B-C are fully merged even when A and C are not
    directly within threshold of each other.

    Args:
        sprite_bounds: List of (x, y, width, height) tuples
        threshold: Maximum center-to-center Euclidean distance (px) for merging sprites
        debug_log: List to append debug messages to

    Returns:
        List of merged sprite bounds
    """
    if debug_log is None:
        debug_log = []

    if threshold <= 0:
        debug_log.append(f"   Merging disabled (threshold: {threshold})")
        return sprite_bounds

    n = len(sprite_bounds)
    uf = _UnionFind(n)

    # Precompute centers
    centers = [(x + w // 2, y + h // 2) for x, y, w, h in sprite_bounds]

    # Union every pair within threshold distance
    for i in range(n):
        cx1, cy1 = centers[i]
        for j in range(i + 1, n):
            cx2, cy2 = centers[j]
            distance = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5
            if distance <= threshold:
                uf.union(i, j)

    # Collect groups by root
    groups: dict[int, list[tuple[int, int, int, int]]] = {}
    for i, sprite in enumerate(sprite_bounds):
        root = uf.find(i)
        groups.setdefault(root, []).append(sprite)

    # Merge bounding boxes within each group
    merged = []
    merge_count = 0
    for group_sprites in groups.values():
        min_x = min(x for x, _y, _w, _h in group_sprites)
        min_y = min(y for _x, y, _w, _h in group_sprites)
        max_x = max(x + w for x, _y, w, _h in group_sprites)
        max_y = max(y + h for _x, y, _w, h in group_sprites)
        merged.append((min_x, min_y, max_x - min_x, max_y - min_y))

        if len(group_sprites) > 1:
            merge_count += 1
            debug_log.append(
                f"      Group: {len(group_sprites)} parts -> ({min_x}, {min_y}) {max_x - min_x}x{max_y - min_y}"
            )

    debug_log.append(
        f"   Merging complete: {merge_count} groups merged, {len(merged)} final sprites"
    )
    return merged


def _analyze_ccl_results(
    sprite_bounds: list[tuple[int, int, int, int]],
    sheet_width: int,
    sheet_height: int,
    debug_log: list[str] | None = None,
) -> dict:
    """Analyze CCL results and suggest frame settings."""
    if debug_log is None:
        debug_log = []

    if not sprite_bounds:
        return {"success": False, "method": "ccl_enhanced"}

    # Calculate statistics
    widths = [w for _x, _y, w, _h in sprite_bounds]
    heights = [h for _x, _y, _w, h in sprite_bounds]
    avg_width = int(np.mean(widths))
    avg_height = int(np.mean(heights))
    width_std = np.std(widths)
    height_std = np.std(heights)

    debug_log.append(
        f"Analyzing {len(sprite_bounds)} sprites: avg={avg_width}x{avg_height}, std={width_std:.1f}x{height_std:.1f}"
    )

    # Check if layout is regular (uniform sprite sizes)
    uniform_size = width_std < 8 and height_std < 8

    if uniform_size and len(sprite_bounds) >= 2:
        return _infer_grid_from_positions(sprite_bounds, sheet_width, sheet_height, debug_log)

    # Fallback: Handle irregular sprite sheets
    if len(sprite_bounds) >= 4:
        result = _analyze_irregular_sprites(
            sprite_bounds, widths, heights, avg_width, avg_height, debug_log
        )
        if result is not None:
            return result

    debug_log.append("CCL Failed: layout too irregular or insufficient sprites")
    return {"success": False, "method": "ccl_enhanced"}


def _group_positions(positions: list[int], tolerance: int = 15) -> list[int]:
    """Group nearby 1D positions and return one representative per group.

    Consecutive values within *tolerance* of each other are merged into a single
    group, represented by its arithmetic mean.

    Args:
        positions: Unsorted list of 1D coordinates
        tolerance: Maximum gap between values in the same group

    Returns:
        Sorted list of group-representative positions
    """
    if not positions:
        return []
    sorted_pos = sorted(set(positions))
    groups: list[list[int]] = [[sorted_pos[0]]]
    for pos in sorted_pos[1:]:
        if pos - groups[-1][-1] <= tolerance:
            groups[-1].append(pos)
        else:
            groups.append([pos])
    return [sum(group) // len(group) for group in groups]


def _infer_grid_from_positions(
    sprite_bounds: list[tuple[int, int, int, int]],
    sheet_width: int,
    sheet_height: int,
    debug_log: list[str],
) -> dict:
    """Infer a regular grid structure from uniformly-sized sprite positions.

    Args:
        sprite_bounds: List of (x, y, width, height) tuples (assumed uniform size)
        sheet_width: Total image width
        sheet_height: Total image height
        debug_log: List to append debug messages to

    Returns:
        Detection result dict
    """
    centers_x = [x + w // 2 for x, _y, w, _h in sprite_bounds]
    centers_y = [y + h // 2 for _x, y, _w, h in sprite_bounds]

    grouped_x = _group_positions(centers_x, tolerance=_CCL_POSITION_GROUP_TOLERANCE)

    y_range = max(centers_y) - min(centers_y)
    avg_sprite_height = np.mean([h for _x, _y, _w, h in sprite_bounds])

    if (
        y_range <= avg_sprite_height * 0.4
    ):  # Single-row threshold: row must span at least 40% of image width
        grouped_y = [int(np.mean(centers_y))]
    else:
        grouped_y = _group_positions(centers_y, tolerance=_CCL_POSITION_GROUP_TOLERANCE)

    cols = len(grouped_x)
    rows = len(grouped_y)

    frame_width = int(sheet_width / cols) if cols > 1 else sheet_width
    frame_height = int(sheet_height / rows) if rows > 1 else sheet_height

    confidence = "high" if cols * rows == len(sprite_bounds) else "medium"
    debug_log.append(
        f"Grid: {cols}x{rows}, frame: {frame_width}x{frame_height}, confidence: {confidence}"
    )

    return {
        "success": True,
        "frame_width": frame_width,
        "frame_height": frame_height,
        "offset_x": 0,
        "offset_y": 0,
        "spacing_x": 0,
        "spacing_y": 0,
        "sprite_count": len(sprite_bounds),
        "confidence": confidence,
        "method": "ccl_enhanced",
        "ccl_sprite_bounds": sprite_bounds,
        "irregular_collection": False,
    }


def _choose_frame_size(
    widths: list[int],
    heights: list[int],
    common_width: int,
    common_height: int,
    is_irregular: bool,
) -> tuple[int, int, str]:
    """Choose a representative frame size for non-uniform sprites.

    For irregular collections (icon atlases), uses median of mid-range sprites.
    For semi-regular sheets (RPG style), uses mode or median of all sprites.

    Returns:
        Tuple of (width, height, method_name)
    """
    if is_irregular:
        # 20-80px is the typical character sprite size band for pixel art
        char_sprites = [
            (w, h) for w, h in zip(widths, heights, strict=False) if 20 <= w <= 80 and 20 <= h <= 80
        ]
        if len(char_sprites) >= 10:  # Need sufficient samples for statistical estimate
            return (
                int(np.median([w for w, _h in char_sprites])),
                int(np.median([h for _w, h in char_sprites])),
                _METHOD_BEST_EFFORT,
            )
        return _DEFAULT_FALLBACK_FRAME_SIZE, _DEFAULT_FALLBACK_FRAME_SIZE, _METHOD_FALLBACK

    median_width = int(np.median(widths))
    median_height = int(np.median(heights))

    if (
        abs(median_width - common_width) <= 10 and abs(median_height - common_height) <= 10
    ):  # Mode and median agree within 10px
        return common_width, common_height, _METHOD_MODE
    return median_width, median_height, _METHOD_MEDIAN


def _analyze_irregular_sprites(
    sprite_bounds: list[tuple[int, int, int, int]],
    widths: list[int],
    heights: list[int],
    avg_width: int,
    avg_height: int,
    debug_log: list[str],
) -> dict | None:
    """
    Analyze sprites that didn't pass the uniform-size check.

    Attempts to pick a representative frame size from the distribution of sprite
    sizes, returning a result dict on success or None when the data is too sparse.

    Args:
        sprite_bounds: List of (x, y, width, height) tuples for all sprites
        widths: Pre-computed list of sprite widths (same order as sprite_bounds)
        heights: Pre-computed list of sprite heights (same order as sprite_bounds)
        avg_width: Integer mean of widths
        avg_height: Integer mean of heights
        debug_log: List to append debug messages to

    Returns:
        Result dict with the same keys as _analyze_ccl_results returns on success,
        plus additional keys ``size_alternatives`` (dict of mode/median/average/top_sizes)
        and ``note`` (human-readable description of the chosen method).
        Returns None if the data does not meet the minimum threshold.
    """
    width_std = float(np.std(widths))
    height_std = float(np.std(heights))

    # Find most common sprite size
    size_frequency: dict[tuple[int, int], int] = {}
    for w, h in zip(widths, heights, strict=False):
        size_frequency[w, h] = size_frequency.get((w, h), 0) + 1

    (common_width, common_height), frequency = max(size_frequency.items(), key=lambda x: x[1])

    # Reject if most common size is too rare
    if (
        frequency / len(sprite_bounds) < 0.02
    ):  # Mode represents <2% of sprites — too rare to be meaningful
        return None

    sorted_sizes = sorted(size_frequency.items(), key=lambda x: x[1], reverse=True)

    # Determine if this is a truly irregular collection (e.g., icon atlas)
    avg_size_std = (width_std + height_std) / 2
    size_range_w = max(widths) - min(widths)
    size_range_h = max(heights) - min(heights)

    small_count = sum(1 for w, h in zip(widths, heights, strict=False) if w < 24 or h < 24)
    medium_count = sum(
        1 for w, h in zip(widths, heights, strict=False) if 24 <= w <= 64 and 24 <= h <= 64
    )

    is_irregular_collection = (
        len(sprite_bounds) > 50
        and avg_size_std > 10
        and (size_range_w > min(widths) * 3 or size_range_h > min(heights) * 3)
        and small_count > 5
        and medium_count > 5
    )

    # Choose frame size based on collection type
    chosen_width, chosen_height, chosen_method = _choose_frame_size(
        widths, heights, common_width, common_height, is_irregular_collection
    )

    debug_log.append(
        f"Irregular: {chosen_width}x{chosen_height} ({chosen_method}), {len(sprite_bounds)} sprites"
    )

    return {
        "success": True,
        "frame_width": chosen_width,
        "frame_height": chosen_height,
        "offset_x": 0,
        "offset_y": 0,
        "spacing_x": 0,
        "spacing_y": 0,
        "sprite_count": len(sprite_bounds),
        "confidence": "low" if is_irregular_collection else "medium",
        "method": f"ccl_enhanced_{chosen_method}",
        "note": f"{'IRREGULAR COLLECTION' if is_irregular_collection else 'RPG sprite sheet'}: {chosen_method} size",
        "irregular_collection": is_irregular_collection,
        "ccl_sprite_bounds": sprite_bounds,
        "size_alternatives": {
            "mode": (common_width, common_height),
            "median": (int(np.median(widths)), int(np.median(heights))),
            "average": (avg_width, avg_height),
            "top_sizes": sorted_sizes[:3],
        },
    }
