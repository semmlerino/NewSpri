"""
Integrated SpriteModel using refactored modules.
Maintains complete API compatibility with original implementation.
Part of Legacy Integration Phase 1: Create integrated SpriteModel structure.
"""


from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap

from sprite_model.sprite_animation import AnimationStateManager
from sprite_model.sprite_ccl import CCLOperations
from sprite_model.sprite_detection import (
    comprehensive_auto_detect,
    detect_content_based,
    detect_frame_size,
    detect_margins,
    detect_rectangular_frames,
    detect_spacing,
)
from sprite_model.sprite_extraction import (
    GridConfig,
    extract_grid_frames,
)
from sprite_model.sprite_extraction import (
    validate_frame_settings as validate_grid_frame_settings,
)

# Import all refactored modules
from sprite_model.sprite_file_ops import FileLoader, FileValidator, MetadataExtractor


class SpriteModel(QObject):
    """
    Main model class for sprite sheet operations using modular architecture.

    This class maintains 100% API compatibility with the original implementation
    while using the refactored modular components internally.
    """

    # Qt Signals - must match original exactly
    frameChanged = Signal(int, int)         # current_frame, total_frames
    dataLoaded = Signal(str)                # file_path
    extractionCompleted = Signal(int)       # frame_count
    playbackStateChanged = Signal(bool)     # is_playing
    errorOccurred = Signal(str)            # error_message
    configurationChanged = Signal()         # frame settings changed

    def __init__(self):
        """Initialize SpriteModel with all refactored modules."""
        super().__init__()

        # Primary state variables (maintaining compatibility)
        self._original_sprite_sheet: QPixmap | None = None
        self._sprite_frames: list[QPixmap] = []
        self._file_path: str = ""
        self._sprite_sheet_path: str = ""

        # Initialize refactored modules (pass dependencies directly)
        self._file_loader = FileLoader()
        self._file_validator = FileValidator()
        self._metadata_extractor = MetadataExtractor()
        self._animation_state = AnimationStateManager(self._sprite_frames)  # Pass frames reference
        self._ccl_operations = CCLOperations()

        # Frame extraction settings (for backward compatibility)
        self._frame_width: int = 0
        self._frame_height: int = 0
        self._offset_x: int = 0
        self._offset_y: int = 0
        self._spacing_x: int = 0
        self._spacing_y: int = 0

        # Setup module connections and callbacks
        self._setup_module_connections()

    def _setup_module_connections(self):
        """Connect modules with required callbacks and signal forwarding."""
        # Forward animation signals to maintain compatibility
        self._animation_state.frameChanged.connect(self.frameChanged.emit)
        self._animation_state.playbackStateChanged.connect(self.playbackStateChanged.emit)

        # Note: CCLOperations now uses direct parameters instead of callbacks

    # File Operations Methods
    def load_sprite_sheet(self, file_path: str) -> tuple[bool, str]:
        """
        Load a sprite sheet from file.

        Args:
            file_path: Path to the sprite sheet file

        Returns:
            Tuple of (success, message)
        """
        try:
            # Use FileLoader module
            success, pixmap, _metadata, message = self._file_loader.load_sprite_sheet(file_path)

            if success:
                # Store state
                self._original_sprite_sheet = pixmap
                self._file_path = file_path
                self._sprite_sheet_path = file_path

                # Clear previous frames and reset animation
                self._sprite_frames.clear()
                self._animation_state.reset_state()

                # Emit dataLoaded signal for compatibility
                self.dataLoaded.emit(file_path)

                return True, "Sprite sheet loaded successfully"
            else:
                return False, message

        except Exception as e:
            error_msg = f"Error loading sprite sheet: {e!s}"
            self.errorOccurred.emit(error_msg)
            return False, error_msg

    def reload_current_sheet(self) -> tuple[bool, str]:
        """Reload the current sprite sheet."""
        if not self._file_path:
            return False, "No sprite sheet loaded"

        # Use FileLoader's reload method
        success, pixmap, _metadata, message = self._file_loader.reload_sprite_sheet(self._file_path)

        if success:
            self._original_sprite_sheet = pixmap
            # Re-extract frames if we had them before
            if self._sprite_frames:
                self._re_extract_frames()
            return True, "Sprite sheet reloaded successfully"
        else:
            return False, message

    def clear_sprite_data(self) -> None:
        """Clear all sprite data and reset state."""
        # Clear primary state
        self._original_sprite_sheet = None
        self._sprite_frames.clear()
        self._file_path = ""
        self._sprite_sheet_path = ""

        # Reset frame settings
        self._frame_width = 0
        self._frame_height = 0
        self._offset_x = 0
        self._offset_y = 0
        self._spacing_x = 0
        self._spacing_y = 0

        # Clear module states
        self._animation_state.reset_state()
        self._ccl_operations.clear_ccl_data()

    # Frame Extraction Methods
    def extract_frames(self, width: int, height: int, offset_x: int = 0,
                      offset_y: int = 0, spacing_x: int = 0, spacing_y: int = 0) -> tuple[bool, str, int]:
        """
        Extract frames from sprite sheet using grid-based extraction.

        Args:
            width: Frame width
            height: Frame height
            offset_x: X offset for first frame
            offset_y: Y offset for first frame
            spacing_x: Horizontal spacing between frames
            spacing_y: Vertical spacing between frames

        Returns:
            Tuple of (success, message, frame_count)
        """
        # Store settings for reuse and property access
        self._frame_width = width
        self._frame_height = height
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._spacing_x = spacing_x
        self._spacing_y = spacing_y

        # Validate settings first
        valid, msg = self.validate_frame_settings(width, height, offset_x, offset_y, spacing_x, spacing_y)
        if not valid:
            return False, msg, 0

        # Create GridConfig for the extractor
        config = GridConfig(
            width=width,
            height=height,
            offset_x=offset_x,
            offset_y=offset_y,
            spacing_x=spacing_x,
            spacing_y=spacing_y
        )

        # Extract frames based on current mode
        if self._ccl_operations.get_extraction_mode() == 'grid':
            if self._original_sprite_sheet is None:
                return False, "No sprite sheet loaded", 0

            success, message, frames = extract_grid_frames(
                self._original_sprite_sheet, config
            )

            if success:
                # Modify list in-place to preserve AnimationStateManager reference
                self._sprite_frames.clear()
                self._sprite_frames.extend(frames)
                self._animation_state.update_frame_count(len(frames))
                self.extractionCompleted.emit(len(frames))
                return True, f"Extracted {len(frames)} frames", len(frames)
            else:
                return False, message, 0
        else:
            # Use CCL extraction instead
            return self.extract_ccl_frames()

    def set_frame_settings(self, width: int, height: int, offset_x: int = 0,
                         offset_y: int = 0, spacing_x: int = 0, spacing_y: int = 0) -> None:
        """Set frame extraction parameters without extracting.

        This method is for setting parameters only, without triggering extraction.
        For extraction, use extract_frames() after setting parameters.
        """
        # Validate inputs
        if width <= 0 or height <= 0:
            raise ValueError(f"Frame dimensions must be positive: {width}x{height}")
        if offset_x < 0 or offset_y < 0:
            raise ValueError(f"Offsets cannot be negative: ({offset_x}, {offset_y})")
        if spacing_x < 0 or spacing_y < 0:
            raise ValueError(f"Spacing cannot be negative: ({spacing_x}, {spacing_y})")

        # Store settings
        self._frame_width = width
        self._frame_height = height
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._spacing_x = spacing_x
        self._spacing_y = spacing_y

    def validate_frame_settings(self, width: int, height: int, offset_x: int = 0,
                              offset_y: int = 0, spacing_x: int = 0, spacing_y: int = 0) -> tuple[bool, str]:
        """Validate frame extraction settings."""
        if not self._original_sprite_sheet:
            return False, "No sprite sheet loaded"

        # Create GridConfig for validation
        config = GridConfig(
            width=width,
            height=height,
            offset_x=offset_x,
            offset_y=offset_y,
            spacing_x=spacing_x,
            spacing_y=spacing_y
        )

        return validate_grid_frame_settings(self._original_sprite_sheet, config)

    def extract_ccl_frames(self) -> tuple[bool, str, int]:
        """Extract frames using Connected Component Labeling."""
        from sprite_model.sprite_extraction import (
            detect_background_color,
            detect_sprites_ccl_enhanced,
        )

        # Get sprite sheet, defaulting to empty QPixmap if None
        sprite_sheet = self._original_sprite_sheet if self._original_sprite_sheet else QPixmap()

        # Call CCLOperations with direct parameters
        success, message, frame_count, frames, _info = self._ccl_operations.extract_ccl_frames(
            sprite_sheet=sprite_sheet,
            sprite_sheet_path=self._sprite_sheet_path,
            ccl_available=self.is_ccl_available(),
            detect_sprites_ccl_enhanced=detect_sprites_ccl_enhanced,
            detect_background_color=detect_background_color,
            emit_extraction_completed=lambda count: self.extractionCompleted.emit(count)
        )

        if success:
            # Modify list in-place to preserve AnimationStateManager reference
            self._sprite_frames.clear()
            self._sprite_frames.extend(frames)
            self._animation_state.update_frame_count(frame_count)

        return success, message, frame_count

    def set_extraction_mode(self, mode: str) -> bool:
        """Set extraction mode (grid or ccl)."""
        from sprite_model.sprite_extraction import (
            detect_background_color,
            detect_sprites_ccl_enhanced,
        )

        def extract_grid_callback():
            # Re-extract using current settings
            return self.extract_frames(
                self._frame_width, self._frame_height,
                self._offset_x, self._offset_y,
                self._spacing_x, self._spacing_y
            )

        # Get sprite sheet, defaulting to empty QPixmap if None
        sprite_sheet = self._original_sprite_sheet if self._original_sprite_sheet else QPixmap()

        success = self._ccl_operations.set_extraction_mode(
            mode=mode,
            sprite_sheet=sprite_sheet,
            sprite_sheet_path=self._sprite_sheet_path,
            ccl_available=self.is_ccl_available(),
            extract_grid_frames_callback=extract_grid_callback,
            detect_sprites_ccl_enhanced=detect_sprites_ccl_enhanced,
            detect_background_color=detect_background_color,
            emit_extraction_completed=lambda count: self.extractionCompleted.emit(count)
        )

        # If CCL mode succeeded, retrieve and store the extracted frames
        if success and mode == "ccl":
            ccl_frames = self._ccl_operations.get_last_extracted_frames()
            ccl_info = self._ccl_operations.get_last_extracted_info()

            if ccl_frames:
                # Update main model state with CCL results
                # Modify list in-place to preserve AnimationStateManager reference
                self._sprite_frames.clear()
                self._sprite_frames.extend(ccl_frames)
                # CRITICAL FIX: Update animation state so total_frames property reflects CCL frame count
                self._animation_state.update_frame_count(len(ccl_frames))

                # Update sprite info to include CCL information
                if hasattr(self, '_sprite_info'):
                    self._sprite_info = self._build_sprite_info() + ccl_info

                # Emit extraction completed signal
                self.extractionCompleted.emit(len(ccl_frames))

        return success

    def get_extraction_mode(self) -> str:
        """Get current extraction mode."""
        return self._ccl_operations.get_extraction_mode()

    def is_ccl_available(self) -> bool:
        """Check if CCL extraction is available."""
        # CCL mode should be available whenever a sprite sheet is loaded
        # The actual CCL detection will happen during extraction
        if self._original_sprite_sheet is None:
            return False
        return not self._original_sprite_sheet.isNull()

    def get_ccl_sprite_bounds(self) -> list[tuple[int, int, int, int]]:
        """Get bounding boxes of detected sprites."""
        return self._ccl_operations.get_ccl_sprite_bounds()

    # Auto-Detection Methods
    def should_auto_detect_size(self) -> bool:
        """Check if auto-detection should be attempted."""
        if not self._original_sprite_sheet:
            return False

        # Simple heuristic: sheets larger than 100x100
        return (self._original_sprite_sheet.width() > 100 and
                self._original_sprite_sheet.height() > 100)

    def auto_detect_frame_size(self) -> tuple[bool, int, int, str]:
        """Auto-detect frame size using detect_frame_size function."""
        if not self._original_sprite_sheet:
            return False, 0, 0, "No sprite sheet loaded"

        success, width, height, message = detect_frame_size(self._original_sprite_sheet)

        if success:
            # Update internal state
            self._frame_width = width
            self._frame_height = height
            self.configurationChanged.emit()

            return True, width, height, message
        else:
            return False, 0, 0, message

    def auto_detect_rectangular_frames(self) -> tuple[bool, int, int, str]:
        """Auto-detect rectangular frames using detect_rectangular_frames function."""
        if not self._original_sprite_sheet:
            return False, 0, 0, "No sprite sheet loaded"

        success, width, height, message = detect_rectangular_frames(self._original_sprite_sheet)

        if success:
            # Update internal state
            self._frame_width = width
            self._frame_height = height
            self.configurationChanged.emit()

            return True, width, height, message
        else:
            return False, 0, 0, message

    def auto_detect_content_based(self) -> tuple[bool, int, int, str]:
        """Auto-detect content-based frames using detect_content_based function."""
        if not self._original_sprite_sheet:
            return False, 0, 0, "No sprite sheet loaded"

        success, width, height, message = detect_content_based(self._original_sprite_sheet)

        if success:
            # Update internal state
            self._frame_width = width
            self._frame_height = height
            self.configurationChanged.emit()

            return True, width, height, message
        else:
            return False, 0, 0, message

    def auto_detect_margins(self) -> tuple[bool, int, int, str]:
        """Auto-detect margins using detect_margins function."""
        if not self._original_sprite_sheet:
            return False, 0, 0, "No sprite sheet loaded"

        success, offset_x, offset_y, message = detect_margins(
            self._original_sprite_sheet,
            self._frame_width,
            self._frame_height
        )

        if success:
            # Update internal state
            self._offset_x = offset_x
            self._offset_y = offset_y
            self.configurationChanged.emit()

            return True, offset_x, offset_y, message
        else:
            return False, 0, 0, message

    def auto_detect_spacing_enhanced(self) -> tuple[bool, int, int, str]:
        """Auto-detect spacing using detect_spacing function."""
        if not self._original_sprite_sheet:
            return False, 0, 0, "No sprite sheet loaded"

        success, spacing_x, spacing_y, message = detect_spacing(
            self._original_sprite_sheet,
            self._frame_width,
            self._frame_height,
            self._offset_x,
            self._offset_y
        )

        if success:
            # Update internal state
            self._spacing_x = spacing_x
            self._spacing_y = spacing_y
            self.configurationChanged.emit()

            return True, spacing_x, spacing_y, message
        else:
            return False, 0, 0, message

    def auto_detect_spacing(self) -> tuple[bool, int, int, str]:
        """Legacy alias for auto_detect_spacing_enhanced."""
        return self.auto_detect_spacing_enhanced()

    def comprehensive_auto_detect(self) -> tuple[bool, str]:
        """Run comprehensive auto-detection."""
        if not self._original_sprite_sheet:
            return False, "No sprite sheet loaded"

        success, message, result = comprehensive_auto_detect(
            self._original_sprite_sheet,
            self._sprite_sheet_path
        )

        if success and result:
            # Update internal state from result
            if hasattr(result, 'frame_width'):
                self._frame_width = result.frame_width
            if hasattr(result, 'frame_height'):
                self._frame_height = result.frame_height
            if hasattr(result, 'offset_x'):
                self._offset_x = result.offset_x
            if hasattr(result, 'offset_y'):
                self._offset_y = result.offset_y
            if hasattr(result, 'spacing_x'):
                self._spacing_x = result.spacing_x
            if hasattr(result, 'spacing_y'):
                self._spacing_y = result.spacing_y

            self.configurationChanged.emit()

            # Auto-extract frames using grid mode (since we detected grid parameters)
            # Save current extraction mode
            original_mode = self._ccl_operations.get_extraction_mode()

            # Temporarily switch to grid mode for testing detected parameters
            self.set_extraction_mode("grid")

            try:
                extract_success, extract_msg, _count = self.extract_frames(
                    self._frame_width, self._frame_height,
                    self._offset_x, self._offset_y,
                    self._spacing_x, self._spacing_y
                )

                if extract_success:
                    return True, f"{message}. {extract_msg}"
                else:
                    return True, message
            finally:
                # Always restore original mode
                self.set_extraction_mode(original_mode)

        return False, message

    # Animation Control Methods (delegate to AnimationStateManager)
    def set_current_frame(self, frame: int) -> bool:
        """Set current frame index."""
        return self._animation_state.set_current_frame(frame)

    def next_frame(self) -> tuple[int, bool]:
        """Move to next frame."""
        return self._animation_state.next_frame()

    def previous_frame(self) -> int:
        """Move to previous frame."""
        return self._animation_state.previous_frame()

    def first_frame(self) -> int:
        """Move to first frame."""
        return self._animation_state.first_frame()

    def last_frame(self) -> int:
        """Move to last frame."""
        return self._animation_state.last_frame()

    def play(self) -> bool:
        """Start animation playback."""
        return self._animation_state.play()

    def pause(self) -> None:
        """Pause animation playback."""
        self._animation_state.pause()

    def stop(self) -> None:
        """Stop animation playback."""
        self._animation_state.stop()

    def toggle_playback(self) -> bool:
        """Toggle animation playback."""
        return self._animation_state.toggle_playback()

    def set_fps(self, fps: int) -> bool:
        """Set frames per second."""
        return self._animation_state.set_fps(fps)

    def set_loop_enabled(self, enabled: bool) -> None:
        """Enable/disable animation looping."""
        self._animation_state.set_loop_enabled(enabled)

    # Properties (backward compatibility)
    @property
    def current_frame_pixmap(self) -> QPixmap | None:
        """Get current frame pixmap."""
        return self._animation_state.current_frame_pixmap

    @property
    def sprite_info(self) -> str:
        """Get sprite sheet information string."""
        if not self._original_sprite_sheet:
            return "No sprite sheet loaded"

        info_parts = []

        # Basic info
        info_parts.append(f"Size: {self._original_sprite_sheet.width()}x{self._original_sprite_sheet.height()}")

        # Frame info
        if self._sprite_frames:
            info_parts.append(f"Frames: {len(self._sprite_frames)}")
            if self._frame_width > 0 and self._frame_height > 0:
                info_parts.append(f"Frame size: {self._frame_width}x{self._frame_height}")

        # Extraction mode
        mode = self.get_extraction_mode()
        if mode == 'ccl':
            info_parts.append("Mode: CCL")
        else:
            info_parts.append("Mode: Grid")

        return " | ".join(info_parts)

    @property
    def frame_count(self) -> int:
        """Get total number of frames."""
        return len(self._sprite_frames)

    @property
    def is_loaded(self) -> bool:
        """Check if sprite sheet is loaded."""
        return self._original_sprite_sheet is not None

    @property
    def sprite_frames(self) -> list[QPixmap]:
        """Get list of extracted frames."""
        return self._sprite_frames

    def get_all_frames(self) -> list[QPixmap]:
        """Get all extracted frames (convenience method for animation splitting)."""
        return self._sprite_frames

    @property
    def original_sprite_sheet(self) -> QPixmap | None:
        """Get original sprite sheet pixmap."""
        return self._original_sprite_sheet

    @property
    def current_frame(self) -> int:
        """Get current frame index."""
        return self._animation_state.current_frame

    @property
    def total_frames(self) -> int:
        """
        Get total number of frames.

        Returns the count from the animation state manager, which computes
        it dynamically from the actual sprite frames list.
        """
        return self._animation_state.total_frames

    @property
    def is_playing(self) -> bool:
        """Check if animation is playing."""
        return self._animation_state.is_playing

    @property
    def fps(self) -> int:
        """Get frames per second."""
        return self._animation_state.fps

    @property
    def loop_enabled(self) -> bool:
        """Check if looping is enabled."""
        return self._animation_state.is_loop_enabled

    @property
    def file_path(self) -> str:
        """Get file path of loaded sprite sheet."""
        return self._file_path

    @property
    def file_name(self) -> str:
        """Get file name of loaded sprite sheet."""
        import os
        return os.path.basename(self._file_path) if self._file_path else ""

    # Helper Methods
    def _re_extract_frames(self) -> None:
        """Re-extract frames using current settings."""
        if self._frame_width > 0 and self._frame_height > 0:
            self.extract_frames(
                self._frame_width, self._frame_height,
                self._offset_x, self._offset_y,
                self._spacing_x, self._spacing_y
            )

    def _build_sprite_info(self) -> str:
        """Build sprite information string."""
        if not self._original_sprite_sheet:
            return ""

        info_parts = []
        info_parts.append(f"Size: {self._original_sprite_sheet.width()}x{self._original_sprite_sheet.height()}")

        if self._sprite_frames:
            info_parts.append(f"Frames: {len(self._sprite_frames)}")
            if self._frame_width > 0 and self._frame_height > 0:
                info_parts.append(f"Frame size: {self._frame_width}x{self._frame_height}")

        return " | ".join(info_parts)
