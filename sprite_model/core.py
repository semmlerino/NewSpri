"""
Central data model for sprite sheet operations.
Delegates file loading to FileLoader, animation state to AnimationStateManager,
and CCL extraction to CCLOperations.
"""

import os

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap

from sprite_model.extraction_mode import ExtractionMode
from sprite_model.extraction_strategies import ExtractionContext, get_extraction_strategy
from sprite_model.sprite_animation import AnimationStateManager
from sprite_model.sprite_ccl import CCLOperations
from sprite_model.sprite_detection import (
    DetectionResult,
    comprehensive_auto_detect,
    detect_margins,
    detect_rectangular_frames,
    detect_spacing,
)
from sprite_model.sprite_extraction import (
    GridConfig,
    detect_background_color,
    detect_sprites_ccl_enhanced,
)
from sprite_model.sprite_extraction import (
    validate_frame_settings as validate_grid_frame_settings,
)
from sprite_model.sprite_file_ops import FileLoader


class SpriteModel(QObject):
    """
    Main model class for sprite sheet operations using modular architecture.

    This class maintains 100% API compatibility with the original implementation
    while using the refactored modular components internally.
    """

    # Qt Signals - must match original exactly
    frameChanged = Signal(int, int)  # current_frame, total_frames
    dataLoaded = Signal(str)  # file_path
    extractionCompleted = Signal(int)  # frame_count
    playbackStateChanged = Signal(bool)  # is_playing
    errorOccurred = Signal(str)  # error_message
    configurationChanged = Signal()  # frame settings changed

    def __init__(self):
        """Initialize SpriteModel state and submodule instances."""
        super().__init__()

        # Core sprite sheet state
        self._original_sprite_sheet: QPixmap | None = None
        self._sprite_frames: list[QPixmap] = []
        self._file_path: str = ""

        # Initialize refactored modules (pass dependencies directly)
        self._file_loader = FileLoader()
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
            success, pixmap, message = self._file_loader.load_sprite_sheet(file_path)

            if not success:
                return False, message

            # Store state
            self._original_sprite_sheet = pixmap
            self._file_path = file_path

            # Clear previous frames and reset animation
            self._sprite_frames.clear()
            self._animation_state.reset_state()
            self._ccl_operations.clear_ccl_data()

            self.dataLoaded.emit(file_path)
            return True, "Sprite sheet loaded successfully"

        except Exception as e:
            error_msg = f"Error loading sprite sheet: {e!s}"
            self.errorOccurred.emit(error_msg)
            return False, error_msg

    # Frame Extraction Methods
    def extract_frames(
        self,
        width: int,
        height: int,
        offset_x: int = 0,
        offset_y: int = 0,
        spacing_x: int = 0,
        spacing_y: int = 0,
    ) -> tuple[bool, str, int]:
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

        valid, msg = self.validate_frame_settings(
            width, height, offset_x, offset_y, spacing_x, spacing_y
        )
        if not valid:
            return False, msg, 0

        config = GridConfig(
            width=width,
            height=height,
            offset_x=offset_x,
            offset_y=offset_y,
            spacing_x=spacing_x,
            spacing_y=spacing_y,
        )

        return self.extract_frames_for_mode(ExtractionMode.GRID, config)

    def validate_frame_settings(
        self,
        width: int,
        height: int,
        offset_x: int = 0,
        offset_y: int = 0,
        spacing_x: int = 0,
        spacing_y: int = 0,
    ) -> tuple[bool, str]:
        """Validate frame extraction settings."""
        if self._original_sprite_sheet is None:
            return False, "No sprite sheet loaded"

        # Create GridConfig for validation
        config = GridConfig(
            width=width,
            height=height,
            offset_x=offset_x,
            offset_y=offset_y,
            spacing_x=spacing_x,
            spacing_y=spacing_y,
        )

        return validate_grid_frame_settings(self._original_sprite_sheet, config)

    def extract_frames_for_mode(
        self,
        mode: ExtractionMode,
        grid_config: GridConfig | None = None,
    ) -> tuple[bool, str, int]:
        """Extract frames using the strategy registered for the requested mode."""
        if self._original_sprite_sheet is None:
            return False, "No sprite sheet loaded", 0

        if mode is ExtractionMode.GRID and grid_config is not None:
            self._apply_grid_config(grid_config)

        if mode is ExtractionMode.GRID and grid_config is None:
            grid_config = self._current_grid_config()

        context = self._extraction_context(self._original_sprite_sheet)
        strategy = get_extraction_strategy(mode)
        result = strategy.extract(context, grid_config)

        if result.success:
            self._store_frames(result.frames)
            self.extractionCompleted.emit(len(result.frames))

        return result.success, result.message, result.frame_count

    def set_extraction_mode(self, mode: object) -> bool:
        """Set extraction mode (grid or ccl)."""
        if self._original_sprite_sheet is None:
            return False
        if not isinstance(mode, ExtractionMode):
            return False

        old_mode = self.get_extraction_mode()
        success, _message, _frame_count = self.extract_frames_for_mode(mode)
        if not success:
            self._ccl_operations.set_current_mode(old_mode)

        return success

    def get_extraction_mode(self) -> ExtractionMode:
        """Get current extraction mode."""
        return self._ccl_operations.get_extraction_mode()

    def get_ccl_sprite_bounds(self) -> list[tuple[int, int, int, int]]:
        """Get bounding boxes of detected sprites."""
        return self._ccl_operations.get_ccl_sprite_bounds()

    # Auto-Detection Methods
    def auto_detect_rectangular_frames(self) -> tuple[bool, int, int, str]:
        """Detect uniform frame dimensions from the loaded sprite sheet."""
        if self._original_sprite_sheet is None:
            return False, 0, 0, "No sprite sheet loaded"

        success, width, height, message = detect_rectangular_frames(self._original_sprite_sheet)

        if not success:
            return False, 0, 0, message

        # Update internal state
        self._frame_width = width
        self._frame_height = height
        self.configurationChanged.emit()
        return True, width, height, message

    def auto_detect_margins(self) -> tuple[bool, int, int, str]:
        """Detect the sheet margins (x/y offsets) for the current frame size."""
        if self._original_sprite_sheet is None:
            return False, 0, 0, "No sprite sheet loaded"

        success, offset_x, offset_y, message = detect_margins(
            self._original_sprite_sheet, self._frame_width, self._frame_height
        )

        if not success:
            return False, 0, 0, message

        # Update internal state
        self._offset_x = offset_x
        self._offset_y = offset_y
        self.configurationChanged.emit()
        return True, offset_x, offset_y, message

    def auto_detect_spacing_enhanced(self) -> tuple[bool, int, int, str]:
        """Detect inter-frame spacing for the current frame size and offsets."""
        if self._original_sprite_sheet is None:
            return False, 0, 0, "No sprite sheet loaded"

        success, spacing_x, spacing_y, message, _confidence = detect_spacing(
            self._original_sprite_sheet,
            self._frame_width,
            self._frame_height,
            self._offset_x,
            self._offset_y,
        )

        if not success:
            return False, 0, 0, message

        # Update internal state
        self._spacing_x = spacing_x
        self._spacing_y = spacing_y
        self.configurationChanged.emit()
        return True, spacing_x, spacing_y, message

    def comprehensive_auto_detect(self) -> tuple[bool, DetectionResult]:
        """Run comprehensive auto-detection and extract frames with detected parameters."""
        if self._original_sprite_sheet is None:
            empty_result = DetectionResult()
            empty_result.messages = ["No sprite sheet loaded"]
            return False, empty_result

        success, _message, result = comprehensive_auto_detect(
            self._original_sprite_sheet, self._file_path
        )

        if not (success and result):
            return False, result

        # Apply detected parameters to internal state
        self._frame_width = result.frame_width
        self._frame_height = result.frame_height
        self._offset_x = result.offset_x
        self._offset_y = result.offset_y
        self._spacing_x = result.spacing_x
        self._spacing_y = result.spacing_y
        self.configurationChanged.emit()

        # Extract frames using detected grid parameters
        extract_success, extract_msg, _count = self.extract_frames_for_mode(ExtractionMode.GRID)

        if extract_success:
            result.messages.append(extract_msg)
            return True, result

        result.messages.append(f"Extraction failed: {extract_msg}")
        return False, result

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
        if self._original_sprite_sheet is None:
            return "No sprite sheet loaded"

        info_parts = []

        # Basic info
        info_parts.append(
            f"Size: {self._original_sprite_sheet.width()}x{self._original_sprite_sheet.height()}"
        )

        # Frame info
        if self._sprite_frames:
            info_parts.append(f"Frames: {len(self._sprite_frames)}")
            if self._frame_width > 0 and self._frame_height > 0:
                info_parts.append(f"Frame size: {self._frame_width}x{self._frame_height}")

        # Extraction mode
        mode = self.get_extraction_mode()
        if mode is ExtractionMode.CCL:
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

    @property
    def frame_width(self) -> int:
        """Get configured frame width."""
        return self._frame_width

    @property
    def frame_height(self) -> int:
        """Get configured frame height."""
        return self._frame_height

    @property
    def offset_x(self) -> int:
        """Get horizontal offset (left margin)."""
        return self._offset_x

    @property
    def offset_y(self) -> int:
        """Get vertical offset (top margin)."""
        return self._offset_y

    @property
    def spacing_x(self) -> int:
        """Get horizontal spacing between frames."""
        return self._spacing_x

    @property
    def spacing_y(self) -> int:
        """Get vertical spacing between frames."""
        return self._spacing_y

    @property
    def original_sprite_sheet(self) -> QPixmap | None:
        """Get original sprite sheet pixmap."""
        return self._original_sprite_sheet

    @property
    def current_frame(self) -> int:
        """Get current frame index."""
        return self._animation_state.current_frame

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
        return os.path.basename(self._file_path) if self._file_path else ""

    # Helper Methods
    def _current_grid_config(self) -> GridConfig:
        """Return the current grid extraction settings as a value object."""
        return GridConfig(
            width=self._frame_width,
            height=self._frame_height,
            offset_x=self._offset_x,
            offset_y=self._offset_y,
            spacing_x=self._spacing_x,
            spacing_y=self._spacing_y,
        )

    def _apply_grid_config(self, config: GridConfig) -> None:
        """Store grid extraction settings for later re-extraction."""
        self._frame_width = config.width
        self._frame_height = config.height
        self._offset_x = config.offset_x
        self._offset_y = config.offset_y
        self._spacing_x = config.spacing_x
        self._spacing_y = config.spacing_y

    def _extraction_context(self, sprite_sheet: QPixmap) -> ExtractionContext:
        """Build the shared dependency bundle for extraction strategies."""
        return ExtractionContext(
            sprite_sheet=sprite_sheet,
            sprite_sheet_path=self._file_path,
            ccl_operations=self._ccl_operations,
            detect_sprites_ccl_enhanced=detect_sprites_ccl_enhanced,
            detect_background_color=detect_background_color,
        )

    def _store_frames(self, frames: list[QPixmap]) -> None:
        """Replace stored frames in-place and update animation state.

        Modifies the list in-place to preserve the AnimationStateManager reference.
        Does NOT emit extractionCompleted -- callers handle that individually.
        """
        self._sprite_frames.clear()
        self._sprite_frames.extend(frames)
        self._animation_state.update_frame_count(len(frames))
