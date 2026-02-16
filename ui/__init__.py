"""
UI package - User interface components.

Contains all UI widgets and visual components:
- Core display widgets (canvas, playback controls)
- Specialized widgets (frame extractor, animation grid)
- Segment preview/selection and status bar components
- Status bar and progress indicators
"""

# Import main UI components
from .animation_grid_view import AnimationGridView
from .animation_segment_preview import AnimationSegmentPreview
from .animation_segment_widget import AnimationSegmentSelector
from .enhanced_status_bar import EnhancedStatusBar, StatusBarManager
from .frame_extractor import FrameExtractor
from .playback_controls import PlaybackControls
from .sprite_canvas import SpriteCanvas

__all__ = [
    "AnimationGridView",
    "AnimationSegmentPreview",
    "AnimationSegmentSelector",
    "EnhancedStatusBar",
    "FrameExtractor",
    "PlaybackControls",
    "SpriteCanvas",
    "StatusBarManager",
]
