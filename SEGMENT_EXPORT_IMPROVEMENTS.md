# Animation Segment Export Improvements

## Overview
Enhanced the export functionality to better support animation segments, making "Segments Per Row" export more prominent and adding direct export options from segment UI elements.

## Changes Made

### 1. Export Type Selection Enhancement
**File:** `export/steps/type_selection.py`
- Added segment detection to automatically recommend "Segments Per Row" when segments exist
- Reordered export options to prioritize "Segments Per Row" when segments are detected
- Added visual emphasis with blue border and recommendation banner
- Pre-selects "Segments Per Row" option when animation segments exist

### 2. Segment Preview Export Menu
**File:** `ui/animation_segment_preview.py`
- Added context menu to individual segment preview items
- Right-click on any segment shows export options:
  - Export as Individual Frames
  - Export as Sprite Sheet
- Emits `exportRequested` signal with segment name

### 3. Grid View Export Menu
**File:** `ui/animation_grid_view.py`
- Enhanced right-click menu for frames that are part of segments
- Added segment-specific submenu with export options
- Detects which segment a frame belongs to
- Provides quick access to export individual segments

### 4. Controller Integration
**File:** `core/animation_segment_controller.py`
- Added `_on_export_requested` handler for export signals
- Connected export signals from both grid view and preview panel
- Routes export requests to the existing export dialog
- Automatically extracts frames for the selected segment

## User Workflow

### Creating and Exporting Segments:
1. **Create Segments:** Select frames in grid view → Right-click → "Create Animation Segment"
2. **Export Options:**
   - **Option A:** Animation menu → Export Sprites → "Segments Per Row" is highlighted
   - **Option B:** Right-click on segment in preview panel → Export Segment
   - **Option C:** Right-click on frame in grid → Segment menu → Export options

### Export Result:
When using "Segments Per Row" export:
- Each animation segment becomes one row in the sprite sheet
- Segments can have different numbers of frames
- Maintains visual organization for game engines and animation tools

## Technical Details

### Signal Flow:
```
User Action → UI Component → exportRequested Signal → Controller → Export Dialog
```

### Key Components:
- **ExportTypeStepSimple:** Enhanced to detect and recommend segment export
- **SegmentPreviewItem:** Added context menu with export options
- **AnimationGridView:** Enhanced right-click menu for segment-aware export
- **AnimationSegmentController:** Handles export routing and frame extraction

## Benefits

1. **Improved Discoverability:** "Segments Per Row" is now prominently featured when segments exist
2. **Direct Export:** Can export individual segments without going through full export dialog
3. **Contextual Actions:** Right-click menus provide quick access to relevant export options
4. **Maintains Organization:** Exported sprite sheets preserve segment structure

## Testing

Created `test_segment_export.py` to verify:
- Context menu functionality
- Signal emission and connection
- Export request handling

The implementation successfully addresses the requirement: "I want every segment to be a row on the exportable sprite sheet (regardless if there are different number of frames)"