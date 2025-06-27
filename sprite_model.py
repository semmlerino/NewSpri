#!/usr/bin/env python3
"""
Sprite Data Model for Sprite Viewer
Centralizes all sprite data and processing logic separate from UI components.
"""

import os
import math
from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QTimer, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor

from config import Config


class SpriteModel(QObject):
    """
    Centralized data model for sprite sheet processing and animation state.
    Separates sprite data/logic from UI components for better testability and maintainability.
    """
    
    # ============================================================================
    # SIGNALS FOR UI NOTIFICATION
    # ============================================================================
    
    frameChanged = Signal(int, int)          # current_frame, total_frames
    dataLoaded = Signal(str)                 # file_path
    extractionCompleted = Signal(int)        # frame_count
    playbackStateChanged = Signal(bool)      # is_playing
    errorOccurred = Signal(str)             # error_message
    configurationChanged = Signal()         # frame size/offset changed
    
    def __init__(self):
        super().__init__()
        
        # ============================================================================
        # IMAGE DATA
        # ============================================================================
        
        self._original_sprite_sheet: Optional[QPixmap] = None
        self._sprite_frames: List[QPixmap] = []
        self._file_path: str = ""
        self._file_name: str = ""
        
        # ============================================================================
        # FRAME CONFIGURATION
        # ============================================================================
        
        self._frame_width: int = Config.FrameExtraction.DEFAULT_FRAME_WIDTH
        self._frame_height: int = Config.FrameExtraction.DEFAULT_FRAME_HEIGHT
        self._offset_x: int = Config.FrameExtraction.DEFAULT_OFFSET
        self._offset_y: int = Config.FrameExtraction.DEFAULT_OFFSET
        
        # ============================================================================
        # ANIMATION STATE
        # ============================================================================
        
        self._current_frame: int = 0
        self._total_frames: int = 0
        self._is_playing: bool = False
        self._loop_enabled: bool = True
        self._fps: int = Config.Animation.DEFAULT_FPS
        
        # ============================================================================
        # METADATA
        # ============================================================================
        
        self._sheet_width: int = 0
        self._sheet_height: int = 0
        self._file_format: str = ""
        self._last_modified: float = 0.0
        
        # ============================================================================
        # PROCESSING STATE
        # ============================================================================
        
        self._is_valid: bool = False
        self._error_message: str = ""
    
    # ============================================================================
    # FILE OPERATIONS (Will be implemented in Step 3.3)
    # ============================================================================
    
    def load_sprite_sheet(self, file_path: str) -> Tuple[bool, str]:
        """
        Load and validate sprite sheet from file path.
        Returns (success, error_message).
        """
        try:
            # Load pixmap from file
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                return False, "Failed to load image file"
            
            # Store original sprite sheet for re-slicing
            self._original_sprite_sheet = pixmap
            
            # Extract file metadata
            file_path_obj = Path(file_path)
            self._file_path = file_path
            self._file_name = file_path_obj.name
            self._sheet_width = pixmap.width()
            self._sheet_height = pixmap.height()
            self._file_format = file_path_obj.suffix.upper()[1:] if file_path_obj.suffix else "UNKNOWN"
            self._last_modified = os.path.getmtime(file_path)
            
            # Generate sprite sheet info string
            self._sprite_sheet_info = (
                f"<b>File:</b> {self._file_name}<br>"
                f"<b>Size:</b> {self._sheet_width} × {self._sheet_height} px<br>"
                f"<b>Format:</b> {self._file_format}"
            )
            
            # Reset to first frame
            self._current_frame = 0
            self._is_valid = True
            self._error_message = ""
            
            # Emit data loaded signal
            self.dataLoaded.emit(file_path)
            
            return True, ""
            
        except Exception as e:
            self._is_valid = False
            self._error_message = str(e)
            return False, f"Error loading sprite sheet: {str(e)}"
    
    def reload_current_sheet(self) -> Tuple[bool, str]:
        """Reload the current sprite sheet (for file changes)."""
        if not self._file_path:
            return False, "No sprite sheet currently loaded"
        return self.load_sprite_sheet(self._file_path)
    
    def clear_sprite_data(self) -> None:
        """Clear all sprite data and reset to empty state."""
        self._original_sprite_sheet = None
        self._sprite_frames.clear()
        self._file_path = ""
        self._file_name = ""
        self._sprite_sheet_info = ""
        self._current_frame = 0
        self._total_frames = 0
        self._is_playing = False
        self._sheet_width = 0
        self._sheet_height = 0
        self._file_format = ""
        self._last_modified = 0.0
        self._is_valid = False
        self._error_message = ""
    
    # ============================================================================
    # FRAME EXTRACTION & PROCESSING (Will be implemented in Step 3.4)
    # ============================================================================
    
    def extract_frames(self, width: int, height: int, offset_x: int = 0, offset_y: int = 0) -> Tuple[bool, str, int]:
        """
        Extract frames from sprite sheet with given parameters.
        Returns (success, error_message, frame_count).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, "No sprite sheet loaded", 0
        
        # Validate frame settings
        valid, error_msg = self.validate_frame_settings(width, height)
        if not valid:
            return False, error_msg, 0
        
        try:
            # Store extraction settings
            self._frame_width = width
            self._frame_height = height
            self._offset_x = offset_x
            self._offset_y = offset_y
            
            sheet_width = self._original_sprite_sheet.width()
            sheet_height = self._original_sprite_sheet.height()
            
            # Calculate available area after margins (exact same algorithm)
            available_width = sheet_width - offset_x
            available_height = sheet_height - offset_y
            
            # Calculate how many frames fit (exact same algorithm)
            frames_per_row = available_width // width if width > 0 else 0
            frames_per_col = available_height // height if height > 0 else 0
            
            # Extract individual frames (exact same algorithm)
            self._sprite_frames = []
            for row in range(frames_per_col):
                for col in range(frames_per_row):
                    x = offset_x + (col * width)
                    y = offset_y + (row * height)
                    
                    # Extract frame from sprite sheet (exact same method)
                    frame_rect = QRect(x, y, width, height)
                    frame = self._original_sprite_sheet.copy(frame_rect)
                    
                    if not frame.isNull():
                        self._sprite_frames.append(frame)
            
            # Update frame count and metadata
            self._total_frames = len(self._sprite_frames)
            self._current_frame = 0  # Reset to first frame
            
            # Update sprite info with frame information
            if self._total_frames > 0:
                frame_info = (
                    f"<br><b>Frames:</b> {self._total_frames} "
                    f"({frames_per_row}×{frames_per_col})<br>"
                    f"<b>Frame size:</b> {width}×{height} px"
                )
                self._sprite_sheet_info = self._sprite_sheet_info.split('<br><b>Frames:</b>')[0] + frame_info
            else:
                self._sprite_sheet_info = self._sprite_sheet_info.split('<br><b>Frames:</b>')[0] + "<br><b>Frames:</b> 0"
            
            # Emit extraction completed signal
            self.extractionCompleted.emit(self._total_frames)
            
            return True, "", self._total_frames
            
        except Exception as e:
            self._error_message = str(e)
            return False, f"Error extracting frames: {str(e)}", 0
    
    def validate_frame_settings(self, width: int, height: int) -> Tuple[bool, str]:
        """Validate frame extraction parameters."""
        if width <= 0:
            return False, "Frame width must be greater than 0"
        if height <= 0:
            return False, "Frame height must be greater than 0"
        if width > Config.FrameExtraction.MAX_FRAME_SIZE:
            return False, f"Frame width cannot exceed {Config.FrameExtraction.MAX_FRAME_SIZE}"
        if height > Config.FrameExtraction.MAX_FRAME_SIZE:
            return False, f"Frame height cannot exceed {Config.FrameExtraction.MAX_FRAME_SIZE}"
        
        # Check if frame size is reasonable for the sprite sheet
        if self._original_sprite_sheet and not self._original_sprite_sheet.isNull():
            sheet_width = self._original_sprite_sheet.width()
            sheet_height = self._original_sprite_sheet.height()
            if width > sheet_width:
                return False, f"Frame width ({width}) larger than sprite sheet width ({sheet_width})"
            if height > sheet_height:
                return False, f"Frame height ({height}) larger than sprite sheet height ({sheet_height})"
        
        return True, ""
    
    # ============================================================================
    # AUTO-DETECTION (Will be implemented in Step 3.5)
    # ============================================================================
    
    def should_auto_detect_size(self) -> bool:
        """Check if we should auto-detect frame size based on sprite sheet dimensions."""
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False
        
        # Simple heuristic: if dimensions are multiples of common sizes (exact same algorithm)
        width = self._original_sprite_sheet.width()
        height = self._original_sprite_sheet.height()
        
        common_sizes = Config.File.COMMON_FRAME_SIZES
        for size in common_sizes:
            if width % size == 0 and height % size == 0:
                return True
        return False
    
    def auto_detect_frame_size(self) -> Tuple[bool, int, int, str]:
        """
        Automatically detect optimal frame size for the sprite sheet.
        Returns (success, width, height, status_message).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet loaded"
        
        width = self._original_sprite_sheet.width()
        height = self._original_sprite_sheet.height()
        
        # Try common sprite sizes (exact same algorithm)
        common_sizes = Config.FrameExtraction.AUTO_DETECT_SIZES
        
        for size in common_sizes:
            if width % size == 0 and height % size == 0:
                # Check if this produces a reasonable number of frames (exact same logic)
                frames_x = width // size
                frames_y = height // size
                total_frames = frames_x * frames_y
                
                if Config.Animation.MIN_REASONABLE_FRAMES <= total_frames <= Config.Animation.MAX_REASONABLE_FRAMES:
                    # Store the detected size
                    self._frame_width = size
                    self._frame_height = size
                    return True, size, size, f"Auto-detected frame size: {size}×{size}"
        
        # If no common size fits, try to find the GCD (exact same algorithm)
        from math import gcd
        frame_size = gcd(width, height)
        if frame_size >= Config.FrameExtraction.MIN_SPRITE_SIZE:
            # Store the detected size
            self._frame_width = frame_size
            self._frame_height = frame_size
            return True, frame_size, frame_size, f"Auto-detected frame size: {frame_size}×{frame_size}"
        
        return False, 0, 0, "Could not auto-detect suitable frame size"
    
    def auto_detect_margins(self) -> Tuple[bool, int, int, str]:
        """
        Detect transparent margins around sprite content.
        Returns (success, offset_x, offset_y, status_message).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet loaded"
        
        try:
            # Convert to QImage for pixel analysis (exact same method)
            image = self._original_sprite_sheet.toImage()
            width = image.width()
            height = image.height()
            
            # Detect left margin (exact same algorithm)
            left_margin = 0
            for x in range(width):
                has_content = False
                for y in range(height):
                    pixel = image.pixel(x, y)
                    alpha = (pixel >> 24) & 0xFF
                    if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:
                        has_content = True
                        break
                if has_content:
                    break
                left_margin += 1
            
            # Detect top margin (exact same algorithm)
            top_margin = 0
            for y in range(height):
                has_content = False
                for x in range(width):
                    pixel = image.pixel(x, y)
                    alpha = (pixel >> 24) & 0xFF
                    if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:
                        has_content = True
                        break
                if has_content:
                    break
                top_margin += 1
            
            # Store the detected margins
            self._offset_x = left_margin
            self._offset_y = top_margin
            
            return True, left_margin, top_margin, f"Auto-detected margins: X={left_margin}, Y={top_margin}"
            
        except Exception as e:
            return False, 0, 0, f"Error detecting margins: {str(e)}"
    
    # ============================================================================
    # ANIMATION STATE MANAGEMENT (Will be implemented in Step 3.6)
    # ============================================================================
    
    def set_current_frame(self, frame: int) -> bool:
        """Set the current animation frame with bounds checking."""
        if not self._sprite_frames:
            return False
        
        if 0 <= frame < len(self._sprite_frames):
            self._current_frame = frame
            self.frameChanged.emit(self._current_frame, self._total_frames)
            return True
        return False
    
    def next_frame(self) -> Tuple[int, bool]:
        """
        Advance to next frame, handling looping.
        Returns (new_frame_index, should_continue_playing).
        """
        if not self._sprite_frames:
            return 0, False
        
        # Core animation advancement logic (exact same algorithm)
        self._current_frame += 1
        
        if self._current_frame >= len(self._sprite_frames):
            if self._loop_enabled:
                self._current_frame = 0
                should_continue = True
            else:
                self._current_frame = len(self._sprite_frames) - 1
                should_continue = False  # Stop playback when not looping
        else:
            should_continue = True
        
        # Emit frame change signal
        self.frameChanged.emit(self._current_frame, self._total_frames)
        
        return self._current_frame, should_continue
    
    def previous_frame(self) -> int:
        """Go to previous frame with bounds checking."""
        if self._sprite_frames and self._current_frame > 0:
            self._current_frame -= 1
            self.frameChanged.emit(self._current_frame, self._total_frames)
        return self._current_frame
    
    def first_frame(self) -> int:
        """Jump to first frame."""
        if self._sprite_frames:
            self._current_frame = 0
            self.frameChanged.emit(self._current_frame, self._total_frames)
        return self._current_frame
    
    def last_frame(self) -> int:
        """Jump to last frame."""
        if self._sprite_frames:
            self._current_frame = len(self._sprite_frames) - 1
            self.frameChanged.emit(self._current_frame, self._total_frames)
        return self._current_frame
    
    # ============================================================================
    # PLAYBACK CONTROL (Will be implemented in Step 3.6)
    # ============================================================================
    
    def play(self) -> bool:
        """Start animation playback. Returns success status."""
        if not self._sprite_frames:
            return False
        self._is_playing = True
        self.playbackStateChanged.emit(True)
        return True
    
    def pause(self) -> None:
        """Pause animation playback."""
        self._is_playing = False
        self.playbackStateChanged.emit(False)
    
    def stop(self) -> None:
        """Stop animation and reset to first frame."""
        self._is_playing = False
        if self._sprite_frames:
            self._current_frame = 0
            self.frameChanged.emit(self._current_frame, self._total_frames)
        self.playbackStateChanged.emit(False)
    
    def toggle_playback(self) -> bool:
        """Toggle playback state. Returns new playing state."""
        if self._is_playing:
            self.pause()
        else:
            self.play()
        return self._is_playing
    
    def set_fps(self, fps: int) -> bool:
        """Set animation speed with validation."""
        if Config.Animation.MIN_FPS <= fps <= Config.Animation.MAX_FPS:
            self._fps = fps
            return True
        return False
    
    def set_loop_enabled(self, enabled: bool) -> None:
        """Set animation loop mode."""
        self._loop_enabled = enabled
    
    # ============================================================================
    # DATA ACCESS PROPERTIES (Will be implemented in Step 3.2)
    # ============================================================================
    
    @property
    def current_frame_pixmap(self) -> Optional[QPixmap]:
        """Get the currently selected frame as QPixmap."""
        if 0 <= self._current_frame < len(self._sprite_frames):
            return self._sprite_frames[self._current_frame]
        return None
    
    @property
    def sprite_info(self) -> str:
        """Get formatted sprite sheet information string."""
        return self._sprite_sheet_info
    
    @property
    def frame_count(self) -> int:
        """Get total number of extracted frames."""
        return len(self._sprite_frames)
    
    @property
    def is_loaded(self) -> bool:
        """Check if sprite sheet is loaded and valid."""
        return self._original_sprite_sheet is not None and not self._original_sprite_sheet.isNull()
    
    @property
    def sprite_frames(self) -> List[QPixmap]:
        """Get list of all sprite frames."""
        return self._sprite_frames.copy()  # Return copy to prevent external modification
    
    @property
    def original_sprite_sheet(self) -> Optional[QPixmap]:
        """Get the original sprite sheet pixmap."""
        return self._original_sprite_sheet
    
    @property
    def current_frame(self) -> int:
        """Get current frame index."""
        return self._current_frame
    
    @property
    def total_frames(self) -> int:
        """Get total frame count."""
        return self._total_frames
    
    @property
    def is_playing(self) -> bool:
        """Get animation playback state."""
        return self._is_playing
    
    @property
    def fps(self) -> int:
        """Get current FPS setting."""
        return self._fps
    
    @property
    def loop_enabled(self) -> bool:
        """Get animation loop setting."""
        return self._loop_enabled
    
    @property
    def file_path(self) -> str:
        """Get loaded file path."""
        return self._file_path
    
    @property
    def file_name(self) -> str:
        """Get loaded file name."""
        return self._file_name


# Export for easy importing
__all__ = ['SpriteModel']