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
from PySide6.QtGui import QPixmap, QPainter, QColor, QImage

from config import Config

# Import extracted functionality
try:
    from sprite_model.extraction.background_detector import detect_background_color
    from sprite_model.extraction.ccl_extractor import detect_sprites_ccl_enhanced
    from sprite_model.extraction.grid_extractor import GridExtractor, GridConfig
    from sprite_model.animation.state_manager import AnimationStateManager
    CCL_AVAILABLE = True
    GRID_EXTRACTOR_AVAILABLE = True
    ANIMATION_MANAGER_AVAILABLE = True
except ImportError:
    CCL_AVAILABLE = False
    GRID_EXTRACTOR_AVAILABLE = False
    ANIMATION_MANAGER_AVAILABLE = False
    
    def detect_background_color(image_path: str) -> Optional[Tuple[Tuple[int, int, int], int]]:
        return None
    
    def detect_sprites_ccl_enhanced(image_path: str) -> Optional[dict]:
        return None
    
    # Fallback GridExtractor class
    class GridExtractor:
        def extract_frames(self, *args, **kwargs):
            return False, "Grid extractor not available", []
        def validate_frame_settings(self, *args, **kwargs):
            return False, "Grid extractor not available"
    
    class GridConfig:
        def __init__(self, *args, **kwargs):
            pass
    
    # Fallback AnimationStateManager class
    from PySide6.QtCore import QObject, Signal
    
    class AnimationStateManager(QObject):
        frameChanged = Signal(int, int)
        playbackStateChanged = Signal(bool)
        
        def __init__(self):
            super().__init__()
            print("Warning: Using fallback AnimationStateManager")
        
        def set_sprite_frames_getter(self, getter): pass
        def update_frame_count(self, total_frames): pass
        def set_current_frame(self, frame): return False
        def next_frame(self): return 0, False
        def previous_frame(self): return 0
        def first_frame(self): return 0
        def last_frame(self): return 0
        def play(self): return False
        def pause(self): pass
        def stop(self): pass
        def toggle_playback(self): return False
        def set_fps(self, fps): return False
        def set_loop_enabled(self, enabled): pass
        def reset_state(self): pass
        
        @property
        def current_frame(self): return 0
        @property
        def total_frames(self): return 0
        @property
        def is_playing(self): return False
        @property
        def is_loop_enabled(self): return True
        @property
        def fps(self): return 10
        @property
        def current_frame_pixmap(self): return None


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
        self._spacing_x: int = Config.FrameExtraction.DEFAULT_SPACING
        self._spacing_y: int = Config.FrameExtraction.DEFAULT_SPACING
        
        # ============================================================================
        # ANIMATION STATE (Now managed by AnimationStateManager)
        # ============================================================================
        
        # Animation state is now handled by self._animation_state
        
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
        self._sprite_sheet_info: str = ""
        
        # ============================================================================
        # CCL MODE SUPPORT
        # ============================================================================
        
        self._ccl_sprite_bounds: List[Tuple[int, int, int, int]] = []  # (x, y, w, h) for each sprite
        self._extraction_mode: str = "grid"  # "grid" or "ccl"
        self._ccl_available: bool = False
        self._ccl_background_color: Optional[Tuple[int, int, int]] = None  # RGB background color for transparency
        self._ccl_color_tolerance: int = 10  # Tolerance for background color matching
        
        # ============================================================================
        # EXTRACTED FUNCTIONALITY
        # ============================================================================
        
        # Initialize grid extractor for modular frame extraction
        self._grid_extractor = GridExtractor()
        
        # Initialize animation state manager for modular animation control
        self._animation_state = AnimationStateManager()
        self._animation_state.set_sprite_frames_getter(lambda: self._sprite_frames)
        
        # Connect animation state signals to our signals for backwards compatibility
        self._animation_state.frameChanged.connect(self.frameChanged.emit)
        self._animation_state.playbackStateChanged.connect(self.playbackStateChanged.emit)
    
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
            self._sprite_sheet_path = file_path  # Store for CCL detection
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
        # Reset animation state using animation state manager
        self._animation_state.reset_state()
        self._sheet_width = 0
        self._sheet_height = 0
        self._file_format = ""
        self._last_modified = 0.0
        self._is_valid = False
        self._error_message = ""
    
    # ============================================================================
    # FRAME EXTRACTION & PROCESSING (Will be implemented in Step 3.4)
    # ============================================================================
    
    def extract_frames(self, width: int, height: int, offset_x: int = 0, offset_y: int = 0, 
                      spacing_x: int = 0, spacing_y: int = 0) -> Tuple[bool, str, int]:
        """
        Extract frames from sprite sheet with given parameters using modular grid extractor.
        Now supports frame spacing for sprite sheets with gaps between frames.
        Returns (success, error_message, frame_count).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, "No sprite sheet loaded", 0
        
        try:
            # Store extraction settings
            self._frame_width = width
            self._frame_height = height
            self._offset_x = offset_x
            self._offset_y = offset_y
            self._spacing_x = spacing_x
            self._spacing_y = spacing_y
            
            # Create grid configuration
            config = GridConfig(width, height, offset_x, offset_y, spacing_x, spacing_y)
            
            # Use extracted grid extractor module
            success, error_msg, frames = self._grid_extractor.extract_frames(self._original_sprite_sheet, config)
            
            if not success:
                return False, error_msg, 0
            
            # Store extracted frames and update animation state
            self._sprite_frames = frames
            total_frames = len(self._sprite_frames)
            
            # Update animation state manager with new frame count
            self._animation_state.update_frame_count(total_frames)
            
            # Calculate layout for info display
            layout = self._grid_extractor.calculate_grid_layout(self._original_sprite_sheet, config)
            
            # Update sprite info with frame information
            if layout and total_frames > 0:
                frame_info = (
                    f"<br><b>Frames:</b> {total_frames} "
                    f"({layout.frames_per_row}×{layout.frames_per_col})<br>"
                    f"<b>Frame size:</b> {width}×{height} px"
                )
                self._sprite_sheet_info = self._sprite_sheet_info.split('<br><b>Frames:</b>')[0] + frame_info
            else:
                self._sprite_sheet_info = self._sprite_sheet_info.split('<br><b>Frames:</b>')[0] + "<br><b>Frames:</b> 0"
            
            # Emit extraction completed signal
            self.extractionCompleted.emit(total_frames)
            
            return True, "", total_frames
            
        except Exception as e:
            self._error_message = str(e)
            return False, f"Error extracting frames: {str(e)}", 0
    
    def validate_frame_settings(self, width: int, height: int, offset_x: int = 0, offset_y: int = 0,
                               spacing_x: int = 0, spacing_y: int = 0) -> Tuple[bool, str]:
        """Validate frame extraction parameters using modular grid extractor validation."""
        try:
            # Create grid configuration
            config = GridConfig(width, height, offset_x, offset_y, spacing_x, spacing_y)
            
            # Use extracted grid extractor validation
            return self._grid_extractor.validate_frame_settings(self._original_sprite_sheet, config)
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def extract_ccl_frames(self) -> Tuple[bool, str, int]:
        """
        Extract frames using CCL-detected sprite boundaries (for irregular sprite collections).
        Returns (success, error_message, frame_count).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, "No sprite sheet loaded", 0
        
        if not self._ccl_sprite_bounds:
            return False, "No CCL sprite boundaries available. Run auto-detection first.", 0
        
        try:
            # Extract individual sprites using exact CCL boundaries
            self._sprite_frames = []
            
            for i, (x, y, width, height) in enumerate(self._ccl_sprite_bounds):
                # Ensure bounds are within sheet dimensions
                sheet_width = self._original_sprite_sheet.width()
                sheet_height = self._original_sprite_sheet.height()
                
                if x >= 0 and y >= 0 and x + width <= sheet_width and y + height <= sheet_height:
                    frame_rect = QRect(x, y, width, height)
                    frame = self._original_sprite_sheet.copy(frame_rect)
                    
                    if not frame.isNull():
                        # Apply background color transparency if available
                        if self._ccl_background_color is not None:
                            frame = self._apply_background_transparency(frame, self._ccl_background_color, self._ccl_color_tolerance)
                        
                        self._sprite_frames.append(frame)
                else:
                    # Log invalid bounds but continue
                    print(f"Warning: Skipping sprite {i+1} with invalid bounds: ({x}, {y}) {width}×{height}")
            
            # Update frame count and metadata
            self._total_frames = len(self._sprite_frames)
            self._current_frame = 0
            self._extraction_mode = "ccl"
            
            # Update sprite info with CCL extraction information
            if self._total_frames > 0:
                bounds_info = [(x, y, w, h) for x, y, w, h in self._ccl_sprite_bounds[:5]]  # Show first 5
                bounds_preview = str(bounds_info) + ("..." if len(self._ccl_sprite_bounds) > 5 else "")
                
                frame_info = (
                    f"<br><b>CCL Frames:</b> {self._total_frames} individual sprites<br>"
                    f"<b>Extraction:</b> Connected-Component Labeling<br>"
                    f"<b>Boundaries:</b> {bounds_preview}"
                )
                self._sprite_sheet_info = self._sprite_sheet_info.split('<br><b>Frames:</b>')[0].split('<br><b>CCL Frames:</b>')[0] + frame_info
            else:
                self._sprite_sheet_info = self._sprite_sheet_info.split('<br><b>Frames:</b>')[0].split('<br><b>CCL Frames:</b>')[0] + "<br><b>CCL Frames:</b> 0"
            
            # Emit extraction completed signal
            self.extractionCompleted.emit(self._total_frames)
            
            return True, "", self._total_frames
            
        except Exception as e:
            self._error_message = str(e)
            return False, f"Error extracting CCL frames: {str(e)}", 0
    
    def get_extraction_mode(self) -> str:
        """Get current extraction mode: 'grid' or 'ccl'."""
        return self._extraction_mode
    
    def set_extraction_mode(self, mode: str) -> bool:
        """
        Set extraction mode and extract frames accordingly.
        Returns True if successful.
        """
        if mode not in ["grid", "ccl"]:
            return False
        
        if mode == "ccl" and not self._ccl_available:
            return False
        
        old_mode = self._extraction_mode
        self._extraction_mode = mode
        
        # Re-extract frames with new mode
        if mode == "ccl":
            success, error, count = self.extract_ccl_frames()
        else:
            success, error, count = self.extract_frames(
                self._frame_width, self._frame_height,
                self._offset_x, self._offset_y,
                self._spacing_x, self._spacing_y
            )
        
        if not success:
            # Revert mode if extraction failed
            self._extraction_mode = old_mode
            return False
        
        return True
    
    def is_ccl_available(self) -> bool:
        """Check if CCL extraction mode is available."""
        return self._ccl_available and len(self._ccl_sprite_bounds) > 0
    
    def get_ccl_sprite_bounds(self) -> List[Tuple[int, int, int, int]]:
        """Get the CCL-detected sprite boundaries."""
        return self._ccl_sprite_bounds.copy()
    
    def _apply_background_transparency(self, pixmap: QPixmap, background_color: Tuple[int, int, int], tolerance: int) -> QPixmap:
        """Apply background color transparency to a QPixmap."""
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
    
    def auto_detect_rectangular_frames(self) -> Tuple[bool, int, int, str]:
        """
        Enhanced frame size detection supporting rectangular frames and horizontal strips.
        Uses aspect ratios, scoring, and specialized detection for different sprite sheet types.
        Returns (success, width, height, status_message).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet loaded"
        
        try:
            # Get available area (accounting for margins)
            available_width = self._original_sprite_sheet.width() - self._offset_x
            available_height = self._original_sprite_sheet.height() - self._offset_y
            sheet_aspect_ratio = available_width / available_height
            
            best_score = 0
            best_width = 0
            best_height = 0
            candidates_tested = 0
            detection_method = "standard"
            
            # PHASE 1: Check for horizontal animation strips (aspect ratio > 3:1)
            if sheet_aspect_ratio > 3.0:
                # Try horizontal strip detection first
                strip_score, strip_width, strip_height, strip_tested = self._detect_horizontal_strip(available_width, available_height)
                if strip_score > best_score:
                    best_score = strip_score
                    best_width = strip_width
                    best_height = strip_height
                    detection_method = "horizontal_strip"
                candidates_tested += strip_tested
            
            # PHASE 2: Standard rectangular detection
            # Test combinations of base sizes and aspect ratios
            for base_size in Config.FrameExtraction.BASE_SIZES:
                for width_ratio, height_ratio in Config.FrameExtraction.COMMON_ASPECT_RATIOS:
                    width = base_size * width_ratio
                    height = base_size * height_ratio
                    
                    # Skip if frames would be too large for the sprite sheet
                    if width > available_width or height > available_height:
                        continue
                    
                    # Calculate how many frames would fit
                    frames_x = available_width // width
                    frames_y = available_height // height
                    total_frames = frames_x * frames_y
                    
                    if total_frames < Config.FrameExtraction.MIN_REASONABLE_FRAMES:
                        continue
                    
                    candidates_tested += 1
                    
                    # Score this candidate
                    score = self._calculate_frame_score(width, height, total_frames, sheet_aspect_ratio)
                    
                    # Use tie-breaking: prefer the size that uses more of the available space
                    if score > best_score or (score == best_score and self._is_better_fit(width, height, best_width, best_height)):
                        best_score = score
                        best_width = width
                        best_height = height
                        detection_method = "standard"
            
            # Also test exact divisors of sheet dimensions for edge cases
            for width in [available_width // i for i in range(2, 21) if available_width % i == 0]:
                for height in [available_height // j for j in range(2, 21) if available_height % j == 0]:
                    if width < Config.FrameExtraction.MIN_SPRITE_SIZE or height < Config.FrameExtraction.MIN_SPRITE_SIZE:
                        continue
                    if width > 512 or height > 512:
                        continue
                    
                    total_frames = (available_width // width) * (available_height // height)
                    
                    if total_frames < Config.FrameExtraction.MIN_REASONABLE_FRAMES:
                        continue
                    
                    candidates_tested += 1
                    score = self._calculate_frame_score(width, height, total_frames, sheet_aspect_ratio)
                    
                    if score > best_score or (score == best_score and self._is_better_fit(width, height, best_width, best_height)):
                        best_score = score
                        best_width = width
                        best_height = height
                        detection_method = "divisor"
            
            if best_width > 0 and best_height > 0:
                # Calculate confidence based on score
                confidence = min(100, max(0, (best_score - 100) * 2))  # Normalize score to 0-100%
                confidence_text = "high" if confidence >= 80 else "medium" if confidence >= 50 else "low"
                
                # Store the detected size
                self._frame_width = best_width
                self._frame_height = best_height
                
                return True, best_width, best_height, (
                    f"Auto-detected frame size: {best_width}×{best_height} "
                    f"(confidence: {confidence_text}, score: {best_score:.1f}, method: {detection_method}, tested: {candidates_tested})"
                )
            
            return False, 0, 0, f"Could not detect suitable frame size (tested {candidates_tested} candidates)"
            
        except Exception as e:
            return False, 0, 0, f"Error in rectangular frame detection: {str(e)}"
    
    def auto_detect_content_based(self) -> Tuple[bool, int, int, str]:
        """
        Content-based sprite detection - finds actual sprite boundaries.
        Superior to mathematical grid detection.
        Returns (success, width, height, status_message).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet loaded"
        
        try:
            from content_based_sprite_detection import ContentBasedSpriteDetector
            
            # Create temporary file to pass to detector
            temp_path = "temp_sprite_sheet.png"
            self._original_sprite_sheet.save(temp_path)
            
            try:
                # Detect actual sprite regions
                detector = ContentBasedSpriteDetector()
                sprites = detector.detect_sprites(temp_path)
                pattern_info = detector.analyze_grid_pattern(sprites)
                
                if not sprites:
                    return False, 0, 0, "No sprites detected in content analysis"
                
                # Analyze detected sprites to determine frame size
                if len(sprites) == 1:
                    # Single sprite - use its dimensions
                    sprite = sprites[0]
                    frame_width = sprite.width
                    frame_height = sprite.height
                    grid_info = "1×1"
                    
                elif pattern_info["pattern"] == "regular_grid":
                    # Regular grid - use most common sprite size
                    sizes = [(s.width, s.height) for s in sprites]
                    most_common_size = max(set(sizes), key=sizes.count)
                    frame_width, frame_height = most_common_size
                    grid_info = pattern_info["grid"]
                    
                elif pattern_info["pattern"] in ["horizontal_strip", "vertical_strip"]:
                    # Strip layout - use average sprite size
                    avg_width = sum(s.width for s in sprites) // len(sprites)
                    avg_height = sum(s.height for s in sprites) // len(sprites)
                    frame_width = avg_width
                    frame_height = avg_height
                    grid_info = pattern_info["grid"]
                    
                else:
                    # Irregular - use most common size or average
                    if len(sprites) > 1:
                        sizes = [(s.width, s.height) for s in sprites]
                        most_common_size = max(set(sizes), key=sizes.count)
                        frame_width, frame_height = most_common_size
                        grid_info = f"{pattern_info['cols']}×{pattern_info['rows']} irregular"
                    else:
                        sprite = sprites[0]
                        frame_width = sprite.width
                        frame_height = sprite.height
                        grid_info = "1×1"
                
                # Store detected dimensions
                self._frame_width = frame_width
                self._frame_height = frame_height
                
                # Calculate margins to position the grid at the top-left sprite
                if sprites:
                    # Find the top-left sprite (minimum x and y coordinates)
                    min_x = min(s.x for s in sprites)
                    min_y = min(s.y for s in sprites)
                    self._offset_x = min_x
                    self._offset_y = min_y
                else:
                    self._offset_x = 0
                    self._offset_y = 0
                
                # Detect spacing from sprite positions
                if len(sprites) > 1:
                    spacing_x, spacing_y = self._calculate_spacing_from_sprites(sprites)
                    self._spacing_x = spacing_x
                    self._spacing_y = spacing_y
                else:
                    self._spacing_x = 0
                    self._spacing_y = 0
                
                # Store the actual detected grid layout for accurate frame extraction
                self._detected_grid_cols = pattern_info['cols']
                self._detected_grid_rows = pattern_info['rows']
                self._detected_sprites = sprites
                self._is_content_based_detection = True
                
                status_msg = (f"Content-based detection: {frame_width}×{frame_height} frames, "
                            f"grid {pattern_info['cols']}×{pattern_info['rows']}, {len(sprites)} sprites found, "
                            f"pattern: {pattern_info['pattern']}")
                
                return True, frame_width, frame_height, status_msg
                
            finally:
                # Clean up temp file
                import os
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
        except Exception as e:
            return False, 0, 0, f"Error in content-based detection: {str(e)}"
    
    def _calculate_spacing_from_sprites(self, sprites) -> Tuple[int, int]:
        """Calculate spacing between sprites from their actual positions."""
        if len(sprites) < 2:
            return 0, 0
        
        # Find sprites that are horizontally adjacent
        horizontal_gaps = []
        for i, sprite1 in enumerate(sprites):
            for sprite2 in sprites[i+1:]:
                # Check if sprites are in same row (similar Y positions)
                if abs(sprite1.y - sprite2.y) < 10:
                    # Calculate gap between sprites
                    if sprite1.x < sprite2.x:
                        gap = sprite2.x - (sprite1.x + sprite1.width)
                        if gap >= 0:
                            horizontal_gaps.append(gap)
                    else:
                        gap = sprite1.x - (sprite2.x + sprite2.width)
                        if gap >= 0:
                            horizontal_gaps.append(gap)
        
        # Find sprites that are vertically adjacent
        vertical_gaps = []
        for i, sprite1 in enumerate(sprites):
            for sprite2 in sprites[i+1:]:
                # Check if sprites are in same column (similar X positions)
                if abs(sprite1.x - sprite2.x) < 10:
                    # Calculate gap between sprites
                    if sprite1.y < sprite2.y:
                        gap = sprite2.y - (sprite1.y + sprite1.height)
                        if gap >= 0:
                            vertical_gaps.append(gap)
                    else:
                        gap = sprite1.y - (sprite2.y + sprite2.height)
                        if gap >= 0:
                            vertical_gaps.append(gap)
        
        # Use most common gap size, or 0 if no clear pattern
        spacing_x = max(set(horizontal_gaps), key=horizontal_gaps.count) if horizontal_gaps else 0
        spacing_y = max(set(vertical_gaps), key=vertical_gaps.count) if vertical_gaps else 0
        
        return spacing_x, spacing_y
    
    def _detect_horizontal_strip(self, available_width: int, available_height: int) -> Tuple[float, int, int, int]:
        """
        Specialized detection for horizontal animation strips.
        Returns (best_score, best_width, best_height, candidates_tested).
        """
        best_score = 0
        best_width = 0
        best_height = 0
        candidates_tested = 0
        
        # For horizontal strips, try frame_height = available_height
        # and test various frame widths
        frame_height = available_height
        
        # Test frame widths that are divisors of available_width
        for frames_count in range(2, 21):  # Try 2-20 frames
            if available_width % frames_count == 0:
                frame_width = available_width // frames_count
                
                # Skip if frame is too small or unreasonably large
                if frame_width < 16 or frame_width > 512:
                    continue
                
                candidates_tested += 1
                
                # Score this horizontal strip candidate
                score = self._calculate_frame_score(frame_width, frame_height, frames_count, 
                                                  available_width / available_height, is_horizontal_strip=True)
                
                if score > best_score:
                    best_score = score
                    best_width = frame_width
                    best_height = frame_height
        
        # Also try common square sizes with full height
        for size in [16, 24, 32, 48, 64, 96, 128, 160, 192, 256]:
            if size <= available_height and size <= available_width:
                frames_count = available_width // size
                if frames_count >= 2:
                    candidates_tested += 1
                    
                    score = self._calculate_frame_score(size, available_height, frames_count,
                                                      available_width / available_height, is_horizontal_strip=True)
                    
                    if score > best_score:
                        best_score = score
                        best_width = size
                        best_height = available_height
        
        return best_score, best_width, best_height, candidates_tested
    
    def _calculate_frame_score(self, width: int, height: int, frame_count: int, sheet_aspect_ratio: float = 1.0, is_horizontal_strip: bool = False) -> float:
        """
        Calculate a score for how good a frame size candidate is.
        Higher scores indicate better matches.
        Improved version with reduced bias and better dimension matching.
        """
        score = 0
        
        # Frame count reasonableness
        if Config.FrameExtraction.MIN_REASONABLE_FRAMES <= frame_count <= Config.FrameExtraction.MAX_REASONABLE_FRAMES:
            score += 100
            
            # Sweet spot for frame counts (moderate bonus)
            if Config.FrameExtraction.OPTIMAL_FRAME_COUNT_MIN <= frame_count <= Config.FrameExtraction.OPTIMAL_FRAME_COUNT_MAX:
                score += 30
            
            # Penalty for excessive frame counts (indicates frames too small)
            if frame_count > 50 and not is_horizontal_strip:
                score -= min(50, (frame_count - 50) * 2)
        
        # Dimension matching bonus - NEW: prioritize frames that match sheet dimensions
        if self._original_sprite_sheet:
            available_width = self._original_sprite_sheet.width() - self._offset_x
            available_height = self._original_sprite_sheet.height() - self._offset_y
            
            # High bonus for frames that match a sheet dimension exactly
            if width == available_width or height == available_height:
                score += 100  # Major bonus for dimension matching
            elif width == available_height or height == available_width:
                score += 80   # Bonus for swapped dimension matching
            
            # Bonus for frames that are clean divisors of sheet dimensions
            if available_width % width == 0 and available_height % height == 0:
                score += 60   # Clean divisor bonus
        
        # Improved size appropriateness - FIXED: removed bias toward 32-128 range
        if 8 <= width <= 512 and 8 <= height <= 512:
            # Base score for reasonable sizes
            score += 60
            
            # Small bonus for power-of-2 sizes
            if (width & (width - 1)) == 0 and (height & (height - 1)) == 0:
                score += 20
            
            # Bonus for common sprite sizes without extreme bias
            common_sizes = [16, 24, 32, 48, 64, 96, 128, 160, 192, 256]
            if width in common_sizes or height in common_sizes:
                score += 30  # Reduced from 60 to reduce bias
        
        # Horizontal strip bonuses - IMPROVED
        if is_horizontal_strip:
            score += 80  # Significant bonus for horizontal strip detection
            
            # Strongly prioritize typical animation frame counts for horizontal strips
            if 8 <= frame_count <= 16:  # Very common animation frame counts
                score += 60  # Strong bonus for very typical frame counts
            elif 6 <= frame_count <= 24:  # Common animation frame counts
                score += 40  # Bonus for typical animation frame counts
            elif 4 <= frame_count <= 32:
                score += 20  # Smaller bonus for extended range
            
            # Reduce square frame bias for horizontal strips
            if width == height and self._original_sprite_sheet:
                available_height = self._original_sprite_sheet.height() - self._offset_y
                if height == available_height:
                    score += 30  # Reduced from 60 to prevent square frame dominance
        
        # Aspect ratio handling - IMPROVED
        gcd_val = math.gcd(width, height)
        ratio_w = width // gcd_val
        ratio_h = height // gcd_val
        
        if (ratio_w, ratio_h) in Config.FrameExtraction.COMMON_ASPECT_RATIOS:
            score += 40  # Reduced from 50
        elif ratio_w == ratio_h:  # Square
            score += 25  # Reduced from 30
        
        # Grid layout scoring - FIXED: don't penalize horizontal strips
        if self._original_sprite_sheet:
            available_width = self._original_sprite_sheet.width() - self._offset_x
            available_height = self._original_sprite_sheet.height() - self._offset_y
            
            cols = available_width // width
            rows = available_height // height
            
            if is_horizontal_strip:
                # For horizontal strips, prioritize single row
                if rows == 1:
                    score += 60  # Major bonus for single-row strips
                elif rows <= 3:
                    score += 30  # Bonus for few rows
            else:
                # Standard grid scoring for non-strips
                if 2 <= cols <= 8 and 2 <= rows <= 8:
                    score += 40  # Good grid size
                elif cols >= 2 and rows >= 2:
                    score += 20  # At least 2×2
                
                # Penalty for overly dense grids (only for non-strips)
                if cols > 10 and rows > 10:
                    score -= 30
        
        # Space utilization bonus
        if self._original_sprite_sheet:
            available_width = self._original_sprite_sheet.width() - self._offset_x
            available_height = self._original_sprite_sheet.height() - self._offset_y
            
            utilization = (width * height * frame_count) / (available_width * available_height)
            score += min(1.0, utilization)  # Fractional bonus for better space usage
        
        return score
    
    def _is_better_fit(self, new_width: int, new_height: int, current_width: int, current_height: int) -> bool:
        """
        Tie-breaking logic: determine if new size is better than current when scores are equal.
        """
        if current_width == 0 or current_height == 0:
            return True
        
        if not self._original_sprite_sheet:
            return False
        
        available_width = self._original_sprite_sheet.width() - self._offset_x
        available_height = self._original_sprite_sheet.height() - self._offset_y
        
        # Calculate space utilization
        new_util = (new_width * new_height) / (available_width * available_height)
        current_util = (current_width * current_height) / (available_width * available_height)
        
        # Prefer better space utilization
        if abs(new_util - current_util) > 0.1:
            return new_util > current_util
        
        # If utilization is similar, prefer more standard sizes
        new_standard = new_width in [16, 24, 32, 48, 64, 96, 128] and new_height in [16, 24, 32, 48, 64, 96, 128]
        current_standard = current_width in [16, 24, 32, 48, 64, 96, 128] and current_height in [16, 24, 32, 48, 64, 96, 128]
        
        if new_standard != current_standard:
            return new_standard
        
        # Finally, prefer aspect ratios closer to square
        new_ratio = max(new_width, new_height) / min(new_width, new_height)
        current_ratio = max(current_width, current_height) / min(current_width, current_height)
        
        return new_ratio < current_ratio
    
    def auto_detect_margins(self) -> Tuple[bool, int, int, str]:
        """
        Detect transparent margins around sprite content from all four edges.
        Improved version with validation and reasonableness checks.
        Returns (success, offset_x, offset_y, status_message).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet loaded"
        
        try:
            # Convert to QImage for pixel analysis
            image = self._original_sprite_sheet.toImage()
            width = image.width()
            height = image.height()
            
            # Get raw margin measurements
            raw_left, raw_right, raw_top, raw_bottom = self._detect_raw_margins(image)
            
            # Apply validation and reasonableness checks
            validated_left, validated_top, validation_msg = self._validate_margins(
                raw_left, raw_right, raw_top, raw_bottom, width, height)
            
            # Store the validated margins
            self._offset_x = validated_left
            self._offset_y = validated_top
            
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
        """Detect raw margin measurements from image edges."""
        width = image.width()
        height = image.height()
        
        # Detect left margin
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
        
        # Detect right margin
        right_margin = 0
        for x in range(width - 1, -1, -1):
            has_content = False
            for y in range(height):
                pixel = image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:
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
                if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:
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
                if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:
                    has_content = True
                    break
            if has_content:
                break
            bottom_margin += 1
        
        return left_margin, right_margin, top_margin, bottom_margin
    
    def _validate_margins(self, left: int, right: int, top: int, bottom: int, width: int, height: int) -> Tuple[int, int, str]:
        """
        Validate detected margins and apply reasonableness checks.
        Returns (validated_left, validated_top, validation_message).
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
        if hasattr(self, '_frame_width') and hasattr(self, '_frame_height'):
            if self._frame_width > 0 and self._frame_height > 0:
                # Check if margins make sense with current frame size
                available_after_margins = (width - validated_left, height - validated_top)
                
                # If margins would prevent clean division by frame size, reduce them
                if available_after_margins[0] % self._frame_width != 0:
                    # Try reducing left margin to get clean division
                    for reduced_left in range(validated_left - 1, -1, -1):
                        if (width - reduced_left) % self._frame_width == 0:
                            validated_left = reduced_left
                            validation_msg += f"Adjusted left margin to {reduced_left} for clean frame division; "
                            break
                
                if available_after_margins[1] % self._frame_height != 0:
                    # Try reducing top margin to get clean division
                    for reduced_top in range(validated_top - 1, -1, -1):
                        if (height - reduced_top) % self._frame_height == 0:
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
    
    def auto_detect_spacing_enhanced(self) -> Tuple[bool, int, int, str]:
        """
        Enhanced spacing detection that validates across multiple frame positions.
        Returns (success, spacing_x, spacing_y, status_message).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet loaded"
        
        if self._frame_width <= 0 or self._frame_height <= 0:
            return False, 0, 0, "Frame size must be set before detecting spacing"
        
        try:
            image = self._original_sprite_sheet.toImage()
            available_width = image.width() - self._offset_x
            available_height = image.height() - self._offset_y
            
            # Test spacing values from 0-10 pixels
            best_spacing_x = 0
            best_score_x = 0
            best_spacing_y = 0
            best_score_y = 0
            
            # Horizontal spacing detection
            for test_spacing in range(0, 11):
                score = 0
                positions_checked = 0
                
                # Calculate how many frames we could check with this spacing
                frames_per_row = (available_width + test_spacing) // (self._frame_width + test_spacing) if test_spacing > 0 else available_width // self._frame_width
                positions_to_check = min(3, frames_per_row - 1)  # Check up to 3 gap positions
                
                if positions_to_check <= 0:
                    continue
                
                for position in range(positions_to_check):
                    x_gap_start = self._offset_x + (position + 1) * self._frame_width + position * test_spacing
                    x_gap_end = x_gap_start + test_spacing
                    x_next_frame = x_gap_end
                    
                    # Check bounds
                    if x_next_frame + self._frame_width > image.width():
                        break
                        
                    positions_checked += 1
                    
                    # Check if gap is empty (for non-zero spacing)
                    gap_valid = True
                    if test_spacing > 0:
                        for y in range(self._offset_y, min(self._offset_y + self._frame_height, image.height()), 5):
                            for x in range(x_gap_start, x_gap_end):
                                if x < image.width():
                                    pixel = image.pixel(x, y)
                                    alpha = (pixel >> 24) & 0xFF
                                    if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:
                                        gap_valid = False
                                        break
                            if not gap_valid:
                                break
                    
                    # Check if frame exists at expected position
                    frame_exists = False
                    if gap_valid:
                        for y in range(self._offset_y, min(self._offset_y + 20, image.height()), 5):
                            pixel = image.pixel(x_next_frame, y)
                            alpha = (pixel >> 24) & 0xFF
                            if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:
                                frame_exists = True
                                break
                    
                    if gap_valid and frame_exists:
                        score += 1
                
                # Calculate consistency score
                consistency = score / positions_checked if positions_checked > 0 else 0
                if consistency > best_score_x:
                    best_score_x = consistency
                    best_spacing_x = test_spacing
            
            # Vertical spacing detection
            for test_spacing in range(0, 11):
                score = 0
                positions_checked = 0
                
                # Calculate how many frames we could check with this spacing
                frames_per_col = (available_height + test_spacing) // (self._frame_height + test_spacing) if test_spacing > 0 else available_height // self._frame_height
                positions_to_check = min(3, frames_per_col - 1)  # Check up to 3 gap positions
                
                if positions_to_check <= 0:
                    continue
                
                for position in range(positions_to_check):
                    y_gap_start = self._offset_y + (position + 1) * self._frame_height + position * test_spacing
                    y_gap_end = y_gap_start + test_spacing
                    y_next_frame = y_gap_end
                    
                    # Check bounds
                    if y_next_frame + self._frame_height > image.height():
                        break
                        
                    positions_checked += 1
                    
                    # Check if gap is empty (for non-zero spacing)
                    gap_valid = True
                    if test_spacing > 0:
                        for x in range(self._offset_x, min(self._offset_x + self._frame_width, image.width()), 5):
                            for y in range(y_gap_start, y_gap_end):
                                if y < image.height():
                                    pixel = image.pixel(x, y)
                                    alpha = (pixel >> 24) & 0xFF
                                    if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:
                                        gap_valid = False
                                        break
                            if not gap_valid:
                                break
                    
                    # Check if frame exists at expected position
                    frame_exists = False
                    if gap_valid:
                        for x in range(self._offset_x, min(self._offset_x + 20, image.width()), 5):
                            pixel = image.pixel(x, y_next_frame)
                            alpha = (pixel >> 24) & 0xFF
                            if alpha > Config.FrameExtraction.MARGIN_DETECTION_ALPHA_THRESHOLD:
                                frame_exists = True
                                break
                    
                    if gap_valid and frame_exists:
                        score += 1
                
                # Calculate consistency score
                consistency = score / positions_checked if positions_checked > 0 else 0
                if consistency > best_score_y:
                    best_score_y = consistency
                    best_spacing_y = test_spacing
            
            # Store detected spacing
            self._spacing_x = best_spacing_x
            self._spacing_y = best_spacing_y
            
            # Calculate confidence based on consistency scores
            avg_confidence = (best_score_x + best_score_y) / 2
            confidence_text = "high" if avg_confidence >= 0.8 else "medium" if avg_confidence >= 0.5 else "low"
            
            return True, best_spacing_x, best_spacing_y, (
                f"Auto-detected spacing: X={best_spacing_x}, Y={best_spacing_y} "
                f"(confidence: {confidence_text}, consistency: {avg_confidence:.2f})"
            )
            
        except Exception as e:
            return False, 0, 0, f"Error in enhanced spacing detection: {str(e)}"
    
    # Keep the old method for backward compatibility
    def auto_detect_spacing(self) -> Tuple[bool, int, int, str]:
        """Legacy spacing detection method. Use auto_detect_spacing_enhanced for better results."""
        return self.auto_detect_spacing_enhanced()
    
    def comprehensive_auto_detect(self) -> Tuple[bool, str]:
        """
        Comprehensive one-click auto-detection workflow.
        Detects margins, frame size, and spacing in optimal order with cross-validation.
        Returns (success, detailed_status_message).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, "No sprite sheet loaded"
        
        results = []
        overall_success = True
        confidence_scores = []
        
        try:
            # Step 1: Detect margins first (affects all other calculations)
            results.append("🔍 Step 1: Detecting margins...")
            
            try:
                margin_success, offset_x, offset_y, margin_msg = self.auto_detect_margins()
            except Exception as e:
                margin_success, offset_x, offset_y, margin_msg = False, 0, 0, f"Error: {str(e)}"
            
            if margin_success:
                results.append(f"   ✓ {margin_msg}")
                confidence_scores.append(0.9)  # Margin detection is usually reliable
            else:
                results.append(f"   ⚠ Margin detection failed: {margin_msg}")
                results.append("   → Using default margins (0, 0)")
                confidence_scores.append(0.3)
            
            # Step 2: Detect optimal frame size (content-based detection with fallback)
            results.append("\n🔍 Step 2: Detecting frame size...")
            frame_success = False
            ccl_used = False
            
            # Try CCL detection first (if available)
            if CCL_AVAILABLE and hasattr(self, '_sprite_sheet_path'):
                try:
                    ccl_msg = f"   🧪 Attempting CCL (Connected-Component Labeling) detection [NumPy+SciPy available]..."
                    results.append(ccl_msg)
                    print(ccl_msg)  # Console output
                    ccl_result = detect_sprites_ccl_enhanced(self._sprite_sheet_path)
                    
                    # Add CCL debug log to results
                    if ccl_result and 'debug_log' in ccl_result:
                        for log_line in ccl_result['debug_log']:
                            results.append(log_line)
                    
                    if ccl_result and ccl_result.get('success', False):
                        self._frame_width = ccl_result['frame_width']
                        self._frame_height = ccl_result['frame_height']
                        self._offset_x = ccl_result['offset_x']
                        self._offset_y = ccl_result['offset_y']
                        self._spacing_x = ccl_result['spacing_x']
                        self._spacing_y = ccl_result['spacing_y']
                        
                        frame_success = True
                        confidence = ccl_result.get('confidence', 'high')
                        sprite_count = ccl_result.get('sprite_count', 0)
                        success_msg = f"   ✅ CCL SUCCESS: {self._frame_width}×{self._frame_height}, {sprite_count} sprites, confidence: {confidence}"
                        results.append(success_msg)
                        print(success_msg)  # Console output
                        confidence_scores.append(0.98)  # CCL is most accurate
                        
                        # Store CCL sprite boundaries for CCL extraction mode
                        if 'ccl_sprite_bounds' in ccl_result:
                            self._ccl_sprite_bounds = ccl_result['ccl_sprite_bounds']
                            self._ccl_available = True
                            
                            ccl_bounds_msg = f"   💾 Stored {len(self._ccl_sprite_bounds)} exact sprite boundaries for CCL mode"
                            results.append(ccl_bounds_msg)
                            print(ccl_bounds_msg)
                            
                            # Detect background color separately (clean approach)
                            bg_detection_msg = f"   🔍 Running separate background color detection..."
                            results.append(bg_detection_msg)
                            print(bg_detection_msg)
                            
                            bg_color_info = detect_background_color(self._sprite_sheet_path)
                            if bg_color_info is not None:
                                self._ccl_background_color = bg_color_info[0]  # RGB color tuple  
                                self._ccl_color_tolerance = bg_color_info[1]   # Tolerance
                                bg_color_msg = f"   🎨 Detected background color {self._ccl_background_color} (tolerance: {self._ccl_color_tolerance}px) for transparency"
                                results.append(bg_color_msg)
                                print(bg_color_msg)
                            else:
                                bg_none_msg = f"   ℹ️  No background color detected (transparent image or detection failed)"
                                results.append(bg_none_msg)
                                print(bg_none_msg)
                                self._ccl_background_color = None
                                self._ccl_color_tolerance = 0
                            
                            # Check if this is an irregular collection
                            if ccl_result.get('irregular_collection', False):
                                irregular_msg = f"   ⚠️  IRREGULAR COLLECTION: Consider switching to CCL extraction mode"
                                results.append(irregular_msg)
                                print(irregular_msg)
                        
                        # Skip other detection methods since CCL succeeded
                        skip_msg = f"   🎯 Skipping fallback methods - CCL provided excellent results"
                        results.append(skip_msg)
                        print(skip_msg)  # Console output
                        ccl_used = True
                    else:
                        error_msg = ccl_result.get('error', 'unknown reason') if ccl_result else 'no result returned'
                        fail_msg = f"   ❌ CCL detection failed ({error_msg}), falling back to content-based..."
                        results.append(fail_msg)
                        print(fail_msg)  # Console output
                except Exception as e:
                    error_msg = f"   💥 CCL detection error: {str(e)}, falling back..."
                    results.append(error_msg)
                    print(error_msg)  # Console output
            else:
                if not CCL_AVAILABLE:
                    unavail_msg = f"   ⚠ CCL detection unavailable (NumPy/SciPy not installed), using traditional methods..."
                    results.append(unavail_msg)
                    print(unavail_msg)  # Console output
                else:
                    skip_msg = f"   ⚠ CCL detection skipped (no sprite sheet path), using traditional methods..."
                    results.append(skip_msg)
                    print(skip_msg)  # Console output
            
            # Try content-based detection if CCL failed
            if not frame_success:
                try:
                    content_success, frame_width, frame_height, content_msg = self.auto_detect_content_based()
                    
                    if content_success:
                        frame_success = True
                        results.append(f"   ✓ {content_msg}")
                        confidence_scores.append(0.95)  # Content-based detection is very reliable
                    else:
                        results.append(f"   ⚠ Content-based detection failed: {content_msg}")
                        results.append("   → Falling back to mathematical detection...")
                        
                        # Fall back to rectangular detection
                        try:
                            rect_success, frame_width, frame_height, frame_msg = self.auto_detect_rectangular_frames()
                            
                            if rect_success:
                                frame_success = True
                                results.append(f"   ✓ {frame_msg}")
                                # Extract confidence from message if available
                                if "confidence: high" in frame_msg:
                                    confidence_scores.append(0.9)
                                elif "confidence: medium" in frame_msg:
                                    confidence_scores.append(0.7)
                                else:
                                    confidence_scores.append(0.5)
                            else:
                                results.append(f"   ⚠ Rectangular detection failed: {frame_msg}")
                                results.append("   → Falling back to legacy square detection...")
                                
                                # Try legacy square detection as final fallback
                                try:
                                    legacy_success, legacy_width, legacy_height, legacy_msg = self.auto_detect_frame_size()
                                    if legacy_success:
                                        frame_success = True
                                        results.append(f"   ✓ Legacy detection: {legacy_msg}")
                                        confidence_scores.append(0.6)
                                    else:
                                        results.append(f"   ✗ All frame detection failed: {legacy_msg}")
                                        overall_success = False
                                        confidence_scores.append(0.1)
                                except Exception as e:
                                    results.append(f"   ✗ Legacy detection error: {str(e)}")
                                    overall_success = False
                                    confidence_scores.append(0.1)
                        except Exception as e:
                            results.append(f"   ✗ Rectangular detection error: {str(e)}")
                            overall_success = False
                            confidence_scores.append(0.1)
                except Exception as e:
                    results.append(f"   ✗ Content-based detection error: {str(e)}")
                    overall_success = False
                    confidence_scores.append(0.1)
            
            # Step 3: Detect spacing (only if frame size detection succeeded and CCL wasn't used)
            if self._frame_width > 0 and self._frame_height > 0:
                if ccl_used:
                    results.append("\n🔍 Step 3: Frame spacing...")
                    results.append(f"   ✅ Spacing already detected by CCL: ({self._spacing_x}, {self._spacing_y})")
                    confidence_scores.append(0.95)  # CCL spacing is very reliable
                else:
                    results.append("\n🔍 Step 3: Detecting frame spacing...")
                    
                    try:
                        spacing_success, spacing_x, spacing_y, spacing_msg = self.auto_detect_spacing_enhanced()
                        
                        if spacing_success:
                            results.append(f"   ✓ {spacing_msg}")
                            # Extract confidence from message
                            if "confidence: high" in spacing_msg:
                                confidence_scores.append(0.9)
                            elif "confidence: medium" in spacing_msg:
                                confidence_scores.append(0.7)
                            else:
                                confidence_scores.append(0.5)
                        else:
                            results.append(f"   ⚠ Spacing detection failed: {spacing_msg}")
                            results.append("   → Using default spacing (0, 0)")
                            confidence_scores.append(0.3)
                    except Exception as e:
                        results.append(f"   ✗ Spacing detection error: {str(e)}")
                        results.append("   → Using default spacing (0, 0)")
                        confidence_scores.append(0.2)
            else:
                results.append("\n⚠ Step 3: Skipped spacing detection (no valid frame size)")
                confidence_scores.append(0.1)
            
            # Step 4: Cross-validation and final verification
            results.append("\n🔍 Step 4: Cross-validation...")
            try:
                validation_success, validation_msg = self._validate_detection_consistency()
                
                if validation_success:
                    results.append(f"   ✓ {validation_msg}")
                    confidence_scores.append(0.8)
                else:
                    results.append(f"   ⚠ {validation_msg}")
                    confidence_scores.append(0.4)
            except Exception as e:
                results.append(f"   ✗ Validation error: {str(e)}")
                confidence_scores.append(0.3)
            
            # Step 5: Calculate overall confidence and summary
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            confidence_text = "high" if overall_confidence >= 0.8 else "medium" if overall_confidence >= 0.6 else "low"
            
            results.append(f"\n📊 Overall Result:")
            results.append(f"   • Frame Size: {self._frame_width}×{self._frame_height}")
            results.append(f"   • Margins: X={self._offset_x}, Y={self._offset_y}")
            results.append(f"   • Spacing: X={self._spacing_x}, Y={self._spacing_y}")
            results.append(f"   • Confidence: {confidence_text} ({overall_confidence:.1%})")
            
            if overall_success and overall_confidence >= 0.6:
                results.append("   🎉 Auto-detection completed successfully!")
            elif overall_confidence >= 0.4:
                results.append("   ⚠ Auto-detection completed with warnings")
            else:
                results.append("   ❌ Auto-detection completed with low confidence")
                overall_success = False
            
            return overall_success, "\n".join(results)
            
        except Exception as e:
            error_msg = f"❌ Comprehensive auto-detection failed: {str(e)}"
            results.append(error_msg)
            return False, "\n".join(results)
    
    def _validate_detection_consistency(self) -> Tuple[bool, str]:
        """
        Validate that all detected parameters work together consistently.
        Returns (success, status_message).
        """
        try:
            if not self._original_sprite_sheet:
                return False, "No sprite sheet loaded"
            
            # Check basic parameter validity
            if self._frame_width <= 0 or self._frame_height <= 0:
                return False, "Invalid frame dimensions detected"
            
            # Validate with current sheet dimensions
            valid, error_msg = self.validate_frame_settings(
                self._frame_width, self._frame_height, 
                self._offset_x, self._offset_y,
                self._spacing_x, self._spacing_y
            )
            
            if not valid:
                return False, f"Parameter validation failed: {error_msg}"
            
            # Calculate expected frame count
            available_width = self._original_sprite_sheet.width() - self._offset_x
            available_height = self._original_sprite_sheet.height() - self._offset_y
            
            if self._spacing_x > 0:
                frames_x = (available_width + self._spacing_x) // (self._frame_width + self._spacing_x)
            else:
                frames_x = available_width // self._frame_width
                
            if self._spacing_y > 0:
                frames_y = (available_height + self._spacing_y) // (self._frame_height + self._spacing_y)
            else:
                frames_y = available_height // self._frame_height
            
            expected_frames = frames_x * frames_y
            
            # Check if frame count is reasonable
            if expected_frames < Config.FrameExtraction.MIN_REASONABLE_FRAMES:
                return False, f"Too few frames detected ({expected_frames})"
            
            if expected_frames > Config.FrameExtraction.MAX_REASONABLE_FRAMES:
                return False, f"Too many frames detected ({expected_frames})"
            
            return True, f"Validation passed: {frames_x}×{frames_y} = {expected_frames} frames"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    # ============================================================================
    # ANIMATION STATE MANAGEMENT (Will be implemented in Step 3.6)
    # ============================================================================
    
    def set_current_frame(self, frame: int) -> bool:
        """Set the current animation frame with bounds checking using animation state manager."""
        return self._animation_state.set_current_frame(frame)
    
    def next_frame(self) -> Tuple[int, bool]:
        """Advance to next frame, handling looping using animation state manager."""
        return self._animation_state.next_frame()
    
    def previous_frame(self) -> int:
        """Go to previous frame with bounds checking using animation state manager."""
        return self._animation_state.previous_frame()
    
    def first_frame(self) -> int:
        """Jump to first frame using animation state manager."""
        return self._animation_state.first_frame()
    
    def last_frame(self) -> int:
        """Jump to last frame using animation state manager."""
        return self._animation_state.last_frame()
    
    # ============================================================================
    # PLAYBACK CONTROL (Will be implemented in Step 3.6)
    # ============================================================================
    
    def play(self) -> bool:
        """Start animation playback using animation state manager."""
        return self._animation_state.play()
    
    def pause(self) -> None:
        """Pause animation playback using animation state manager."""
        self._animation_state.pause()
    
    def stop(self) -> None:
        """Stop animation and reset to first frame using animation state manager."""
        self._animation_state.stop()
    
    def toggle_playback(self) -> bool:
        """Toggle playback state using animation state manager."""
        return self._animation_state.toggle_playback()
    
    def set_fps(self, fps: int) -> bool:
        """Set animation speed with validation using animation state manager."""
        return self._animation_state.set_fps(fps)
    
    def set_loop_enabled(self, enabled: bool) -> None:
        """Set animation loop mode using animation state manager."""
        self._animation_state.set_loop_enabled(enabled)
    
    # ============================================================================
    # DATA ACCESS PROPERTIES (Will be implemented in Step 3.2)
    # ============================================================================
    
    @property
    def current_frame_pixmap(self) -> Optional[QPixmap]:
        """Get the currently selected frame as QPixmap using animation state manager."""
        return self._animation_state.current_frame_pixmap
    
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
        """Get current frame index using animation state manager."""
        return self._animation_state.current_frame
    
    @property
    def total_frames(self) -> int:
        """Get total frame count using animation state manager."""
        return self._animation_state.total_frames
    
    @property
    def is_playing(self) -> bool:
        """Get animation playback state using animation state manager."""
        return self._animation_state.is_playing
    
    @property
    def fps(self) -> int:
        """Get current FPS setting using animation state manager."""
        return self._animation_state.fps
    
    @property
    def loop_enabled(self) -> bool:
        """Get animation loop setting using animation state manager."""
        return self._animation_state.is_loop_enabled
    
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