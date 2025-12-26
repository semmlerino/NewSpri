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

import contextlib
import os
import tempfile
from typing import NamedTuple, cast

import numpy as np
from PIL import Image
from PySide6.QtCore import QRect
from PySide6.QtGui import QPixmap
from scipy import ndimage

from config import Config

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
    total_frames: int
    available_width: int
    available_height: int


# ============================================================================
# Grid Extraction Functions
# ============================================================================

def extract_grid_frames(sprite_sheet: QPixmap, config: GridConfig) -> tuple[bool, str, list[QPixmap]]:
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
    valid, error_msg = validate_frame_settings(sprite_sheet, config)
    if not valid:
        return False, error_msg, []

    try:
        sheet_width = sprite_sheet.width()
        sheet_height = sprite_sheet.height()

        # Calculate available area after margins
        available_width = sheet_width - config.offset_x
        available_height = sheet_height - config.offset_y

        # Calculate grid layout
        layout = _calculate_grid_layout(available_width, available_height, config)

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
            return False, f"Frame width + X offset ({config.offset_x + config.width}) exceeds sheet width ({sheet_width})"
        if config.offset_y + config.height > sheet_height:
            return False, f"Frame height + Y offset ({config.offset_y + config.height}) exceeds sheet height ({sheet_height})"

    return True, ""


def calculate_grid_layout(sprite_sheet: QPixmap, config: GridConfig) -> GridLayout | None:
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
    valid, _ = validate_frame_settings(sprite_sheet, config)
    if not valid:
        return None

    available_width = sprite_sheet.width() - config.offset_x
    available_height = sprite_sheet.height() - config.offset_y

    return _calculate_grid_layout(available_width, available_height, config)


def _calculate_grid_layout(available_width: int, available_height: int, config: GridConfig) -> GridLayout:
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


def create_frame_info_string(layout: GridLayout, config: GridConfig) -> str:
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
            img_array = np.array(img.convert('RGBA'))

        # Check if image is mostly opaque (needs color key detection)
        alpha_channel = img_array[:, :, 3]
        binary_mask = (alpha_channel > 128).astype(np.uint8)
        opaque_pixels = np.sum(binary_mask)
        total_pixels = binary_mask.size
        alpha_transparency_ratio = 100 * opaque_pixels / total_pixels

        if alpha_transparency_ratio > 95:  # Less than 5% alpha transparency
            # Try to detect background color (color key)
            color_key_result = _detect_color_key_mask(img_array, [])
            if color_key_result is not None:
                _color_key_mask, background_color, color_tolerance = color_key_result
                # Convert numpy types to Python ints
                rgb_tuple = (int(background_color[0]), int(background_color[1]), int(background_color[2]))
                return (rgb_tuple, int(color_tolerance))

        return None  # No background color detected (transparent image)

    except Exception as e:
        print(f"   ⚠️  Background color detection failed: {e}")
        return None


def _detect_color_key_mask(img_array: np.ndarray, debug_log: list) -> tuple[np.ndarray, np.ndarray, int] | None:
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
            img_array[0, 0, :3],      # Top-left
            img_array[0, -1, :3],     # Top-right
            img_array[-1, 0, :3],     # Bottom-left
            img_array[-1, -1, :3],    # Bottom-right
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

        # Test multiple tolerance levels to find optimal background separation
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
            debug_log.append(f"   ✅ Selected color key: {bg_color} with tolerance {tolerance}")
            print(f"   ✅ Selected color key: {bg_color} with tolerance {tolerance}")
            return best_result

        return None

    except Exception as e:
        debug_log.append(f"   ❌ Color key detection error: {e}")
        return None


