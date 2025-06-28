#!/usr/bin/env python3
"""
Simple debug script to analyze sprite dimensions and test detection logic
without requiring PySide6 dependencies.
"""

from PIL import Image
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

def analyze_sprite_dimensions(sprite_path):
    """Analyze sprite sheet dimensions and calculate possible frame configurations."""
    print(f"\n=== Analyzing {sprite_path} ===")
    
    try:
        # Load image
        img = Image.open(sprite_path)
        width, height = img.size
        aspect_ratio = width / height
        
        print(f"Sheet size: {width}×{height}")
        print(f"Sheet aspect ratio: {aspect_ratio:.2f}")
        print(f"Horizontal strip candidate: {'Yes' if aspect_ratio > 3.0 else 'No'}")
        
        # Test all base size + aspect ratio combinations
        print(f"\nTesting BASE_SIZES × ASPECT_RATIOS combinations:")
        possible_configs = []
        
        for base_size in BASE_SIZES:
            for width_ratio, height_ratio in COMMON_ASPECT_RATIOS:
                frame_width = base_size * width_ratio
                frame_height = base_size * height_ratio
                
                # Check if this frame size could fit in the sheet
                if frame_width <= width and frame_height <= height:
                    frames_x = width // frame_width
                    frames_y = height // frame_height
                    total_frames = frames_x * frames_y
                    
                    # Check for reasonable frame counts (like the algorithm does)
                    if 2 <= total_frames <= 200:
                        utilization = (frames_x * frame_width * frames_y * frame_height) / (width * height)
                        possible_configs.append({
                            'frame_size': (frame_width, frame_height),
                            'grid': (frames_x, frames_y),
                            'total_frames': total_frames,
                            'utilization': utilization,
                            'base_size': base_size,
                            'aspect_ratio': f"{width_ratio}:{height_ratio}"
                        })
        
        # Sort by utilization (best fit first)
        possible_configs.sort(key=lambda x: x['utilization'], reverse=True)
        
        print(f"Found {len(possible_configs)} possible configurations:")
        
        if possible_configs:
            # Show top 5 configurations
            for i, config in enumerate(possible_configs[:5]):
                print(f"  {i+1}. {config['frame_size'][0]}×{config['frame_size'][1]} "
                      f"({config['aspect_ratio']}) → {config['grid'][0]}×{config['grid'][1]} grid "
                      f"= {config['total_frames']} frames, {config['utilization']:.1%} utilization")
        else:
            print("  ❌ No valid configurations found!")
        
        # Test horizontal strip detection specifically
        print(f"\nTesting horizontal strip detection:")
        if aspect_ratio > 3.0:
            print("  Sheet qualifies for horizontal strip detection (aspect > 3.0)")
            strip_configs = []
            
            # Test frame heights that use full available height
            available_height = height
            available_width = width
            
            for frames_count in range(2, 21):  # 2-20 frames like the algorithm
                if available_width % frames_count == 0:
                    frame_width = available_width // frames_count
                    frame_height = available_height
                    
                    strip_configs.append({
                        'frame_size': (frame_width, frame_height),
                        'frames_count': frames_count,
                        'perfect_division': True
                    })
            
            if strip_configs:
                print(f"  Found {len(strip_configs)} horizontal strip configurations:")
                for config in strip_configs:
                    print(f"    {config['frame_size'][0]}×{config['frame_size'][1]} "
                          f"× {config['frames_count']} frames")
            else:
                print("  ❌ No valid horizontal strip configurations found!")
        else:
            print(f"  Sheet does not qualify for horizontal strip detection (aspect {aspect_ratio:.2f} <= 3.0)")
        
        return possible_configs
        
    except Exception as e:
        print(f"❌ Error analyzing {sprite_path}: {e}")
        return []

def main():
    """Analyze detection capabilities on test sprites."""
    
    sprites = [
        "spritetests/Archer_Run.png",
        "spritetests/Lancer_Run.png", 
        "spritetests/Lancer_Idle.png",
        "spritetests/test_sprite_sheet.png"
    ]
    
    print("🔍 Sprite Detection Analysis")
    print("=" * 60)
    
    results = {}
    for sprite_path in sprites:
        if Path(sprite_path).exists():
            configs = analyze_sprite_dimensions(sprite_path)
            results[sprite_path] = len(configs) > 0
        else:
            print(f"❌ File not found: {sprite_path}")
            results[sprite_path] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("DETECTION ANALYSIS SUMMARY:")
    for sprite_path, has_configs in results.items():
        status = "✅ Detectable" if has_configs else "❌ Not detectable"
        print(f"  {Path(sprite_path).name}: {status}")

if __name__ == "__main__":
    main()