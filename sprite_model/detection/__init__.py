"""
Auto-Detection Module
====================

Intelligent algorithms for automatically detecting sprite sheet parameters:
- Margin detection: Find sprite sheet borders
- Spacing detection: Detect gaps between frames
- Frame size detection: Determine optimal frame dimensions
- Comprehensive detection: Combined workflow with validation
"""

from .margin_detector import MarginDetector
from .spacing_detector import SpacingDetector  
from .frame_detector import FrameDetector
from .comprehensive_detector import ComprehensiveDetector

__all__ = [
    'MarginDetector',
    'SpacingDetector',
    'FrameDetector', 
    'ComprehensiveDetector'
]