def _test_color_key_background(img_array: np.ndarray, background_color: np.ndarray, tolerance: int, debug_log: list) -> tuple[np.ndarray, float] | None:
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
        _labeled_array, num_components = cast('tuple[np.ndarray, int]', labeled_result)

        # Calculate quality score based on background percentage and component count
        # Good background detection should have high background % and reasonable component count
        if background_percentage > 50 and num_components > 0:
            # Score = background_percentage + bonus for reasonable component count
            component_bonus = min(num_components / 10, 50)  # Cap bonus at 50
            score = background_percentage + component_bonus

            debug_log.append(f"   🧪 Testing {background_color} (tol={tolerance}): {background_percentage:.1f}% bg, {num_components} comp, score: {score:.1f}")
            print(f"   🧪 Testing {background_color} (tol={tolerance}): {background_percentage:.1f}% bg, {num_components} comp, score: {score:.1f}")

            return sprite_mask.astype(np.uint8), score

        return None

    except Exception as e:
        debug_log.append(f"   ❌ Color key test error: {e}")
        return None


# ============================================================================
# CCL Extraction Functions
# ============================================================================

def detect_sprites_ccl_enhanced(image_path: str) -> dict | None:
    """
    Enhanced CCL detection for sprite boundary detection.
    Returns sprite boundaries only - background color detection is handled separately.

    Args:
        image_path: Path to the sprite sheet image

    Returns:
        Dictionary with detection results:
        {
            'success': bool,
            'frame_width': int,
            'frame_height': int,
            'offset_x': int,
            'offset_y': int,
            'spacing_x': int,
            'spacing_y': int,
            'sprite_count': int,
            'confidence': str,
            'method': str,
            'ccl_sprite_bounds': List[Tuple[int, int, int, int]],
            'irregular_collection': bool,
            'size_alternatives': dict
        }

    Example:
        >>> result = detect_sprites_ccl_enhanced("sprite_atlas.png")
        >>> if result and result['success']:
        ...     bounds = result['ccl_sprite_bounds']
        ...     print(f"Detected {len(bounds)} sprites")
    """
    debug_log = []
    try:
        debug_log.append(f"CCL Detection starting on: {image_path}")

        # Load image as RGBA numpy array - use context manager to ensure file handle is closed
        with Image.open(image_path) as img:
            img_array = np.array(img.convert('RGBA'))
        debug_log.append(f"Loaded image: {img_array.shape} (height, width, channels)")

        # Create binary mask based on alpha channel
        alpha_channel = img_array[:, :, 3]
        binary_mask = (alpha_channel > 128).astype(np.uint8)
        opaque_pixels = np.sum(binary_mask)
        total_pixels = binary_mask.size
        alpha_transparency_ratio = 100 * opaque_pixels / total_pixels
        debug_log.append(f"Alpha mask: {opaque_pixels}/{total_pixels} opaque ({alpha_transparency_ratio:.1f}%)")

        # For CCL, we always use alpha channel for initial detection
        debug_log.append("Using alpha channel for sprite boundary detection")

        # If image is mostly/completely opaque, try color key detection
        if alpha_transparency_ratio > 95:
            debug_log.append(f"Solid image detected ({alpha_transparency_ratio:.1f}% opaque)")
            color_key_result = _detect_color_key_mask(img_array, debug_log)
            if color_key_result is not None:
                color_key_mask, _background_color, _color_tolerance = color_key_result
                binary_mask = color_key_mask
                opaque_pixels = np.sum(binary_mask)
                debug_log.append(f"Color key boundaries: {opaque_pixels}/{total_pixels} sprite pixels")
            else:
                debug_log.append("No suitable color key found, using alpha channel")

        # Label connected components
        label_result = ndimage.label(binary_mask)
        labeled_array, num_features = cast('tuple[np.ndarray, int]', label_result)
        debug_log.append(f"Found {num_features} connected components")

        if num_features == 0:
            debug_log.append("No connected components found")
            return {'success': False, 'debug_log': debug_log}

        # Extract bounding boxes
        objects = ndimage.find_objects(labeled_array)
        sprite_bounds = []

        for _i, obj in enumerate(objects):
            if obj is None:
                continue

            y_slice, x_slice = obj
            x_start, x_end = x_slice.start, x_slice.stop
            y_start, y_end = y_slice.start, y_slice.stop
            width, height = x_end - x_start, y_end - y_start

            # Filter tiny components
            if width >= 8 and height >= 8:
                sprite_bounds.append((x_start, y_start, width, height))

        debug_log.append(f"Valid components: {len(sprite_bounds)}")

        # Pre-analyze for irregular collections before merging
        widths = [w for _x, _y, w, _h in sprite_bounds]
        heights = [h for _x, _y, _w, h in sprite_bounds]
        width_std = np.std(widths)
        height_std = np.std(heights)

        # Check if this is an irregular sprite collection
        size_range_w = max(widths) - min(widths)
        size_range_h = max(heights) - min(heights)
        size_diversity = (width_std + height_std) / 2

        small_sprites = [(w, h) for w, h in zip(widths, heights, strict=False) if w < 24 or h < 24]

        is_irregular_collection = (
            len(sprite_bounds) > 50 and
            (size_diversity > 10 or
             (size_range_w > min(widths) * 3 or size_range_h > min(heights) * 3) or
             len(small_sprites) > 20 or
             len(sprite_bounds) > 200)
        )

        debug_log.append(f"Analysis: {len(sprite_bounds)} sprites, diversity={size_diversity:.1f}, irregular={is_irregular_collection}")

        if is_irregular_collection:
            debug_log.append("Irregular collection - disabling sprite merging")
            merged_bounds = sprite_bounds
        else:
            debug_log.append("Regular sprite sheet - merging nearby components")
            merged_bounds = _merge_nearby_components(sprite_bounds, 15, debug_log)

        debug_log.append(f"After merging: {len(merged_bounds)} sprites")

        analysis_result = _analyze_ccl_results(merged_bounds, img_array.shape[1], img_array.shape[0], debug_log)
        if analysis_result.get('success', False):
            return analysis_result

        debug_log.append("CCL Failed: layout too irregular or insufficient sprites")
        return {'success': False, 'method': 'ccl_enhanced'}

    except Exception as e:
        debug_log.append(f"CCL Detection Error: {e!s}")
        return {'success': False, 'method': 'ccl_enhanced', 'error': str(e), 'debug_log': debug_log}


