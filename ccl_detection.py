#!/usr/bin/env python3
"""
Connected-Component Labeling (CCL) sprite detection implementation.
Uses computer vision techniques to find exact sprite boundaries.
"""

import numpy as np
from PIL import Image
from scipy import ndimage
from typing import List, Tuple, Optional
import math

def detect_sprites_ccl(image_path: str, min_sprite_size: int = 8, alpha_threshold: int = 128, merge_threshold: int = 50) -> List[Tuple[int, int, int, int]]:
    """
    Detect individual sprites using Connected-Component Labeling.
    
    Args:
        image_path: Path to sprite sheet image
        min_sprite_size: Minimum size (width or height) for a valid sprite
        alpha_threshold: Alpha value threshold for opacity (0-255)
        merge_threshold: Distance threshold for merging nearby components (pixels)
    
    Returns:
        List of (x, y, width, height) tuples for each detected sprite
    """
    
    # Step 1: Load image as RGBA numpy array
    try:
        img = Image.open(image_path).convert('RGBA')
        img_array = np.array(img)
        print(f"Loaded image: {img_array.shape} (height, width, channels)")
    except Exception as e:
        print(f"Error loading image: {e}")
        return []
    
    # Step 2: Create binary mask based on alpha channel
    alpha_channel = img_array[:, :, 3]  # Extract alpha channel
    binary_mask = (alpha_channel > alpha_threshold).astype(np.uint8)
    
    print(f"Created binary mask: {np.sum(binary_mask)} opaque pixels out of {binary_mask.size}")
    
    # Step 3: Label connected components
    labeled_array, num_features = ndimage.label(binary_mask)
    print(f"Found {num_features} connected components")
    
    # Step 4: Extract bounding boxes for each component
    sprite_bounds = []
    objects = ndimage.find_objects(labeled_array)
    
    for i, obj in enumerate(objects):
        if obj is None:
            continue
            
        # Extract slice coordinates
        y_slice, x_slice = obj
        y_start, y_end = y_slice.start, y_slice.stop
        x_start, x_end = x_slice.start, x_slice.stop
        
        width = x_end - x_start
        height = y_end - y_start
        
        # Filter out tiny components (noise, single pixels, etc.)
        if width >= min_sprite_size and height >= min_sprite_size:
            sprite_bounds.append((x_start, y_start, width, height))
            print(f"  Component {i+1}: ({x_start}, {y_start}) {width}×{height}")
        else:
            print(f"  Component {i+1}: FILTERED (too small: {width}×{height})")
    
    # Step 5: Merge nearby components (for multi-part sprites)
    merged_bounds = merge_nearby_components(sprite_bounds, merge_threshold)
    
    print(f"After merging nearby components: {len(merged_bounds)} sprites")
    print(f"Final result: {len(merged_bounds)} valid sprites detected")
    return merged_bounds

def merge_nearby_components(sprite_bounds: List[Tuple[int, int, int, int]], 
                           merge_threshold: int) -> List[Tuple[int, int, int, int]]:
    """
    Merge nearby sprite components that likely belong to the same sprite.
    Useful for multi-part characters (body + weapon, etc.)
    """
    if len(sprite_bounds) <= 1:
        return sprite_bounds
    
    # Convert to list for easier manipulation
    components = list(sprite_bounds)
    merged = []
    used = set()
    
    for i, (x1, y1, w1, h1) in enumerate(components):
        if i in used:
            continue
        
        # Find nearby components to merge with this one
        merge_group = [(x1, y1, w1, h1)]
        used.add(i)
        
        for j, (x2, y2, w2, h2) in enumerate(components):
            if j in used:
                continue
            
            # Check if components are close enough to merge
            # Consider both horizontal and vertical proximity
            center_x1, center_y1 = x1 + w1//2, y1 + h1//2
            center_x2, center_y2 = x2 + w2//2, y2 + h2//2
            
            distance = math.sqrt((center_x2 - center_x1)**2 + (center_y2 - center_y1)**2)
            
            # Also check if they're in the same general area (same "frame slot")
            horizontal_overlap = not (x1 + w1 < x2 - merge_threshold or x2 + w2 < x1 - merge_threshold)
            vertical_overlap = not (y1 + h1 < y2 - merge_threshold or y2 + h2 < y1 - merge_threshold)
            
            if distance < merge_threshold or (horizontal_overlap and vertical_overlap):
                merge_group.append((x2, y2, w2, h2))
                used.add(j)
        
        # Create bounding box for the merged group
        if merge_group:
            min_x = min(x for x, y, w, h in merge_group)
            min_y = min(y for x, y, w, h in merge_group)
            max_x = max(x + w for x, y, w, h in merge_group)
            max_y = max(y + h for x, y, w, h in merge_group)
            
            merged_width = max_x - min_x
            merged_height = max_y - min_y
            
            merged.append((min_x, min_y, merged_width, merged_height))
            
            if len(merge_group) > 1:
                print(f"  Merged {len(merge_group)} components into ({min_x}, {min_y}) {merged_width}×{merged_height}")
    
    return merged

