#!/usr/bin/env python3
"""
CCL Operations Module
=====================

Connected Component Labeling (CCL) operations for sprite extraction.
Extracted from monolithic SpriteModel for better separation of concerns and testability.

Handles:
- CCL-based frame extraction from irregular sprite collections
- Background transparency processing
- CCL mode switching and state management
- Sprite boundary management
"""

from typing import List, Optional, Tuple, Callable
from PySide6.QtCore import QRect
from PySide6.QtGui import QPixmap, QImage


class CCLOperations:
    """
    CCL (Connected Component Labeling) operations for sprite extraction.
    
    Handles extraction of individual sprites from irregular collections using
    connected component labeling algorithms, background transparency processing,
    and CCL-specific state management.
    """
    
    def __init__(self):
        """Initialize CCL operations with default state."""
        # CCL-specific state
        self._ccl_sprite_bounds: List[Tuple[int, int, int, int]] = []  # (x, y, w, h) for each sprite
        self._ccl_available: bool = False
        self._ccl_background_color: Optional[Tuple[int, int, int]] = None  # RGB background color for transparency
        self._ccl_color_tolerance: int = 10  # Tolerance for background color matching
        
        # Mode state
        self._extraction_mode: str = "grid"  # "grid" or "ccl"
        
        # Callbacks for integration with main model
        self._get_original_sprite_sheet: Optional[Callable[[], QPixmap]] = None
        self._get_sprite_sheet_path: Optional[Callable[[], str]] = None
        self._emit_extraction_completed: Optional[Callable[[int], None]] = None
    
    def set_callbacks(self, 
                     get_original_sprite_sheet: Callable[[], QPixmap],
                     get_sprite_sheet_path: Callable[[], str],
                     emit_extraction_completed: Callable[[int], None]) -> None:
        """
        Set callback functions for integration with main sprite model.
        
        Args:
            get_original_sprite_sheet: Function to get the original sprite sheet QPixmap
            get_sprite_sheet_path: Function to get the sprite sheet file path
            emit_extraction_completed: Function to emit extraction completed signal
        """
        self._get_original_sprite_sheet = get_original_sprite_sheet
        self._get_sprite_sheet_path = get_sprite_sheet_path
        self._emit_extraction_completed = emit_extraction_completed
    
    def extract_ccl_frames(self, ccl_available: bool,
                          detect_sprites_ccl_enhanced: Callable[[str], Optional[dict]],
                          detect_background_color: Callable[[str], Optional[Tuple[Tuple[int, int, int], int]]]) -> Tuple[bool, str, int, List[QPixmap], str]:
        """
        Extract frames using CCL-detected sprite boundaries (for irregular sprite collections).
        
        Args:
            ccl_available: Whether CCL functionality is available
            detect_sprites_ccl_enhanced: Function to detect sprites using CCL
            detect_background_color: Function to detect background color
            
        Returns:
            Tuple of (success, error_message, frame_count, sprite_frames, updated_info)
        """
        if not self._get_original_sprite_sheet:
            return False, "CCL operations not properly initialized", 0, [], ""
        
        original_sprite_sheet = self._get_original_sprite_sheet()
        if not original_sprite_sheet or original_sprite_sheet.isNull():
            return False, "No sprite sheet loaded", 0, [], ""
        
        # If no CCL sprite bounds, try to run auto-detection first
        if not self._ccl_sprite_bounds:
            if ccl_available and self._get_sprite_sheet_path:
                sprite_sheet_path = self._get_sprite_sheet_path()
                if sprite_sheet_path:
                    # Try to run CCL detection automatically
                    try:
                        ccl_result = detect_sprites_ccl_enhanced(sprite_sheet_path)
                        if ccl_result and ccl_result.get('success', False):
                            # Store CCL sprite boundaries
                            if 'ccl_sprite_bounds' in ccl_result:
                                self._ccl_sprite_bounds = ccl_result['ccl_sprite_bounds']
                                self._ccl_available = True
                                
                                # Store background color info if available
                                if ccl_available:
                                    bg_color_info = detect_background_color(sprite_sheet_path)
                                    if bg_color_info is not None:
                                        self._ccl_background_color = bg_color_info[0]
                                        # Cap tolerance at 25 for CCL mode to prevent destroying sprite content
                                        raw_tolerance = bg_color_info[1]
                                        self._ccl_color_tolerance = min(raw_tolerance, 25)
                                        if raw_tolerance > 25:
                                            print(f"   🛡️ CCL: Reduced tolerance from {raw_tolerance} to {self._ccl_color_tolerance} to preserve sprite content")
                        else:
                            return False, "CCL auto-detection failed. Cannot extract CCL frames.", 0, [], ""
                    except Exception as e:
                        return False, f"CCL auto-detection error: {str(e)}", 0, [], ""
                else:
                    return False, "No sprite sheet path available for CCL detection.", 0, [], ""
            else:
                return False, "No CCL sprite boundaries available. Auto-detection not possible.", 0, [], ""
        
        # Check again after potential auto-detection
        if not self._ccl_sprite_bounds:
            return False, "No CCL sprite boundaries detected.", 0, [], ""
        
        try:
            # Extract individual sprites using exact CCL boundaries
            sprite_frames = []
            filtered_count = 0
            null_frame_count = 0
            
            sheet_width = original_sprite_sheet.width()
            sheet_height = original_sprite_sheet.height()
            print(f"   📐 Sheet dimensions: {sheet_width}×{sheet_height}")
            print(f"   🎯 Processing {len(self._ccl_sprite_bounds)} detected sprite bounds...")
            
            for i, (x, y, width, height) in enumerate(self._ccl_sprite_bounds):
                # Ensure bounds are within sheet dimensions
                if x >= 0 and y >= 0 and x + width <= sheet_width and y + height <= sheet_height:
                    frame_rect = QRect(x, y, width, height)
                    frame = original_sprite_sheet.copy(frame_rect)
                    
                    if not frame.isNull():
                        # Apply background color transparency if available
                        if self._ccl_background_color is not None:
                            frame = self._apply_background_transparency(frame, self._ccl_background_color, self._ccl_color_tolerance)
                        
                        sprite_frames.append(frame)
                    else:
                        null_frame_count += 1
                        if null_frame_count <= 5:  # Only log first few
                            print(f"   ❌ Sprite {i+1}: NULL frame from ({x}, {y}) {width}×{height}")
                else:
                    # Log invalid bounds but continue
                    filtered_count += 1
                    if filtered_count <= 5:  # Only log first few invalid bounds
                        print(f"   ❌ Sprite {i+1}: Invalid bounds ({x}, {y}) {width}×{height} vs sheet {sheet_width}×{sheet_height}")
            
            # Report filtering statistics
            total_detected = len(self._ccl_sprite_bounds)
            total_extracted = len(sprite_frames)
            print(f"   📊 Extraction Results: {total_extracted}/{total_detected} sprites extracted")
            if filtered_count > 0:
                print(f"   ⚠️  {filtered_count} sprites filtered (invalid bounds)")
            if null_frame_count > 0:
                print(f"   ⚠️  {null_frame_count} sprites failed (null frames)")
            
            # Set extraction mode
            self._extraction_mode = "ccl"
            
            # Generate updated sprite sheet info with CCL extraction information
            updated_info = ""
            if len(sprite_frames) > 0:
                bounds_info = [(x, y, w, h) for x, y, w, h in self._ccl_sprite_bounds[:5]]  # Show first 5
                bounds_preview = str(bounds_info) + ("..." if len(self._ccl_sprite_bounds) > 5 else "")
                
                frame_info = (
                    f"<br><b>CCL Frames:</b> {len(sprite_frames)} individual sprites<br>"
                    f"<b>Extraction:</b> Connected-Component Labeling<br>"
                    f"<b>Boundaries:</b> {bounds_preview}"
                )
                updated_info = frame_info
            else:
                updated_info = "<br><b>CCL Frames:</b> 0"
            
            # Emit extraction completed signal if callback available
            if self._emit_extraction_completed:
                self._emit_extraction_completed(len(sprite_frames))
            
            return True, "", len(sprite_frames), sprite_frames, updated_info
            
        except Exception as e:
            return False, f"Error extracting CCL frames: {str(e)}", 0, [], ""
    
    def set_extraction_mode(self, mode: str, ccl_available: bool,
                           extract_grid_frames_callback: Callable[[], Tuple[bool, str, int]],
                           detect_sprites_ccl_enhanced: Callable[[str], Optional[dict]],
                           detect_background_color: Callable[[str], Optional[Tuple[Tuple[int, int, int], int]]]) -> bool:
        """
        Set extraction mode and extract frames accordingly.
        
        Args:
            mode: Extraction mode ("grid" or "ccl")
            ccl_available: Whether CCL functionality is available
            extract_grid_frames_callback: Callback to extract grid frames
            detect_sprites_ccl_enhanced: Function to detect sprites using CCL
            detect_background_color: Function to detect background color
            
        Returns:
            True if successful, False otherwise
        """
        if mode not in ["grid", "ccl"]:
            return False
        
        if mode == "ccl" and not ccl_available:
            return False
        
        old_mode = self._extraction_mode
        self._extraction_mode = mode
        
        # Re-extract frames with new mode
        if mode == "ccl":
            success, error, count, frames, info = self.extract_ccl_frames(
                ccl_available, detect_sprites_ccl_enhanced, detect_background_color
            )
            # Store the extracted frames and info for the main model to retrieve
            self._last_extracted_frames = frames if success else []
            self._last_extracted_info = info if success else ""
            # Return consistent format for main model
            return success
        else:
            success, error, count = extract_grid_frames_callback()
            self._last_extracted_frames = []
            self._last_extracted_info = ""
        
        if not success:
            # Revert mode if extraction failed
            self._extraction_mode = old_mode
            return False
        
        return True
    
    def get_extraction_mode(self) -> str:
        """Get current extraction mode: 'grid' or 'ccl'."""
        return self._extraction_mode
    
    def is_ccl_available(self, ccl_available: bool) -> bool:
        """
        Check if CCL extraction mode is available.
        
        Args:
            ccl_available: Whether CCL modules are available
            
        Returns:
            True if CCL is available
        """
        return ccl_available  # Make CCL always available when modules exist
    
    def get_ccl_sprite_bounds(self) -> List[Tuple[int, int, int, int]]:
        """Get the CCL-detected sprite boundaries."""
        return self._ccl_sprite_bounds.copy()
    
    def set_ccl_sprite_bounds(self, bounds: List[Tuple[int, int, int, int]]) -> None:
        """Set the CCL sprite boundaries."""
        self._ccl_sprite_bounds = bounds.copy()
        self._ccl_available = len(bounds) > 0
    
    def clear_ccl_data(self) -> None:
        """Clear all CCL-related data and reset to defaults."""
        self._ccl_sprite_bounds.clear()
        self._ccl_available = False
        self._ccl_background_color = None
        self._ccl_color_tolerance = 10
        self._extraction_mode = "grid"
    
    def _apply_background_transparency(self, pixmap: QPixmap, background_color: Tuple[int, int, int], tolerance: int) -> QPixmap:
        """
        Apply background color transparency to a QPixmap.
        
        Args:
            pixmap: Source QPixmap to process
            background_color: RGB background color to make transparent
            tolerance: Color matching tolerance (0-255)
            
        Returns:
            QPixmap with background transparency applied
        """
        try:
            # Convert QPixmap to QImage for pixel manipulation
            image = pixmap.toImage()
            
            # Convert to ARGB format for transparency support
            if image.format() != QImage.Format_ARGB32:
                image = image.convertToFormat(QImage.Format_ARGB32)
            
            # Get image dimensions
            width = image.width()
            height = image.height()
            
            # Process each pixel
            bg_r, bg_g, bg_b = background_color
            for y in range(height):
                for x in range(width):
                    # Get pixel color
                    pixel = image.pixel(x, y)
                    r = (pixel >> 16) & 0xFF
                    g = (pixel >> 8) & 0xFF
                    b = pixel & 0xFF
                    
                    # Check if pixel matches background color within tolerance
                    if (abs(r - bg_r) <= tolerance and 
                        abs(g - bg_g) <= tolerance and 
                        abs(b - bg_b) <= tolerance):
                        # Make pixel transparent
                        image.setPixel(x, y, 0x00000000)  # Fully transparent
            
            # Convert back to QPixmap
            return QPixmap.fromImage(image)
            
        except Exception as e:
            print(f"Warning: Failed to apply background transparency: {e}")
            return pixmap  # Return original if processing fails
    
    # State accessors for integration
    def get_ccl_background_color(self) -> Optional[Tuple[int, int, int]]:
        """Get the CCL background color."""
        return self._ccl_background_color
    
    def set_ccl_background_color(self, color: Optional[Tuple[int, int, int]]) -> None:
        """Set the CCL background color."""
        self._ccl_background_color = color
    
    def get_ccl_color_tolerance(self) -> int:
        """Get the CCL color tolerance."""
        return self._ccl_color_tolerance
    
    def set_ccl_color_tolerance(self, tolerance: int) -> None:
        """Set the CCL color tolerance."""
        self._ccl_color_tolerance = max(0, min(255, tolerance))  # Clamp to valid range
    
    def is_ccl_state_available(self) -> bool:
        """Check if CCL state indicates sprites are available."""
        return self._ccl_available and len(self._ccl_sprite_bounds) > 0
    
    def get_last_extracted_frames(self) -> List[QPixmap]:
        """Get the frames from the last CCL extraction."""
        return getattr(self, '_last_extracted_frames', [])
    
    def get_last_extracted_info(self) -> str:
        """Get the info from the last CCL extraction."""
        return getattr(self, '_last_extracted_info', "")


# Convenience functions for direct usage
def apply_background_transparency(pixmap: QPixmap, background_color: Tuple[int, int, int], tolerance: int = 10) -> QPixmap:
    """
    Convenience function for applying background transparency.
    
    Args:
        pixmap: Source QPixmap to process
        background_color: RGB background color to make transparent
        tolerance: Color matching tolerance (0-255)
        
    Returns:
        QPixmap with background transparency applied
    """
    ccl_ops = CCLOperations()
    return ccl_ops._apply_background_transparency(pixmap, background_color, tolerance)