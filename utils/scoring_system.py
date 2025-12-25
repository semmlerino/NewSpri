"""
Frame Scoring System
Modular scoring components for sprite sheet frame detection.
Part of Phase 3 refactoring: Complex Logic Simplification.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple
from abc import ABC, abstractmethod

from config import Config


@dataclass
class FrameParameters:
    """Parameters for frame scoring."""
    width: int
    height: int
    frame_count: int
    sheet_width: int
    sheet_height: int
    offset_x: int = 0
    offset_y: int = 0
    is_horizontal_strip: bool = False
    
    @property
    def available_width(self) -> int:
        """Width available for frames after offset."""
        return self.sheet_width - self.offset_x
    
    @property
    def available_height(self) -> int:
        """Height available for frames after offset."""
        return self.sheet_height - self.offset_y
    
    @property
    def cols(self) -> int:
        """Number of columns in grid."""
        return self.available_width // self.width if self.width > 0 else 0
    
    @property
    def rows(self) -> int:
        """Number of rows in grid."""
        return self.available_height // self.height if self.height > 0 else 0
    
    @property
    def aspect_ratio(self) -> Tuple[int, int]:
        """Reduced aspect ratio as (width, height) tuple."""
        gcd_val = math.gcd(self.width, self.height)
        return (self.width // gcd_val, self.height // gcd_val)
    
    @property
    def utilization(self) -> float:
        """Space utilization ratio (0.0 to 1.0)."""
        total_frame_area = self.width * self.height * self.frame_count
        available_area = self.available_width * self.available_height
        return min(1.0, total_frame_area / available_area) if available_area > 0 else 0.0


@dataclass
class ScoreComponent:
    """Individual scoring component result."""
    score: float
    name: str
    reason: str
    
    def __str__(self) -> str:
        return f"{self.name}: {self.score:+.1f} ({self.reason})"


@dataclass
class FrameScore:
    """Complete frame scoring result."""
    total_score: float
    components: List[ScoreComponent]
    parameters: FrameParameters
    
    @classmethod
    def combine(cls, components: List[ScoreComponent], parameters: FrameParameters) -> 'FrameScore':
        """Combine score components into final score."""
        total = sum(c.score for c in components)
        return cls(total_score=total, components=components, parameters=parameters)
    
    def get_breakdown(self) -> str:
        """Get human-readable score breakdown."""
        lines = [f"Total Score: {self.total_score:.1f}"]
        lines.append("-" * 40)
        for component in self.components:
            lines.append(str(component))
        return "\n".join(lines)


class ScoringComponent(ABC):
    """Base class for scoring components."""
    
    @abstractmethod
    def calculate(self, params: FrameParameters) -> ScoreComponent:
        """Calculate score for this component."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Component name."""
        pass


class FrameCountScorer(ScoringComponent):
    """Scores based on frame count reasonableness."""
    
    name = "Frame Count"
    
    def calculate(self, params: FrameParameters) -> ScoreComponent:
        score = 0
        reason_parts = []
        
        # Basic reasonableness check
        if Config.FrameExtraction.MIN_REASONABLE_FRAMES <= params.frame_count <= Config.FrameExtraction.MAX_REASONABLE_FRAMES:
            score += 100
            reason_parts.append("reasonable count")
            
            # Sweet spot bonus
            if Config.FrameExtraction.OPTIMAL_FRAME_COUNT_MIN <= params.frame_count <= Config.FrameExtraction.OPTIMAL_FRAME_COUNT_MAX:
                score += 30
                reason_parts.append("optimal range")
            
            # Penalty for excessive frames (unless horizontal strip)
            if params.frame_count > 50 and not params.is_horizontal_strip:
                penalty = min(50, (params.frame_count - 50) * 2)
                score -= penalty
                reason_parts.append(f"excessive count (-{penalty})")
        else:
            reason_parts.append("out of range")
        
        # Horizontal strip frame count bonuses
        if params.is_horizontal_strip:
            if 8 <= params.frame_count <= 16:
                score += 60
                reason_parts.append("ideal animation count")
            elif 6 <= params.frame_count <= 24:
                score += 40
                reason_parts.append("common animation count")
            elif 4 <= params.frame_count <= 32:
                score += 20
                reason_parts.append("extended animation range")
        
        reason = ", ".join(reason_parts) if reason_parts else "no criteria met"
        return ScoreComponent(score, self.name, reason)


class DimensionMatchScorer(ScoringComponent):
    """Scores based on dimension matching with sheet."""
    
    name = "Dimension Match"
    
    def calculate(self, params: FrameParameters) -> ScoreComponent:
        score = 0
        reason_parts = []
        
        # Exact dimension matching
        if params.width == params.available_width or params.height == params.available_height:
            score += 100
            reason_parts.append("exact dimension match")
        elif params.width == params.available_height or params.height == params.available_width:
            score += 80
            reason_parts.append("swapped dimension match")
        
        # Clean divisor bonus
        if params.available_width % params.width == 0 and params.available_height % params.height == 0:
            score += 60
            reason_parts.append("clean divisor")
        
        reason = ", ".join(reason_parts) if reason_parts else "no dimension match"
        return ScoreComponent(score, self.name, reason)