def _merge_nearby_components(sprite_bounds: list[tuple[int, int, int, int]],
                           threshold: int, debug_log: list[str] | None = None) -> list[tuple[int, int, int, int]]:
    """
    Merge sprite components that are close to each other (multi-part sprites).

    Args:
        sprite_bounds: List of (x, y, width, height) tuples
        threshold: Maximum distance for merging sprites
        debug_log: List to append debug messages to

    Returns:
        List of merged sprite bounds
    """
    if debug_log is None:
        debug_log = []

    if threshold <= 0:
        debug_log.append(f"   🚫 Merging disabled (threshold: {threshold})")
        return sprite_bounds

    merged = []
    used = set()
    merge_count = 0

    for i, (x1, y1, w1, h1) in enumerate(sprite_bounds):
        if i in used:
            continue

        # Start a new merge group with this sprite
        merge_group = [(x1, y1, w1, h1)]
        used.add(i)

        # Find nearby sprites to merge
        for j, (x2, y2, w2, h2) in enumerate(sprite_bounds):
            if j in used:
                continue

            # Check distance between sprite centers
            center1_x, center1_y = x1 + w1//2, y1 + h1//2
            center2_x, center2_y = x2 + w2//2, y2 + h2//2
            distance = ((center1_x - center2_x)**2 + (center1_y - center2_y)**2)**0.5

            if distance <= threshold:
                merge_group.append((x2, y2, w2, h2))
                used.add(j)

        # Create merged bounding box for this group
        if merge_group:
            min_x = min(x for x, _y, _w, _h in merge_group)
            min_y = min(y for _x, y, _w, _h in merge_group)
            max_x = max(x + w for x, _y, w, _h in merge_group)
            max_y = max(y + h for _x, y, _w, h in merge_group)
            merged_bounds = (min_x, min_y, max_x - min_x, max_y - min_y)
            merged.append(merged_bounds)

            if len(merge_group) > 1:
                merge_count += 1
                debug_log.append(f"      ✅ Group {i+1}: {len(merge_group)} parts → ({min_x}, {min_y}) {max_x - min_x}×{max_y - min_y}")

    debug_log.append(f"   🔀 Merging complete: {merge_count} groups merged, {len(merged)} final sprites")
    return merged


