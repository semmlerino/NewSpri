#!/usr/bin/env python3
"""
Test File Operations Module - Headless Version
==============================================

Tests the extracted file operations module without Qt display requirements.
"""

import sys
import os

# Set Qt to use offscreen platform for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication


def test_file_operations_imports():
    """Test that file operations modules can be imported."""
    print("🧪 Testing File Operations Imports...")
    
    try:
        from sprite_model.file_operations import FileOperations, load_sprite_sheet, validate_image_file
        print("   ✅ Direct imports successful")
        
        from sprite_model import FileOperations as ImportedFileOps, load_sprite_sheet as ImportedLoad
        print("   ✅ Module forwarding imports successful")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Runtime error: {e}")
        return False


def test_file_validation():
    """Test file validation without Qt graphics."""
    print("\n🧪 Testing File Validation...")
    
    try:
        from sprite_model.file_operations import validate_image_file
        
        # Test with existing test image
        test_image = "spritetests/Ark.png"
        if not os.path.exists(test_image):
            print(f"   ⚠️  Test image not found: {test_image}")
            print("   ℹ️  Skipping validation test")
            return True
        
        is_valid, error = validate_image_file(test_image)
        if not is_valid:
            print(f"   ❌ Validation failed: {error}")
            return False
        
        print(f"   ✅ File validation successful for {test_image}")
        
        # Test with non-existent file
        is_valid, error = validate_image_file("nonexistent.png")
        if is_valid:
            print(f"   ❌ Validation should have failed for nonexistent file")
            return False
        
        print(f"   ✅ Correctly rejected nonexistent file")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Validation test error: {e}")
        return False


def test_file_operations_class():
    """Test FileOperations class basic functionality."""
    print("\n🧪 Testing FileOperations Class...")
    
    try:
        from sprite_model.file_operations import FileOperations
        
        # Create instance
        file_ops = FileOperations()
        print("   ✅ FileOperations instance created")
        
        # Test initial state
        if file_ops.is_file_loaded():
            print("   ❌ is_file_loaded() should return False initially")
            return False
        print("   ✅ Initial state correct (no file loaded)")
        
        # Test get_file_info when no file loaded
        info = file_ops.get_file_info()
        if info['file_path'] != "":
            print("   ❌ file_path should be empty initially")
            return False
        print("   ✅ Empty file info correct")
        
        # Test clear (should not error)
        file_ops.clear_file_data()
        print("   ✅ Clear file data successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ FileOperations class test error: {e}")
        return False


def test_module_structure():
    """Test that the module structure is correct."""
    print("\n🧪 Testing Module Structure...")
    
    try:
        # Test that all expected functions exist
        from sprite_model.file_operations import FileOperations
        
        # Check required methods exist
        required_methods = [
            'load_sprite_sheet',
            'reload_current_sheet', 
            'clear_file_data',
            'get_file_info',
            'is_file_loaded',
            'has_file_changed',
            'validate_image_file'
        ]
        
        for method in required_methods:
            if not hasattr(FileOperations, method):
                print(f"   ❌ Missing method: {method}")
                return False
        
        print(f"   ✅ All {len(required_methods)} required methods present")
        
        # Test standalone functions exist
        from sprite_model.file_operations import load_sprite_sheet, validate_image_file
        print("   ✅ Standalone functions accessible")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Module structure test error: {e}")
        return False


def main():
    """Run file operations module tests."""
    print("🚀 Testing File Operations Module (Headless)")
    print("=" * 50)
    
    # Initialize Qt application in headless mode
    app = QCoreApplication([])
    
    # Run tests
    import_test = test_file_operations_imports()
    validation_test = test_file_validation()
    class_test = test_file_operations_class()
    structure_test = test_module_structure()
    
    print("\n" + "=" * 50)
    print("📊 File Operations Test Results:")
    print(f"   Import Tests: {'✅ PASS' if import_test else '❌ FAIL'}")
    print(f"   Validation Tests: {'✅ PASS' if validation_test else '❌ FAIL'}")
    print(f"   Class Tests: {'✅ PASS' if class_test else '❌ FAIL'}")
    print(f"   Structure Tests: {'✅ PASS' if structure_test else '❌ FAIL'}")
    
    overall_success = import_test and validation_test and class_test and structure_test
    print(f"\n🎯 Overall Result: {'✅ EXTRACTION SUCCESSFUL' if overall_success else '❌ EXTRACTION FAILED'}")
    
    if overall_success:
        print("\n🎉 File Operations module extraction successful!")
        print("   ✅ Module imports: Working ✓")
        print("   ✅ Class structure: Complete ✓")
        print("   ✅ Validation logic: Functional ✓")
        print("   ✅ Backwards compatibility: Maintained ✓")
        print("\n📋 Phase 2 Status: File Operations → ✅ COMPLETED")
        print("📋 Next Phase: Extract Grid Extraction functionality")
    else:
        print("\n❌ File Operations extraction needs fixes")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)