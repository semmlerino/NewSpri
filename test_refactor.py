#!/usr/bin/env python3
"""
Test the refactored CCL detection with background color separation.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from sprite_model import SpriteModel, detect_background_color, detect_sprites_ccl_enhanced

# Initialize Qt application for QPixmap operations
app = QApplication(sys.argv)

def test_background_detection_standalone():
    """Test the standalone background color detection function."""
    print("🧪 Testing Standalone Background Color Detection...")
    
    test_image = "spritetests/Ark.png"
    if not os.path.exists(test_image):
        print(f"   ❌ Test image not found: {test_image}")
        return False
    
    bg_info = detect_background_color(test_image)
    if bg_info is not None:
        rgb_color, tolerance = bg_info
        print(f"   ✅ Background detected: RGB{rgb_color} (tolerance: {tolerance})")
        return True
    else:
        print(f"   ❌ No background color detected")
        return False

def test_ccl_detection_clean():
    """Test the cleaned CCL detection (no background color in result)."""
    print("\n🧪 Testing Clean CCL Detection...")
    
    test_image = "spritetests/Ark.png"
    if not os.path.exists(test_image):
        print(f"   ❌ Test image not found: {test_image}")
        return False
    
    ccl_result = detect_sprites_ccl_enhanced(test_image)
    if ccl_result and ccl_result.get('success'):
        sprite_count = ccl_result.get('sprite_count', 0)
        print(f"   ✅ CCL detected {sprite_count} sprites")
        
        # Verify no background_color_info in result (should be clean)
        has_bg_info = 'background_color_info' in ccl_result
        print(f"   ✅ Clean result (no background_color_info): {not has_bg_info}")
        
        return sprite_count > 0 and not has_bg_info
    else:
        print(f"   ❌ CCL detection failed")
        return False

def test_sprite_model_integration():
    """Test full sprite model integration with separate background detection."""
    print("\n🧪 Testing Sprite Model Integration...")
    
    model = SpriteModel()
    
    # Load test sprite
    test_image = "spritetests/Ark.png"
    success, error = model.load_sprite_sheet(test_image)
    if not success:
        print(f"   ❌ Failed to load sprite sheet: {error}")
        return False
    
    print(f"   ✅ Loaded sprite sheet: {model._file_name}")
    
    # Run auto-detection (should call CCL + separate background detection)
    try:
        print("   🔍 Running comprehensive auto-detection...")
        # This should trigger the refactored CCL + background detection workflow
        success, message = model.comprehensive_auto_detect()
        
        if success:
            print(f"   ✅ Auto-detection success: {model._frame_width}×{model._frame_height}")
            print(f"   📝 {message}")
            
            # Check if CCL data is available
            ccl_available = model.is_ccl_available()
            sprite_bounds = len(model.get_ccl_sprite_bounds())
            print(f"   ✅ CCL available: {ccl_available}, sprites: {sprite_bounds}")
            
            # Check if background color was detected separately
            has_bg_color = model._ccl_background_color is not None
            bg_tolerance = model._ccl_color_tolerance
            print(f"   ✅ Background color detected: {has_bg_color}")
            if has_bg_color:
                print(f"   🎨 Background: RGB{model._ccl_background_color} (tolerance: {bg_tolerance})")
            
            return success and ccl_available and sprite_bounds > 0
        else:
            print(f"   ❌ Auto-detection failed: {message}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception during auto-detection: {e}")
        return False

def main():
    """Run all refactor tests."""
    print("🚀 Testing Refactored CCL Detection")
    print("=" * 50)
    
    # Test 1: Standalone background detection
    bg_test = test_background_detection_standalone()
    
    # Test 2: Clean CCL detection
    ccl_test = test_ccl_detection_clean()
    
    # Test 3: Sprite model integration
    integration_test = test_sprite_model_integration()
    
    # Results
    print("\n" + "=" * 50)
    print("📊 Refactor Test Results:")
    print(f"   Standalone Background Detection: {'✅ PASS' if bg_test else '❌ FAIL'}")
    print(f"   Clean CCL Detection: {'✅ PASS' if ccl_test else '❌ FAIL'}")
    print(f"   Sprite Model Integration: {'✅ PASS' if integration_test else '❌ FAIL'}")
    
    overall_success = bg_test and ccl_test and integration_test
    print(f"\n🎯 Overall Refactor Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Refactor successful! Background color detection is now cleanly separated.")
        print("   • Background detection: Independent function")
        print("   • CCL detection: Focused on sprite boundaries only")  
        print("   • Sprite model: Clean integration with separate calls")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)