"""
Background Color Detection Module
================================

Detects background colors in sprite sheets for transparency application.
"""


import numpy as np
from PIL import Image


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
        # Load image as RGBA numpy array
        img = Image.open(image_path).convert('RGBA')
        img_array = np.array(img)

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
        from scipy import ndimage
        _labeled_array, num_components = ndimage.label(sprite_mask.astype(np.uint8))

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
