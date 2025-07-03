"""
UI package - User interface components.

Contains all UI widgets and visual components:
- Core display widgets (canvas, playback controls)
- Specialized widgets (frame extractor, animation grid)
- Common UI utilities and validation widgets
- Status bar and progress indicators
"""

# Import main UI components
from .sprite_canvas import SpriteCanvas
from .playback_controls import PlaybackControls
from .frame_extractor import FrameExtractor
from .animation_grid_view import AnimationGridView
from .animation_segment_widget import AnimationSegmentSelector
from .animation_segment_preview import AnimationSegmentPreview
from .enhanced_status_bar import EnhancedStatusBar, StatusBarManager

__all__ = [
    'SpriteCanvas',
    'PlaybackControls', 
    'FrameExtractor',
    'AnimationGridView',
    'AnimationSegmentSelector',
    'AnimationSegmentPreview',
    'EnhancedStatusBar',
    'StatusBarManager'
]