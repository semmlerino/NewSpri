"""
Frame Extraction Module
======================

Handles different methods of extracting frames from sprite sheets:
- Grid-based extraction: Regular grid patterns
- CCL extraction: Connected-component labeling for irregular sprites
- Background detection: Color key detection for transparency
"""

from .background_detector import detect_background_color
from .ccl_extractor import CCLExtractor, detect_sprites_ccl_enhanced
from .grid_extractor import GridConfig, GridExtractor, GridLayout

__all__ = [
    'CCLExtractor',
    'GridConfig',
    'GridExtractor',
    'GridLayout',
    'detect_background_color',
    'detect_sprites_ccl_enhanced',
]
