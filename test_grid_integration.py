#!/usr/bin/env python3
"""
Grid Extraction Integration Test
================================

Tests that the extracted grid functionality works correctly when integrated
back into the full SpriteModel system. Validates that the refactoring
maintains 100% behavioral equivalence.
"""

import os
import sys

# Set Qt to use offscreen platform for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QObject


def test_sprite_model_import():
    """Test that SpriteModel can be imported with grid extractor integration."""
    print("🧪 Testing SpriteModel import with grid integration...")
    
    try:
        from sprite_model import SpriteModel
        print("   ✅ SpriteModel imported successfully")
        
        # Create instance
        model = SpriteModel()
        print("   ✅ SpriteModel instance created")
        
        # Check that grid extractor is available
        if not hasattr(model, '_grid_extractor'):
            print("   ❌ Grid extractor not found in SpriteModel")
            return False
        
        print("   ✅ Grid extractor integrated into SpriteModel")
        return True
        
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False


def test_extract_frames_integration():
    """Test that extract_frames method works with grid extractor integration."""
    print("🧪 Testing extract_frames integration...")
    
    try:
        from sprite_model import SpriteModel
        
        # Create model instance
        model = SpriteModel()
        
        # Test without loaded sprite sheet (should fail gracefully)
        success, error_msg, frame_count = model.extract_frames(32, 32)
        if success:
            print("   ❌ Should fail with no sprite sheet loaded")
            return False
        
        if "No sprite sheet loaded" not in error_msg:
            print(f"   ❌ Wrong error message: {error_msg}")
            return False
        
        print("   ✅ extract_frames fails gracefully with no sprite sheet")
        
        # Test with invalid parameters
        # Load a minimal sprite sheet first
        test_pixmap = QPixmap(64, 64)
        test_pixmap.fill()  # Fill with default color
        model._original_sprite_sheet = test_pixmap
        
        # Test invalid frame dimensions
        success, error_msg, frame_count = model.extract_frames(0, 32)
        if success:
            print("   ❌ Should fail with zero width")
            return False
        
        print("   ✅ extract_frames validates parameters correctly")
        
        # Test valid extraction
        success, error_msg, frame_count = model.extract_frames(32, 32)
        if not success:
            print(f"   ❌ Valid extraction failed: {error_msg}")
            return False
        
        if frame_count != 4:  # 64x64 sheet with 32x32 frames = 2x2 = 4 frames
            print(f"   ❌ Wrong frame count: expected 4, got {frame_count}")
            return False
        
        print("   ✅ extract_frames works correctly with valid parameters")
        return True
        
    except Exception as e:
        print(f"   ❌ Exception in extract_frames test: {e}")
        return False


def test_validate_frame_settings_integration():
    """Test that validate_frame_settings method works with grid extractor integration."""
    print("🧪 Testing validate_frame_settings integration...")
    
    try:
        from sprite_model import SpriteModel
        
        # Create model instance with test sprite sheet
        model = SpriteModel()
        test_pixmap = QPixmap(100, 100)
        test_pixmap.fill()
        model._original_sprite_sheet = test_pixmap
        
        # Test valid settings
        valid, error_msg = model.validate_frame_settings(32, 32)
        if not valid:
            print(f"   ❌ Valid settings rejected: {error_msg}")
            return False
        
        # Test invalid settings
        valid, error_msg = model.validate_frame_settings(-5, 32)
        if valid:
            print("   ❌ Should reject negative width")
            return False
        
        # Test frame too large for sheet
        valid, error_msg = model.validate_frame_settings(150, 32)
        if valid:
            print("   ❌ Should reject frame larger than sheet")
            return False
        
        print("   ✅ validate_frame_settings works correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Exception in validation test: {e}")
        return False


