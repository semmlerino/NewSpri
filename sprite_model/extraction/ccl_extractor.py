"""
Connected-Component Labeling (CCL) Extraction Module
===================================================

Advanced sprite detection using computer vision techniques.
Handles irregular sprite collections and complex sprite atlases.

Features:
- Connected-component analysis for sprite boundary detection
- Intelligent merging of multi-part sprites
- Irregular collection detection (sprite atlases vs. animation frames)
- Grid inference from sprite positions
"""


import numpy as np
from PIL import Image
from scipy import ndimage

from .background_detector import _detect_color_key_mask


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
        try:
            # Save QPixmap to temporary file for processing
            import os
            import tempfile

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                temp_path = tmp_file.name

            # Save sprite sheet to temp file
            if not sprite_sheet.save(temp_path, 'PNG'):
                return [], "Failed to save sprite sheet for CCL processing"

            try:
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

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except Exception as e:
            return [], f"CCL extraction error: {e!s}"


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

        # Load image as RGBA numpy array
        img = Image.open(image_path).convert('RGBA')
        img_array = np.array(img)
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
                color_key_mask, background_color, color_tolerance = color_key_result
                binary_mask = color_key_mask
                opaque_pixels = np.sum(binary_mask)
                debug_log.append(f"Color key boundaries: {opaque_pixels}/{total_pixels} sprite pixels")
            else:
                debug_log.append("No suitable color key found, using alpha channel")

        # Label connected components
        labeled_array, num_features = ndimage.label(binary_mask)
        debug_log.append(f"Found {num_features} connected components")

        if num_features == 0:
            debug_log.append("No connected components found")
            return {'success': False, 'debug_log': debug_log}

        # Extract bounding boxes
        objects = ndimage.find_objects(labeled_array)
        sprite_bounds = []

        for i, obj in enumerate(objects):
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
        widths = [w for x, y, w, h in sprite_bounds]
        heights = [h for x, y, w, h in sprite_bounds]
        width_std = np.std(widths)
        height_std = np.std(heights)

        # Check if this is an irregular sprite collection
        size_range_w = max(widths) - min(widths)
        size_range_h = max(heights) - min(heights)
        size_diversity = (width_std + height_std) / 2

        small_sprites = [(w, h) for w, h in zip(widths, heights) if w < 24 or h < 24]

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
                           threshold: int, debug_log: list[str] = None) -> list[tuple[int, int, int, int]]:
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
            min_x = min(x for x, y, w, h in merge_group)
            min_y = min(y for x, y, w, h in merge_group)
            max_x = max(x + w for x, y, w, h in merge_group)
            max_y = max(y + h for x, y, w, h in merge_group)
            merged_bounds = (min_x, min_y, max_x - min_x, max_y - min_y)
            merged.append(merged_bounds)

            if len(merge_group) > 1:
                merge_count += 1
                debug_log.append(f"      ✅ Group {i+1}: {len(merge_group)} parts → ({min_x}, {min_y}) {max_x - min_x}×{max_y - min_y}")

    debug_log.append(f"   🔀 Merging complete: {merge_count} groups merged, {len(merged)} final sprites")
    return merged


def _analyze_ccl_results(sprite_bounds: list[tuple[int, int, int, int]],
                        sheet_width: int, sheet_height: int, debug_log: list[str] = None) -> dict:
    """Analyze CCL results and suggest frame settings."""
    if debug_log is None:
        debug_log = []

    if not sprite_bounds:
        return {'success': False, 'method': 'ccl_enhanced'}

    # Calculate statistics
    widths = [w for x, y, w, h in sprite_bounds]
    heights = [h for x, y, w, h in sprite_bounds]
    avg_width = int(np.mean(widths))
    avg_height = int(np.mean(heights))
    width_std = np.std(widths)
    height_std = np.std(heights)

    debug_log.append(f"Analyzing {len(sprite_bounds)} sprites: avg={avg_width}x{avg_height}, std={width_std:.1f}x{height_std:.1f}")

    # Check if layout is regular
    uniform_size = width_std < 8 and height_std < 8

    if uniform_size and len(sprite_bounds) >= 2:
        # Infer grid structure from sprite positions
        centers_x = [x + w//2 for x, y, w, h in sprite_bounds]
        centers_y = [y + h//2 for x, y, w, h in sprite_bounds]

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
        avg_sprite_height = np.mean([h for x, y, w, h in sprite_bounds])

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
        for w, h in zip(widths, heights):
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

            small_sprites = [(w, h) for w, h in zip(widths, heights) if w < 24 or h < 24]
            medium_sprites = [(w, h) for w, h in zip(widths, heights) if 24 <= w <= 64 and 24 <= h <= 64]

            is_irregular_collection = (
                len(sprite_bounds) > 50 and
                size_diversity > 10 and
                (size_range_w > min(widths) * 3 or size_range_h > min(heights) * 3) and
                len(small_sprites) > 5 and len(medium_sprites) > 5
            )

            if is_irregular_collection:
                char_sprites = [(w, h) for w, h in zip(widths, heights) if 20 <= w <= 80 and 20 <= h <= 80]
                if len(char_sprites) >= 10:
                    chosen_width = int(np.median([w for w, h in char_sprites]))
                    chosen_height = int(np.median([h for w, h in char_sprites]))
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
