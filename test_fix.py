#!/usr/bin/env python3
"""
Test the improved scoring fix on Lancer sprites.
"""

import math

# Updated scoring function with the fix
def calculate_frame_score_fixed(width, height, frame_count, sheet_width, sheet_height, offset_x=0, offset_y=0, is_horizontal_strip=False):
    """Updated scoring function with horizontal strip improvements."""
    score = 0
    
    # Frame count reasonableness
    MIN_REASONABLE_FRAMES = 2
    MAX_REASONABLE_FRAMES = 200
    OPTIMAL_FRAME_COUNT_MIN = 4
    OPTIMAL_FRAME_COUNT_MAX = 32
    
    if MIN_REASONABLE_FRAMES <= frame_count <= MAX_REASONABLE_FRAMES:
        score += 100
        
        if OPTIMAL_FRAME_COUNT_MIN <= frame_count <= OPTIMAL_FRAME_COUNT_MAX:
            score += 30
        
        if frame_count > 50 and not is_horizontal_strip:
            score -= min(50, (frame_count - 50) * 2)
    
    available_width = sheet_width - offset_x
    available_height = sheet_height - offset_y
    
    # Dimension matching bonus
    if width == available_width or height == available_height:
        score += 100
    elif width == available_height or height == available_width:
        score += 80
    
    if available_width % width == 0 and available_height % height == 0:
        score += 60
    
    # Size appropriateness
    if 8 <= width <= 512 and 8 <= height <= 512:
        score += 60
        
        if (width & (width - 1)) == 0 and (height & (height - 1)) == 0:
            score += 20
        
        common_sizes = [16, 24, 32, 48, 64, 96, 128, 160, 192, 256]
        if width in common_sizes or height in common_sizes:
            score += 30
    
    # IMPROVED: Horizontal strip bonuses
    if is_horizontal_strip:
        score += 80  # Base horizontal strip bonus
        
        # NEW: Strongly prioritize typical animation frame counts
        if 8 <= frame_count <= 16:  # Very common animation frame counts
            score += 60  # Strong bonus for very typical frame counts
        elif 6 <= frame_count <= 24:  # Common animation frame counts
            score += 40  # Bonus for typical animation frame counts
        elif 4 <= frame_count <= 32:
            score += 20  # Smaller bonus for extended range
        
        # REDUCED: Square frame bias for horizontal strips
        if width == height and height == available_height:
            score += 30  # Reduced from 60 to prevent square frame dominance
    
    # Aspect ratio handling
    COMMON_ASPECT_RATIOS = [(1, 1), (1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3)]
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
        if rows == 1:
            score += 60  # Major bonus for single-row strips
        elif rows <= 3:
            score += 30
    else:
        if 2 <= cols <= 8 and 2 <= rows <= 8:
            score += 40
        elif cols >= 2 and rows >= 2:
            score += 20
        
        if cols > 10 and rows > 10:
            score -= 30
    
    # Space utilization bonus
    if available_width % width == 0 and available_height % height == 0:
        if True:  # Perfect utilization for clean divisors
            score += 80
    
    return score

def test_lancer_with_fix():
    """Test the fix on Lancer_Run."""
    sheet_width, sheet_height = 1920, 320
    print(f"Testing Lancer_Run ({sheet_width}×{sheet_height}) with fix...")
    
    # Test the two competing configurations:
    # 1. Square frames: 320×320 → 6×1 = 6 frames 
    # 2. Correct frames: 160×320 → 12×1 = 12 frames
    
    square_score = calculate_frame_score_fixed(320, 320, 6, sheet_width, sheet_height, is_horizontal_strip=True)
    correct_score = calculate_frame_score_fixed(160, 320, 12, sheet_width, sheet_height, is_horizontal_strip=True)
    
    print(f"Square frames (320×320, 6 frames): {square_score}")
    print(f"Correct frames (160×320, 12 frames): {correct_score}")
    
    if correct_score > square_score:
        print("✅ Fix successful! Correct frames now score higher.")
        print(f"   Improvement: +{correct_score - square_score} points")
    else:
        print("❌ Fix failed. Square frames still score higher.")
        print(f"   Deficit: -{square_score - correct_score} points")
    
    return correct_score > square_score

def main():
    """Test the fix."""
    print("🔧 Testing Auto-Detection Fix")
    print("=" * 50)
    
    success = test_lancer_with_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Fix successful! Lancer sprites should now detect correctly.")
    else:
        print("⚠️  Fix needs more adjustment.")

if __name__ == "__main__":
    main()