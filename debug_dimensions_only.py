#!/usr/bin/env python3
"""
Ultra-simple debug script to get image dimensions using file command
and analyze detection logic without any Python image dependencies.
"""

import subprocess
import re
from pathlib import Path

# Copy of relevant config values
BASE_SIZES = [8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128, 160, 192, 256]
COMMON_ASPECT_RATIOS = [
    (1, 1),   # Square: 32×32, 64×64
    (1, 2),   # Tall: 16×32, 32×64, 48×96
    (2, 1),   # Wide: 32×16, 64×32, 96×48
    (2, 3),   # Character: 32×48, 64×96
    (3, 2),   # Wide char: 48×32, 96×64
    (3, 4),   # Portrait: 48×64, 72×96
    (4, 3),   # Landscape: 64×48, 96×72
]

def get_image_dimensions(filepath):
    """Get image dimensions using file command."""
    try:
        result = subprocess.run(['file', str(filepath)], capture_output=True, text=True)
        output = result.stdout
        
        # Look for dimension patterns like "1024 x 64" or "1024x64"
        patterns = [
            r'(\d+)\s*x\s*(\d+)',  # "1024 x 64"
            r'(\d+)×(\d+)',         # "1024×64"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                return width, height
        
        return None, None
    except Exception as e:
        print(f"Error getting dimensions for {filepath}: {e}")
        return None, None

def analyze_detection_potential(width, height, filename):
    """Analyze if the current detection algorithm could work on this sprite."""
    print(f"\n=== {filename} ===")
    print(f"Dimensions: {width}×{height}")
    
    if width is None or height is None:
        print("❌ Could not determine dimensions")
        return False
    
    aspect_ratio = width / height
    print(f"Aspect ratio: {aspect_ratio:.2f}")
    
    # Check horizontal strip qualification
    is_horizontal_strip = aspect_ratio > 3.0
    print(f"Horizontal strip candidate: {'Yes' if is_horizontal_strip else 'No'}")
    
    possible_configs = []
    
    # Test BASE_SIZES × ASPECT_RATIOS (standard detection)
    for base_size in BASE_SIZES:
        for width_ratio, height_ratio in COMMON_ASPECT_RATIOS:
            frame_width = base_size * width_ratio
            frame_height = base_size * height_ratio
            
            if frame_width <= width and frame_height <= height:
                frames_x = width // frame_width
                frames_y = height // frame_height
                total_frames = frames_x * frames_y
                
                if 2 <= total_frames <= 200:
                    utilization = (frames_x * frame_width * frames_y * frame_height) / (width * height)
                    possible_configs.append({
                        'frame_size': (frame_width, frame_height),
                        'grid': (frames_x, frames_y),
                        'total_frames': total_frames,
                        'utilization': utilization,
                        'aspect_ratio': f"{width_ratio}:{height_ratio}"
                    })
    
    possible_configs.sort(key=lambda x: x['utilization'], reverse=True)
    
    print(f"Standard detection: {len(possible_configs)} configs found")
    if possible_configs:
        best = possible_configs[0]
        print(f"  Best: {best['frame_size'][0]}×{best['frame_size'][1]} → {best['grid'][0]}×{best['grid'][1]} = {best['total_frames']} frames ({best['utilization']:.1%})")
    
    # Test horizontal strip detection
    strip_configs = []
    if is_horizontal_strip:
        for frames_count in range(2, 21):
            if width % frames_count == 0:
                frame_width = width // frames_count
                frame_height = height
                strip_configs.append({
                    'frame_size': (frame_width, frame_height),
                    'frames_count': frames_count
                })
        
        print(f"Strip detection: {len(strip_configs)} configs found")
        if strip_configs:
            for config in strip_configs[:3]:  # Show first 3
                print(f"  {config['frame_size'][0]}×{config['frame_size'][1]} × {config['frames_count']} frames")
    
    total_configs = len(possible_configs) + len(strip_configs)
    detectable = total_configs > 0
    
    print(f"Result: {'✅ Detectable' if detectable else '❌ Not detectable'} ({total_configs} total configs)")
    
    return detectable

def main():
    """Test detection analysis on sprite files."""
    
    sprites = [
        "spritetests/Archer_Run.png",
        "spritetests/Lancer_Run.png", 
        "spritetests/Lancer_Idle.png",
        "spritetests/test_sprite_sheet.png"
    ]
    
    print("🔍 Sprite Detection Analysis (Dimensions Only)")
    print("=" * 60)
    
    results = {}
    for sprite_path in sprites:
        if Path(sprite_path).exists():
            width, height = get_image_dimensions(sprite_path)
            detectable = analyze_detection_potential(width, height, Path(sprite_path).name)
            results[sprite_path] = detectable
        else:
            print(f"❌ File not found: {sprite_path}")
            results[sprite_path] = False
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    for sprite_path, detectable in results.items():
        status = "✅ Should work" if detectable else "❌ Algorithm limitation"
        print(f"  {Path(sprite_path).name}: {status}")

if __name__ == "__main__":
    main()