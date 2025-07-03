# Segment Export Fix Summary

## Issues Fixed

### 1. Preview Format Issue
**Problem**: The preview showed incorrect format for "Segments Per Row" export mode.

**Root Cause**: 
- ModernExportSettings wasn't receiving the segment_manager parameter
- No special preview generation for segments_per_row mode

**Fix**:
- Added `segment_manager` parameter to ModernExportSettings constructor in export_wizard.py
- Updated ModernExportSettings to accept and store segment_manager
- Added `_generate_segments_preview()` method to handle segments per row preview
- Modified `_update_preview()` to use the new method for segments_sheet mode

### 2. Export Crash
**Problem**: Application crashed when trying to export with "Segments Per Row" mode.

**Root Cause**:
- Preview generation tried to access segment data that wasn't available
- Potential null pointer access when calculating segment layouts

**Fix**:
- Ensured sprite_sheet_layout is properly created and added to config
- Added proper error handling in preview generation
- Preview now shows placeholder text when segments are not available

## Files Modified

1. **export/dialogs/export_wizard.py**
   - Pass segment_manager to ModernExportSettings (line 80)
   - Ensure sprite_sheet_layout is added to config (line 271)

2. **export/steps/modern_settings_preview.py**
   - Add segment_manager parameter to constructor (line 131)
   - Add special handling for segments_sheet mode (line 883-884)
   - Implement _generate_segments_preview() method (lines 956-1073)

## How It Works Now

1. When "Segments Per Row" is selected, the preview:
   - Checks if segment_manager is available
   - Gets all segments and calculates the layout (one row per segment)
   - Shows each segment as a row with all its frames
   - Scales the preview if it's too large
   - Shows placeholder if no segments are defined

2. During export:
   - The layout is properly configured with mode='segments_per_row'
   - Segment information is passed to the frame exporter
   - Each segment becomes one row in the exported sprite sheet

## Testing

To test the fixes:
1. Load a sprite sheet
2. Create animation segments using the Animation Splitting tab
3. Go to export (Ctrl+E)
4. Select "Segments Per Row" (should be highlighted when segments exist)
5. Preview should show segments arranged in rows
6. Export should work without crashing

The export will create a sprite sheet where:
- Each animation segment occupies one row
- Segments can have different numbers of frames
- Empty spaces are left transparent for shorter segments