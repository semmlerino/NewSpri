#!/usr/bin/env python3
"""
Debug script to test auto-detection on Lancer sprites specifically.
"""

import sys
from pathlib import Path
from sprite_model import SpriteModel
from config import Config
from PIL import Image

def test_detection(sprite_path):
    """Test auto-detection on a specific sprite."""
    print(f"\n=== Testing Auto-Detection on {sprite_path} ===")
    
    # Load the sprite
    model = SpriteModel()
    
    try:
        # Load the sprite image
        sprite_pixmap = Image.open(sprite_path)
        sprite_size = sprite_pixmap.size
        print(f"Sprite dimensions: {sprite_size[0]}×{sprite_size[1]}")
        print(f"Aspect ratio: {sprite_size[0]/sprite_size[1]:.2f}")
        
        # Load into model
        model.load_sprite_sheet(str(sprite_path))
        
        if not model.original_sprite_sheet:
            print("❌ Failed to load sprite sheet")
            return False
        
        print(f"Loaded successfully into model")
        
        # Test comprehensive auto-detection
        print("\n--- Testing Comprehensive Auto-Detection ---")
        success, detailed_report = model.comprehensive_auto_detect()
        
        print(f"Detection Success: {success}")
        print(f"Final Settings:")
        print(f"  Frame Size: {model._frame_width}×{model._frame_height}")
        print(f"  Margins: ({model._offset_x}, {model._offset_y})")
        print(f"  Spacing: ({model._spacing_x}, {model._spacing_y})")
        
        print(f"\nDetailed Report:")
        print(detailed_report)
        
        # Test rectangular frame detection specifically
        print("\n--- Testing Rectangular Frame Detection ---")
        rect_success, width, height, message = model.auto_detect_rectangular_frames()
        print(f"Rectangular Detection Success: {rect_success}")
        print(f"Detected Size: {width}×{height}")
        print(f"Message: {message}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error during detection: {e}")
        return False

def main():
    """Test detection on both Archer and Lancer sprites for comparison."""
    
    # Test sprites
    archer_path = "spritetests/Archer_Run.png"
    lancer_run_path = "spritetests/Lancer_Run.png"
    lancer_idle_path = "spritetests/Lancer_Idle.png"
    
    # Check if files exist
    for path in [archer_path, lancer_run_path, lancer_idle_path]:
        if not Path(path).exists():
            print(f"❌ File not found: {path}")
            return
    
    print("🔍 Auto-Detection Debug Test")
    print("=" * 50)
    
    # Test Archer (known working)
    archer_success = test_detection(archer_path)
    
    # Test Lancer Run
    lancer_run_success = test_detection(lancer_run_path)
    
    # Test Lancer Idle  
    lancer_idle_success = test_detection(lancer_idle_path)
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Archer_Run.png: {'✅ Success' if archer_success else '❌ Failed'}")
    print(f"Lancer_Run.png: {'✅ Success' if lancer_run_success else '❌ Failed'}")
    print(f"Lancer_Idle.png: {'✅ Success' if lancer_idle_success else '❌ Failed'}")

if __name__ == "__main__":
    main()