def _analyze_ccl_results(sprite_bounds: list[tuple[int, int, int, int]],
                        sheet_width: int, sheet_height: int, debug_log: list[str] | None = None) -> dict:
    """Analyze CCL results and suggest frame settings."""
    if debug_log is None:
        debug_log = []

    if not sprite_bounds:
        return {'success': False, 'method': 'ccl_enhanced'}

    # Calculate statistics
    widths = [w for _x, _y, w, _h in sprite_bounds]
    heights = [h for _x, _y, _w, h in sprite_bounds]
    avg_width = int(np.mean(widths))
    avg_height = int(np.mean(heights))
    width_std = np.std(widths)
    height_std = np.std(heights)

    debug_log.append(f"Analyzing {len(sprite_bounds)} sprites: avg={avg_width}x{avg_height}, std={width_std:.1f}x{height_std:.1f}")

    # Check if layout is regular
    uniform_size = width_std < 8 and height_std < 8

    if uniform_size and len(sprite_bounds) >= 2:
        # Infer grid structure from sprite positions
        centers_x = [x + w//2 for x, _y, w, _h in sprite_bounds]
        centers_y = [y + h//2 for _x, y, _w, h in sprite_bounds]

        def group_positions(positions, tolerance=15):
            if not positions:
                return []
            sorted_pos = sorted(set(positions))
            groups = [[sorted_pos[0]]]
            for pos in sorted_pos[1:]:
                if pos - groups[-1][-1] <= tolerance:
                    groups[-1].append(pos)
                else:
                    groups.append([pos])
            return [sum(group) // len(group) for group in groups]

        grouped_x = group_positions(centers_x, tolerance=15)

        y_range = max(centers_y) - min(centers_y)
        avg_sprite_height = np.mean([h for _x, _y, _w, h in sprite_bounds])

        if y_range <= avg_sprite_height * 0.4:
            grouped_y = [int(np.mean(centers_y))]
        else:
            grouped_y = group_positions(centers_y, tolerance=15)

        cols = len(grouped_x)
        rows = len(grouped_y)

        frame_width = int(sheet_width / cols) if cols > 1 else sheet_width
        frame_height = int(sheet_height / rows) if rows > 1 else sheet_height

        confidence = 'high' if cols * rows == len(sprite_bounds) else 'medium'
        debug_log.append(f"Grid: {cols}x{rows}, frame: {frame_width}x{frame_height}, confidence: {confidence}")

        return {
            'success': True,
            'frame_width': frame_width,
            'frame_height': frame_height,
            'offset_x': 0,
            'offset_y': 0,
            'spacing_x': 0,
            'spacing_y': 0,
            'sprite_count': len(sprite_bounds),
            'confidence': confidence,
            'method': 'ccl_enhanced',
            'ccl_sprite_bounds': sprite_bounds,
            'irregular_collection': False,
        }

    # Fallback: Handle irregular sprite sheets
    if len(sprite_bounds) >= 4:
        # Find most common sprite size
        size_frequency = {}
        for w, h in zip(widths, heights, strict=False):
            size_key = (w, h)
            size_frequency[size_key] = size_frequency.get(size_key, 0) + 1

        most_common_size = max(size_frequency.items(), key=lambda x: x[1])
        (common_width, common_height), frequency = most_common_size

        min_threshold = 0.02
        common_percentage = frequency / len(sprite_bounds)

        if common_percentage >= min_threshold:
            sorted_sizes = sorted(size_frequency.items(), key=lambda x: x[1], reverse=True)
            top_3_sizes = sorted_sizes[:3]

            size_range_w = max(widths) - min(widths)
            size_range_h = max(heights) - min(heights)
            size_diversity = (width_std + height_std) / 2

            small_sprites = [(w, h) for w, h in zip(widths, heights, strict=False) if w < 24 or h < 24]
            medium_sprites = [(w, h) for w, h in zip(widths, heights, strict=False) if 24 <= w <= 64 and 24 <= h <= 64]

            is_irregular_collection = (
                len(sprite_bounds) > 50 and
                size_diversity > 10 and
                (size_range_w > min(widths) * 3 or size_range_h > min(heights) * 3) and
                len(small_sprites) > 5 and len(medium_sprites) > 5
            )

            if is_irregular_collection:
                char_sprites = [(w, h) for w, h in zip(widths, heights, strict=False) if 20 <= w <= 80 and 20 <= h <= 80]
                if len(char_sprites) >= 10:
                    chosen_width = int(np.median([w for w, _h in char_sprites]))
                    chosen_height = int(np.median([h for _w, h in char_sprites]))
                    chosen_method = "best_effort_warning"
                else:
                    chosen_width, chosen_height = 48, 48
                    chosen_method = "fallback_warning"
            else:
                median_width = int(np.median(widths))
                median_height = int(np.median(heights))
                if abs(median_width - common_width) <= 10 and abs(median_height - common_height) <= 10:
                    chosen_width, chosen_height = common_width, common_height
                    chosen_method = "mode"
                else:
                    chosen_width, chosen_height = median_width, median_height
                    chosen_method = "median"

            debug_log.append(f"Irregular: {chosen_width}x{chosen_height} ({chosen_method}), {len(sprite_bounds)} sprites")

            return {
                'success': True,
                'frame_width': chosen_width,
                'frame_height': chosen_height,
                'offset_x': 0,
                'offset_y': 0,
                'spacing_x': 0,
                'spacing_y': 0,
                'sprite_count': len(sprite_bounds),
                'confidence': 'low' if is_irregular_collection else 'medium',
                'method': f'ccl_enhanced_{chosen_method.replace("-", "_")}',
                'note': f'{"IRREGULAR COLLECTION" if is_irregular_collection else "RPG sprite sheet"}: {chosen_method} size',
                'irregular_collection': is_irregular_collection,
                'ccl_sprite_bounds': sprite_bounds,
                'size_alternatives': {
                    'mode': (common_width, common_height),
                    'median': (int(np.median(widths)), int(np.median(heights))),
                    'average': (avg_width, avg_height),
                    'top_sizes': top_3_sizes[:3]
                }
            }

    debug_log.append("CCL Failed: layout too irregular or insufficient sprites")
    return {'success': False, 'method': 'ccl_enhanced'}


# ============================================================================
# CCL Extractor Class (for backward compatibility)
# ============================================================================

class CCLExtractor:
    """
    Connected Component Labeling extractor class.
    Provides object-oriented interface for CCL sprite extraction.
    """

    def __init__(self):
        """Initialize CCL extractor."""
        pass

    def extract_sprites(self, sprite_sheet):
        """
        Extract sprites from sprite sheet using CCL.

        Args:
            sprite_sheet: QPixmap sprite sheet

        Returns:
            Tuple of (sprites_list, info_string)
        """
        temp_path = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                temp_path = tmp_file.name

            # Save sprite sheet to temp file
            if not sprite_sheet.save(temp_path, 'PNG'):
                return [], "Failed to save sprite sheet for CCL processing"

            # Run CCL detection
            ccl_result = detect_sprites_ccl_enhanced(temp_path)

            # Ensure we got a dictionary result
            if not isinstance(ccl_result, dict):
                return [], f"CCL detection returned unexpected type: {type(ccl_result)}"

            if ccl_result and ccl_result.get('success', False):
                sprite_bounds = ccl_result.get('ccl_sprite_bounds', [])
                sprite_count = len(sprite_bounds)

                if sprite_count >= 2:
                    # Create list of individual sprite QPixmaps
                    sprites = []
                    for x, y, w, h in sprite_bounds:
                        sprite_pixmap = sprite_sheet.copy(x, y, w, h)
                        sprites.append(sprite_pixmap)

                    info_string = f"CCL detected {sprite_count} sprites"
                    return sprites, info_string
                else:
                    return [], f"CCL detected only {sprite_count} sprites (need at least 2)"
            else:
                error_msg = ccl_result.get('error', 'Unknown error') if ccl_result else 'No result returned'
                return [], f"CCL detection failed: {error_msg}"

        except Exception as e:
            return [], f"CCL extraction error: {e!s}"

        finally:
            # Clean up temporary file - guaranteed to run on all exit paths
            if temp_path is not None:
                with contextlib.suppress(OSError):
                    os.unlink(temp_path)
