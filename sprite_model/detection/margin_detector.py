#!/usr/bin/env python3
"""
Margin Detection Module
=======================

Automatic transparent margin detection for sprite sheets.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""

from typing import Tuple, Optional
from PySide6.QtGui import QPixmap
from config import Config


class MarginDetector:
    """
    Automatic margin detection for sprite sheets.
    
    Detects transparent margins around sprite content from all four edges
    with validation and reasonableness checks.
    """
    
    def __init__(self):
        """Initialize margin detector."""
        pass
    
    def detect_margins(self, sprite_sheet: QPixmap, frame_width: Optional[int] = None, 
                      frame_height: Optional[int] = None) -> Tuple[bool, int, int, str]:
        """
        Detect transparent margins around sprite content from all four edges.
        
        Args:
            sprite_sheet: Source sprite sheet pixmap
            frame_width: Optional frame width for validation (if known)
            frame_height: Optional frame height for validation (if known)
            
        Returns:
            Tuple of (success, offset_x, offset_y, status_message)
        """
        if not sprite_sheet or sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet provided"
        
        try:
            # Convert to QImage for pixel analysis
            image = sprite_sheet.toImage()
            width = image.width()
            height = image.height()
            
            # Get raw margin measurements
            raw_left, raw_right, raw_top, raw_bottom = self._detect_raw_margins(image)
            
            # Apply validation and reasonableness checks
            validated_left, validated_top, validation_msg = self._validate_margins(
                raw_left, raw_right, raw_top, raw_bottom, width, height, frame_width, frame_height)
            
            # Calculate final content area
            content_width = width - validated_left - (raw_right if validated_left == raw_left else 0)
            content_height = height - validated_top - (raw_bottom if validated_top == raw_top else 0)
            
            status_msg = (f"Margins: L={raw_left}, R={raw_right}, T={raw_top}, B={raw_bottom} | "
                         f"Validated: X={validated_left}, Y={validated_top} | "
                         f"Content: {content_width}×{content_height}")
            
            if validation_msg:
                status_msg += f" | {validation_msg}"
            
            return True, validated_left, validated_top, status_msg
            
        except Exception as e:
            return False, 0, 0, f"Error detecting margins: {str(e)}"
    
    def _detect_raw_margins(self, image) -> Tuple[int, int, int, int]:
        """
        Detect raw margin measurements from image edges.
        
        Args:
            image: QImage to analyze
            
        Returns:
            Tuple of (left_margin, right_margin, top_margin, bottom_margin)
        """
        width = image.width()
        height = image.height()
        alpha_threshold = Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD
        
        # Detect left margin
        left_margin = 0
        for x in range(width):
            has_content = False
            for y in range(height):
                pixel = image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                if alpha > alpha_threshold:
                    has_content = True
                    break
            if has_content:
                break
            left_margin += 1
        
        # Detect right margin
        right_margin = 0
        for x in range(width - 1, -1, -1):
            has_content = False
            for y in range(height):
                pixel = image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                if alpha > alpha_threshold:
                    has_content = True
                    break
            if has_content:
                break
            right_margin += 1
        
        # Detect top margin
        top_margin = 0
        for y in range(height):
            has_content = False
            for x in range(width):
                pixel = image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                if alpha > alpha_threshold:
                    has_content = True
                    break
            if has_content:
                break
            top_margin += 1
        
        # Detect bottom margin
        bottom_margin = 0
        for y in range(height - 1, -1, -1):
            has_content = False
            for x in range(width):
                pixel = image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                if alpha > alpha_threshold:
                    has_content = True
                    break
            if has_content:
                break
            bottom_margin += 1
        
        return left_margin, right_margin, top_margin, bottom_margin
    
    def _validate_margins(self, left: int, right: int, top: int, bottom: int, 
                         width: int, height: int, 
                         frame_width: Optional[int] = None, frame_height: Optional[int] = None) -> Tuple[int, int, str]:
        """
        Validate detected margins and apply reasonableness checks.
        
        Args:
            left, right, top, bottom: Raw margin measurements
            width, height: Image dimensions
            frame_width, frame_height: Optional frame dimensions for validation
            
        Returns:
            Tuple of (validated_left, validated_top, validation_message)
        """
        validation_msg = ""
        validated_left = left
        validated_top = top
        
        # Check for excessive margins (more than 25% of dimension)
        max_reasonable_x = width // 4
        max_reasonable_y = height // 4
        
        if left > max_reasonable_x:
            validated_left = 0
            validation_msg += f"Left margin {left}px excessive (>{max_reasonable_x}px), reset to 0; "
        
        if top > max_reasonable_y:
            validated_top = 0
            validation_msg += f"Top margin {top}px excessive (>{max_reasonable_y}px), reset to 0; "
        
        # Check for margins that would create problematic frame sizes
        if frame_width and frame_height and frame_width > 0 and frame_height > 0:
            # Check if margins make sense with current frame size
            available_after_margins = (width - validated_left, height - validated_top)
            
            # If margins would prevent clean division by frame size, reduce them
            if available_after_margins[0] % frame_width != 0:
                # Try reducing left margin to get clean division
                for reduced_left in range(validated_left - 1, -1, -1):
                    if (width - reduced_left) % frame_width == 0:
                        validated_left = reduced_left
                        validation_msg += f"Adjusted left margin to {reduced_left} for clean frame division; "
                        break
            
            if available_after_margins[1] % frame_height != 0:
                # Try reducing top margin to get clean division
                for reduced_top in range(validated_top - 1, -1, -1):
                    if (height - reduced_top) % frame_height == 0:
                        validated_top = reduced_top
                        validation_msg += f"Adjusted top margin to {reduced_top} for clean frame division; "
                        break
        
        # For horizontal strips (wide aspect ratio), minimize margins
        aspect_ratio = width / height
        if aspect_ratio > 3.0:
            # This looks like a horizontal strip - minimize margins
            if validated_left > 5:
                validated_left = min(5, validated_left)
                validation_msg += "Reduced margins for horizontal strip; "
            if validated_top > 5:
                validated_top = min(5, validated_top)
                validation_msg += "Reduced top margin for horizontal strip; "
        
        # If margins are very small, set to zero to avoid noise
        if validated_left <= 2:
            validated_left = 0
        if validated_top <= 2:
            validated_top = 0
        
        return validated_left, validated_top, validation_msg.rstrip('; ')


# Convenience function for direct usage
def detect_margins(sprite_sheet: QPixmap, frame_width: Optional[int] = None, 
                  frame_height: Optional[int] = None) -> Tuple[bool, int, int, str]:
    """
    Convenience function for margin detection.
    
    Args:
        sprite_sheet: Source sprite sheet pixmap
        frame_width: Optional frame width for validation
        frame_height: Optional frame height for validation
        
    Returns:
        Tuple of (success, offset_x, offset_y, status_message)
    """
    detector = MarginDetector()
    return detector.detect_margins(sprite_sheet, frame_width, frame_height)