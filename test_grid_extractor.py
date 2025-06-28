#!/usr/bin/env python3
"""
Test Grid Extractor Module
===========================

Comprehensive tests for the standalone grid-based frame extraction functionality.
Tests all aspects including validation, layout calculation, and frame extraction.
"""

import os
import sys
from pathlib import Path

# Set Qt to use offscreen platform for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QColor, QPainter
from PySide6.QtCore import QRect

# Import the grid extractor module
from sprite_model.extraction.grid_extractor import GridExtractor, GridConfig, extract_grid_frames


class GridExtractorTest:
    """Comprehensive test suite for grid extraction functionality."""
    
    def __init__(self):
        """Initialize test suite."""
        self.extractor = GridExtractor()
        self.test_results = []
        
    def create_test_sprite_sheet(self, width: int, height: int, frame_width: int, frame_height: int,
                                frames_per_row: int, frames_per_col: int, spacing_x: int = 0, spacing_y: int = 0) -> QPixmap:
        """
        Create a test sprite sheet with known frame layout for testing.
        
        Args:
            width: Total sheet width
            height: Total sheet height  
            frame_width: Width of each frame
            frame_height: Height of each frame
            frames_per_row: Number of frames horizontally
            frames_per_col: Number of frames vertically
            spacing_x: Horizontal spacing between frames
            spacing_y: Vertical spacing between frames
            
        Returns:
            QPixmap with test sprite sheet
        """
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(255, 255, 255))  # White background
        
        painter = QPainter(pixmap)
        
        # Draw colored rectangles for each frame
        colors = [
            QColor(255, 0, 0),    # Red
            QColor(0, 255, 0),    # Green  
            QColor(0, 0, 255),    # Blue
            QColor(255, 255, 0),  # Yellow
            QColor(255, 0, 255),  # Magenta
            QColor(0, 255, 255),  # Cyan
        ]
        
        frame_index = 0
        for row in range(frames_per_col):
            for col in range(frames_per_row):
                x = col * (frame_width + spacing_x)
                y = row * (frame_height + spacing_y)
                
                # Use different colors for different frames
                color = colors[frame_index % len(colors)]
                painter.fillRect(QRect(x, y, frame_width, frame_height), color)
                frame_index += 1
        
        painter.end()
        return pixmap
    
    def test_basic_grid_extraction(self) -> bool:
        """Test basic grid extraction without spacing or offsets."""
        print("🧪 Testing basic grid extraction...")
        
        try:
            # Create 4x3 grid of 32x32 frames (128x96 total)
            test_sheet = self.create_test_sprite_sheet(128, 96, 32, 32, 4, 3)
            config = GridConfig(width=32, height=32)
            
            success, error_msg, frames = self.extractor.extract_frames(test_sheet, config)
            
            if not success:
                print(f"   ❌ Extraction failed: {error_msg}")
                return False
            
            if len(frames) != 12:  # 4x3 = 12 frames
                print(f"   ❌ Wrong frame count: expected 12, got {len(frames)}")
                return False
            
            # Verify frame dimensions
            for i, frame in enumerate(frames):
                if frame.width() != 32 or frame.height() != 32:
                    print(f"   ❌ Frame {i} has wrong size: {frame.width()}x{frame.height()}")
                    return False
            
            print("   ✅ Basic grid extraction successful")
            return True
            
        except Exception as e:
            print(f"   ❌ Exception in basic extraction test: {e}")
            return False
    
    def test_grid_with_spacing(self) -> bool:
        """Test grid extraction with spacing between frames."""
        print("🧪 Testing grid extraction with spacing...")
        
        try:
            # Create 3x2 grid of 32x32 frames with 4px spacing (104x68 total)
            test_sheet = self.create_test_sprite_sheet(104, 68, 32, 32, 3, 2, 4, 4)
            config = GridConfig(width=32, height=32, spacing_x=4, spacing_y=4)
            
            success, error_msg, frames = self.extractor.extract_frames(test_sheet, config)
            
            if not success:
                print(f"   ❌ Spacing extraction failed: {error_msg}")
                return False
            
            if len(frames) != 6:  # 3x2 = 6 frames
                print(f"   ❌ Wrong frame count with spacing: expected 6, got {len(frames)}")
                return False
            
            print("   ✅ Grid extraction with spacing successful")
            return True
            
        except Exception as e:
            print(f"   ❌ Exception in spacing test: {e}")
            return False
    
    def test_grid_with_offsets(self) -> bool:
        """Test grid extraction with margin offsets."""
        print("🧪 Testing grid extraction with offsets...")
        
        try:
            # Create 2x2 grid of 32x32 frames with 8px margins (80x80 total)
            test_sheet = self.create_test_sprite_sheet(80, 80, 32, 32, 2, 2)
            config = GridConfig(width=32, height=32, offset_x=8, offset_y=8)
            
            success, error_msg, frames = self.extractor.extract_frames(test_sheet, config)
            
            if not success:
                print(f"   ❌ Offset extraction failed: {error_msg}")
                return False
            
            if len(frames) != 4:  # 2x2 = 4 frames  
                print(f"   ❌ Wrong frame count with offsets: expected 4, got {len(frames)}")
                return False
            
            print("   ✅ Grid extraction with offsets successful")
            return True
            
        except Exception as e:
            print(f"   ❌ Exception in offset test: {e}")
            return False
    
    def test_parameter_validation(self) -> bool:
        """Test parameter validation edge cases."""
        print("🧪 Testing parameter validation...")
        
        try:
            test_sheet = self.create_test_sprite_sheet(100, 100, 32, 32, 3, 3)
            
            # Test invalid frame dimensions
            config = GridConfig(width=0, height=32)
            valid, error_msg = self.extractor.validate_frame_settings(test_sheet, config)
            if valid:
                print("   ❌ Should reject zero width")
                return False
            
            config = GridConfig(width=32, height=-5)
            valid, error_msg = self.extractor.validate_frame_settings(test_sheet, config)
            if valid:
                print("   ❌ Should reject negative height")
                return False
            
            # Test negative offsets
            config = GridConfig(width=32, height=32, offset_x=-5, offset_y=0)
            valid, error_msg = self.extractor.validate_frame_settings(test_sheet, config)
            if valid:
                print("   ❌ Should reject negative X offset")
                return False
            
            # Test negative spacing
            config = GridConfig(width=32, height=32, spacing_x=0, spacing_y=-2)
            valid, error_msg = self.extractor.validate_frame_settings(test_sheet, config)
            if valid:
                print("   ❌ Should reject negative Y spacing")
                return False
            
            # Test frame too large for sheet
            config = GridConfig(width=150, height=32)  # Wider than 100px sheet
            valid, error_msg = self.extractor.validate_frame_settings(test_sheet, config)
            if valid:
                print("   ❌ Should reject frame larger than sheet")
                return False
            
            print("   ✅ Parameter validation working correctly")
            return True
            
        except Exception as e:
            print(f"   ❌ Exception in validation test: {e}")
            return False
    
    def test_layout_calculation(self) -> bool:
        """Test grid layout calculation."""
        print("🧪 Testing grid layout calculation...")
        
        try:
            # Test basic layout
            test_sheet = self.create_test_sprite_sheet(128, 96, 32, 32, 4, 3)
            config = GridConfig(width=32, height=32)
            
            layout = self.extractor.calculate_grid_layout(test_sheet, config)
            if not layout:
                print("   ❌ Layout calculation returned None")
                return False
            
            if layout.frames_per_row != 4:
                print(f"   ❌ Wrong frames per row: expected 4, got {layout.frames_per_row}")
                return False
            
            if layout.frames_per_col != 3:
                print(f"   ❌ Wrong frames per column: expected 3, got {layout.frames_per_col}")
                return False
            
            if layout.total_frames != 12:
                print(f"   ❌ Wrong total frames: expected 12, got {layout.total_frames}")
                return False
            
            print("   ✅ Grid layout calculation successful")
            return True
            
        except Exception as e:
            print(f"   ❌ Exception in layout test: {e}")
            return False
    
    def test_convenience_function(self) -> bool:
        """Test the convenience function for direct extraction."""
        print("🧪 Testing convenience function...")
        
        try:
            test_sheet = self.create_test_sprite_sheet(64, 64, 32, 32, 2, 2)
            
            success, error_msg, frames = extract_grid_frames(test_sheet, 32, 32)
            
            if not success:
                print(f"   ❌ Convenience function failed: {error_msg}")
                return False
            
            if len(frames) != 4:
                print(f"   ❌ Convenience function wrong frame count: expected 4, got {len(frames)}")
                return False
            
            print("   ✅ Convenience function working correctly")
            return True
            
        except Exception as e:
            print(f"   ❌ Exception in convenience function test: {e}")
            return False
    
    def test_real_sprite_sheet(self) -> bool:
        """Test with a real sprite sheet if available."""
        print("🧪 Testing with real sprite sheet...")
        
        try:
            # Look for test sprite sheets
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
            
            # Load the sprite sheet
            test_sheet = QPixmap(sprite_path)
            if test_sheet.isNull():
                print(f"   ⚠️ Could not load {sprite_path} (OK)")
                return True
            
            # Try extraction with reasonable frame size
            config = GridConfig(width=32, height=32)
            success, error_msg, frames = self.extractor.extract_frames(test_sheet, config)
            
            if success:
                print(f"   ✅ Real sprite extraction: {len(frames)} frames from {sprite_path}")
            else:
                print(f"   ⚠️ Real sprite extraction failed: {error_msg} (OK)")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Exception in real sprite test: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all grid extractor tests."""
        print("🚀 Running Grid Extractor Test Suite")
        print("=" * 50)
        
        tests = [
            self.test_basic_grid_extraction,
            self.test_grid_with_spacing,
            self.test_grid_with_offsets,
            self.test_parameter_validation,
            self.test_layout_calculation,
            self.test_convenience_function,
            self.test_real_sprite_sheet
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
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Grid extractor is working correctly.")
            return True
        else:
            print(f"❌ {total - passed} tests failed. Review grid extractor implementation.")
            return False


def main():
    """Run the grid extractor test suite."""
    # Initialize Qt application
    app = QApplication([])
    
    # Run tests
    tester = GridExtractorTest()
    success = tester.run_all_tests()
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)