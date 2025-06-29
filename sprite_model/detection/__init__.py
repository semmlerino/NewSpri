"""
Detection Module
================

Automatic detection algorithms for sprite sheets including frame size, margins, and spacing.
"""

from .frame_detector import FrameDetector, detect_frame_size, detect_rectangular_frames, detect_content_based
from .margin_detector import MarginDetector, detect_margins
from .spacing_detector import SpacingDetector, detect_spacing
from .coordinator import DetectionCoordinator, DetectionResult, comprehensive_auto_detect

__all__ = [
    'FrameDetector', 'detect_frame_size', 'detect_rectangular_frames', 'detect_content_based',
    'MarginDetector', 'detect_margins',
    'SpacingDetector', 'detect_spacing', 
    'DetectionCoordinator', 'DetectionResult', 'comprehensive_auto_detect'
]