def analyze_sprite_layout(sprite_bounds: List[Tuple[int, int, int, int]]) -> dict:
    """
    Analyze the detected sprites to determine layout characteristics.
    
    Args:
        sprite_bounds: List of (x, y, width, height) tuples
        
    Returns:
        Dictionary with layout analysis
    """
    if not sprite_bounds:
        return {}
    
    # Extract coordinates and dimensions
    x_coords = [x for x, y, w, h in sprite_bounds]
    y_coords = [y for x, y, w, h in sprite_bounds]
    widths = [w for x, y, w, h in sprite_bounds]
    heights = [h for x, y, w, h in sprite_bounds]
    
    analysis = {
        'sprite_count': len(sprite_bounds),
        'avg_width': np.mean(widths),
        'avg_height': np.mean(heights),
        'width_std': np.std(widths),
        'height_std': np.std(heights),
        'min_width': min(widths),
        'max_width': max(widths),
        'min_height': min(heights),
        'max_height': max(heights),
        'uniform_width': np.std(widths) < 2,  # Nearly identical widths
        'uniform_height': np.std(heights) < 2,  # Nearly identical heights
    }
    
    # Determine layout type
    if analysis['uniform_width'] and analysis['uniform_height']:
        analysis['layout_type'] = 'regular_grid'
    elif analysis['uniform_height']:
        analysis['layout_type'] = 'horizontal_strip'
    elif analysis['uniform_width']:
        analysis['layout_type'] = 'vertical_strip'
    else:
        analysis['layout_type'] = 'irregular'
    
    # Calculate grid dimensions for regular layouts
    if analysis['layout_type'] in ['regular_grid', 'horizontal_strip']:
        # Sort by Y then X to find grid structure
        sorted_sprites = sorted(sprite_bounds, key=lambda s: (s[1], s[0]))
        
        # Find number of columns (sprites with same Y coordinate)
        unique_y = sorted(set(y_coords))
        if len(unique_y) > 0:
            first_row_y = unique_y[0]
            cols = sum(1 for x, y, w, h in sprite_bounds if abs(y - first_row_y) < 5)
            rows = len(sprite_bounds) // cols if cols > 0 else 1
            
            analysis['grid_cols'] = cols
            analysis['grid_rows'] = rows
        else:
            analysis['grid_cols'] = len(sprite_bounds)
            analysis['grid_rows'] = 1
    
    return analysis

