#!/usr/bin/env python3
"""
Spacing Detection Module
========================

Automatic spacing detection for sprite sheets with gaps between frames.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""

from typing import Tuple
from PySide6.QtGui import QPixmap
from config import Config


class SpacingDetector:
    """
    Automatic spacing detection for sprite sheets.
    
    Enhanced spacing detection that validates across multiple frame positions
    to determine optimal spacing between frames in both horizontal and vertical directions.
    """
    
    def __init__(self):
        """Initialize spacing detector."""
        pass
    
    def detect_spacing(self, sprite_sheet: QPixmap, frame_width: int, frame_height: int,
                      offset_x: int = 0, offset_y: int = 0) -> Tuple[bool, int, int, str]:
        """
        Enhanced spacing detection that validates across multiple frame positions.
        
        Args:
            sprite_sheet: Source sprite sheet pixmap
            frame_width: Width of individual frames
            frame_height: Height of individual frames  
            offset_x: X offset (margin) from left edge
            offset_y: Y offset (margin) from top edge
            
        Returns:
            Tuple of (success, spacing_x, spacing_y, status_message)
        """
        if not sprite_sheet or sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet provided"
        
        if frame_width <= 0 or frame_height <= 0:
            return False, 0, 0, "Frame size must be greater than 0"
        
        try:
            image = sprite_sheet.toImage()
            available_width = image.width() - offset_x
            available_height = image.height() - offset_y
            
            # Test spacing values from 0-10 pixels
            best_spacing_x = 0
            best_score_x = 0
            best_spacing_y = 0
            best_score_y = 0
            
            # Horizontal spacing detection
            best_spacing_x, best_score_x = self._detect_horizontal_spacing(
                image, frame_width, frame_height, offset_x, offset_y, available_width)
            
            # Vertical spacing detection  
            best_spacing_y, best_score_y = self._detect_vertical_spacing(
                image, frame_width, frame_height, offset_x, offset_y, available_height)
            
            # Calculate confidence based on consistency scores
            avg_confidence = (best_score_x + best_score_y) / 2
            confidence_text = "high" if avg_confidence >= 0.8 else "medium" if avg_confidence >= 0.5 else "low"
            
            return True, best_spacing_x, best_spacing_y, (
                f"Auto-detected spacing: X={best_spacing_x}, Y={best_spacing_y} "
                f"(confidence: {confidence_text}, consistency: {avg_confidence:.2f})"
            )
            
        except Exception as e:
            return False, 0, 0, f"Error in enhanced spacing detection: {str(e)}"
    
    def _detect_horizontal_spacing(self, image, frame_width: int, frame_height: int,
                                  offset_x: int, offset_y: int, available_width: int) -> Tuple[int, float]:
        """
        Detect horizontal spacing between frames.
        
        Args:
            image: QImage to analyze
            frame_width, frame_height: Frame dimensions
            offset_x, offset_y: Margin offsets
            available_width: Available width after margins
            
        Returns:
            Tuple of (best_spacing, best_score)
        """
        best_spacing_x = 0
        best_score_x = 0
        alpha_threshold = Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD
        
        for test_spacing in range(0, 11):
            score = 0
            positions_checked = 0
            
            # Calculate how many frames we could check with this spacing
            frames_per_row = (available_width + test_spacing) // (frame_width + test_spacing) if test_spacing > 0 else available_width // frame_width
            positions_to_check = min(3, frames_per_row - 1)  # Check up to 3 gap positions
            
            if positions_to_check <= 0:
                continue
            
            for position in range(positions_to_check):
                x_gap_start = offset_x + (position + 1) * frame_width + position * test_spacing
                x_gap_end = x_gap_start + test_spacing
                x_next_frame = x_gap_end
                
                # Check bounds
                if x_next_frame + frame_width > image.width():
                    break
                    
                positions_checked += 1
                
                # Check if gap is empty (for non-zero spacing)
                gap_valid = True
                if test_spacing > 0:
                    for y in range(offset_y, min(offset_y + frame_height, image.height()), 5):
                        for x in range(x_gap_start, x_gap_end):
                            if x < image.width():
                                pixel = image.pixel(x, y)
                                alpha = (pixel >> 24) & 0xFF
                                if alpha > alpha_threshold:
                                    gap_valid = False
                                    break
                        if not gap_valid:
                            break
                
                # Check if frame exists at expected position
                frame_exists = False
                if gap_valid:
                    for y in range(offset_y, min(offset_y + 20, image.height()), 5):
                        pixel = image.pixel(x_next_frame, y)
                        alpha = (pixel >> 24) & 0xFF
                        if alpha > alpha_threshold:
                            frame_exists = True
                            break
                
                if gap_valid and frame_exists:
                    score += 1
            
            # Calculate consistency score
            consistency = score / positions_checked if positions_checked > 0 else 0
            if consistency > best_score_x:
                best_score_x = consistency
                best_spacing_x = test_spacing
        
        return best_spacing_x, best_score_x
    
    def _detect_vertical_spacing(self, image, frame_width: int, frame_height: int,
                                offset_x: int, offset_y: int, available_height: int) -> Tuple[int, float]:
        """
        Detect vertical spacing between frames.
        
        Args:
            image: QImage to analyze
            frame_width, frame_height: Frame dimensions
            offset_x, offset_y: Margin offsets
            available_height: Available height after margins
            
        Returns:
            Tuple of (best_spacing, best_score)
        """
        best_spacing_y = 0
        best_score_y = 0
        alpha_threshold = Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD
        
        for test_spacing in range(0, 11):
            score = 0
            positions_checked = 0
            
            # Calculate how many frames we could check with this spacing
            frames_per_col = (available_height + test_spacing) // (frame_height + test_spacing) if test_spacing > 0 else available_height // frame_height
            positions_to_check = min(3, frames_per_col - 1)  # Check up to 3 gap positions
            
            if positions_to_check <= 0:
                continue
            
            for position in range(positions_to_check):
                y_gap_start = offset_y + (position + 1) * frame_height + position * test_spacing
                y_gap_end = y_gap_start + test_spacing
                y_next_frame = y_gap_end
                
                # Check bounds
                if y_next_frame + frame_height > image.height():
                    break
                    
                positions_checked += 1
                
                # Check if gap is empty (for non-zero spacing)
                gap_valid = True
                if test_spacing > 0:
                    for x in range(offset_x, min(offset_x + frame_width, image.width()), 5):
                        for y in range(y_gap_start, y_gap_end):
                            if y < image.height():
                                pixel = image.pixel(x, y)
                                alpha = (pixel >> 24) & 0xFF
                                if alpha > alpha_threshold:
                                    gap_valid = False
                                    break
                        if not gap_valid:
                            break
                
                # Check if frame exists at expected position
                frame_exists = False
                if gap_valid:
                    for x in range(offset_x, min(offset_x + 20, image.width()), 5):
                        pixel = image.pixel(x, y_next_frame)
                        alpha = (pixel >> 24) & 0xFF
                        if alpha > alpha_threshold:
                            frame_exists = True
                            break
                
                if gap_valid and frame_exists:
                    score += 1
            
            # Calculate consistency score
            consistency = score / positions_checked if positions_checked > 0 else 0
            if consistency > best_score_y:
                best_score_y = consistency
                best_spacing_y = test_spacing
        
        return best_spacing_y, best_score_y