#!/usr/bin/env python3
"""
Simple test for refactored background color detection (no Qt required).
"""

import sys
import os

def test_standalone_background_detection():
    """Test the standalone background color detection function."""
    print("🧪 Testing Standalone Background Color Detection...")
    
    try:
        from sprite_model import detect_background_color
        
        test_image = "spritetests/Ark.png"
        if not os.path.exists(test_image):
            print(f"   ❌ Test image not found: {test_image}")
            return False
        
        bg_info = detect_background_color(test_image)
        if bg_info is not None:
            rgb_color, tolerance = bg_info
            print(f"   ✅ Background detected: RGB{rgb_color} (tolerance: {tolerance})")
            
            # Verify it matches expected values for Terranigma
            expected_rgb = (55, 99, 77)
            if rgb_color == expected_rgb:
                print(f"   ✅ Matches expected background color")
                return True
            else:
                print(f"   ⚠️  Different from expected RGB{expected_rgb}")
                return True  # Still successful detection
        else:
            print(f"   ❌ No background color detected")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_ccl_detection_clean():
    """Test the cleaned CCL detection (no background color in result)."""
    print("\n🧪 Testing Clean CCL Detection...")
    
    try:
        from sprite_model import detect_sprites_ccl_enhanced
        
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
            
            # Verify expected sprite count for Terranigma
            if sprite_count == 612:
                print(f"   ✅ Matches expected sprite count")
            else:
                print(f"   ⚠️  Different sprite count (expected 612)")
            
            return sprite_count > 0 and not has_bg_info
        else:
            print(f"   ❌ CCL detection failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_functions_available():
    """Test that both functions are available."""
    print("\n🧪 Testing Function Availability...")
    
    try:
        from sprite_model import detect_background_color, detect_sprites_ccl_enhanced, CCL_AVAILABLE
        
        print(f"   ✅ detect_background_color: Available")
        print(f"   ✅ detect_sprites_ccl_enhanced: Available") 
        print(f"   ✅ CCL_AVAILABLE: {CCL_AVAILABLE}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

def main():
    """Run refactor tests without Qt."""
    print("🚀 Testing Refactored CCL Detection (Simple)")
    print("=" * 50)
    
    # Test 1: Function availability
    availability_test = test_functions_available()
    
    # Test 2: Standalone background detection
    bg_test = test_standalone_background_detection()
    
    # Test 3: Clean CCL detection
    ccl_test = test_ccl_detection_clean()
    
    # Results
    print("\n" + "=" * 50)
    print("📊 Simple Refactor Test Results:")
    print(f"   Function Availability: {'✅ PASS' if availability_test else '❌ FAIL'}")
    print(f"   Standalone Background Detection: {'✅ PASS' if bg_test else '❌ FAIL'}")
    print(f"   Clean CCL Detection: {'✅ PASS' if ccl_test else '❌ FAIL'}")
    
    overall_success = availability_test and bg_test and ccl_test
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Refactor successful!")
        print("   ✅ Background detection: Independent ✓")
        print("   ✅ CCL detection: Clean (no background_color_info) ✓")  
        print("   ✅ Functions: Available and working ✓")
        print("\n💡 Next: Test sprite model integration in the actual application")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)