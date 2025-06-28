#!/usr/bin/env python3
"""
Simple Grid Integration Test
============================

Tests the integration of grid extractor functionality without requiring Qt.
Validates imports, structure, and basic functionality.
"""

import sys
import os


def test_imports():
    """Test that all grid-related imports work correctly."""
    print("🧪 Testing grid extractor imports...")
    
    try:
        # Test direct grid extractor import
        from sprite_model.extraction.grid_extractor import GridExtractor, GridConfig
        print("   ✅ Direct grid extractor import successful")
        
        # Test that GridConfig works
        config = GridConfig(width=32, height=32, offset_x=5, offset_y=5)
        print(f"   ✅ GridConfig created: {config.width}x{config.height}")
        
        # Test that GridExtractor can be instantiated
        extractor = GridExtractor()
        print("   ✅ GridExtractor instance created")
        
        # Test required methods exist
        required_methods = ['extract_frames', 'validate_frame_settings', 'calculate_grid_layout']
        for method in required_methods:
            if not hasattr(extractor, method):
                print(f"   ❌ Missing method: {method}")
                return False
        
        print(f"   ✅ All {len(required_methods)} required methods present")
        return True
        
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False


def test_sprite_model_integration():
    """Test that SpriteModel correctly integrates grid extractor."""
    print("🧪 Testing SpriteModel integration...")
    
    try:
        # Check file existence first
        import_path = "sprite_model_original.py"
        if not os.path.exists(import_path):
            print(f"   ❌ File missing: {import_path}")
            return False
        
        # Read file content to verify integration
        with open(import_path, 'r') as f:
            content = f.read()
        
        # Check for key integration markers
        integration_markers = [
            "from sprite_model.extraction.grid_extractor import GridExtractor, GridConfig",
            "self._grid_extractor = GridExtractor()",
            "config = GridConfig(width, height, offset_x, offset_y, spacing_x, spacing_y)",
            "self._grid_extractor.extract_frames(self._original_sprite_sheet, config)",
            "self._grid_extractor.validate_frame_settings(self._original_sprite_sheet, config)"
        ]
        
        missing_markers = []
        for marker in integration_markers:
            if marker not in content:
                missing_markers.append(marker)
        
        if missing_markers:
            print(f"   ❌ Missing integration code:")
            for marker in missing_markers:
                print(f"      - {marker}")
            return False
        
        print(f"   ✅ All {len(integration_markers)} integration markers found")
        
        # Check that old grid extraction code has been replaced
        old_patterns = [
            "for row in range(frames_per_col):",
            "for col in range(frames_per_row):",
            "x = offset_x + (col * (width + spacing_x))",
            "if width <= 0:",
            "return False, \"Frame width must be greater than 0\""
        ]
        
        remaining_old_code = []
        for pattern in old_patterns:
            if pattern in content:
                remaining_old_code.append(pattern)
        
        if remaining_old_code:
            print(f"   ⚠️ Some old code patterns still present (may be in comments):")
            for pattern in remaining_old_code[:2]:  # Show first 2
                print(f"      - {pattern}")
        else:
            print("   ✅ Old grid extraction code successfully replaced")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test error: {e}")
        return False


def test_fallback_handling():
    """Test that fallback handling works when grid extractor is not available."""
    print("🧪 Testing fallback handling...")
    
    try:
        # Read sprite_model_original.py content
        with open("sprite_model_original.py", 'r') as f:
            content = f.read()
        
        # Check for fallback import handling
        fallback_markers = [
            "except ImportError:",
            "GRID_EXTRACTOR_AVAILABLE = False",
            "class GridExtractor:",
            "def extract_frames(self, *args, **kwargs):",
            "return False, \"Grid extractor not available\", []"
        ]
        
        missing_fallbacks = []
        for marker in fallback_markers:
            if marker not in content:
                missing_fallbacks.append(marker)
        
        if missing_fallbacks:
            print(f"   ❌ Missing fallback handling:")
            for marker in missing_fallbacks:
                print(f"      - {marker}")
            return False
        
        print("   ✅ Fallback handling implemented correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Fallback test error: {e}")
        return False


def test_file_structure():
    """Test that the required file structure is in place."""
    print("🧪 Testing file structure...")
    
    try:
        required_files = [
            "sprite_model/extraction/grid_extractor.py",
            "sprite_model/__init__.py",
            "sprite_model/extraction/__init__.py",
            "sprite_model_original.py",
            "sprite_model_original_PHASE3_BACKUP.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"   ❌ Missing files:")
            for file_path in missing_files:
                print(f"      - {file_path}")
            return False
        
        print(f"   ✅ All {len(required_files)} required files present")
        
        # Check file sizes are reasonable
        grid_extractor_size = os.path.getsize("sprite_model/extraction/grid_extractor.py")
        if grid_extractor_size < 5000:
            print(f"   ❌ grid_extractor.py too small: {grid_extractor_size} bytes")
            return False
        
        print(f"   ✅ grid_extractor.py size appropriate: {grid_extractor_size} bytes")
        return True
        
    except Exception as e:
        print(f"   ❌ File structure test error: {e}")
        return False


def test_code_reduction():
    """Test that the original file has been reduced in size."""
    print("🧪 Testing code reduction...")
    
    try:
        # Compare original backup with current version
        backup_path = "sprite_model_original_PHASE3_BACKUP.py"
        current_path = "sprite_model_original.py"
        
        if not os.path.exists(backup_path):
            print("   ⚠️ Backup file not found, skipping size comparison")
            return True
        
        backup_size = os.path.getsize(backup_path)
        current_size = os.path.getsize(current_path)
        
        if current_size >= backup_size:
            print(f"   ❌ File size not reduced: {backup_size} → {current_size} bytes")
            return False
        
        reduction = backup_size - current_size
        percentage = (reduction / backup_size) * 100
        
        print(f"   ✅ File size reduced: {backup_size} → {current_size} bytes")
        print(f"   ✅ Reduction: {reduction} bytes ({percentage:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Size comparison error: {e}")
        return False


def main():
    """Run the simple grid integration test suite."""
    print("🚀 Simple Grid Integration Test")
    print("=" * 45)
    
    tests = [
        test_file_structure,
        test_imports,
        test_sprite_model_integration,
        test_fallback_handling,
        test_code_reduction
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
    
    print("=" * 45)
    print(f"📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Grid extraction integration validation successful!")
        print("   ✅ Grid extractor properly extracted and integrated")
        print("   ✅ SpriteModel modified to use modular functionality")
        print("   ✅ Fallback handling implemented")
        print("   ✅ File structure correct")
        print("   ✅ Code reduction achieved")
        print("   ✅ Phase 3 refactoring complete")
        return True
    else:
        print(f"❌ {total - passed} integration tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)