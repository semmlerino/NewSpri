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

from typing import Optional, List, Tuple
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
            import tempfile
            import os
            
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
            return [], f"CCL extraction error: {str(e)}"


def detect_sprites_ccl_enhanced(image_path: str) -> Optional[dict]:
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
        log_msg = f"🔬 CCL Detection starting on: {image_path}"
        debug_log.append(log_msg)
        print(log_msg)
        
        # Load image as RGBA numpy array
        img = Image.open(image_path).convert('RGBA')
        img_array = np.array(img)
        log_msg = f"   📁 Loaded image: {img_array.shape} (height, width, channels)"
        debug_log.append(log_msg)
        print(log_msg)
        
        # Create binary mask based on alpha channel
        alpha_channel = img_array[:, :, 3]
        binary_mask = (alpha_channel > 128).astype(np.uint8)
        opaque_pixels = np.sum(binary_mask)
        total_pixels = binary_mask.size
        alpha_transparency_ratio = 100 * opaque_pixels / total_pixels
        log_msg = f"   🎭 Alpha mask: {opaque_pixels}/{total_pixels} opaque pixels ({alpha_transparency_ratio:.1f}%)"
        debug_log.append(log_msg)
        print(log_msg)
        
        # For CCL, we always use alpha channel for initial detection
        # Background color will be detected separately and applied during extraction
        log_msg = f"   🔬 Using alpha channel for sprite boundary detection"
        debug_log.append(log_msg)
        print(log_msg)
        
        # If image is mostly/completely opaque, try color key detection for sprite boundaries
        if alpha_transparency_ratio > 95:  # Less than 5% alpha transparency
            debug_log.append(f"   🔍 Solid image detected ({alpha_transparency_ratio:.1f}% opaque), using color key for boundaries...")
            print(f"   🔍 Solid image detected, using color key for boundaries...")
            
            # Use color key detection for sprite boundaries (not for transparency yet)
            color_key_result = _detect_color_key_mask(img_array, debug_log)
            if color_key_result is not None:
                color_key_mask, background_color, color_tolerance = color_key_result
                binary_mask = color_key_mask
                opaque_pixels = np.sum(binary_mask)
                log_msg = f"   🎨 Color key boundaries: {opaque_pixels}/{total_pixels} sprite pixels ({100*opaque_pixels/total_pixels:.1f}%)"
                debug_log.append(log_msg)
                print(log_msg)
            else:
                debug_log.append(f"   ❌ No suitable color key found, using alpha channel")
                print(f"   ❌ No suitable color key found, using alpha channel")
        
        # Label connected components
        labeled_array, num_features = ndimage.label(binary_mask)
        log_msg = f"   🔗 Found {num_features} connected components"
        debug_log.append(log_msg)
        print(log_msg)
        
        if num_features == 0:
            log_msg = "   ❌ No connected components found"
            debug_log.append(log_msg)
            print(log_msg)
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
                debug_log.append(f"   ✅ Component {i+1}: ({x_start}, {y_start}) {width}×{height}")
            else:
                debug_log.append(f"   🗑️ Component {i+1}: FILTERED (too small: {width}×{height})")
        
        log_msg = f"   📊 Valid components: {len(sprite_bounds)}"
        debug_log.append(log_msg)
        print(log_msg)
        
        # Pre-analyze for irregular collections before merging
        widths = [w for x, y, w, h in sprite_bounds]
        heights = [h for x, y, w, h in sprite_bounds]
        np.mean(widths)
        np.mean(heights)
        width_std = np.std(widths)
        height_std = np.std(heights)
        
        # Check if this is an irregular sprite collection (high diversity + many sprites)
        size_range_w = max(widths) - min(widths)
        size_range_h = max(heights) - min(heights)
        size_diversity = (width_std + height_std) / 2
        
        small_sprites = [(w, h) for w, h in zip(widths, heights) if w < 24 or h < 24]
        medium_sprites = [(w, h) for w, h in zip(widths, heights) if 24 <= w <= 64 and 24 <= h <= 64]
        
        is_irregular_collection = (
            len(sprite_bounds) > 50 and  # Many sprites (lowered threshold)
            (size_diversity > 10 or       # High size variation OR
             (size_range_w > min(widths) * 3 or size_range_h > min(heights) * 3) or  # Wide size range OR
             len(small_sprites) > 20 or   # Many small sprites OR
             len(sprite_bounds) > 200)    # Very high sprite count
        )
        
        debug_log.append(f"   🎮 Pre-merge analysis: {len(sprite_bounds)} sprites, diversity={size_diversity:.1f}, range={size_range_w}×{size_range_h}")
        debug_log.append(f"   🎮 Sprite mix: {len(small_sprites)} small, {len(medium_sprites)} medium")
        debug_log.append(f"   🎮 Detection criteria: >50 sprites? {len(sprite_bounds) > 50}, diversity>10? {size_diversity > 10}, range>3x? {size_range_w > min(widths) * 3 or size_range_h > min(heights) * 3}, small>20? {len(small_sprites) > 20}, count>200? {len(sprite_bounds) > 200}")
        debug_log.append(f"   🎮 Irregular collection: {is_irregular_collection}")
        print(f"   🎮 Pre-merge analysis: {len(sprite_bounds)} sprites, diversity={size_diversity:.1f}, irregular={is_irregular_collection}")
        print(f"   🎮 Criteria check: sprites>50:{len(sprite_bounds) > 50}, diversity>10:{size_diversity > 10}, small>20:{len(small_sprites) > 20}")
        
        if is_irregular_collection:
            # For irregular collections (sprite atlases), disable merging entirely
            # These are individual sprites that should NOT be combined
            merge_threshold = 0  # No merging - keep all sprites separate
            debug_log.append(f"   🚫 Irregular collection detected - DISABLING sprite merging")
            print(f"   🚫 Irregular collection - NO MERGING (keeping {len(sprite_bounds)} individual sprites)")
            merged_bounds = sprite_bounds  # Use original bounds without merging
        else:
            # For regular sprite sheets, allow merging of multi-part sprites
            merge_threshold = 15  # Merge sprites within 15 pixels of each other
            debug_log.append(f"   🔗 Regular sprite sheet detected - merging nearby components (threshold: {merge_threshold}px)")
            print(f"   🔗 Regular collection - merging nearby sprites (threshold: {merge_threshold}px)")
            merged_bounds = _merge_nearby_components(sprite_bounds, merge_threshold, debug_log)
        
        log_msg = f"   🔀 After merging: {len(merged_bounds)} sprites"
        debug_log.append(log_msg)
        print(log_msg)
        
        # Analyze merged sprites and suggest frame settings
        debug_log.append(f"   🔍 Starting analysis of {len(merged_bounds)} merged sprites...")
        print(f"   🔍 Starting analysis of {len(merged_bounds)} merged sprites...")
        
        analysis_result = _analyze_ccl_results(merged_bounds, img_array.shape[1], img_array.shape[0], debug_log)
        if analysis_result.get('success', False):
            return analysis_result
        
        log_msg = f"   ❌ CCL Failed: layout too irregular or insufficient sprites"
        debug_log.append(log_msg)
        print(log_msg)
        return {'success': False, 'method': 'ccl_enhanced'}

    except Exception as e:
        error_msg = f"   💥 CCL Detection Error: {str(e)}"
        debug_log.append(error_msg)
        print(error_msg)
        return {'success': False, 'method': 'ccl_enhanced', 'error': str(e), 'debug_log': debug_log}


