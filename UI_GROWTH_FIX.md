# UI Growth Issue Fix

## Problem
The sprite viewer had a critical usability bug where the "Sprite Sheet Info" section would grow taller each time settings were changed, pushing the entire UI down and making it unusable.

## Root Cause
In the `_slice_sprite_sheet()` method, the code was **appending** to the existing info text instead of replacing it:

```python
# OLD BUGGY CODE:
self._info_label.setText(
    self._info_label.text() +  # ← This appends!
    f"<br><b>Frames:</b> {total_frames}"
)
```

Every time frame extraction settings changed (size, offset, etc.), this would add more lines to the info display, causing infinite growth.

## Solution
1. **Separated basic info storage**: Added `self._sprite_sheet_info` to store base file information
2. **Replace instead of append**: Build complete info text from scratch each time
3. **Added height constraints**: Set maximum height for info group to prevent UI breaking
4. **Better state management**: Proper reset of info when no sprite is loaded

## Changes Made

### 1. Added Separate Info Storage
```python
self._sprite_sheet_info = ""  # Store basic info separately
```

### 2. Store Basic Info in Load Method
```python
# Store basic info separately
self._sprite_sheet_info = (
    f"<b>File:</b> {file_name}<br>"
    f"<b>Size:</b> {pixmap.width()} × {pixmap.height()} px<br>"
    f"<b>Format:</b> {Path(file_path).suffix.upper()[1:]}"
)
```

### 3. Build Complete Info in Slice Method
```python
# Build complete info text from scratch
frame_info = (
    f"<br><b>Frames:</b> {total_frames} "
    f"({frames_per_row}×{frames_per_col})<br>"
    f"<b>Frame size:</b> {frame_width}×{frame_height} px"
)
self._info_label.setText(self._sprite_sheet_info + frame_info)
```

### 4. Added Height Constraints
```python
info_group.setMaximumHeight(120)  # Prevent growing
self._info_label.setAlignment(Qt.AlignTop)
```

### 5. Proper State Reset
```python
def _show_welcome_message(self):
    # Reset info label to default state
    self._sprite_sheet_info = ""
    self._info_label.setText("No sprite sheet loaded")
```

## Result
- ✅ Info section no longer grows with each setting change
- ✅ UI remains stable and usable
- ✅ Proper info updates with current frame extraction settings
- ✅ Clean reset when no sprite is loaded
- ✅ Height-constrained info area prevents UI breaking

## Before vs After

### Before (Buggy):
```
Load sprite → Info shows file details
Change frame size → Info shows file details + frame info
Change offset → Info shows file details + frame info + frame info
...continues growing infinitely
```

### After (Fixed):
```
Load sprite → Info shows file details
Change frame size → Info shows file details + current frame info
Change offset → Info shows file details + updated frame info
...always shows complete, current info only
```

The UI now maintains consistent height and provides accurate, up-to-date information without growing uncontrollably.