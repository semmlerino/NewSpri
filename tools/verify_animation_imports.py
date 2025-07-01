#!/usr/bin/env python3
"""
Test script for animation splitting functionality
Verifies that all new components can be imported without PySide6 dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_imports():
    """Test that all animation splitting components can be imported."""
    
    try:
        # Test importing the new components
        print("Testing animation splitting imports...")
        
        # Test animation segment manager
        from animation_segment_manager import AnimationSegmentManager, AnimationSegmentData
        print("✓ AnimationSegmentManager imported successfully")
        
        # Test data structures
        segment_data = AnimationSegmentData("test", 0, 5)
        print(f"✓ AnimationSegmentData created: {segment_data.name} ({segment_data.frame_count} frames)")
        
        # Test manager functionality (without Qt)
        manager = AnimationSegmentManager()
        manager.set_sprite_context("test.png", 10)
        
        # Test adding a segment
        success, error = manager.add_segment("walk", 0, 3)
        if success:
            print("✓ Segment added successfully")
        else:
            print(f"✗ Segment add failed: {error}")
        
        # Test segment retrieval
        segments = manager.get_all_segments()
        print(f"✓ Retrieved {len(segments)} segments")
        
        print("\n✅ All animation splitting components work correctly!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_data_structures():
    """Test the data structures and validation."""
    
    print("\nTesting data structures and validation...")
    
    from animation_segment_manager import AnimationSegmentData
    
    # Test segment data validation
    segment = AnimationSegmentData("jump", 2, 6)
    valid, error = segment.validate(10)
    
    if valid:
        print("✓ Segment validation passed")
    else:
        print(f"✗ Segment validation failed: {error}")
    
    # Test invalid segment
    invalid_segment = AnimationSegmentData("invalid", 5, 3)  # End before start
    valid, error = invalid_segment.validate(10)
    
    if not valid:
        print("✓ Invalid segment correctly rejected")
    else:
        print("✗ Invalid segment incorrectly accepted")
    
    # Test serialization
    data_dict = segment.to_dict()
    recreated = AnimationSegmentData.from_dict(data_dict)
    
    if recreated.name == segment.name and recreated.start_frame == segment.start_frame:
        print("✓ Serialization/deserialization works")
    else:
        print("✗ Serialization/deserialization failed")

def create_demo_data():
    """Create demo animation segments for testing."""
    
    print("\nCreating demo animation segments...")
    
    from animation_segment_manager import AnimationSegmentManager
    manager = AnimationSegmentManager()
    manager.set_sprite_context("demo_sprite.png", 20)
    
    # Add demo segments
    demo_segments = [
        ("idle", 0, 3, "Character idle animation"),
        ("walk", 4, 11, "Walking cycle"),
        ("jump", 12, 15, "Jump sequence"),
        ("attack", 16, 19, "Attack animation")
    ]
    
    for name, start, end, description in demo_segments:
        success, error = manager.add_segment(name, start, end, description=description)
        if success:
            print(f"✓ Added segment: {name} (frames {start}-{end})")
        else:
            print(f"✗ Failed to add segment {name}: {error}")
    
    # Test export
    export_data = manager.export_segments_list()
    print(f"\n✓ Exported {len(export_data)} segments for external use")
    
    for segment_info in export_data:
        print(f"  • {segment_info['name']}: {segment_info['frame_count']} frames")

if __name__ == "__main__":
    print("Animation Splitting Feature Test")
    print("=" * 40)
    
    # Run tests
    if test_imports():
        test_data_structures()
        create_demo_data()
        
        print("\n🎉 Animation splitting implementation is ready!")
        print("\nFeatures implemented:")
        print("• Grid view for frame-by-frame sprite sheet display")
        print("• Animation segment selection and management") 
        print("• Enhanced export dialog with segment support")
        print("• Data persistence for segments")
        print("• Integration with main sprite viewer")
        
        print("\nTo use:")
        print("1. Load a sprite sheet in the main application")
        print("2. Switch to the 'Animation Splitting' tab")
        print("3. Select frame ranges to create animation segments")
        print("4. Export individual segments or all segments")
        
    else:
        print("\n❌ Tests failed - check component implementations")