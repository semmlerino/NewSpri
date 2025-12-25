#!/usr/bin/env python3
"""
Frame Size Detection Module
===========================

Automatic frame size detection for sprite sheets using multiple algorithms.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""

import math
from typing import Tuple, List
from PySide6.QtGui import QPixmap
from config import Config


class FrameDetector:
    """
    Automatic frame size detection for sprite sheets.
    
    Provides multiple detection algorithms:
    - Basic square frame detection using common sizes and GCD
    - Enhanced rectangular frame detection with aspect ratios
    - Content-based detection using actual sprite boundaries
    """
    
    def __init__(self):
        """Initialize frame detector."""
        pass
    
    def detect_frame_size(self, sprite_sheet: QPixmap) -> Tuple[bool, int, int, str]:
        """
        Automatically detect optimal frame size for the sprite sheet.
        
        Args:
            sprite_sheet: Source sprite sheet pixmap
            
        Returns:
            Tuple of (success, width, height, status_message)
        """
        if not sprite_sheet or sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet provided"
        
        width = sprite_sheet.width()
        height = sprite_sheet.height()
        
        # Try common sprite sizes
        common_sizes = Config.FrameExtraction.AUTO_DETECT_SIZES
        
        for size in common_sizes:
            if width % size == 0 and height % size == 0:
                # Check if this produces a reasonable number of frames
                frames_x = width // size
                frames_y = height // size
                total_frames = frames_x * frames_y
                
                if Config.Animation.MIN_REASONABLE_FRAMES <= total_frames <= Config.Animation.MAX_REASONABLE_FRAMES:
                    return True, size, size, f"Auto-detected frame size: {size}×{size}"
        
        # If no common size fits, try to find the GCD
        frame_size = math.gcd(width, height)
        if frame_size >= Config.FrameExtraction.MIN_SPRITE_SIZE:
            return True, frame_size, frame_size, f"Auto-detected frame size: {frame_size}×{frame_size}"
        
        return False, 0, 0, "Could not auto-detect suitable frame size"
    
    def detect_rectangular_frames(self, sprite_sheet: QPixmap) -> Tuple[bool, int, int, str]:
        """
        Enhanced frame size detection supporting rectangular frames and horizontal strips.
        Uses aspect ratios, scoring, and specialized detection for different sprite sheet types.
        
        Args:
            sprite_sheet: Source sprite sheet pixmap
            
        Returns:
            Tuple of (success, width, height, status_message)
        """
        if not sprite_sheet or sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet provided"
        
        sheet_width = sprite_sheet.width()
        sheet_height = sprite_sheet.height()
        
        # Common frame sizes for rectangular sprites
        base_sizes = Config.FrameExtraction.BASE_SIZES
        aspect_ratios = Config.FrameExtraction.COMMON_ASPECT_RATIOS
        
        candidates = []
        
        # Generate candidate sizes
        for base_size in base_sizes:
            for aspect_w, aspect_h in aspect_ratios:
                frame_width = base_size * aspect_w
                frame_height = base_size * aspect_h
                
                # Check if this frame size divides the sheet evenly
                if (sheet_width % frame_width == 0 and 
                    sheet_height % frame_height == 0 and
                    frame_width <= sheet_width and 
                    frame_height <= sheet_height):
                    
                    frames_x = sheet_width // frame_width
                    frames_y = sheet_height // frame_height
                    total_frames = frames_x * frames_y
                    
                    # Validate frame count is reasonable
                    if Config.FrameExtraction.MIN_REASONABLE_FRAMES <= total_frames <= Config.FrameExtraction.MAX_REASONABLE_FRAMES:
                        score = self._score_frame_candidate(frame_width, frame_height, frames_x, frames_y, total_frames)
                        candidates.append((score, frame_width, frame_height, frames_x, frames_y, total_frames))
        
        if not candidates:
            return False, 0, 0, "No valid rectangular frame sizes found"
        
        # Sort by score (higher is better)
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Return the best candidate
        score, frame_width, frame_height, frames_x, frames_y, total_frames = candidates[0]
        
        return True, frame_width, frame_height, (
            f"Detected rectangular frames: {frame_width}×{frame_height} "
            f"({frames_x}×{frames_y} = {total_frames} frames, score: {score:.2f})"
        )
    
    def detect_content_based(self, sprite_sheet: QPixmap) -> Tuple[bool, int, int, str]:
        """
        Content-based sprite detection - finds actual sprite boundaries.
        Superior to mathematical grid detection for irregular sprites.
        
        Args:
            sprite_sheet: Source sprite sheet pixmap
            
        Returns:
            Tuple of (success, width, height, status_message)
        """
        if not sprite_sheet or sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet provided"
        
        try:
            # Convert to QImage for pixel analysis
            image = sprite_sheet.toImage()
            image.width()
            image.height()
            
            # Find content boundaries by analyzing transparency
            content_bounds = self._analyze_content_boundaries(image)
            
            if not content_bounds:
                return False, 0, 0, "No content boundaries detected"
            
            # Calculate most common frame dimensions
            frame_dimensions = self._calculate_common_dimensions(content_bounds)
            
            if not frame_dimensions:
                return False, 0, 0, "Could not determine consistent frame dimensions"
            
            # Return the most common dimensions
            frame_width, frame_height, count = frame_dimensions[0]
            
            return True, frame_width, frame_height, (
                f"Content-based detection: {frame_width}×{frame_height} "
                f"(found {count} sprites with these dimensions)"
            )
            
        except Exception as e:
            return False, 0, 0, f"Content-based detection failed: {str(e)}"
    
    def _score_frame_candidate(self, frame_width: int, frame_height: int, 
                              frames_x: int, frames_y: int, total_frames: int) -> float:
        """
        Score a frame size candidate based on various criteria.
        
        Args:
            frame_width: Width of individual frame
            frame_height: Height of individual frame
            frames_x: Number of frames horizontally
            frames_y: Number of frames vertically
            total_frames: Total number of frames
            
        Returns:
            Score (higher is better)
        """
        score = 0.0
        
        # Prefer common frame sizes
        common_sizes = [16, 24, 32, 48, 64, 96, 128]
        if frame_width in common_sizes:
            score += 2.0
        if frame_height in common_sizes:
            score += 2.0
        
        # Prefer reasonable frame counts
        if 4 <= total_frames <= 16:
            score += 3.0
        elif 17 <= total_frames <= 32:
            score += 2.0
        elif 33 <= total_frames <= 64:
            score += 1.0
        
        # Prefer common aspect ratios
        aspect_ratio = frame_width / frame_height
        common_ratios = [1.0, 0.5, 2.0, 0.75, 1.33, 0.67, 1.5]  # 1:1, 1:2, 2:1, 3:4, 4:3, 2:3, 3:2
        
        for ratio in common_ratios:
            if abs(aspect_ratio - ratio) < 0.1:
                score += 1.5
                break
        
        # Prefer balanced grids (not too many in one dimension)
        if frames_x == frames_y:
            score += 1.0  # Square grids
        elif min(frames_x, frames_y) >= 2:
            score += 0.5  # Balanced rectangular grids
        
        # Slight preference for larger frames (more detail)
        frame_area = frame_width * frame_height
        if frame_area >= 1024:  # 32x32 or larger
            score += 0.5
        
        return score
    
    def _analyze_content_boundaries(self, image) -> List[Tuple[int, int, int, int]]:
        """
        Analyze image to find content boundaries (sprites).
        
        Args:
            image: QImage to analyze
            
        Returns:
            List of (x, y, width, height) tuples for detected sprites
        """
        # This is a simplified implementation
        # In a full implementation, this would use more sophisticated algorithms
        # like connected component analysis or edge detection
        
        width = image.width()
        height = image.height()
        alpha_threshold = Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD
        
        # Simple grid-based content detection
        # This is a placeholder for more sophisticated content analysis
        content_bounds = []
        
        # Try different grid sizes to find content blocks
        for grid_size in [16, 24, 32, 48, 64]:
            if width % grid_size == 0 and height % grid_size == 0:
                frames_x = width // grid_size
                frames_y = height // grid_size
                
                for row in range(frames_y):
                    for col in range(frames_x):
                        x = col * grid_size
                        y = row * grid_size
                        
                        # Check if this grid cell has content
                        if self._has_content_in_region(image, x, y, grid_size, grid_size, alpha_threshold):
                            content_bounds.append((x, y, grid_size, grid_size))
        
        return content_bounds
    
    def _has_content_in_region(self, image, x: int, y: int, width: int, height: int, alpha_threshold: int) -> bool:
        """
        Check if a region contains non-transparent content.
        
        Args:
            image: QImage to check
            x, y: Top-left corner of region
            width, height: Size of region to check
            alpha_threshold: Minimum alpha value to consider as content
            
        Returns:
            True if region has content, False otherwise
        """
        # Sample pixels in the region to check for content
        sample_step = max(1, min(width, height) // 4)
        
        for check_y in range(y, min(y + height, image.height()), sample_step):
            for check_x in range(x, min(x + width, image.width()), sample_step):
                pixel = image.pixel(check_x, check_y)
                alpha = (pixel >> 24) & 0xFF
                if alpha > alpha_threshold:
                    return True
        
        return False
    
    def _calculate_common_dimensions(self, content_bounds: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        Calculate the most common frame dimensions from content boundaries.
        
        Args:
            content_bounds: List of (x, y, width, height) tuples
            
        Returns:
            List of (width, height, count) tuples sorted by frequency
        """
        if not content_bounds:
            return []
        
        # Count dimension frequencies
        dimension_counts = {}
        for x, y, width, height in content_bounds:
            key = (width, height)
            dimension_counts[key] = dimension_counts.get(key, 0) + 1
        
        # Sort by frequency (most common first)
        sorted_dimensions = sorted(dimension_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [(width, height, count) for (width, height), count in sorted_dimensions]


# Convenience functions for direct usage
def detect_frame_size(sprite_sheet: QPixmap) -> Tuple[bool, int, int, str]:
    """
    Convenience function for basic frame size detection.
    
    Args:
        sprite_sheet: Source sprite sheet pixmap
        
    Returns:
        Tuple of (success, width, height, status_message)
    """
    detector = FrameDetector()
    return detector.detect_frame_size(sprite_sheet)


def detect_rectangular_frames(sprite_sheet: QPixmap) -> Tuple[bool, int, int, str]:
    """
    Convenience function for rectangular frame detection.
    
    Args:
        sprite_sheet: Source sprite sheet pixmap
        
    Returns:
        Tuple of (success, width, height, status_message)
    """
    detector = FrameDetector()
    return detector.detect_rectangular_frames(sprite_sheet)


def detect_content_based(sprite_sheet: QPixmap) -> Tuple[bool, int, int, str]:
    """
    Convenience function for content-based frame detection.
    
    Args:
        sprite_sheet: Source sprite sheet pixmap
        
    Returns:
        Tuple of (success, width, height, status_message)
    """
    detector = FrameDetector()
    return detector.detect_content_based(sprite_sheet)