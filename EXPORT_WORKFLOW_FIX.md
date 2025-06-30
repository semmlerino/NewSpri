# Export Workflow Fix - Clear Animation Segment Export

## Problem Fixed
The "Export Selected" button in Animation Splitting was confusing because:
1. **Clicking a segment in the list automatically switched to Frame View tab**
2. **This took you away from the Animation Splitting tab where the export button is**
3. **The export button didn't show which segment was selected**
4. **No clear way to preview segments without losing your place**

## Solution Implemented

### 1. Fixed Tab Switching Behavior
- **Single-click on segment**: Now just selects it (stays in Animation Splitting tab)
- **Double-click on segment**: Previews it (switches to Frame View tab)

### 2. Enhanced Export Button
- **Shows selected segment name**: "Export 'Walk_Animation'" instead of generic "Export Selected"
- **Disabled when nothing selected**: Button is grayed out until you select a segment
- **Clear visual feedback**: You can see exactly which segment will be exported

### 3. Added Clear Instructions
- **In segment panel**: "Click to select • Double-click to preview"
- **In status bar**: Shows selected segment with export hint

## How to Use Animation Segment Export

### Step 1: Create Animation Segments
1. Load your sprite sheet (like Ark.png)
2. Switch to "Animation Splitting" tab
3. Select frames for an animation (click, drag, shift+click, ctrl+click)
4. Click "Create Animation Segment"
5. Name your animation (e.g., "Walk", "Attack", "Idle")

### Step 2: Export Animation Segments
1. **Stay in Animation Splitting tab**
2. **Click once** on the segment you want to export in the right panel
3. **Export button updates** to show "Export 'YourSegmentName'"
4. **Click the export button** to export that specific segment
5. **Choose export settings** in the dialog that opens

### Step 3: Preview Segments (Optional)
- **Double-click** any segment in the list to preview it in Frame View
- This helps verify you have the right frames before exporting

## Export Options Available

When you click "Export Selected", you get these options:

### Individual Frames
- Exports each frame as a separate file
- Files named like: `walk_001.png`, `walk_002.png`, etc.

### Sprite Sheet
- Combines all segment frames into one image
- Creates a single file with all frames arranged in a grid

### Animated GIF
- Creates an animated GIF of your segment
- Adjustable speed and loop settings

### Batch Export
- You can also use File > Export Frames and switch to "Animation Segments" tab
- Select multiple segments to export at once

## Visual Workflow

```
Animation Splitting Tab:
┌─────────────────────────────────────┬─────────────────┐
│ Frame Grid (Select frames here)     │ Animation Segments │
│ [🖼️][🖼️][🖼️][🖼️][🖼️][🖼️][🖼️][🖼️]         │ Click to select    │
│ [🖼️][🖼️][🖼️][🖼️][🖼️][🖼️][🖼️][🖼️]         │ Double-click preview│
│ [🖼️][🖼️][🖼️][🖼️][🖼️][🖼️][🖼️][🖼️]         │                 │
│                                     │ ◆ Walk Animation   │ ← Click this
│ [Create Animation Segment]         │ ◇ Attack Cycle     │
│ [Clear Selection]                  │ ◇ Idle Loop        │
│                                     │                 │
│                                     │ [Export 'Walk']    │ ← Then click this
└─────────────────────────────────────┴─────────────────┘
```

## Key Improvements

✅ **No more tab confusion** - Single-click doesn't switch tabs
✅ **Clear export target** - Button shows which segment you're exporting  
✅ **Easy preview** - Double-click to preview without losing your place
✅ **Visual feedback** - Selected segments are clearly indicated
✅ **Intuitive workflow** - Select → Export, or Double-click → Preview

## Status Bar Messages

The status bar now provides helpful guidance:
- `"Selected segment 'Walk' (frames 0-7) - Use 'Export Selected' to export"`
- `"Previewing segment 'Walk' (frames 0-7)"`

This makes it crystal clear what you're doing and what the next step is.

## Testing the Fix

1. Load Ark.png in the sprite viewer
2. Switch to Animation Splitting tab
3. Create a few animation segments
4. Try clicking vs double-clicking segments
5. Notice how the export button changes
6. Export a segment and verify it works

The export workflow is now intuitive and clear!