def _merge_nearby_components(sprite_bounds: List[Tuple[int, int, int, int]], 
                           threshold: int, debug_log: List[str] = None) -> List[Tuple[int, int, int, int]]:
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


def _analyze_ccl_results(sprite_bounds: List[Tuple[int, int, int, int]], 
                        sheet_width: int, sheet_height: int, debug_log: List[str] = None) -> dict:
    """Analyze CCL results and suggest frame settings."""
    if debug_log is None:
        debug_log = []
        
    log_msg = f"   📐 Analyzing {len(sprite_bounds)} sprites for layout..."
    debug_log.append(log_msg)
    print(log_msg)
    
    if not sprite_bounds:
        log_msg = "   ❌ No sprites to analyze"
        debug_log.append(log_msg)
        print(log_msg)
        return {'success': False, 'method': 'ccl_enhanced'}
    
    # Calculate statistics
    widths = [w for x, y, w, h in sprite_bounds]
    heights = [h for x, y, w, h in sprite_bounds]
    
    avg_width = int(np.mean(widths))
    avg_height = int(np.mean(heights))
    width_std = np.std(widths)
    height_std = np.std(heights)
    
    log_msg = f"   📊 Size analysis:"
    debug_log.append(log_msg)
    print(log_msg)
    log_msg = f"      Average: {avg_width}×{avg_height}"
    debug_log.append(log_msg)
    print(log_msg)
    log_msg = f"      Variation: ±{width_std:.1f}×±{height_std:.1f}"
    debug_log.append(log_msg)
    print(log_msg)
    log_msg = f"      Range: {min(widths)}-{max(widths)} × {min(heights)}-{max(heights)}"
    debug_log.append(log_msg)
    print(log_msg)
    
    # Check if layout is regular (increased tolerance for Lancer-style sprites)
    uniform_size = width_std < 8 and height_std < 8
    log_msg = f"   🎯 Uniform size check: width_std={width_std:.2f} < 8px? {width_std < 8}"
    debug_log.append(log_msg)
    print(log_msg)
    log_msg = f"   🎯 Uniform size check: height_std={height_std:.2f} < 8px? {height_std < 8}"
    debug_log.append(log_msg)
    print(log_msg)
    log_msg = f"   🎯 Uniform size result: {uniform_size} (both must be < 8px)"
    debug_log.append(log_msg)
    print(log_msg)
    
    # Debug sprite count threshold
    log_msg = f"   🎯 Sprite count: {len(sprite_bounds)} >= 2? {len(sprite_bounds) >= 2}"
    debug_log.append(log_msg)
    print(log_msg)
    
    # Show what path we're taking
    if uniform_size and len(sprite_bounds) >= 2:
        log_msg = f"   ✅ Taking SUCCESS path: uniform_size={uniform_size} and count={len(sprite_bounds)}>=2"
        debug_log.append(log_msg)
        print(log_msg)
    else:
        log_msg = f"   ❌ Taking FAILURE path: uniform_size={uniform_size} or count={len(sprite_bounds)}<2"
        debug_log.append(log_msg)
        print(log_msg)
    
    if uniform_size and len(sprite_bounds) >= 2:  # Lowered threshold from 4 to 2
        # Infer grid structure from sprite positions (not content bounds)
        sorted(sprite_bounds, key=lambda s: (s[1], s[0]))
        debug_log.append(f"   🗂️ Sorted sprites by position for grid analysis")
        
        # Extract sprite center positions
        centers_x = [x + w//2 for x, y, w, h in sprite_bounds]
        centers_y = [y + h//2 for x, y, w, h in sprite_bounds]
        debug_log.append(f"   🎯 Sprite centers: X={sorted(centers_x)}, Y={sorted(centers_y)}")
        
        # Group centers with tolerance (sprites in same row/col can be slightly offset)
        def group_positions(positions, tolerance=15):
            """Group similar positions within tolerance."""
            if not positions:
                return []
            sorted_pos = sorted(set(positions))
            groups = [[sorted_pos[0]]]
            for pos in sorted_pos[1:]:
                if pos - groups[-1][-1] <= tolerance:
                    groups[-1].append(pos)
                else:
                    groups.append([pos])
            return [sum(group) // len(group) for group in groups]  # Return group averages
        
        grouped_x = group_positions(centers_x, tolerance=15)
        
        # For Y grouping, detect obvious horizontal strips and use higher tolerance
        y_range = max(centers_y) - min(centers_y)
        avg_sprite_height = np.mean([h for x, y, w, h in sprite_bounds])
        
        # If Y variation is small relative to sprite height, it's likely a horizontal strip
        if y_range <= avg_sprite_height * 0.4:  # Y variation < 40% of sprite height
            grouped_y = [int(np.mean(centers_y))]  # Treat all as single row
            debug_log.append(f"   📐 Horizontal strip detected (Y range: {y_range:.1f}px ≤ {avg_sprite_height*0.4:.1f}px), forcing single row")
        else:
            grouped_y = group_positions(centers_y, tolerance=15)
            debug_log.append(f"   📐 Multi-row layout detected (Y range: {y_range:.1f}px > {avg_sprite_height*0.4:.1f}px)")
        cols = len(grouped_x)
        rows = len(grouped_y)
        debug_log.append(f"   🔗 Grouped centers: X={grouped_x}, Y={grouped_y}")
        debug_log.append(f"   📐 Grid structure: {cols}×{rows} (from center positions)")
        
        # Calculate frame size based on grid, not content bounds
        if cols > 1:
            frame_width = int(sheet_width / cols)
            debug_log.append(f"   📏 Frame width: {sheet_width}/{cols} = {frame_width}px")
        else:
            frame_width = sheet_width
            debug_log.append(f"   📏 Frame width: full width = {frame_width}px")
            
        if rows > 1:
            frame_height = int(sheet_height / rows)
            debug_log.append(f"   📏 Frame height: {sheet_height}/{rows} = {frame_height}px")
        else:
            frame_height = sheet_height
            debug_log.append(f"   📏 Frame height: full height = {frame_height}px")
        
        # Calculate margins from content bounds
        offset_x = min(x for x, y, w, h in sprite_bounds)
        offset_y = min(y for x, y, w, h in sprite_bounds)
        debug_log.append(f"   📍 Content margins: ({offset_x}, {offset_y})")
        
        # For grid-based extraction, use 0 spacing (frames are adjacent)
        spacing_x = 0
        spacing_y = 0
        debug_log.append(f"   ✅ Grid extraction: spacing=({spacing_x}, {spacing_y})")
        
        confidence = 'high' if cols * rows == len(sprite_bounds) else 'medium'
        debug_log.append(f"   🎯 Grid validation: {cols}×{rows}={cols*rows} vs {len(sprite_bounds)} sprites")
        
        result = {
            'success': True,
            'frame_width': frame_width,
            'frame_height': frame_height,
            'offset_x': 0,  # Grid starts at 0,0
            'offset_y': 0,
            'spacing_x': spacing_x,
            'spacing_y': spacing_y,
            'sprite_count': len(sprite_bounds),
            'confidence': confidence,
            'method': 'ccl_enhanced',
            'ccl_sprite_bounds': sprite_bounds,  # Store exact sprite boundaries for CCL mode
            'irregular_collection': False,  # Regular grid layout
            # Note: background_color_info will be detected separately
        }
        
        debug_log.append(f"   🎉 CCL Success: {frame_width}×{frame_height}, {len(sprite_bounds)} sprites, confidence: {confidence}")
        return result
    else:
        log_msg = f"   🔄 Uniform grid failed, trying irregular sprite analysis..."
        debug_log.append(log_msg)
        print(log_msg)
        
        # Fallback: Handle irregular sprite sheets (like Ark.png with many different sprite sizes)
        if len(sprite_bounds) >= 4:  # Need reasonable number of sprites for analysis
            log_msg = f"   📊 Irregular analysis: {len(sprite_bounds)} sprites detected"
            debug_log.append(log_msg)
            print(log_msg)
            
            # Find most common sprite size (mode)
            size_frequency = {}
            for w, h in zip(widths, heights):
                size_key = (w, h)
                size_frequency[size_key] = size_frequency.get(size_key, 0) + 1
            
            # Get most common size
            most_common_size = max(size_frequency.items(), key=lambda x: x[1])
            (common_width, common_height), frequency = most_common_size
            
            log_msg = f"   🎯 Most common size: {common_width}×{common_height} ({frequency}/{len(sprite_bounds)} sprites)"
            debug_log.append(log_msg)
            print(log_msg)
            
            # RPG-aware thresholds: very low for diverse character sprite sheets like Terranigma
            min_threshold = 0.02  # 2% minimum for RPG sprite sheets (handles extreme variety)
            common_percentage = frequency / len(sprite_bounds)
            
            log_msg = f"   🎮 RPG Analysis: {frequency}/{len(sprite_bounds)} = {common_percentage:.1%} (need ≥{min_threshold:.1%})"
            debug_log.append(log_msg)
            print(log_msg)
            
            if common_percentage >= min_threshold:
                log_msg = f"   ✅ Acceptable for RPG sprite sheet: {common_percentage:.1%} ≥ {min_threshold:.1%}"
                debug_log.append(log_msg)
                print(log_msg)
                
                # For RPG sheets, also provide size alternatives
                sorted_sizes = sorted(size_frequency.items(), key=lambda x: x[1], reverse=True)
                top_3_sizes = sorted_sizes[:3]
                
                log_msg = f"   📊 Top 3 sizes: {[(size, count) for size, count in top_3_sizes]}"
                debug_log.append(log_msg)
                print(log_msg)
                
                # Detect if this is an irregular sprite collection vs regular animation frames
                # Look for high size diversity and large sprite count
                size_range_w = max(widths) - min(widths)
                size_range_h = max(heights) - min(heights)
                size_diversity = (width_std + height_std) / 2
                
                # Check for mixed sprite types (small effects + medium characters + large objects)
                small_sprites = [(w, h) for w, h in zip(widths, heights) if w < 24 or h < 24]
                medium_sprites = [(w, h) for w, h in zip(widths, heights) if 24 <= w <= 64 and 24 <= h <= 64]
                large_sprites = [(w, h) for w, h in zip(widths, heights) if w > 64 or h > 64]
                
                # This is an irregular collection if:
                # 1. Many sprites (>50) with high diversity
                # 2. Wide size range (>3x difference)
                # 3. Mixed sprite categories
                is_irregular_collection = (
                    len(sprite_bounds) > 50 and 
                    size_diversity > 10 and
                    (size_range_w > min(widths) * 3 or size_range_h > min(heights) * 3) and
                    len(small_sprites) > 5 and len(medium_sprites) > 5
                )
                
                log_msg = f"   🔍 Collection analysis: diversity={size_diversity:.1f}, range={size_range_w}×{size_range_h}, sprites={len(small_sprites)}S+{len(medium_sprites)}M+{len(large_sprites)}L"
                debug_log.append(log_msg)
                print(log_msg)
                
                log_msg = f"   🎮 Irregular collection: {is_irregular_collection} (need: >50 sprites, >10 diversity, >3x range, mixed sizes)"
                debug_log.append(log_msg) 
                print(log_msg)
                
                if is_irregular_collection:
                    # This is an irregular sprite collection - grid extraction won't work well
                    log_msg = f"   ⚠️  IRREGULAR COLLECTION DETECTED"
                    debug_log.append(log_msg)
                    print(log_msg)
                    
                    log_msg = f"   📝 This appears to be a sprite atlas/collection with {len(sprite_bounds)} individual sprites"
                    debug_log.append(log_msg)
                    print(log_msg)
                    
                    log_msg = f"   🚫 Regular grid extraction will NOT align properly with these sprites"
                    debug_log.append(log_msg)
                    print(log_msg)
                    
                    log_msg = f"   💡 CCL detected exact boundaries for each sprite - individual extraction needed"
                    debug_log.append(log_msg)
                    print(log_msg)
                    
                    # Still provide a "best effort" frame size for those who want to try
                    char_sprites = [(w, h) for w, h in zip(widths, heights) if 20 <= w <= 80 and 20 <= h <= 80]
                    if len(char_sprites) >= 10:
                        char_median_w = int(np.median([w for w, h in char_sprites]))
                        char_median_h = int(np.median([h for w, h in char_sprites]))
                        chosen_width, chosen_height = char_median_w, char_median_h
                        chosen_method = "best_effort_warning"
                        
                        log_msg = f"   🎯 Best-effort size: {chosen_width}×{chosen_height} (median of {len(char_sprites)} character-sized sprites)"
                        debug_log.append(log_msg)
                        print(log_msg)
                        
                        log_msg = f"   ⚠️  WARNING: This size is unlikely to extract sprites correctly!"
                        debug_log.append(log_msg)
                        print(log_msg)
                    else:
                        # Even more conservative fallback
                        chosen_width, chosen_height = 48, 48  # Safe default
                        chosen_method = "fallback_warning"
                        
                        log_msg = f"   🎯 Fallback size: {chosen_width}×{chosen_height} (standard game sprite size)"
                        debug_log.append(log_msg)
                        print(log_msg)
                        
                        log_msg = f"   ⚠️  WARNING: Grid extraction not recommended for this sprite type!"
                        debug_log.append(log_msg)
                        print(log_msg)
                else:
                    # Original RPG character sheet logic
                    median_width = int(np.median(widths))
                    median_height = int(np.median(heights))
                    
                    if abs(median_width - common_width) <= 10 and abs(median_height - common_height) <= 10:
                        chosen_width, chosen_height = common_width, common_height
                        chosen_method = "mode"
                    else:
                        chosen_width, chosen_height = median_width, median_height
                        chosen_method = "median"
                
                log_msg = f"   📐 Size options: Mode={common_width}×{common_height}, Avg={avg_width}×{avg_height}"
                debug_log.append(log_msg)
                print(log_msg)
                
                log_msg = f"   🎯 Chosen size: {chosen_width}×{chosen_height} ({chosen_method})"
                debug_log.append(log_msg)
                print(log_msg)
                
                result = {
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
                    'note': f'{"IRREGULAR COLLECTION - Grid extraction not recommended" if is_irregular_collection else "RPG sprite sheet"}: {chosen_method} size from {len(sprite_bounds)} varied sprites',
                    'irregular_collection': is_irregular_collection,
                    'ccl_sprite_bounds': sprite_bounds,  # Store exact sprite boundaries for CCL mode
                    # Note: background_color_info will be detected separately
                    'size_alternatives': {
                        'mode': (common_width, common_height),
                        'median': (int(np.median(widths)), int(np.median(heights))), 
                        'average': (avg_width, avg_height),
                        'top_sizes': top_3_sizes[:3]
                    }
                }
                
                if is_irregular_collection:
                    success_type = "Irregular Collection (WARNING)"
                    log_msg = f"   ⚠️  CCL {success_type}: {chosen_width}×{chosen_height}, {len(sprite_bounds)} sprites, {chosen_method}"
                else:
                    success_type = "RPG Character"
                    log_msg = f"   🎉 CCL {success_type} Success: {chosen_width}×{chosen_height}, {len(sprite_bounds)} sprites, {chosen_method}-based"
                debug_log.append(log_msg)
                print(log_msg)
                return result
            else:
                log_msg = f"   ❌ Too irregular even for RPG: {common_percentage:.1%} < {min_threshold:.1%}"
                debug_log.append(log_msg)
                print(log_msg)
        
        log_msg = f"   ❌ CCL Failed: layout too irregular or insufficient sprites"
        debug_log.append(log_msg)
        print(log_msg)
        return {'success': False, 'method': 'ccl_enhanced'}