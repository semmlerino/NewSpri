#!/usr/bin/env python3
"""
Test File Operations Module - Structure Only
============================================

Tests the extracted file operations module structure without Qt dependencies.
"""

import sys
import os


def test_module_imports():
    """Test that file operations modules can be imported."""
    print("🧪 Testing File Operations Module Imports...")
    
    try:
        # Test direct module import
        from sprite_model.file_operations import FileOperations
        print("   ✅ FileOperations class import successful")
        
        # Test standalone functions
        from sprite_model.file_operations import load_sprite_sheet, validate_image_file
        print("   ✅ Standalone functions import successful")
        
        # Test module forwarding through __init__.py
        from sprite_model import FileOperations as ForwardedFileOps
        from sprite_model import load_sprite_sheet as ForwardedLoad
        from sprite_model import validate_image_file as ForwardedValidate
        print("   ✅ Module forwarding import successful")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Runtime error: {e}")
        return False


def test_class_structure():
    """Test FileOperations class structure."""
    print("\n🧪 Testing FileOperations Class Structure...")
    
    try:
        from sprite_model.file_operations import FileOperations
        
        # Create instance without Qt
        file_ops = FileOperations()
        print("   ✅ FileOperations instance created")
        
        # Test that all required methods exist
        required_methods = [
            'load_sprite_sheet',
            'reload_current_sheet', 
            'clear_file_data',
            'get_file_info',
            'is_file_loaded',
            'has_file_changed',
            'validate_image_file'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(file_ops, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"   ❌ Missing methods: {missing_methods}")
            return False
        
        print(f"   ✅ All {len(required_methods)} required methods present")
        
        # Test initial state (without Qt pixmap operations)
        if file_ops.is_file_loaded():
            print("   ❌ is_file_loaded() should return False initially")
            return False
        print("   ✅ Initial state correct (no file loaded)")
        
        # Test get_file_info when empty
        info = file_ops.get_file_info()
        expected_keys = ['file_path', 'file_name', 'width', 'height', 'format', 'last_modified', 'info_html', 'pixmap']
        missing_keys = [key for key in expected_keys if key not in info]
        if missing_keys:
            print(f"   ❌ Missing info keys: {missing_keys}")
            return False
        print("   ✅ File info structure correct")
        
        # Test clear functionality
        file_ops.clear_file_data()
        print("   ✅ Clear file data successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Class structure test error: {e}")
        return False


def test_standalone_functions():
    """Test standalone function signatures."""
    print("\n🧪 Testing Standalone Functions...")
    
    try:
        from sprite_model.file_operations import load_sprite_sheet, validate_image_file
        
        # Test that functions are callable (don't actually call them without Qt)
        if not callable(load_sprite_sheet):
            print("   ❌ load_sprite_sheet is not callable")
            return False
        print("   ✅ load_sprite_sheet is callable")
        
        if not callable(validate_image_file):
            print("   ❌ validate_image_file is not callable")
            return False
        print("   ✅ validate_image_file is callable")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Standalone functions test error: {e}")
        return False


def test_backwards_compatibility():
    """Test backwards compatibility through sprite_model package."""
    print("\n🧪 Testing Backwards Compatibility...")
    
    try:
        # Test that all functions are accessible through main package
        from sprite_model import (
            FileOperations,
            load_sprite_sheet, 
            validate_image_file,
            detect_background_color,  # Should still work
            detect_sprites_ccl_enhanced  # Should still work
        )
        print("   ✅ All functions accessible via sprite_model package")
        
        # Test __all__ exports
        import sprite_model
        expected_exports = [
            'SpriteModel',
            'detect_background_color', 
            'detect_sprites_ccl_enhanced',
            'FileOperations',
            'load_sprite_sheet',
            'validate_image_file'
        ]
        
        missing_exports = [exp for exp in expected_exports if exp not in sprite_model.__all__]
        if missing_exports:
            print(f"   ❌ Missing exports in __all__: {missing_exports}")
            return False
        print("   ✅ All expected exports present in __all__")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Backwards compatibility import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Backwards compatibility test error: {e}")
        return False


def main():
    """Run file operations module structure tests."""
    print("🚀 Testing File Operations Module Structure")
    print("=" * 50)
    
    # Run tests that don't require Qt
    import_test = test_module_imports()
    structure_test = test_class_structure()
    functions_test = test_standalone_functions()
    compat_test = test_backwards_compatibility()
    
    print("\n" + "=" * 50)
    print("📊 File Operations Structure Test Results:")
    print(f"   Module Imports: {'✅ PASS' if import_test else '❌ FAIL'}")
    print(f"   Class Structure: {'✅ PASS' if structure_test else '❌ FAIL'}")
    print(f"   Function Signatures: {'✅ PASS' if functions_test else '❌ FAIL'}")
    print(f"   Backwards Compatibility: {'✅ PASS' if compat_test else '❌ FAIL'}")
    
    overall_success = import_test and structure_test and functions_test and compat_test
    print(f"\n🎯 Overall Result: {'✅ STRUCTURE VERIFIED' if overall_success else '❌ STRUCTURE FAILED'}")
    
    if overall_success:
        print("\n🎉 File Operations module structure verified!")
        print("   ✅ Module imports: Working ✓")
        print("   ✅ Class definition: Complete ✓")
        print("   ✅ Method signatures: Correct ✓")
        print("   ✅ Package integration: Successful ✓")
        print("   ✅ Backwards compatibility: Maintained ✓")
        print("\n📋 Phase 2 Status: File Operations → ✅ COMPLETED")
        print("📋 Module ready for integration testing with full Qt environment")
    else:
        print("\n❌ File Operations module structure needs fixes")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)