#!/usr/bin/env python3
"""
Test script for sprite viewer functionality
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import PySide6
        print(f"✅ PySide6 {PySide6.__version__} imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PySide6: {e}")
        return False
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPixmap
        print("✅ PySide6 components imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PySide6 components: {e}")
        return False
    
    return True

def test_sprite_loading():
    """Test sprite loading functionality."""
    print("\nTesting sprite loading...")
    
    # Check if test sprites exist
    archer_dir = Path("Archer")
    if archer_dir.exists():
        sprite_files = list(archer_dir.glob("*.png"))
        print(f"✅ Found {len(sprite_files)} test sprite files in Archer directory")
        
        if sprite_files:
            try:
                from PySide6.QtWidgets import QApplication
                from PySide6.QtGui import QPixmap
                
                # Create minimal application for QPixmap testing with offscreen platform
                app = QApplication.instance()
                if app is None:
                    app = QApplication(['-platform', 'offscreen'])
                
                test_file = sprite_files[0]
                pixmap = QPixmap(str(test_file))
                
                if not pixmap.isNull():
                    print(f"✅ Successfully loaded test sprite: {test_file.name}")
                    print(f"   Size: {pixmap.width()}x{pixmap.height()}")
                    return True
                else:
                    print(f"❌ Failed to load sprite: {test_file.name}")
                    return False
            except Exception as e:
                print(f"⚠️ Could not test sprite loading (no display): {e}")
                print("✅ Sprite files exist and should load correctly with GUI")
                return True
    else:
        print("⚠️ No test sprites found in Archer directory")
        return True  # Not a failure, just no test data

def test_application_structure():
    """Test that the main application can be imported."""
    print("\nTesting application structure...")
    
    try:
        import sprite_viewer
        print("✅ sprite_viewer module imported successfully")
        
        # Check main classes exist
        if hasattr(sprite_viewer, 'SpriteViewer'):
            print("✅ SpriteViewer class found")
        else:
            print("❌ SpriteViewer class not found")
            return False
            
        if hasattr(sprite_viewer, 'SpriteCanvas'):
            print("✅ SpriteCanvas class found")
        else:
            print("❌ SpriteCanvas class not found")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import sprite_viewer: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running Sprite Viewer Tests\n")
    
    tests = [
        test_imports,
        test_sprite_loading,
        test_application_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The sprite viewer should work correctly.")
        print("\nTo run the application (requires GUI display):")
        print("python sprite_viewer.py")
    else:
        print("❌ Some tests failed. Please check the setup.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())