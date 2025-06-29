"""
Detection Algorithm Factory
Factory pattern implementation for creating detection algorithms.
Part of Phase 4 refactoring: Design Pattern Implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Type, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum, auto

from ui_common import DetectionResult


class DetectionType(Enum):
    """Types of detection algorithms available."""
    FRAME_SIZE = auto()
    MARGINS = auto()
    SPACING = auto()
    BACKGROUND = auto()
    CONTENT = auto()


@dataclass
class DetectionConfig:
    """Configuration for detection algorithms."""
    confidence_threshold: float = 0.7
    max_iterations: int = 100
    use_cache: bool = True
    debug_mode: bool = False
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


class DetectionAlgorithm(ABC):
    """Abstract base class for all detection algorithms."""
    
    def __init__(self, config: DetectionConfig):
        self.config = config
        self._cache = {}
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Algorithm name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Algorithm description."""
        pass
    
    @abstractmethod
    def detect(self, sprite_sheet: Any, **kwargs) -> DetectionResult:
        """
        Perform detection on sprite sheet.
        
        Args:
            sprite_sheet: The sprite sheet to analyze
            **kwargs: Additional algorithm-specific parameters
            
        Returns:
            DetectionResult with detection outcome
        """
        pass
    
    def validate_input(self, sprite_sheet: Any) -> Tuple[bool, str]:
        """
        Validate input before detection.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if sprite_sheet is None:
            return False, "No sprite sheet provided"
        
        if not hasattr(sprite_sheet, 'width') or not hasattr(sprite_sheet, 'height'):
            return False, "Invalid sprite sheet format"
        
        if sprite_sheet.width() <= 0 or sprite_sheet.height() <= 0:
            return False, "Invalid sprite sheet dimensions"
        
        return True, ""
    
    def get_cache_key(self, **params) -> str:
        """Generate cache key for parameters."""
        import hashlib
        param_str = str(sorted(params.items()))
        return hashlib.md5(param_str.encode()).hexdigest()


class FrameSizeDetector(DetectionAlgorithm):
    """Detects optimal frame size for sprite sheets."""
    
    name = "Frame Size Detector"
    description = "Analyzes sprite sheet to determine frame dimensions"
    
    def detect(self, sprite_sheet: Any, **kwargs) -> DetectionResult:
        # Validate input
        valid, error = self.validate_input(sprite_sheet)
        if not valid:
            return DetectionResult(success=False, message=error)
        
        # Check cache
        cache_key = self.get_cache_key(
            width=sprite_sheet.width(),
            height=sprite_sheet.height(),
            **kwargs
        )
        
        if self.config.use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        # Perform detection (simplified for example)
        width = sprite_sheet.width()
        height = sprite_sheet.height()
        
        # Try common frame sizes
        best_width = 32
        best_height = 32
        best_score = 0
        
        for test_width in [16, 24, 32, 48, 64, 96, 128]:
            for test_height in [16, 24, 32, 48, 64, 96, 128]:
                if width % test_width == 0 and height % test_height == 0:
                    frame_count = (width // test_width) * (height // test_height)
                    if 2 <= frame_count <= 100:
                        score = self._calculate_size_score(
                            test_width, test_height, frame_count, width, height
                        )
                        if score > best_score:
                            best_score = score
                            best_width = test_width
                            best_height = test_height
        
        # Create result
        if best_score > 0:
            result = DetectionResult(
                success=True,
                confidence="high" if best_score > 80 else "medium",
                message=f"Detected frame size: {best_width}x{best_height}",
                parameters={
                    'frame_width': best_width,
                    'frame_height': best_height,
                    'score': best_score
                }
            )
        else:
            result = DetectionResult(
                success=False,
                confidence="failed",
                message="Could not detect suitable frame size"
            )
        
        # Cache result
        if self.config.use_cache:
            self._cache[cache_key] = result
        
        return result
    
    def _calculate_size_score(self, width: int, height: int, frame_count: int,
                            sheet_width: int, sheet_height: int) -> float:
        """Calculate score for frame size candidate."""
        score = 0
        
        # Prefer reasonable frame counts
        if 4 <= frame_count <= 32:
            score += 50
        elif 2 <= frame_count <= 64:
            score += 30
        
        # Prefer common sizes
        if width in [32, 48, 64] and height in [32, 48, 64]:
            score += 30
        
        # Prefer square or common ratios
        if width == height:
            score += 20
        
        return score


class MarginDetector(DetectionAlgorithm):
    """Detects margins/offsets in sprite sheets."""
    
    name = "Margin Detector"
    description = "Finds empty margins around sprite content"
    
    def detect(self, sprite_sheet: Any, **kwargs) -> DetectionResult:
        # Validate input
        valid, error = self.validate_input(sprite_sheet)
        if not valid:
            return DetectionResult(success=False, message=error)
        
        # Simplified margin detection
        # In real implementation, would analyze alpha channel
        margin_left = 0
        margin_top = 0
        margin_right = 0
        margin_bottom = 0
        
        # Mock detection logic
        if sprite_sheet.width() > 100:
            margin_left = 10
            margin_right = 10
        if sprite_sheet.height() > 100:
            margin_top = 10
            margin_bottom = 10
        
        has_margins = any([margin_left, margin_top, margin_right, margin_bottom])
        
        return DetectionResult(
            success=True,
            confidence="high" if has_margins else "medium",
            message=f"Margins detected: L={margin_left}, T={margin_top}, R={margin_right}, B={margin_bottom}",
            parameters={
                'margin_left': margin_left,
                'margin_top': margin_top,
                'margin_right': margin_right,
                'margin_bottom': margin_bottom
            }
        )


class SpacingDetector(DetectionAlgorithm):
    """Detects spacing between frames."""
    
    name = "Spacing Detector"
    description = "Analyzes gaps between sprite frames"
    
    def detect(self, sprite_sheet: Any, **kwargs) -> DetectionResult:
        # Validate input
        valid, error = self.validate_input(sprite_sheet)
        if not valid:
            return DetectionResult(success=False, message=error)
        
        frame_width = kwargs.get('frame_width', 32)
        frame_height = kwargs.get('frame_height', 32)
        
        # Simplified spacing detection
        # In real implementation, would analyze pixel patterns
        spacing_x = 0
        spacing_y = 0
        
        # Mock detection based on sheet size
        if sprite_sheet.width() > frame_width * 4:
            spacing_x = 2
        if sprite_sheet.height() > frame_height * 4:
            spacing_y = 2
        
        has_spacing = spacing_x > 0 or spacing_y > 0
        
        return DetectionResult(
            success=True,
            confidence="high" if has_spacing else "low",
            message=f"Spacing detected: X={spacing_x}px, Y={spacing_y}px",
            parameters={
                'spacing_x': spacing_x,
                'spacing_y': spacing_y
            }
        )


class DetectionAlgorithmFactory:
    """Factory for creating detection algorithms."""
    
    # Registry of available algorithms
    _algorithms: Dict[DetectionType, Type[DetectionAlgorithm]] = {
        DetectionType.FRAME_SIZE: FrameSizeDetector,
        DetectionType.MARGINS: MarginDetector,
        DetectionType.SPACING: SpacingDetector,
    }
    
    # Singleton instance
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._config = DetectionConfig()
        self._instances: Dict[DetectionType, DetectionAlgorithm] = {}
    
    def create(self, detection_type: DetectionType,
              config: Optional[DetectionConfig] = None) -> DetectionAlgorithm:
        """
        Create a detection algorithm instance.
        
        Args:
            detection_type: Type of detection algorithm
            config: Optional configuration override
            
        Returns:
            DetectionAlgorithm instance
        """
        if detection_type not in self._algorithms:
            raise ValueError(f"Unknown detection type: {detection_type}")
        
        # Use provided config or default
        algo_config = config or self._config
        
        # Create instance
        algorithm_class = self._algorithms[detection_type]
        return algorithm_class(algo_config)
    
    def get_or_create(self, detection_type: DetectionType) -> DetectionAlgorithm:
        """
        Get existing instance or create new one (singleton per type).
        
        Args:
            detection_type: Type of detection algorithm
            
        Returns:
            DetectionAlgorithm instance
        """
        if detection_type not in self._instances:
            self._instances[detection_type] = self.create(detection_type)
        
        return self._instances[detection_type]
    
    def register_algorithm(self, detection_type: DetectionType,
                         algorithm_class: Type[DetectionAlgorithm]):
        """
        Register a custom detection algorithm.
        
        Args:
            detection_type: Type identifier for the algorithm
            algorithm_class: Class implementing DetectionAlgorithm
        """
        if not issubclass(algorithm_class, DetectionAlgorithm):
            raise TypeError("Algorithm must inherit from DetectionAlgorithm")
        
        self._algorithms[detection_type] = algorithm_class
        
        # Clear cached instance if exists
        if detection_type in self._instances:
            del self._instances[detection_type]
    
    def get_available_algorithms(self) -> Dict[DetectionType, str]:
        """Get list of available algorithms with descriptions."""
        available = {}
        
        for dtype, algo_class in self._algorithms.items():
            # Create temporary instance to get metadata
            temp_instance = algo_class(self._config)
            available[dtype] = {
                'name': temp_instance.name,
                'description': temp_instance.description
            }
        
        return available
    
    def set_default_config(self, config: DetectionConfig):
        """Set default configuration for new algorithms."""
        self._config = config
    
    def clear_cache(self):
        """Clear all algorithm caches."""
        for instance in self._instances.values():
            if hasattr(instance, '_cache'):
                instance._cache.clear()


# Convenience functions

def get_factory() -> DetectionAlgorithmFactory:
    """Get the singleton factory instance."""
    return DetectionAlgorithmFactory()


def detect_frame_size(sprite_sheet: Any, config: Optional[DetectionConfig] = None) -> DetectionResult:
    """Convenience function for frame size detection."""
    factory = get_factory()
    detector = factory.create(DetectionType.FRAME_SIZE, config)
    return detector.detect(sprite_sheet)


def detect_margins(sprite_sheet: Any, config: Optional[DetectionConfig] = None) -> DetectionResult:
    """Convenience function for margin detection."""
    factory = get_factory()
    detector = factory.create(DetectionType.MARGINS, config)
    return detector.detect(sprite_sheet)


def detect_spacing(sprite_sheet: Any, frame_width: int, frame_height: int,
                  config: Optional[DetectionConfig] = None) -> DetectionResult:
    """Convenience function for spacing detection."""
    factory = get_factory()
    detector = factory.create(DetectionType.SPACING, config)
    return detector.detect(sprite_sheet, frame_width=frame_width, frame_height=frame_height)