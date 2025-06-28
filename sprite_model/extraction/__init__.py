"""
Frame Extraction Module
======================

Handles different methods of extracting frames from sprite sheets:
- Grid-based extraction: Regular grid patterns
- CCL extraction: Connected-component labeling for irregular sprites
- Background detection: Color key detection for transparency
"""

from .background_detector import detect_background_color
from .ccl_extractor import detect_sprites_ccl_enhanced
# TODO: Grid extractor will be added in Phase 3
# from .grid_extractor import GridExtractor

__all__ = [
    'detect_background_color',
    'detect_sprites_ccl_enhanced'
    # TODO: Add 'GridExtractor' when Phase 3 is complete
]