def suggest_frame_settings(sprite_bounds: List[Tuple[int, int, int, int]], 
                          sheet_width: int, sheet_height: int) -> Optional[dict]:
    """
    Suggest frame extraction settings based on CCL detection results.
    
    Args:
        sprite_bounds: Detected sprite boundaries
        sheet_width: Original sheet width
        sheet_height: Original sheet height
        
    Returns:
        Dictionary with suggested settings or None if no clear pattern
    """
    if not sprite_bounds:
        return None
    
    analysis = analyze_sprite_layout(sprite_bounds)
    
    if analysis['layout_type'] in ['regular_grid', 'horizontal_strip']:
        # For regular layouts, suggest uniform frame size
        suggested_width = int(analysis['avg_width'])
        suggested_height = int(analysis['avg_height'])
        
        # Calculate spacing and margins
        if len(sprite_bounds) >= 2:
            # Sort sprites for spacing calculation
            sorted_sprites = sorted(sprite_bounds, key=lambda s: (s[1], s[0]))
            
            # Calculate horizontal spacing
            spacing_x = 0
            if analysis.get('grid_cols', 1) > 1:
                for i in range(1, min(analysis.get('grid_cols', 1), len(sorted_sprites))):
                    prev_x, prev_y, prev_w, prev_h = sorted_sprites[i-1]
                    curr_x, curr_y, curr_w, curr_h = sorted_sprites[i]
                    if abs(curr_y - prev_y) < 5:  # Same row
                        spacing_x = max(spacing_x, curr_x - (prev_x + prev_w))
            
            # Calculate vertical spacing
            spacing_y = 0
            if analysis.get('grid_rows', 1) > 1:
                cols = analysis.get('grid_cols', 1)
                if len(sorted_sprites) > cols:
                    first_row_y = sorted_sprites[0][1]
                    second_row_y = sorted_sprites[cols][1]
                    first_row_h = sorted_sprites[0][3]
                    spacing_y = second_row_y - (first_row_y + first_row_h)
            
            # Calculate margins (offset from sheet edges)
            offset_x = min(x for x, y, w, h in sprite_bounds)
            offset_y = min(y for x, y, w, h in sprite_bounds)
            
            return {
                'frame_width': suggested_width,
                'frame_height': suggested_height,
                'offset_x': max(0, offset_x),
                'offset_y': max(0, offset_y),
                'spacing_x': max(0, spacing_x),
                'spacing_y': max(0, spacing_y),
                'detected_layout': analysis['layout_type'],
                'grid_cols': analysis.get('grid_cols', 1),
                'grid_rows': analysis.get('grid_rows', 1),
                'confidence': 'high' if analysis['uniform_width'] and analysis['uniform_height'] else 'medium'
            }
    
    # For irregular layouts, suggest bounding box approach
    return {
        'frame_width': int(analysis['avg_width']),
        'frame_height': int(analysis['avg_height']),
        'offset_x': 0,
        'offset_y': 0,
        'spacing_x': 0,
        'spacing_y': 0,
        'detected_layout': 'irregular',
        'individual_bounds': sprite_bounds,
        'confidence': 'low'
    }

def test_ccl_detection(image_path: str):
    """Test CCL detection on a sprite sheet."""
    print(f"\n🔍 Testing CCL Detection on {image_path}")
    print("=" * 60)
    
    # Detect sprites
    sprite_bounds = detect_sprites_ccl(image_path)
    
    if not sprite_bounds:
        print("❌ No sprites detected!")
        return
    
    # Analyze layout
    analysis = analyze_sprite_layout(sprite_bounds)
    print(f"\n📊 Layout Analysis:")
    print(f"  Layout type: {analysis.get('layout_type', 'unknown')}")
    print(f"  Sprite count: {analysis.get('sprite_count', 0)}")
    print(f"  Average size: {analysis.get('avg_width', 0):.1f}×{analysis.get('avg_height', 0):.1f}")
    print(f"  Size variation: ±{analysis.get('width_std', 0):.1f}×±{analysis.get('height_std', 0):.1f}")
    if 'grid_cols' in analysis:
        print(f"  Grid structure: {analysis['grid_cols']}×{analysis['grid_rows']}")
    
    # Get frame suggestions
    try:
        img = Image.open(image_path)
        suggestions = suggest_frame_settings(sprite_bounds, img.width, img.height)
        
        if suggestions:
            print(f"\n⚙️ Suggested Settings:")
            print(f"  Frame size: {suggestions['frame_width']}×{suggestions['frame_height']}")
            print(f"  Margins: ({suggestions['offset_x']}, {suggestions['offset_y']})")
            print(f"  Spacing: ({suggestions['spacing_x']}, {suggestions['spacing_y']})")
            print(f"  Confidence: {suggestions['confidence']}")
        else:
            print("❌ Could not generate frame settings suggestions")
            
    except Exception as e:
        print(f"Error getting suggestions: {e}")

def main():
    """Test CCL detection on various sprite sheets."""
    test_sprites = [
        "spritetests/Archer_Run.png",
        "spritetests/Lancer_Run.png",
        "spritetests/Lancer_Idle.png", 
        "spritetests/test_sprite_sheet.png"
    ]
    
    print("🧪 Connected-Component Labeling Sprite Detection Test")
    print("=" * 70)
    
    for sprite_path in test_sprites:
        try:
            test_ccl_detection(sprite_path)
        except Exception as e:
            print(f"❌ Error testing {sprite_path}: {e}")

if __name__ == "__main__":
    main()