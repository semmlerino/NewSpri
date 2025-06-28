#!/usr/bin/env python3
"""
Test extracted modules to ensure they work independently.
"""

import sys
import os

def test_background_detector():
    """Test the extracted background detector module."""
    print("🧪 Testing Extracted Background Detector...")
    
    try:
        from sprite_model.extraction.background_detector import detect_background_color
        
        if not os.path.exists("spritetests/Ark.png"):
            print("   ❌ Test image not found")
            return False
        
        bg_info = detect_background_color("spritetests/Ark.png")
        if bg_info is not None:
            rgb_color, tolerance = bg_info
            print(f"   ✅ Background detected: RGB{rgb_color} (tolerance: {tolerance})")
            return True
        else:
            print("   ❌ No background detected")
            return False
            
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Runtime error: {e}")
        return False

def test_ccl_extractor():
    """Test the extracted CCL extractor module.""" 
    print("\n🧪 Testing Extracted CCL Extractor...")
    
    try:
        from sprite_model.extraction.ccl_extractor import detect_sprites_ccl_enhanced
        
        if not os.path.exists("spritetests/Ark.png"):
            print("   ❌ Test image not found") 
            return False
        
        result = detect_sprites_ccl_enhanced("spritetests/Ark.png")
        if result and result.get('success'):
            sprite_count = result.get('sprite_count', 0)
            print(f"   ✅ CCL detected {sprite_count} sprites")
            return True
        else:
            print("   ❌ CCL detection failed")
            return False
            
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Runtime error: {e}")
        return False

def test_backwards_compatibility():
    """Test that the main sprite_model module imports work."""
    print("\n🧪 Testing Backwards Compatibility...")
    
    try:
        # This should work via the __init__.py forwarding
        from sprite_model import detect_background_color, detect_sprites_ccl_enhanced
        print("   ✅ Imports successful via sprite_model")
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

def main():
    """Run module extraction tests."""
    print("🚀 Testing Extracted Modules")
    print("=" * 40)
    
    # Test individual modules
    bg_test = test_background_detector()
    ccl_test = test_ccl_extractor()
    compat_test = test_backwards_compatibility()
    
    print("\n" + "=" * 40)
    print("📊 Extraction Test Results:")
    print(f"   Background Detector: {'✅ PASS' if bg_test else '❌ FAIL'}")
    print(f"   CCL Extractor: {'✅ PASS' if ccl_test else '❌ FAIL'}")
    print(f"   Backwards Compatibility: {'✅ PASS' if compat_test else '❌ FAIL'}")
    
    overall_success = bg_test and ccl_test and compat_test
    print(f"\n🎯 Overall Result: {'✅ EXTRACTION SUCCESSFUL' if overall_success else '❌ EXTRACTION FAILED'}")
    
    if overall_success:
        print("\n🎉 Module extraction successful!")
        print("   ✅ Background detector: Independent module ✓")
        print("   ✅ CCL extractor: Standalone functionality ✓")
        print("   ✅ Import compatibility: Maintained ✓")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)