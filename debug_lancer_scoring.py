#!/usr/bin/env python3
"""
Debug script to simulate the exact scoring logic for Lancer sprites
to understand why detection fails.
"""

import math

# Config constants
BASE_SIZES = [8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128, 160, 192, 256]
COMMON_ASPECT_RATIOS = [
    (1, 1), (1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3)
]
MIN_REASONABLE_FRAMES = 2
MAX_REASONABLE_FRAMES = 200
OPTIMAL_FRAME_COUNT_MIN = 4
OPTIMAL_FRAME_COUNT_MAX = 32

def calculate_frame_score(width, height, frame_count, sheet_width, sheet_height, offset_x=0, offset_y=0, is_horizontal_strip=False):
    """Simulate the exact _calculate_frame_score logic from sprite_model.py"""
    score = 0
    
    # Frame count reasonableness
    if MIN_REASONABLE_FRAMES <= frame_count <= MAX_REASONABLE_FRAMES:
        score += 100
        
        # Sweet spot for frame counts (moderate bonus)
        if OPTIMAL_FRAME_COUNT_MIN <= frame_count <= OPTIMAL_FRAME_COUNT_MAX:
            score += 30
        
        # Penalty for excessive frame counts (indicates frames too small)
        if frame_count > 50 and not is_horizontal_strip:
            score -= min(50, (frame_count - 50) * 2)
    
    available_width = sheet_width - offset_x
    available_height = sheet_height - offset_y
    
    # Dimension matching bonus
    if width == available_width or height == available_height:
        score += 100  # Major bonus for dimension matching
    elif width == available_height or height == available_width:
        score += 80   # Bonus for swapped dimension matching
    
    # Bonus for frames that are clean divisors of sheet dimensions
    if available_width % width == 0 and available_height % height == 0:
        score += 60   # Clean divisor bonus
    
    # Size appropriateness
    if 8 <= width <= 512 and 8 <= height <= 512:
        score += 60
        
        # Power-of-2 bonus
        if (width & (width - 1)) == 0 and (height & (height - 1)) == 0:
            score += 20
        
        # Common sizes bonus
        common_sizes = [16, 24, 32, 48, 64, 96, 128, 160, 192, 256]
        if width in common_sizes or height in common_sizes:
            score += 30
    
    # Horizontal strip bonuses
    if is_horizontal_strip:
        score += 80  # Significant bonus for horizontal strip detection
        
        # Extra bonus if frame is square and matches height
        if width == height and height == available_height:
            score += 60  # Perfect horizontal strip with square frames
    
    # Aspect ratio handling
    gcd_val = math.gcd(width, height)
    ratio_w = width // gcd_val
    ratio_h = height // gcd_val
    
    if (ratio_w, ratio_h) in COMMON_ASPECT_RATIOS:
        score += 40
    elif ratio_w == ratio_h:  # Square
        score += 25
    
    # Grid layout scoring
    cols = available_width // width
    rows = available_height // height
    
    if is_horizontal_strip:
        # For horizontal strips, prioritize single row
        if rows == 1:
            score += 60  # Major bonus for single-row strips
        elif rows <= 3:
            score += 30  # Bonus for few rows
    else:
        # Standard grid scoring for non-strips
        if 2 <= cols <= 8 and 2 <= rows <= 8:
            score += 40  # Good grid size
        elif cols >= 2 and rows >= 2:
            score += 20  # At least 2×2
        
        # Penalty for overly dense grids
        if cols > 10 and rows > 10:
            score -= 30
    
    # Space utilization bonus (simplified - assume perfect fit for clean divisors)
    if available_width % width == 0 and available_height % height == 0:
        utilization = 1.0  # Perfect utilization
        if utilization >= 0.95:
            score += 80
        elif utilization >= 0.85:
            score += 50
        elif utilization >= 0.70:
            score += 20
    
    return score

