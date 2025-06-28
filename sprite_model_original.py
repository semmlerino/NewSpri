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

# Import CCL functionality (always available when modules exist)
try:
    from sprite_model.extraction.background_detector import detect_background_color
    from sprite_model.extraction.ccl_extractor import detect_sprites_ccl_enhanced
    CCL_AVAILABLE = True
except ImportError:
    CCL_AVAILABLE = False
    def detect_background_color(image_path: str) -> Optional[Tuple[Tuple[int, int, int], int]]:
        return None
    def detect_sprites_ccl_enhanced(image_path: str) -> Optional[dict]:
        return None

# Import grid extraction functionality
try:
    from sprite_model.extraction.grid_extractor import GridExtractor, GridConfig
    GRID_EXTRACTOR_AVAILABLE = True
except ImportError:
    GRID_EXTRACTOR_AVAILABLE = False
    # Fallback GridExtractor class
    class GridExtractor:
        def extract_frames(self, *args, **kwargs):
            return False, "Grid extractor not available", []
        def validate_frame_settings(self, *args, **kwargs):
            return False, "Grid extractor not available"
        def calculate_grid_layout(self, *args, **kwargs):
            return None
    
    class GridConfig:
        def __init__(self, *args, **kwargs):
            pass

# Import animation state management
try:
    from sprite_model.animation.state_manager import AnimationStateManager
    ANIMATION_MANAGER_AVAILABLE = True
except ImportError:
    ANIMATION_MANAGER_AVAILABLE = False
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

# Import detection modules
try:
    from sprite_model.detection.frame_detector import FrameDetector
    from sprite_model.detection.margin_detector import MarginDetector
    from sprite_model.detection.spacing_detector import SpacingDetector
    from sprite_model.detection.coordinator import DetectionCoordinator, DetectionResult
    DETECTION_AVAILABLE = True
except ImportError:
    DETECTION_AVAILABLE = False
    # Fallback Detection classes
    class FrameDetector:
        def detect_frame_size(self, sprite_sheet): return False, 0, 0, "Frame detector not available"
        def detect_rectangular_frames(self, sprite_sheet): return False, 0, 0, "Frame detector not available"
        def detect_content_based(self, sprite_sheet): return False, 0, 0, "Frame detector not available"
    
    class MarginDetector:
        def detect_margins(self, sprite_sheet, frame_width=None, frame_height=None): return False, 0, 0, "Margin detector not available"
    
    class SpacingDetector:
        def detect_spacing(self, sprite_sheet, frame_width, frame_height, offset_x=0, offset_y=0): return False, 0, 0, "Spacing detector not available"
    
    class DetectionResult:
        def __init__(self):
            self.frame_width = 0
            self.frame_height = 0
            self.offset_x = 0
            self.offset_y = 0
            self.spacing_x = 0
            self.spacing_y = 0
            self.success = False
            self.confidence = 0.0
            self.messages = []
    
    class DetectionCoordinator:
        def __init__(self):
            print("Warning: Using fallback DetectionCoordinator")
        def comprehensive_auto_detect(self, sprite_sheet, sprite_sheet_path=None): 
            result = DetectionResult()
            return False, "Detection coordinator not available", result

# Import file operations modules
try:
    from sprite_model.file_operations.file_loader import FileLoader
    from sprite_model.file_operations.metadata_extractor import MetadataExtractor
    from sprite_model.file_operations.file_validator import FileValidator
    FILE_OPERATIONS_AVAILABLE = True
except ImportError:
    FILE_OPERATIONS_AVAILABLE = False
    # Fallback classes for file operations
    class FileLoader:
        def load_sprite_sheet(self, file_path): return False, None, {}, "File operations not available"
        def reload_sprite_sheet(self, file_path): return False, None, {}, "File operations not available"
    
    class MetadataExtractor:
        def extract_file_metadata(self, file_path, pixmap): return {}
        def format_sprite_info(self, *args, **kwargs): return "Metadata extraction not available"
        def update_sprite_info_with_frames(self, current_info, frame_count, frames_per_row=0, frames_per_col=0): return current_info
    
    class FileValidator:
        def validate_file_path(self, file_path): return False, "File validation not available"

