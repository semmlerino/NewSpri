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

# Try to import CCL detection (optional dependency)
try:
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    CCL_AVAILABLE = True
    
    def detect_sprites_ccl_enhanced(image_path: str) -> Optional[dict]:
        """
        Enhanced CCL detection integrated into sprite model.
        Returns detection results or None if CCL fails.
        """
        debug_log = []
        try:
            log_msg = f"🔬 CCL Detection starting on: {image_path}"
            debug_log.append(log_msg)
            print(log_msg)  # Console output
            
            # Load image as RGBA numpy array
            img = Image.open(image_path).convert('RGBA')
            img_array = np.array(img)
            log_msg = f"   📁 Loaded image: {img_array.shape} (height, width, channels)"
            debug_log.append(log_msg)
            print(log_msg)  # Console output
            
            # Create binary mask based on alpha channel
            alpha_channel = img_array[:, :, 3]
            binary_mask = (alpha_channel > 128).astype(np.uint8)
            opaque_pixels = np.sum(binary_mask)
            total_pixels = binary_mask.size
            log_msg = f"   🎭 Binary mask: {opaque_pixels}/{total_pixels} opaque pixels ({100*opaque_pixels/total_pixels:.1f}%)"
            debug_log.append(log_msg)
            print(log_msg)
            
            # Label connected components
            labeled_array, num_features = ndimage.label(binary_mask)
            log_msg = f"   🔗 Found {num_features} connected components"
            debug_log.append(log_msg)
            print(log_msg)
            
            if num_features == 0:
                log_msg = "   ❌ No connected components found"
                debug_log.append(log_msg)
                print(log_msg)
                return {'success': False, 'debug_log': debug_log}
            
            # Extract bounding boxes
            objects = ndimage.find_objects(labeled_array)
            sprite_bounds = []
            
            for i, obj in enumerate(objects):
                if obj is None:
                    continue
                    
                y_slice, x_slice = obj
                x_start, x_end = x_slice.start, x_slice.stop
                y_start, y_end = y_slice.start, y_slice.stop
                width, height = x_end - x_start, y_end - y_start
                
                # Filter tiny components
                if width >= 8 and height >= 8:
                    sprite_bounds.append((x_start, y_start, width, height))
                    debug_log.append(f"   ✅ Component {i+1}: ({x_start}, {y_start}) {width}×{height}")
                else:
                    debug_log.append(f"   🗑️ Component {i+1}: FILTERED (too small: {width}×{height})")
            
            log_msg = f"   📊 Valid components: {len(sprite_bounds)}"
            debug_log.append(log_msg)
            print(log_msg)
            
            # Merge nearby components for multi-part sprites
            merged_bounds = _merge_nearby_components(sprite_bounds, merge_threshold=50, debug_log=debug_log)
            log_msg = f"   🔀 After merging: {len(merged_bounds)} sprites"
            debug_log.append(log_msg)
            print(log_msg)
            
            if not merged_bounds:
                log_msg = "   ❌ No sprites after merging"
                debug_log.append(log_msg)
                print(log_msg)
                return {'success': False, 'debug_log': debug_log}
            
            # Analyze layout and suggest settings
            result = _analyze_ccl_results(merged_bounds, img.width, img.height, debug_log)
            result['debug_log'] = debug_log
            
            # Print final result to console
            if result.get('success', False):
                final_msg = f"   🎉 CCL SUCCESS: {result['frame_width']}×{result['frame_height']}, {result['sprite_count']} sprites"
                print(final_msg)
            else:
                final_msg = f"   ❌ CCL FAILED: {result.get('method', 'unknown')}"
                print(final_msg)
            
            return result
            
        except Exception as e:
            log_msg = f"   💥 CCL Error: {str(e)}"
            debug_log.append(log_msg)
            print(log_msg)
            return {'success': False, 'debug_log': debug_log, 'error': str(e)}
    
    def _merge_nearby_components(sprite_bounds: List[Tuple[int, int, int, int]], 
                                merge_threshold: int, debug_log: List[str] = None) -> List[Tuple[int, int, int, int]]:
        """Merge nearby sprite components."""
        if debug_log is None:
            debug_log = []
            
        if len(sprite_bounds) <= 1:
            debug_log.append("   🔀 No merging needed (≤1 component)")
            return sprite_bounds
        
        debug_log.append(f"   🔀 Merging {len(sprite_bounds)} components (threshold: {merge_threshold}px)")
        
        components = list(sprite_bounds)
        merged = []
        used = set()
        merge_count = 0
        
        for i, (x1, y1, w1, h1) in enumerate(components):
            if i in used:
                continue
            
            merge_group = [(x1, y1, w1, h1)]
            used.add(i)
            
            for j, (x2, y2, w2, h2) in enumerate(components):
                if j in used:
                    continue
                
                # Check proximity
                center_x1, center_y1 = x1 + w1//2, y1 + h1//2
                center_x2, center_y2 = x2 + w2//2, y2 + h2//2
                distance = math.sqrt((center_x2 - center_x1)**2 + (center_y2 - center_y1)**2)
                
                # Check overlap
                horizontal_overlap = not (x1 + w1 < x2 - merge_threshold or x2 + w2 < x1 - merge_threshold)
                vertical_overlap = not (y1 + h1 < y2 - merge_threshold or y2 + h2 < y1 - merge_threshold)
                
                if distance < merge_threshold or (horizontal_overlap and vertical_overlap):
                    merge_group.append((x2, y2, w2, h2))
                    used.add(j)
                    debug_log.append(f"      🔗 Merged component {j+1} into group {i+1} (distance: {distance:.1f}px)")
            
            # Create merged bounding box
            if merge_group:
                min_x = min(x for x, y, w, h in merge_group)
                min_y = min(y for x, y, w, h in merge_group)
                max_x = max(x + w for x, y, w, h in merge_group)
                max_y = max(y + h for x, y, w, h in merge_group)
                merged_bounds = (min_x, min_y, max_x - min_x, max_y - min_y)
                merged.append(merged_bounds)
                
                if len(merge_group) > 1:
                    merge_count += 1
                    debug_log.append(f"      ✅ Group {i+1}: {len(merge_group)} parts → ({min_x}, {min_y}) {max_x - min_x}×{max_y - min_y}")
        
        debug_log.append(f"   🔀 Merging complete: {merge_count} groups merged, {len(merged)} final sprites")
        return merged
    
    def _analyze_ccl_results(sprite_bounds: List[Tuple[int, int, int, int]], 
                            sheet_width: int, sheet_height: int, debug_log: List[str] = None) -> dict:
        """Analyze CCL results and suggest frame settings."""
        if debug_log is None:
            debug_log = []
            
        debug_log.append(f"   📐 Analyzing {len(sprite_bounds)} sprites for layout...")
        
        if not sprite_bounds:
            debug_log.append("   ❌ No sprites to analyze")
            return {'success': False, 'method': 'ccl_enhanced'}
        
        # Calculate statistics
        widths = [w for x, y, w, h in sprite_bounds]
        heights = [h for x, y, w, h in sprite_bounds]
        
        avg_width = int(np.mean(widths))
        avg_height = int(np.mean(heights))
        width_std = np.std(widths)
        height_std = np.std(heights)
        
        debug_log.append(f"   📊 Size analysis:")
        debug_log.append(f"      Average: {avg_width}×{avg_height}")
        debug_log.append(f"      Variation: ±{width_std:.1f}×±{height_std:.1f}")
        debug_log.append(f"      Range: {min(widths)}-{max(widths)} × {min(heights)}-{max(heights)}")
        
        # Check if layout is regular (increased tolerance for Lancer-style sprites)
        uniform_size = width_std < 8 and height_std < 8
        debug_log.append(f"   🎯 Uniform size: {uniform_size} (std < 8px)")
        
        if uniform_size and len(sprite_bounds) >= 2:  # Lowered threshold from 4 to 2
            # Infer grid structure from sprite positions (not content bounds)
            sorted_sprites = sorted(sprite_bounds, key=lambda s: (s[1], s[0]))
            debug_log.append(f"   🗂️ Sorted sprites by position for grid analysis")
            
            # Extract sprite center positions
            centers_x = [x + w//2 for x, y, w, h in sprite_bounds]
            centers_y = [y + h//2 for x, y, w, h in sprite_bounds]
            debug_log.append(f"   🎯 Sprite centers: X={sorted(centers_x)}, Y={sorted(centers_y)}")
            
            # Group centers with tolerance (sprites in same row/col can be slightly offset)
            def group_positions(positions, tolerance=15):
                """Group similar positions within tolerance."""
                if not positions:
                    return []
                sorted_pos = sorted(set(positions))
                groups = [[sorted_pos[0]]]
                for pos in sorted_pos[1:]:
                    if pos - groups[-1][-1] <= tolerance:
                        groups[-1].append(pos)
                    else:
                        groups.append([pos])
                return [sum(group) // len(group) for group in groups]  # Return group averages
            
            grouped_x = group_positions(centers_x, tolerance=15)
            grouped_y = group_positions(centers_y, tolerance=15)
            cols = len(grouped_x)
            rows = len(grouped_y)
            debug_log.append(f"   🔗 Grouped centers: X={grouped_x}, Y={grouped_y}")
            debug_log.append(f"   📐 Grid structure: {cols}×{rows} (from center positions)")
            
            # Calculate frame size based on grid, not content bounds
            if cols > 1:
                frame_width = int(sheet_width / cols)
                debug_log.append(f"   📏 Frame width: {sheet_width}/{cols} = {frame_width}px")
            else:
                frame_width = sheet_width
                debug_log.append(f"   📏 Frame width: full width = {frame_width}px")
                
            if rows > 1:
                frame_height = int(sheet_height / rows)
                debug_log.append(f"   📏 Frame height: {sheet_height}/{rows} = {frame_height}px")
            else:
                frame_height = sheet_height
                debug_log.append(f"   📏 Frame height: full height = {frame_height}px")
            
            # Calculate margins from content bounds
            offset_x = min(x for x, y, w, h in sprite_bounds)
            offset_y = min(y for x, y, w, h in sprite_bounds)
            debug_log.append(f"   📍 Content margins: ({offset_x}, {offset_y})")
            
            # For grid-based extraction, use 0 spacing (frames are adjacent)
            spacing_x = 0
            spacing_y = 0
            debug_log.append(f"   ✅ Grid extraction: spacing=({spacing_x}, {spacing_y})")
            
            confidence = 'high' if cols * rows == len(sprite_bounds) else 'medium'
            debug_log.append(f"   🎯 Grid validation: {cols}×{rows}={cols*rows} vs {len(sprite_bounds)} sprites")
            
            result = {
                'success': True,
                'frame_width': frame_width,
                'frame_height': frame_height,
                'offset_x': 0,  # Grid starts at 0,0
                'offset_y': 0,
                'spacing_x': spacing_x,
                'spacing_y': spacing_y,
                'sprite_count': len(sprite_bounds),
                'confidence': confidence,
                'method': 'ccl_enhanced'
            }
            
            debug_log.append(f"   🎉 CCL Success: {frame_width}×{frame_height}, {len(sprite_bounds)} sprites, confidence: {confidence}")
            return result
        else:
            debug_log.append(f"   ❌ CCL Failed: irregular layout or insufficient sprites")
            return {'success': False, 'method': 'ccl_enhanced'}

except ImportError:
    CCL_AVAILABLE = False
    
    def detect_sprites_ccl_enhanced(image_path: str) -> Optional[dict]:
        return None


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
        self._sprite_sheet_info: str = ""
    
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
    
    def extract_frames(self, width: int, height: int, offset_x: int = 0, offset_y: int = 0, 
                      spacing_x: int = 0, spacing_y: int = 0) -> Tuple[bool, str, int]:
        """
        Extract frames from sprite sheet with given parameters.
        Now supports frame spacing for sprite sheets with gaps between frames.
        Returns (success, error_message, frame_count).
        """
        if not self._original_sprite_sheet or self._original_sprite_sheet.isNull():
            return False, "No sprite sheet loaded", 0
        
        # Validate frame settings (will be updated to include spacing)
        valid, error_msg = self.validate_frame_settings(width, height, offset_x, offset_y, spacing_x, spacing_y)
        if not valid:
            return False, error_msg, 0
        
        try:
            # Store extraction settings
            self._frame_width = width
            self._frame_height = height
            self._offset_x = offset_x
            self._offset_y = offset_y
            self._spacing_x = spacing_x
            self._spacing_y = spacing_y
            
            sheet_width = self._original_sprite_sheet.width()
            sheet_height = self._original_sprite_sheet.height()
            
            # Calculate available area after margins
            available_width = sheet_width - offset_x
            available_height = sheet_height - offset_y
            
            # Calculate how many frames fit (now accounting for spacing)
            # For N frames, we have N-1 gaps between them
            if spacing_x > 0:
                frames_per_row = (available_width + spacing_x) // (width + spacing_x)
            else:
                frames_per_row = available_width // width if width > 0 else 0
                
            if spacing_y > 0:
                frames_per_col = (available_height + spacing_y) // (height + spacing_y)
            else:
                frames_per_col = available_height // height if height > 0 else 0
            
            # Extract individual frames with spacing
            self._sprite_frames = []
            for row in range(frames_per_col):
                for col in range(frames_per_row):
                    x = offset_x + (col * (width + spacing_x))
                    y = offset_y + (row * (height + spacing_y))
                    
                    # Ensure we don't exceed sheet boundaries
                    if x + width <= sheet_width and y + height <= sheet_height:
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
    
    def validate_frame_settings(self, width: int, height: int, offset_x: int = 0, offset_y: int = 0,
                               spacing_x: int = 0, spacing_y: int = 0) -> Tuple[bool, str]:
        """Validate frame extraction parameters including offsets and spacing."""
        # Basic dimension validation
        if width <= 0:
            return False, "Frame width must be greater than 0"
        if height <= 0:
            return False, "Frame height must be greater than 0"
        if width > Config.FrameExtraction.MAX_FRAME_SIZE:
            return False, f"Frame width cannot exceed {Config.FrameExtraction.MAX_FRAME_SIZE}"
        if height > Config.FrameExtraction.MAX_FRAME_SIZE:
            return False, f"Frame height cannot exceed {Config.FrameExtraction.MAX_FRAME_SIZE}"
        
        # Validate offsets
        if offset_x < 0:
            return False, "X offset cannot be negative"
        if offset_y < 0:
            return False, "Y offset cannot be negative"
        if offset_x > Config.FrameExtraction.MAX_OFFSET:
            return False, f"X offset cannot exceed {Config.FrameExtraction.MAX_OFFSET}"
        if offset_y > Config.FrameExtraction.MAX_OFFSET:
            return False, f"Y offset cannot exceed {Config.FrameExtraction.MAX_OFFSET}"
            
        # Validate spacing
        if spacing_x < 0:
            return False, "X spacing cannot be negative"
        if spacing_y < 0:
            return False, "Y spacing cannot be negative"
        if spacing_x > Config.FrameExtraction.MAX_SPACING:
            return False, f"X spacing cannot exceed {Config.FrameExtraction.MAX_SPACING}"
        if spacing_y > Config.FrameExtraction.MAX_SPACING:
            return False, f"Y spacing cannot exceed {Config.FrameExtraction.MAX_SPACING}"
        
        # Check if frame size is reasonable for the sprite sheet
        if self._original_sprite_sheet and not self._original_sprite_sheet.isNull():
            sheet_width = self._original_sprite_sheet.width()
            sheet_height = self._original_sprite_sheet.height()
            
            # At minimum, one frame must fit after applying offset
            if offset_x + width > sheet_width:
                return False, f"Frame width + X offset ({offset_x + width}) exceeds sheet width ({sheet_width})"
            if offset_y + height > sheet_height:
                return False, f"Frame height + Y offset ({offset_y + height}) exceeds sheet height ({sheet_height})"
        
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