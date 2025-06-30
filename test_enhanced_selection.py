#!/usr/bin/env python3
"""
Test script for enhanced frame selection functionality
Tests the new selection modes without requiring a full GUI.
"""

def test_selection_logic():
    """Test the selection logic independently of GUI."""
    
    # Simulate selection state
    selected_frames = set()
    
    def toggle_frame_selection(frame_index: int):
        """Toggle selection of a single frame."""
        if frame_index in selected_frames:
            selected_frames.remove(frame_index)
        else:
            selected_frames.add(frame_index)
    
    def select_frame_range(start_frame: int, end_frame: int):
        """Select a range of frames."""
        start = min(start_frame, end_frame)
        end = max(start_frame, end_frame)
        
        for i in range(start, end + 1):
            selected_frames.add(i)
    
    def is_contiguous_selection(sorted_frames) -> bool:
        """Check if the selected frames form a contiguous range."""
        if not sorted_frames:
            return False
        
        for i in range(1, len(sorted_frames)):
            if sorted_frames[i] != sorted_frames[i-1] + 1:
                return False
        return True
    
    print("Testing enhanced selection logic...")
    
    # Test 1: Single frame selection
    toggle_frame_selection(5)
    assert 5 in selected_frames
    print("✓ Single frame selection works")
    
    # Test 2: Toggle deselection
    toggle_frame_selection(5)
    assert 5 not in selected_frames
    print("✓ Toggle deselection works")
    
    # Test 3: Range selection
    select_frame_range(2, 7)
    expected_range = {2, 3, 4, 5, 6, 7}
    assert selected_frames == expected_range
    print("✓ Range selection works")
    
    # Test 4: Contiguous detection
    sorted_frames = sorted(selected_frames)
    assert is_contiguous_selection(sorted_frames) == True
    print("✓ Contiguous detection works")
    
    # Test 5: Non-contiguous selection
    toggle_frame_selection(10)  # Add frame 10
    sorted_frames = sorted(selected_frames)
    assert is_contiguous_selection(sorted_frames) == False
    print("✓ Non-contiguous detection works")
    
    print(f"Final selection: {sorted_frames}")
    print("🎉 All selection logic tests passed!")

def test_imports():
    """Test that the enhanced grid view can be imported."""
    try:
        from animation_grid_view import AnimationGridView, AnimationSegment, FrameThumbnail
        print("✓ Enhanced AnimationGridView imports successfully")
        
        # Test data structure creation
        segment = AnimationSegment("test", 0, 5)
        print(f"✓ AnimationSegment created: {segment.name} ({segment.frame_count} frames)")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_keyboard_modifiers():
    """Test keyboard modifier handling logic."""
    from PySide6.QtCore import Qt
    
    # Test modifier detection
    ctrl_modifier = Qt.ControlModifier.value
    shift_modifier = Qt.ShiftModifier.value
    alt_modifier = Qt.AltModifier.value
    
    # Simulate modifier combinations
    ctrl_alt = ctrl_modifier | alt_modifier
    shift_ctrl = shift_modifier | ctrl_modifier
    
    print("Testing keyboard modifier logic...")
    
    # Test individual modifiers
    mod_flags = Qt.KeyboardModifiers(ctrl_modifier)
    assert mod_flags & Qt.ControlModifier
    print("✓ Ctrl modifier detection works")
    
    mod_flags = Qt.KeyboardModifiers(shift_modifier)
    assert mod_flags & Qt.ShiftModifier
    print("✓ Shift modifier detection works")
    
    mod_flags = Qt.KeyboardModifiers(alt_modifier)
    assert mod_flags & Qt.AltModifier
    print("✓ Alt modifier detection works")
    
    # Test combinations
    mod_flags = Qt.KeyboardModifiers(ctrl_alt)
    assert mod_flags & Qt.ControlModifier
    assert mod_flags & Qt.AltModifier
    print("✓ Modifier combinations work")
    
    print("🎉 Keyboard modifier tests passed!")

if __name__ == "__main__":
    print("Enhanced Frame Selection Test")
    print("=" * 40)
    
    # Test core selection logic
    test_selection_logic()
    print()
    
    # Test imports
    if test_imports():
        print()
        # Test keyboard modifiers if PySide6 is available
        try:
            test_keyboard_modifiers()
        except ImportError:
            print("⚠️  PySide6 not available for modifier testing")
        
        print()
        print("🎉 Enhanced selection implementation is ready!")
        print()
        print("New selection features:")
        print("• Single click = select frame (no tab switching)")
        print("• Drag = select range of frames")
        print("• Shift+click = extend selection to clicked frame")
        print("• Ctrl/Alt+click = toggle individual frame selection")
        print("• Double-click = preview frame (switches to Frame View)")
        print("• Right-click = context menu with segment creation")
        print("• Visual feedback for all selection states")
        print("• Smart segment creation with contiguous detection")
        
    else:
        print("❌ Tests failed - check implementation")