# Import CCL operations module
try:
    from sprite_model.ccl.ccl_operations import CCLOperations
    CCL_OPERATIONS_AVAILABLE = True
except ImportError:
    CCL_OPERATIONS_AVAILABLE = False
    # Fallback CCL operations class
    class CCLOperations:
        def __init__(self): pass
        def set_callbacks(self, *args): pass
        def extract_ccl_frames(self, *args): return False, "CCL operations not available", 0, [], ""
        def set_extraction_mode(self, *args): return False
        def get_extraction_mode(self): return "grid"
        def is_ccl_available(self, ccl_available): return False
        def get_ccl_sprite_bounds(self): return []
        def clear_ccl_data(self): pass


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
        # EXTRACTED FUNCTIONALITY
        # ============================================================================
        
        # Initialize grid extractor for modular frame extraction
        self._grid_extractor = GridExtractor()
        
        # Initialize animation state manager for modular animation control
        self._animation_state = AnimationStateManager()
        self._animation_state.set_sprite_frames_getter(lambda: self._sprite_frames)
        
        # Initialize file operations modules for modular file handling
        self._file_loader = FileLoader()
        self._metadata_extractor = MetadataExtractor()
        self._file_validator = FileValidator()
        
        # Initialize CCL operations module for modular CCL processing
        self._ccl_operations = CCLOperations()
        self._ccl_operations.set_callbacks(
            get_original_sprite_sheet=lambda: self._original_sprite_sheet,
            get_sprite_sheet_path=lambda: getattr(self, '_sprite_sheet_path', ''),
            emit_extraction_completed=self.extractionCompleted.emit
        )
        
        # Connect animation state signals to our signals for backwards compatibility
        self._animation_state.frameChanged.connect(self.frameChanged.emit)
        self._animation_state.playbackStateChanged.connect(self.playbackStateChanged.emit)
    
    # ============================================================================
    # FILE OPERATIONS (Will be implemented in Step 3.3)
    # ============================================================================
    
    def load_sprite_sheet(self, file_path: str) -> Tuple[bool, str]:
        """
        Load and validate sprite sheet from file path using extracted file operations.
        Returns (success, error_message).
        """
        try:
            if FILE_OPERATIONS_AVAILABLE:
                # Use extracted file loader
                success, pixmap, metadata, error_msg = self._file_loader.load_sprite_sheet(file_path)
                
                if success and pixmap is not None:
                    # Store the loaded data
                    self._original_sprite_sheet = pixmap
                    
                    # Apply metadata
                    self._file_path = metadata.get('file_path', file_path)
                    self._sprite_sheet_path = file_path  # Store for CCL detection
                    self._file_name = metadata.get('file_name', Path(file_path).name)
                    self._sheet_width = metadata.get('sheet_width', pixmap.width())
                    self._sheet_height = metadata.get('sheet_height', pixmap.height())
                    self._file_format = metadata.get('file_format', 'UNKNOWN')
                    self._last_modified = metadata.get('last_modified', 0.0)
                    self._sprite_sheet_info = metadata.get('sprite_sheet_info', '')
                    
                    # Reset state
                    self._current_frame = 0
                    self._is_valid = True
                    self._error_message = ""
                    
                    # Emit data loaded signal
                    self.dataLoaded.emit(file_path)
                    
                    return True, ""
                else:
                    self._is_valid = False
                    self._error_message = error_msg
                    return False, error_msg
            else:
                # Fallback to basic implementation
                return self._fallback_load_sprite_sheet(file_path)
        except Exception as e:
            self._is_valid = False
            self._error_message = str(e)
            return False, f"Error loading sprite sheet: {str(e)}"
    
    def reload_current_sheet(self) -> Tuple[bool, str]:
        """Reload the current sprite sheet (for file changes) using extracted file operations."""
        if not self._file_path:
            return False, "No sprite sheet currently loaded"
        
        if FILE_OPERATIONS_AVAILABLE:
            # Use extracted file loader for consistency
            return self.load_sprite_sheet(self._file_path)
        else:
            # Fallback implementation
            return self._fallback_reload_sprite_sheet()
    
    def clear_sprite_data(self) -> None:
        """Clear all sprite data and reset to empty state using extracted functionality."""
        # Clear image data
        self._original_sprite_sheet = None
        self._sprite_frames.clear()
        
        # Clear file metadata
        self._file_path = ""
        self._file_name = ""
        self._sprite_sheet_info = ""
        self._sheet_width = 0
        self._sheet_height = 0
        self._file_format = ""
        self._last_modified = 0.0
        
        # Clear state
        self._is_valid = False
        self._error_message = ""
        
        # Reset animation state using extracted animation state manager
        self._animation_state.reset_state()
        
        # Clear CCL data using extracted CCL operations module
        self._ccl_operations.clear_ccl_data()
    
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
        try:
            # Use extracted CCL operations module
            success, error, count, frames, info_update = self._ccl_operations.extract_ccl_frames(
                CCL_AVAILABLE, detect_sprites_ccl_enhanced, detect_background_color
            )
            
            if success:
                # Update sprite model state with extracted frames
                print(f"   🎯 CCL extracted {len(frames)} frames, updating self._sprite_frames")
                self._sprite_frames = frames
                print(f"   🎯 self._sprite_frames now has {len(self._sprite_frames)} items")
                self._total_frames = count
                self._current_frame = 0
                
                # Update sprite sheet info with CCL information
                if info_update:
                    # Remove any existing frame info and add CCL info
                    base_info = self._sprite_sheet_info.split('<br><b>Frames:</b>')[0].split('<br><b>CCL Frames:</b>')[0]
                    self._sprite_sheet_info = base_info + info_update
                
                # Update animation state with new frame count
                print(f"   🔧 Before animation state update: self._total_frames={self._total_frames}, animation_state.total_frames={self._animation_state.total_frames}")
                self._animation_state.update_frame_count(self._total_frames)
                print(f"   🔧 After animation state update: self._total_frames={self._total_frames}, animation_state.total_frames={self._animation_state.total_frames}")
            
            return success, error, count
            
        except Exception as e:
            self._error_message = str(e)
            return False, f"Error extracting CCL frames: {str(e)}", 0
    
    def get_extraction_mode(self) -> str:
        """Get current extraction mode: 'grid' or 'ccl'."""
        return self._ccl_operations.get_extraction_mode()
    
    def set_extraction_mode(self, mode: str) -> bool:
        """
        Set extraction mode and extract frames accordingly.
        Returns True if successful.
        """
        # Create callback for grid frame extraction
        def extract_grid_frames_callback():
            return self.extract_frames(
                self._frame_width, self._frame_height,
                self._offset_x, self._offset_y,
                self._spacing_x, self._spacing_y
            )
        
        # Use extracted CCL operations module for mode switching
        success = self._ccl_operations.set_extraction_mode(
            mode, CCL_AVAILABLE, extract_grid_frames_callback,
            detect_sprites_ccl_enhanced, detect_background_color
        )
        
        # If CCL mode was successful, retrieve the extracted frames
        if success and mode == "ccl":
            ccl_frames = self._ccl_operations.get_last_extracted_frames()
            if ccl_frames:
                print(f"🔄 Retrieved {len(ccl_frames)} CCL frames for main sprite model")
                self._sprite_frames = ccl_frames
                # Update animation state manager with new frame count
                if hasattr(self, '_animation_state'):
                    self._animation_state.update_frame_count(len(ccl_frames))
                # Emit extraction completed signal
                self.extractionCompleted.emit(len(ccl_frames))
                print(f"✅ Main sprite model updated: {len(self._sprite_frames)} frames, total_frames: {self.total_frames}")
        
        return success
    
    def is_ccl_available(self) -> bool:
        """Check if CCL extraction mode is available."""
        return self._ccl_operations.is_ccl_available(CCL_AVAILABLE)
    
    def get_ccl_sprite_bounds(self) -> List[Tuple[int, int, int, int]]:
        """Get the CCL-detected sprite boundaries."""
        return self._ccl_operations.get_ccl_sprite_bounds()
    
    def _apply_background_transparency(self, pixmap: QPixmap, background_color: Tuple[int, int, int], tolerance: int) -> QPixmap:
        """Apply background color transparency to a QPixmap using extracted CCL operations."""
        return self._ccl_operations._apply_background_transparency(pixmap, background_color, tolerance)
    
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
        
        try:
            if DETECTION_AVAILABLE:
                # Use extracted frame detector
                frame_detector = FrameDetector()
                success, width, height, msg = frame_detector.detect_frame_size(self._original_sprite_sheet)
                
                if success:
                    # Store the detected size
                    self._frame_width = width
                    self._frame_height = height
                
                return success, width, height, msg
            else:
                # Fallback to basic implementation
                return self._fallback_frame_detection()
        except Exception as e:
            return False, 0, 0, f"Frame detection error: {str(e)}"
    
    def auto_detect_rectangular_frames(self) -> Tuple[bool, int, int, str]:
        """
        Enhanced frame size detection supporting rectangular frames and horizontal strips.
        Uses aspect ratios, scoring, and specialized detection for different sprite sheet types.
        Returns (success, width, height, status_message).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, 0, 0, "No sprite sheet loaded"
        
        try:
            if DETECTION_AVAILABLE:
                # Use extracted frame detector
                frame_detector = FrameDetector()
                success, width, height, msg = frame_detector.detect_rectangular_frames(self._original_sprite_sheet)
                
                if success:
                    # Store the detected size
                    self._frame_width = width
                    self._frame_height = height
                
                return success, width, height, msg
            else:
                # Fallback to basic implementation
                return self._fallback_rectangular_detection()
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
            if DETECTION_AVAILABLE:
                # Use extracted frame detector
                frame_detector = FrameDetector()
                success, width, height, msg = frame_detector.detect_content_based(self._original_sprite_sheet)
                
                if success:
                    # Store the detected size
                    self._frame_width = width
                    self._frame_height = height
                
                return success, width, height, msg
            else:
                # Fallback to basic implementation
                return self._fallback_content_detection()
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
            if DETECTION_AVAILABLE:
                # Use extracted margin detector
                margin_detector = MarginDetector()
                success, offset_x, offset_y, msg = margin_detector.detect_margins(
                    self._original_sprite_sheet, self._frame_width, self._frame_height)
                
                if success:
                    # Store the validated margins
                    self._offset_x = offset_x
                    self._offset_y = offset_y
                
                return success, offset_x, offset_y, msg
            else:
                # Fallback to basic implementation
                return self._fallback_margin_detection()
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
            if DETECTION_AVAILABLE:
                # Use extracted spacing detector
                spacing_detector = SpacingDetector()
                success, spacing_x, spacing_y, msg = spacing_detector.detect_spacing(
                    self._original_sprite_sheet, self._frame_width, self._frame_height,
                    self._offset_x, self._offset_y)
                
                if success:
                    # Store detected spacing
                    self._spacing_x = spacing_x
                    self._spacing_y = spacing_y
                
                return success, spacing_x, spacing_y, msg
            else:
                # Fallback to basic implementation
                return self._fallback_spacing_detection()
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
        
        try:
            if DETECTION_AVAILABLE:
                # Use extracted detection coordinator
                detection_coordinator = DetectionCoordinator()
                success, msg, result = detection_coordinator.comprehensive_auto_detect(
                    self._original_sprite_sheet, getattr(self, '_sprite_sheet_path', None))
                
                if success:
                    # Store detected parameters
                    self._frame_width = result.frame_width
                    self._frame_height = result.frame_height
                    self._offset_x = result.offset_x
                    self._offset_y = result.offset_y
                    self._spacing_x = result.spacing_x
                    self._spacing_y = result.spacing_y
                
                return success, msg
            else:
                # Fallback to basic implementation
                return self._fallback_comprehensive_detection()
        except Exception as e:
            return False, f"❌ Comprehensive auto-detection failed: {str(e)}"
    
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

    # ============================================================================
    # FALLBACK DETECTION METHODS (for when extracted modules are unavailable)
    # ============================================================================
    
    def _fallback_frame_detection(self) -> Tuple[bool, int, int, str]:
        """Fallback frame detection when FrameDetector is unavailable."""
        return False, 0, 0, "Frame detection modules not available"
    
    def _fallback_rectangular_detection(self) -> Tuple[bool, int, int, str]:
        """Fallback rectangular detection when FrameDetector is unavailable."""
        return False, 0, 0, "Rectangular detection modules not available"
    
    def _fallback_content_detection(self) -> Tuple[bool, int, int, str]:
        """Fallback content detection when FrameDetector is unavailable."""
        return False, 0, 0, "Content-based detection modules not available"
    
    def _fallback_margin_detection(self) -> Tuple[bool, int, int, str]:
        """Fallback margin detection when MarginDetector is unavailable."""
        return False, 0, 0, "Margin detection modules not available"
    
    def _fallback_spacing_detection(self) -> Tuple[bool, int, int, str]:
        """Fallback spacing detection when SpacingDetector is unavailable."""
        return False, 0, 0, "Spacing detection modules not available"
    
    def _fallback_comprehensive_detection(self) -> Tuple[bool, str]:
        """Fallback comprehensive detection when DetectionCoordinator is unavailable."""
        return False, "Comprehensive detection modules not available"
    
    # ============================================================================
    # FALLBACK FILE OPERATIONS METHODS (for when extracted modules are unavailable)
    # ============================================================================
    
    def _fallback_load_sprite_sheet(self, file_path: str) -> Tuple[bool, str]:
        """Fallback file loading when FileLoader is unavailable."""
        try:
            # Basic file loading without validation
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                return False, "Failed to load image file"
            
            # Store basic data
            self._original_sprite_sheet = pixmap
            file_path_obj = Path(file_path)
            self._file_path = file_path
            self._sprite_sheet_path = file_path
            self._file_name = file_path_obj.name
            self._sheet_width = pixmap.width()
            self._sheet_height = pixmap.height()
            self._file_format = file_path_obj.suffix.upper()[1:] if file_path_obj.suffix else "UNKNOWN"
            self._last_modified = os.path.getmtime(file_path) if os.path.exists(file_path) else 0.0
            
            # Basic info string
            self._sprite_sheet_info = (
                f"<b>File:</b> {self._file_name}<br>"
                f"<b>Size:</b> {self._sheet_width} × {self._sheet_height} px<br>"
                f"<b>Format:</b> {self._file_format}"
            )
            
            self._current_frame = 0
            self._is_valid = True
            self._error_message = ""
            
            self.dataLoaded.emit(file_path)
            return True, ""
            
        except Exception as e:
            self._is_valid = False
            self._error_message = str(e)
            return False, f"Error loading sprite sheet: {str(e)}"
    
    def _fallback_reload_sprite_sheet(self) -> Tuple[bool, str]:
        """Fallback reload when FileLoader is unavailable."""
        if not self._file_path:
            return False, "No sprite sheet currently loaded"
        return self._fallback_load_sprite_sheet(self._file_path)


# Export for easy importing
__all__ = ['SpriteModel']