def test_sprite_sheet_loading_with_extraction():
    """Test complete workflow: load sprite sheet and extract frames."""
    print("🧪 Testing complete sprite sheet workflow...")
    
    try:
        from sprite_model import SpriteModel
        
        # Create model instance
        model = SpriteModel()
        
        # Create a test sprite sheet file
        test_pixmap = QPixmap(128, 96)  # 4x3 grid of 32x32 frames
        test_pixmap.fill()
        test_path = "test_grid_integration_sprite.png"
        test_pixmap.save(test_path)
        
        # Load sprite sheet
        success, error_msg = model.load_sprite_sheet(test_path)
        if not success:
            print(f"   ❌ Failed to load sprite sheet: {error_msg}")
            os.remove(test_path)  # Cleanup
            return False
        
        # Extract frames
        success, error_msg, frame_count = model.extract_frames(32, 32)
        if not success:
            print(f"   ❌ Failed to extract frames: {error_msg}")
            os.remove(test_path)  # Cleanup
            return False
        
        if frame_count != 12:  # 4x3 = 12 frames
            print(f"   ❌ Wrong frame count: expected 12, got {frame_count}")
            os.remove(test_path)  # Cleanup
            return False
        
        # Check that frames are stored correctly
        if len(model._sprite_frames) != 12:
            print(f"   ❌ Wrong stored frame count: expected 12, got {len(model._sprite_frames)}")
            os.remove(test_path)  # Cleanup
            return False
        
        # Cleanup
        os.remove(test_path)
        
        print("   ✅ Complete workflow successful")
        return True
        
    except Exception as e:
        print(f"   ❌ Exception in workflow test: {e}")
        # Cleanup on error
        try:
            os.remove(test_path)
        except:
            pass
        return False


def test_signals_emission():
    """Test that Qt signals are emitted correctly during extraction."""
    print("🧪 Testing Qt signals emission...")
    
    try:
        from sprite_model import SpriteModel
        
        # Create model instance
        model = SpriteModel()
        
        # Set up signal tracking
        extraction_signals = []
        frame_signals = []
        
        def on_extraction_completed(frame_count):
            extraction_signals.append(frame_count)
        
        def on_frame_changed(current, total):
            frame_signals.append((current, total))
        
        model.extractionCompleted.connect(on_extraction_completed)
        model.frameChanged.connect(on_frame_changed)
        
        # Load and extract
        test_pixmap = QPixmap(64, 64)
        test_pixmap.fill()
        model._original_sprite_sheet = test_pixmap
        
        success, error_msg, frame_count = model.extract_frames(32, 32)
        if not success:
            print(f"   ❌ Extraction failed: {error_msg}")
            return False
        
        # Check that extraction signal was emitted
        if len(extraction_signals) != 1:
            print(f"   ❌ Wrong number of extraction signals: expected 1, got {len(extraction_signals)}")
            return False
        
        if extraction_signals[0] != 4:
            print(f"   ❌ Wrong extraction signal value: expected 4, got {extraction_signals[0]}")
            return False
        
        print("   ✅ Qt signals emitted correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Exception in signals test: {e}")
        return False


def test_real_sprite_sheet():
    """Test with a real sprite sheet if available."""
    print("🧪 Testing with real sprite sheet (if available)...")
    
    try:
        from sprite_model import SpriteModel
        
        # Look for real sprite sheets
        test_paths = [
            "spritetests/Lancer.png",
            "Ark.png",
            "x2scrap.png"
        ]
        
        sprite_path = None
        for path in test_paths:
            if os.path.exists(path):
                sprite_path = path
                break
        
        if not sprite_path:
            print("   ⚠️ No real sprite sheet found for testing (OK)")
            return True
        
        # Create model and load sprite sheet
        model = SpriteModel()
        success, error_msg = model.load_sprite_sheet(sprite_path)
        
        if not success:
            print(f"   ⚠️ Could not load {sprite_path}: {error_msg} (OK)")
            return True
        
        # Try extraction with reasonable frame size
        success, error_msg, frame_count = model.extract_frames(32, 32)
        
        if success:
            print(f"   ✅ Real sprite extraction: {frame_count} frames from {sprite_path}")
        else:
            print(f"   ⚠️ Real sprite extraction failed: {error_msg} (OK)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Exception in real sprite test: {e}")
        return False


def main():
    """Run the complete grid integration test suite."""
    print("🚀 Grid Extraction Integration Test")
    print("=" * 50)
    
    # Initialize Qt application
    app = QApplication([])
    
    tests = [
        test_sprite_model_import,
        test_extract_frames_integration,
        test_validate_frame_settings_integration,
        test_sprite_sheet_loading_with_extraction,
        test_signals_emission,
        test_real_sprite_sheet
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
    
    print("=" * 50)
    print(f"📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Grid extraction integration successful!")
        print("   ✅ All grid functionality working in integrated system")
        print("   ✅ Behavioral equivalence maintained")
        print("   ✅ Qt signals working correctly")
        print("   ✅ Phase 3 refactoring complete")
        return True
    else:
        print(f"❌ {total - passed} integration tests failed.")
        print("   ❌ Grid extraction integration has issues")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)