class SizeAppropriatenessScorer(ScoringComponent):
    """Scores based on frame size appropriateness."""
    
    name = "Size Appropriateness"
    
    def calculate(self, params: FrameParameters) -> ScoreComponent:
        score = 0
        reason_parts = []
        
        # Basic size range check
        if 8 <= params.width <= 512 and 8 <= params.height <= 512:
            score += 60
            reason_parts.append("reasonable size")
            
            # Power-of-2 bonus
            if self._is_power_of_2(params.width) and self._is_power_of_2(params.height):
                score += 20
                reason_parts.append("power-of-2")
            
            # Common sizes bonus
            common_sizes = [16, 24, 32, 48, 64, 96, 128, 160, 192, 256]
            if params.width in common_sizes or params.height in common_sizes:
                score += 30
                reason_parts.append("common sprite size")
        else:
            reason_parts.append("size out of range")
        
        reason = ", ".join(reason_parts) if reason_parts else "inappropriate size"
        return ScoreComponent(score, self.name, reason)
    
    @staticmethod
    def _is_power_of_2(n: int) -> bool:
        """Check if number is power of 2."""
        return n > 0 and (n & (n - 1)) == 0


class AspectRatioScorer(ScoringComponent):
    """Scores based on aspect ratio."""
    
    name = "Aspect Ratio"
    
    def calculate(self, params: FrameParameters) -> ScoreComponent:
        score = 0
        ratio = params.aspect_ratio
        
        if ratio in Config.FrameExtraction.COMMON_ASPECT_RATIOS:
            score += 40
            reason = f"common ratio {ratio[0]}:{ratio[1]}"
        elif ratio[0] == ratio[1]:  # Square
            score += 25
            reason = "square (1:1)"
        else:
            reason = f"uncommon ratio {ratio[0]}:{ratio[1]}"
        
        return ScoreComponent(score, self.name, reason)


class GridLayoutScorer(ScoringComponent):
    """Scores based on grid layout quality."""
    
    name = "Grid Layout"
    
    def calculate(self, params: FrameParameters) -> ScoreComponent:
        score = 0
        reason_parts = []
        
        if params.is_horizontal_strip:
            # Horizontal strip scoring
            if params.rows == 1:
                score += 60
                reason_parts.append("single row strip")
            elif params.rows <= 3:
                score += 30
                reason_parts.append("few rows")
        else:
            # Standard grid scoring
            if 2 <= params.cols <= 8 and 2 <= params.rows <= 8:
                score += 40
                reason_parts.append(f"good grid {params.cols}×{params.rows}")
            elif params.cols >= 2 and params.rows >= 2:
                score += 20
                reason_parts.append(f"minimal grid {params.cols}×{params.rows}")
            
            # Penalty for overly dense grids
            if params.cols > 10 and params.rows > 10:
                score -= 30
                reason_parts.append("overly dense")
        
        reason = ", ".join(reason_parts) if reason_parts else "poor grid layout"
        return ScoreComponent(score, self.name, reason)


class SpaceUtilizationScorer(ScoringComponent):
    """Scores based on space utilization."""
    
    name = "Space Utilization"
    
    def calculate(self, params: FrameParameters) -> ScoreComponent:
        utilization = params.utilization
        score = utilization * 50  # Up to 50 points for perfect utilization
        
        if utilization >= 0.9:
            reason = f"excellent ({utilization:.0%})"
        elif utilization >= 0.7:
            reason = f"good ({utilization:.0%})"
        elif utilization >= 0.5:
            reason = f"moderate ({utilization:.0%})"
        else:
            reason = f"poor ({utilization:.0%})"
        
        return ScoreComponent(score, self.name, reason)


class HorizontalStripScorer(ScoringComponent):
    """Special scoring for horizontal strips."""
    
    name = "Horizontal Strip"
    
    def calculate(self, params: FrameParameters) -> ScoreComponent:
        if not params.is_horizontal_strip:
            return ScoreComponent(0, self.name, "not a horizontal strip")
        
        score = 80  # Base bonus for being a horizontal strip
        reason_parts = ["horizontal strip detected"]
        
        # Additional bonus for square frames matching height
        if params.width == params.height and params.height == params.available_height:
            score += 30
            reason_parts.append("square frames matching height")
        
        reason = ", ".join(reason_parts)
        return ScoreComponent(score, self.name, reason)


class FrameScoreCalculator:
    """Modular frame scoring system."""
    
    def __init__(self):
        """Initialize with default scoring components."""
        self.components = [
            FrameCountScorer(),
            DimensionMatchScorer(),
            SizeAppropriatenessScorer(),
            AspectRatioScorer(),
            GridLayoutScorer(),
            SpaceUtilizationScorer(),
            HorizontalStripScorer()
        ]
    
    def calculate_score(self, params: FrameParameters) -> FrameScore:
        """Calculate comprehensive frame score."""
        component_scores = []
        
        for component in self.components:
            try:
                score = component.calculate(params)
                if score.score != 0:  # Only include non-zero scores
                    component_scores.append(score)
            except Exception as e:
                # Graceful degradation - skip failed components
                print(f"Warning: {component.name} scoring failed: {e}")
        
        return FrameScore.combine(component_scores, params)
    
    def add_component(self, component: ScoringComponent):
        """Add a custom scoring component."""
        self.components.append(component)
    
    def remove_component(self, component_name: str):
        """Remove a scoring component by name."""
        self.components = [c for c in self.components if c.name != component_name]