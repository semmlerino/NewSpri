#!/usr/bin/env python3
"""
Test console logging for CCL detection.
"""

import sys
sys.path.insert(0, '.')

# Import the CCL function directly
from sprite_model import detect_sprites_ccl_enhanced, CCL_AVAILABLE

def test_console_logging():
    """Test that CCL detection logs to console."""
    print("🧪 Testing Console Logging for CCL Detection")
    print("=" * 50)
    
    if not CCL_AVAILABLE:
        print("❌ CCL not available, cannot test console logging")
        return
    
    # Test with a known sprite file
    test_file = "spritetests/Lancer_Run.png"
    
    print(f"Testing console logging with: {test_file}")
    print("-" * 40)
    
    # Run CCL detection - should print to console
    result = detect_sprites_ccl_enhanced(test_file)
    
    print("-" * 40)
    print("Console logging test complete!")
    
    if result and result.get('success'):
        print(f"✅ Result: {result['frame_width']}×{result['frame_height']}, {result['sprite_count']} sprites")
    else:
        print(f"❌ Detection failed")

if __name__ == "__main__":
    test_console_logging()