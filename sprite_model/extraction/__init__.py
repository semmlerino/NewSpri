"""
Frame Extraction Module
======================

Handles different methods of extracting frames from sprite sheets:
- Grid-based extraction: Regular grid patterns
- CCL extraction: Connected-component labeling for irregular sprites
- Background detection: Color key detection for transparency
"""

from .background_detector import detect_background_color, BackgroundDetector
from .ccl_extractor import detect_sprites_ccl_enhanced, CCLExtractor
from .grid_extractor import GridExtractor, GridConfig, GridLayout

__all__ = [
    'detect_background_color',
    'BackgroundDetector',
    'detect_sprites_ccl_enhanced',
    'CCLExtractor',
    'GridExtractor',
    'GridConfig', 
    'GridLayout'
]