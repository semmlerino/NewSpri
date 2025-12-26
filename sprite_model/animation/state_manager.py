#!/usr/bin/env python3
"""
Animation State Manager
=======================

Manages animation state, frame navigation, and playback control for sprite viewer.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap

from config import Config


class AnimationStateManager(QObject):
    """
    Manages all animation state and frame navigation logic.

    Handles frame navigation (next, previous, first, last), playback state
    (play, pause, stop), and animation settings (FPS, looping).

    Designed to work with sprite frame data and emit Qt signals for UI updates.
    """

    # Qt Signals for communication with UI components
    frameChanged = Signal(int, int)          # (current_frame, total_frames)
    playbackStateChanged = Signal(bool)      # is_playing

    def __init__(self):
        """Initialize animation state manager with default values."""
        super().__init__()

        # Animation state
        self._current_frame: int = 0
        self._total_frames: int = 0
        self._is_playing: bool = False
        self._loop_enabled: bool = True
        self._fps: int = Config.Animation.DEFAULT_FPS

        # Sprite frame data (managed externally, accessed via getter)
        self._get_sprite_frames: Callable[[], list[QPixmap]] | None = None

    def set_sprite_frames_getter(self, getter: Callable[[], list[QPixmap]]) -> None:
        """
        Set the function to get current sprite frames.

        Args:
            getter: Function that returns the current list of sprite frames
        """
        self._get_sprite_frames = getter

    def _get_frames(self) -> list[QPixmap]:
        """Get current sprite frames via getter function."""
        if self._get_sprite_frames:
            return self._get_sprite_frames()
        return []

    def update_frame_count(self, total_frames: int) -> None:
        """
        Update the total frame count and reset current frame if needed.

        Args:
            total_frames: New total frame count
        """
        self._total_frames = total_frames
        if self._current_frame >= total_frames:
            self._current_frame = 0 if total_frames > 0 else 0
            self.frameChanged.emit(self._current_frame, self._total_frames)

    # ============================================================================
    # FRAME NAVIGATION
    # ============================================================================

    def set_current_frame(self, frame: int) -> bool:
        """
        Set the current animation frame with bounds checking.

        Args:
            frame: Frame index to set

        Returns:
            True if frame was set successfully, False otherwise
        """
        frames = self._get_frames()
        if not frames:
            return False

        if 0 <= frame < len(frames):
            self._current_frame = frame
            self._total_frames = len(frames)
            self.frameChanged.emit(self._current_frame, self._total_frames)
            return True
        return False

    def next_frame(self) -> tuple[int, bool]:
        """
        Advance to next frame, handling looping.

        Returns:
            Tuple of (new_frame_index, should_continue_playing)
        """
        frames = self._get_frames()
        if not frames:
            return 0, False

        # Core animation advancement logic
        self._current_frame += 1
        self._total_frames = len(frames)

        if self._current_frame >= len(frames):
            if self._loop_enabled:
                self._current_frame = 0
                should_continue = True
            else:
                self._current_frame = len(frames) - 1
                should_continue = False  # Stop playback when not looping
        else:
            should_continue = True

        # Emit frame change signal
        self.frameChanged.emit(self._current_frame, self._total_frames)

        return self._current_frame, should_continue

    def previous_frame(self) -> int:
        """
        Go to previous frame with bounds checking.

        Returns:
            New current frame index
        """
        frames = self._get_frames()
        if frames and self._current_frame > 0:
            self._current_frame -= 1
            self._total_frames = len(frames)
            self.frameChanged.emit(self._current_frame, self._total_frames)
        return self._current_frame

    def first_frame(self) -> int:
        """
        Jump to first frame.

        Returns:
            Current frame index (should be 0)
        """
        frames = self._get_frames()
        if frames:
            self._current_frame = 0
            self._total_frames = len(frames)
            self.frameChanged.emit(self._current_frame, self._total_frames)
        return self._current_frame

    def last_frame(self) -> int:
        """
        Jump to last frame.

        Returns:
            Current frame index (should be last frame)
        """
        frames = self._get_frames()
        if frames:
            self._current_frame = len(frames) - 1
            self._total_frames = len(frames)
            self.frameChanged.emit(self._current_frame, self._total_frames)
        return self._current_frame

    # ============================================================================
    # PLAYBACK CONTROL
    # ============================================================================

    def play(self) -> bool:
        """
        Start animation playback.

        Returns:
            True if playback started successfully, False otherwise
        """
        frames = self._get_frames()
        if not frames:
            return False

        self._is_playing = True
        self._total_frames = len(frames)
        self.playbackStateChanged.emit(True)
        return True

    def pause(self) -> None:
        """Pause animation playback."""
        self._is_playing = False
        self.playbackStateChanged.emit(False)

    def stop(self) -> None:
        """Stop animation and reset to first frame."""
        self._is_playing = False
        frames = self._get_frames()
        if frames:
            self._current_frame = 0
            self._total_frames = len(frames)
            self.frameChanged.emit(self._current_frame, self._total_frames)
        self.playbackStateChanged.emit(False)

    def toggle_playback(self) -> bool:
        """
        Toggle playback state.

        Returns:
            New playing state (True if now playing, False if paused)
        """
        if self._is_playing:
            self.pause()
        else:
            self.play()
        return self._is_playing

    # ============================================================================
    # ANIMATION SETTINGS
    # ============================================================================

    def set_fps(self, fps: int) -> bool:
        """
        Set animation speed with validation.

        Args:
            fps: Frames per second (must be within valid range)

        Returns:
            True if FPS was set successfully, False otherwise
        """
        if Config.Animation.MIN_FPS <= fps <= Config.Animation.MAX_FPS:
            self._fps = fps
            return True
        return False

    def set_loop_enabled(self, enabled: bool) -> None:
        """
        Set animation loop mode.

        Args:
            enabled: True to enable looping, False to disable
        """
        self._loop_enabled = enabled

    # ============================================================================
    # STATE ACCESS PROPERTIES
    # ============================================================================

    @property
    def current_frame(self) -> int:
        """Get current frame index."""
        return self._current_frame

    @property
    def total_frames(self) -> int:
        """
        Get total frame count from the actual frame source.

        This computes the value dynamically to ensure consistency
        with the actual sprite frames, avoiding dual-tracking issues.
        """
        frames = self._get_frames()
        return len(frames)

    @property
    def is_playing(self) -> bool:
        """Get current playback state."""
        return self._is_playing

    @property
    def is_loop_enabled(self) -> bool:
        """Get current loop setting."""
        return self._loop_enabled

    @property
    def fps(self) -> int:
        """Get current FPS setting."""
        return self._fps

    @property
    def current_frame_pixmap(self) -> QPixmap | None:
        """
        Get the currently selected frame as QPixmap.

        Returns:
            Current frame pixmap, or None if no frames available
        """
        frames = self._get_frames()
        if 0 <= self._current_frame < len(frames):
            return frames[self._current_frame]
        return None

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def reset_state(self) -> None:
        """Reset animation state to defaults."""
        self._current_frame = 0
        self._total_frames = 0
        self._is_playing = False
        self._loop_enabled = True
        self._fps = Config.Animation.DEFAULT_FPS

    def get_animation_info(self) -> dict:
        """
        Get comprehensive animation state information.

        Returns:
            Dictionary with all animation state details
        """
        return {
            'current_frame': self._current_frame,
            'total_frames': self._total_frames,
            'is_playing': self._is_playing,
            'loop_enabled': self._loop_enabled,
            'fps': self._fps,
            'has_frames': len(self._get_frames()) > 0
        }