def test_lancer_detection(sheet_width, sheet_height, sprite_name):
    """Test all possible configurations for a Lancer sprite."""
    print(f"\n=== {sprite_name} ({sheet_width}×{sheet_height}) ===")
    
    aspect_ratio = sheet_width / sheet_height
    print(f"Aspect ratio: {aspect_ratio:.2f}")
    
    all_candidates = []
    
    # Test standard detection (BASE_SIZES × ASPECT_RATIOS)
    print("Testing standard detection...")
    for base_size in BASE_SIZES:
        for width_ratio, height_ratio in COMMON_ASPECT_RATIOS:
            frame_width = base_size * width_ratio
            frame_height = base_size * height_ratio
            
            if frame_width <= sheet_width and frame_height <= sheet_height:
                frames_x = sheet_width // frame_width
                frames_y = sheet_height // frame_height
                total_frames = frames_x * frames_y
                
                if MIN_REASONABLE_FRAMES <= total_frames <= MAX_REASONABLE_FRAMES:
                    score = calculate_frame_score(frame_width, frame_height, total_frames, 
                                                sheet_width, sheet_height, is_horizontal_strip=False)
                    
                    all_candidates.append({
                        'type': 'standard',
                        'frame_size': (frame_width, frame_height),
                        'grid': (frames_x, frames_y),
                        'total_frames': total_frames,
                        'score': score,
                        'aspect_ratio': f"{width_ratio}:{height_ratio}"
                    })
    
    # Test horizontal strip detection
    if aspect_ratio > 3.0:
        print("Testing horizontal strip detection...")
        
        # Method 1: frame_height = available_height
        frame_height = sheet_height
        for frames_count in range(2, 21):
            if sheet_width % frames_count == 0:
                frame_width = sheet_width // frames_count
                
                if 16 <= frame_width <= 512:  # Skip check from the algorithm
                    score = calculate_frame_score(frame_width, frame_height, frames_count,
                                                sheet_width, sheet_height, is_horizontal_strip=True)
                    
                    all_candidates.append({
                        'type': 'strip_method1',
                        'frame_size': (frame_width, frame_height),
                        'grid': (frames_count, 1),
                        'total_frames': frames_count,
                        'score': score,
                        'aspect_ratio': f"custom"
                    })
        
        # Method 2: common square sizes with full height
        for size in [16, 24, 32, 48, 64, 96, 128, 160, 192, 256]:
            if size <= sheet_height and size <= sheet_width:
                frames_count = sheet_width // size
                if frames_count >= 2:
                    score = calculate_frame_score(size, sheet_height, frames_count,
                                                sheet_width, sheet_height, is_horizontal_strip=True)
                    
                    all_candidates.append({
                        'type': 'strip_method2',
                        'frame_size': (size, sheet_height),
                        'grid': (frames_count, 1),
                        'total_frames': frames_count,
                        'score': score,
                        'aspect_ratio': f"square+full_height"
                    })
    
    # Sort by score
    all_candidates.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\nFound {len(all_candidates)} total candidates")
    print("Top 10 candidates by score:")
    
    for i, candidate in enumerate(all_candidates[:10]):
        print(f"  {i+1:2d}. {candidate['frame_size'][0]:3d}×{candidate['frame_size'][1]:3d} "
              f"({candidate['type']:15s}) → {candidate['grid'][0]:2d}×{candidate['grid'][1]:2d} "
              f"= {candidate['total_frames']:2d} frames, score: {candidate['score']:3.0f}")
    
    if all_candidates:
        best = all_candidates[0]
        print(f"\n🏆 Winner: {best['frame_size'][0]}×{best['frame_size'][1]} "
              f"({best['type']}) with score {best['score']}")
        
        # Check if this is reasonable for a Lancer sprite
        expected_frame_count = 12 if "Idle" in sprite_name else 6
        if best['total_frames'] != expected_frame_count:
            print(f"⚠️  Expected ~{expected_frame_count} frames, got {best['total_frames']}")
        
        return best
    else:
        print("❌ No candidates found!")
        return None

def main():
    """Test scoring on known problematic sprites."""
    
    # Test cases
    test_cases = [
        (768, 192, "Archer_Run"),    # Known working
        (1920, 320, "Lancer_Run"),   # Problematic  
        (3840, 320, "Lancer_Idle"),  # Problematic
        (256, 256, "test_sprite_sheet")  # Known working
    ]
    
    print("🔍 Lancer Detection Scoring Analysis")
    print("=" * 70)
    
    for width, height, name in test_cases:
        test_lancer_detection(width, height, name)
    
    print("\n" + "=" * 70)
    print("Analysis complete!")

if __name__ == "__main__":
    main()