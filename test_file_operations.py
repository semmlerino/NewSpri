#!/usr/bin/env python3
"""
Test File Operations Module
===========================

Tests the extracted file operations module to ensure it works independently.
"""

import sys
import os
from PySide6.QtWidgets import QApplication


def test_file_operations_module():
    """Test the extracted file operations module."""
    print("🧪 Testing Extracted File Operations Module...")
    
    try:
        from sprite_model.file_operations import FileOperations, load_sprite_sheet, validate_image_file
        
        # Test sprite sheet exists
        test_image = "spritetests/Ark.png"
        if not os.path.exists(test_image):
            print(f"   ❌ Test image not found: {test_image}")
            return False
        
        # Test validation function
        print(f"   🔍 Testing file validation...")
        is_valid, error = validate_image_file(test_image)
        if not is_valid:
            print(f"   ❌ Validation failed: {error}")
            return False
        print(f"   ✅ File validation passed")
        
        # Test standalone load function
        print(f"   📁 Testing standalone load function...")
        success, error, metadata = load_sprite_sheet(test_image)
        if not success:
            print(f"   ❌ Standalone load failed: {error}")
            return False
        
        print(f"   ✅ Standalone load successful:")
        print(f"      File: {metadata['file_name']}")
        print(f"      Size: {metadata['width']}×{metadata['height']}")
        print(f"      Format: {metadata['format']}")
        
        # Test FileOperations class
        print(f"   🏗️ Testing FileOperations class...")
        file_ops = FileOperations()
        
        # Test load
        success, error, metadata = file_ops.load_sprite_sheet(test_image)
        if not success:
            print(f"   ❌ Class load failed: {error}")
            return False
        
        print(f"   ✅ Class load successful")
        
        # Test file info
        info = file_ops.get_file_info()
        print(f"   📊 File info: {info['file_name']} ({info['width']}×{info['height']})")
        
        # Test is_file_loaded
        if not file_ops.is_file_loaded():
            print(f"   ❌ is_file_loaded() returned False after successful load")
            return False
        print(f"   ✅ is_file_loaded() correctly returns True")
        
        # Test reload
        success, error, metadata = file_ops.reload_current_sheet()
        if not success:
            print(f"   ❌ Reload failed: {error}")
            return False
        print(f"   ✅ Reload successful")
        
        # Test clear
        file_ops.clear_file_data()
        if file_ops.is_file_loaded():
            print(f"   ❌ is_file_loaded() returned True after clear")
            return False
        print(f"   ✅ Clear successful")
        
        print(f"   🎉 All FileOperations tests passed!")
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Runtime error: {e}")
        return False


def test_backwards_compatibility():
    """Test that the main sprite_model module imports work."""
    print("\n🧪 Testing File Operations Backwards Compatibility...")
    
    try:
        # This should work via the __init__.py forwarding
        from sprite_model import FileOperations, load_sprite_sheet, validate_image_file
        print("   ✅ FileOperations imports successful via sprite_model")
        
        # Test direct usage
        test_image = "spritetests/Ark.png"
        if os.path.exists(test_image):
            success, error, metadata = load_sprite_sheet(test_image)
            if success:
                print(f"   ✅ Direct function call successful: {metadata['file_name']}")
            else:
                print(f"   ❌ Direct function call failed: {error}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False


def main():
    """Run file operations extraction tests."""
    print("🚀 Testing File Operations Module Extraction")
    print("=" * 50)
    
    # Initialize Qt application for QPixmap
    app = QApplication([])
    
    # Test individual module
    module_test = test_file_operations_module()
    compat_test = test_backwards_compatibility()
    
    print("\n" + "=" * 50)
    print("📊 File Operations Test Results:")
    print(f"   File Operations Module: {'✅ PASS' if module_test else '❌ FAIL'}")
    print(f"   Backwards Compatibility: {'✅ PASS' if compat_test else '❌ FAIL'}")
    
    overall_success = module_test and compat_test
    print(f"\n🎯 Overall Result: {'✅ EXTRACTION SUCCESSFUL' if overall_success else '❌ EXTRACTION FAILED'}")
    
    if overall_success:
        print("\n🎉 File Operations extraction successful!")
        print("   ✅ FileOperations class: Independent service ✓")
        print("   ✅ Standalone functions: Direct access ✓")
        print("   ✅ Import compatibility: Maintained ✓")
        print("   ✅ File validation: Working ✓")
        print("   ✅ Metadata extraction: Complete ✓")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)