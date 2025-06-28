#!/usr/bin/env python3
"""
Simple Grid Extractor Structure Test
====================================

Tests the basic structure and imports of the grid extractor module
without requiring Qt dependencies.
"""

import sys
import os
from pathlib import Path


def test_module_imports():
    """Test that the grid extractor module can be imported."""
    print("🧪 Testing grid extractor module imports...")
    
    try:
        # Test basic import
        from sprite_model.extraction.grid_extractor import GridExtractor, GridConfig
        print("   ✅ GridExtractor and GridConfig imported successfully")
        
        # Test NamedTuple structure
        config = GridConfig(width=32, height=32, offset_x=5, offset_y=5, spacing_x=2, spacing_y=2)
        print(f"   ✅ GridConfig created: {config.width}x{config.height}, offset({config.offset_x},{config.offset_y}), spacing({config.spacing_x},{config.spacing_y})")
        
        # Test class instantiation
        extractor = GridExtractor()
        print("   ✅ GridExtractor instance created")
        
        # Test that required methods exist
        required_methods = [
            'extract_frames',
            'validate_frame_settings',
            'calculate_grid_layout',
            '_calculate_grid_layout',
            'create_frame_info_string'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(extractor, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"   ❌ Missing methods: {missing_methods}")
            return False
        
        print(f"   ✅ All {len(required_methods)} required methods present")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Other error: {e}")
        return False


def test_config_validation():
    """Test GridConfig validation logic."""
    print("🧪 Testing GridConfig validation...")
    
    try:
        from sprite_model.extraction.grid_extractor import GridConfig
        
        # Test valid configuration
        config = GridConfig(width=32, height=32)
        if config.width != 32 or config.height != 32:
            print("   ❌ Basic config values incorrect")
            return False
        
        # Test default values
        if config.offset_x != 0 or config.offset_y != 0:
            print("   ❌ Default offset values incorrect")
            return False
        
        if config.spacing_x != 0 or config.spacing_y != 0:
            print("   ❌ Default spacing values incorrect")
            return False
        
        # Test custom values
        config2 = GridConfig(width=16, height=24, offset_x=8, offset_y=12, spacing_x=4, spacing_y=6)
        if (config2.width != 16 or config2.height != 24 or 
            config2.offset_x != 8 or config2.offset_y != 12 or
            config2.spacing_x != 4 or config2.spacing_y != 6):
            print("   ❌ Custom config values incorrect")
            return False
        
        print("   ✅ GridConfig validation successful")
        return True
        
    except Exception as e:
        print(f"   ❌ Exception in config validation: {e}")
        return False


def test_convenience_function():
    """Test the convenience function import."""
    print("🧪 Testing convenience function import...")
    
    try:
        from sprite_model.extraction.grid_extractor import extract_grid_frames
        
        # Test that function exists and is callable
        if not callable(extract_grid_frames):
            print("   ❌ extract_grid_frames is not callable")
            return False
        
        print("   ✅ Convenience function extract_grid_frames imported successfully")
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Other error: {e}")
        return False


def test_file_structure():
    """Test that the module file structure is correct."""
    print("🧪 Testing file structure...")
    
    try:
        # Check that the grid extractor file exists
        extractor_path = Path("sprite_model/extraction/grid_extractor.py")
        if not extractor_path.exists():
            print(f"   ❌ Grid extractor file missing: {extractor_path}")
            return False
        
        # Check file size (should be substantial)
        file_size = extractor_path.stat().st_size
        if file_size < 5000:  # Expect at least 5KB for a comprehensive module
            print(f"   ❌ Grid extractor file too small: {file_size} bytes")
            return False
        
        # Check that __init__.py exists in extraction directory
        init_path = Path("sprite_model/extraction/__init__.py")
        if not init_path.exists():
            print(f"   ❌ __init__.py missing in extraction directory")
            return False
        
        print(f"   ✅ File structure correct, grid_extractor.py is {file_size} bytes")
        return True
        
    except Exception as e:
        print(f"   ❌ Exception in file structure test: {e}")
        return False


def main():
    """Run simple grid extractor structure tests."""
    print("🚀 Grid Extractor Structure Test")
    print("=" * 40)
    
    tests = [
        test_file_structure,
        test_module_imports,
        test_config_validation,
        test_convenience_function
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"   ❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Grid extractor structure validation passed!")
        print("   ✅ Module can be imported correctly")
        print("   ✅ All required classes and functions present")
        print("   ✅ Configuration objects work correctly")
        print("   ✅ Ready for integration testing")
        return True
    else:
        print(f"❌ {total - passed} tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)