"""Detection algorithms for sprite sheets."""

from .coordinator import DetectionCoordinator, DetectionResult, comprehensive_auto_detect
from .frame_detector import FrameDetector
from .margin_detector import MarginDetector
from .spacing_detector import SpacingDetector

__all__ = [
    'DetectionCoordinator',
    'DetectionResult',
    'FrameDetector',
    'MarginDetector',
    'SpacingDetector',
    'comprehensive_auto_detect',
]
