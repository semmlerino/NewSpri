#!/usr/bin/env python3
"""
Test Circular Import Fix
========================

Tests that the SpriteModel can be imported and has the clear_sprite_data method.
"""

import sys
import os

# Set Qt to use offscreen platform for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

def test_sprite_model_import():
    """Test that SpriteModel imports correctly and has required methods."""
    print("🧪 Testing SpriteModel Import Fix...")
    
    try:
        # This is the exact import that was failing
        from sprite_model import SpriteModel
        print("   ✅ SpriteModel import successful")
        
        # Create an instance
        model = SpriteModel()
        print("   ✅ SpriteModel instance created")
        
        # Test that the problematic method exists
        if not hasattr(model, 'clear_sprite_data'):
            print("   ❌ clear_sprite_data method missing")
            return False
        print("   ✅ clear_sprite_data method exists")
        
        # Test that we can call it without error
        model.clear_sprite_data()
        print("   ✅ clear_sprite_data method callable")
        
        # Test a few other key methods that should exist
        required_methods = [
            'load_sprite_sheet',
            'reload_current_sheet',
            'extract_frames',
            'is_loaded'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(model, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"   ❌ Missing methods: {missing_methods}")
            return False
        
        print(f"   ✅ All {len(required_methods)} key methods present")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Runtime error: {e}")
        return False


def main():
    """Run the circular import fix test."""
    print("🚀 Testing Circular Import Fix")
    print("=" * 40)
    
    success = test_sprite_model_import()
    
    print("\n" + "=" * 40)
    print(f"🎯 Result: {'✅ IMPORT FIX SUCCESSFUL' if success else '❌ IMPORT FIX FAILED'}")
    
    if success:
        print("\n🎉 Circular import issue resolved!")
        print("   ✅ SpriteModel imports correctly from modular structure")
        print("   ✅ clear_sprite_data method accessible")
        print("   ✅ All core methods present")
        print("   ✅ Ready for main application usage")
    else:
        print("\n❌ Circular import issue still exists")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)