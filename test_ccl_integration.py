#!/usr/bin/env python3
"""
Test the CCL integration in sprite_model.py
"""

import sys
import os
sys.path.insert(0, '.')

# Mock PySide6 for testing without GUI
class MockQObject:
    def __init__(self):
        pass

class MockSignal:
    def __init__(self, *args):
        pass
    def emit(self, *args):
        pass

class MockQPixmap:
    def __init__(self, path):
        self.path = path
        self._null = False
        
    def isNull(self):
        return self._null
        
    def width(self):
        return 1920 if "Lancer_Run" in self.path else 768
        
    def height(self):
        return 320 if "Lancer" in self.path else 192

class MockQTimer:
    def __init__(self):
        pass
    def start(self, ms):
        pass
    def stop(self):
        pass

# Mock the PySide6 modules
sys.modules['PySide6'] = type(sys)('PySide6')
sys.modules['PySide6.QtCore'] = type(sys)('QtCore')
sys.modules['PySide6.QtWidgets'] = type(sys)('QtWidgets')
sys.modules['PySide6.QtGui'] = type(sys)('QtGui')

sys.modules['PySide6.QtCore'].QObject = MockQObject
sys.modules['PySide6.QtCore'].Signal = MockSignal
sys.modules['PySide6.QtCore'].QTimer = MockQTimer
sys.modules['PySide6.QtCore'].QRect = lambda x, y, w, h: (x, y, w, h)
sys.modules['PySide6.QtGui'].QPixmap = MockQPixmap
sys.modules['PySide6.QtGui'].QPainter = object
sys.modules['PySide6.QtGui'].QColor = object
sys.modules['PySide6.QtWidgets'].QApplication = object

# Now import sprite_model
from sprite_model import SpriteModel

def test_ccl_integration():
    """Test CCL detection integration in SpriteModel."""
    print("🧪 Testing CCL Integration in SpriteModel")
    print("=" * 50)
    
    model = SpriteModel()
    
    test_sprites = [
        "spritetests/Lancer_Run.png",
        "spritetests/Lancer_Idle.png", 
        "spritetests/Archer_Run.png"
    ]
    
    for sprite_path in test_sprites:
        if not os.path.exists(sprite_path):
            print(f"❌ {sprite_path} not found")
            continue
            
        print(f"\n🔍 Testing {sprite_path}")
        print("-" * 40)
        
        # Load sprite
        success, error = model.load_sprite_sheet(sprite_path)
        if not success:
            print(f"❌ Failed to load: {error}")
            continue
            
        print("✅ Sprite loaded successfully")
        
        # Run comprehensive auto-detection
        try:
            success, report = model.comprehensive_auto_detect()
            
            print(f"Detection Success: {success}")
            print(f"Final Settings:")
            print(f"  Frame Size: {model._frame_width}×{model._frame_height}")
            print(f"  Margins: ({model._offset_x}, {model._offset_y})")
            print(f"  Spacing: ({model._spacing_x}, {model._spacing_y})")
            
            if "CCL detection" in report:
                print("🎉 CCL detection was used!")
            elif "content-based" in report.lower():
                print("📄 Content-based detection was used")
            elif "rectangular" in report.lower():
                print("📐 Rectangular detection was used")
            else:
                print("🔧 Legacy detection was used")
                
        except Exception as e:
            print(f"❌ Detection failed: {e}")

if __name__ == "__main__":
    test_ccl_integration()