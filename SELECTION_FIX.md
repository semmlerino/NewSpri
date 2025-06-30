# Selection Fix - Resolving Janky Multi-Frame Selection

## Problem
The multi-frame selection was "janky" - selections would randomly disappear when clicking or moving the mouse slightly. This made it difficult to build reliable multi-frame selections.

## Root Causes
1. **Over-sensitive drag detection** - 3 pixel threshold triggered accidental drags
2. **Aggressive selection clearing** - Any drag operation immediately cleared all selections
3. **No state preservation** - Existing selections were lost during drag operations
4. **Mouse event conflicts** - Click and drag events interfered with each other

## Solution

### 1. Increased Drag Threshold
```python
# Before: self._drag_threshold = 3
# After:  self._drag_threshold = 8  # Less sensitive
```
This reduces accidental drag detection from tiny mouse movements.

### 2. Smart Drag Start Logic
```python
def _on_drag_started(self, frame_index: int):
    # Store current selection before starting drag
    self._pre_drag_selection = self._selected_frames.copy()
    
    # Only clear selection if dragging from unselected frame
    if frame_index not in self._selected_frames:
        self._clear_selection()
        self._select_frame(frame_index)
        self._pre_drag_selection = self._selected_frames.copy()
    else:
        # Preserve existing selection when dragging from selected frame
        print(f"DEBUG: Extending selection from frame {frame_index}")
```

### 3. Preserved Selection State During Drag
```python
def _update_drag_selection(self, start_frame: int, end_frame: int):
    # Start with pre-drag selection (preserve existing selections)
    if hasattr(self, '_pre_drag_selection'):
        self._selected_frames = self._pre_drag_selection.copy()
    
    # Add the current drag range
    for i in range(start, end + 1):
        if i < len(self._thumbnails):
            self._selected_frames.add(i)
```

### 4. Proper State Cleanup
Added cleanup in multiple locations:
- `mouseReleaseEvent()` - Clean up when drag ends
- `_clear_selection()` - Clean up when selection is cleared
- Proper state management throughout drag operations

## Fixed Behaviors

### Before the Fix
- ❌ Selections disappeared randomly
- ❌ Tiny mouse movements triggered drags
- ❌ Multi-select was unreliable
- ❌ Dragging from selected frames cleared everything
- ❌ Selection state was lost during operations

### After the Fix
- ✅ Selections are preserved reliably
- ✅ Only intentional drags are detected (8+ pixel movement)
- ✅ Multi-select works consistently
- ✅ Dragging from selected frames extends selection
- ✅ Selection state is maintained throughout operations

## Enhanced Selection Modes

The fix maintains all advanced selection modes while making them reliable:

1. **Single Click** - Select individual frame
2. **Click & Drag** - Select range (more intentional threshold)
3. **Shift+Click** - Extend selection range
4. **Ctrl/Alt+Click** - Toggle individual frames (multi-select)
5. **Double-Click** - Preview frame
6. **Drag from selected** - Extend existing selection without clearing

## Usage Verification

To test the improved selection:

1. Load a sprite sheet in Animation Splitting tab
2. Try clicking multiple frames - selections should stay
3. Try Ctrl+clicking to build multi-selections - should be reliable
4. Try dragging from selected frames - should extend, not clear
5. Small mouse movements during clicks should not trigger drags

## Files Modified

- `animation_grid_view.py` - Main selection logic improvements
- Added debug output for selection operations
- Enhanced state management and cleanup

The selection system is now robust and predictable, eliminating the "janky" behavior reported by the user.