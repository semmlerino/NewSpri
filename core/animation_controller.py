#!/usr/bin/env python3
"""
Animation Controller for Sprite Viewer
Manages animation timing, state coordination, and UI/Model synchronization.
Complete MVC Controller implementation for sprite animation.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Signal

from config import Config

if TYPE_CHECKING:
    from sprite_model.core import SpriteModel
    from sprite_viewer import SpriteViewer


class AnimationController(QObject):
    """
    Centralized animation controller implementing the Controller layer of MVC.
    Coordinates animation timing between SpriteModel (data) and SpriteViewer (UI).
    """

    # ============================================================================
    # CONTROLLER SIGNALS FOR COORDINATION
    # ============================================================================

    # Timing & State Signals
    animationStarted = Signal()  # Animation playback began
    animationPaused = Signal()  # Animation playback paused
    animationStopped = Signal()  # Animation playback stopped
    animationCompleted = Signal()  # Animation completed (non-looping)

    # Frame Control Signals
    frameAdvanced = Signal(int)  # Frame advanced to index
    playbackStateChanged = Signal(bool)  # Playing state changed

    # Configuration Signals
    fpsChanged = Signal(int)  # Animation speed changed
    loopModeChanged = Signal(bool)  # Loop mode toggled

    # Error & Status Signals
    errorOccurred = Signal(str)  # Error in animation processing
    statusChanged = Signal(str)  # Status message updates

    def __init__(
        self,
        sprite_model: "SpriteModel",
        sprite_viewer: "SpriteViewer",
    ):
        """
        Initialize controller with Model and View components.

        Args:
            sprite_model: The sprite data model
            sprite_viewer: The main application window
        """
        super().__init__()

        # ============================================================================
        # CONNECTED COMPONENTS
        # ============================================================================

        self._sprite_model: SpriteModel = sprite_model
        self._sprite_viewer: SpriteViewer = sprite_viewer

        # ============================================================================
        # TIMER MANAGEMENT
        # ============================================================================

        self._animation_timer: QTimer = QTimer()
        self._animation_timer.setSingleShot(False)  # Repeating timer

        # ============================================================================
        # ANIMATION STATE
        # ============================================================================

        self._is_active: bool = True  # Controller is managing animation
        self._is_playing: bool = False  # Animation is currently playing
        self._current_fps: int = Config.Animation.DEFAULT_FPS
        self._loop_enabled: bool = True

        # Timer precision tracking (for get_actual_fps)
        self._timer_precision: float = 0.0

        # Connect timer
        self._animation_timer.timeout.connect(self._on_timer_timeout)

        # Connect to Model signals
        self._connect_model_signals()

        # Connect to View signals
        self._connect_view_signals()

        # Initialize state from model
        self._sync_state_from_model()

        self.statusChanged.emit("Animation controller initialized")

    def shutdown(self) -> None:
        """Clean shutdown of animation controller."""
        if self._is_playing:
            self.stop_animation()

        self._animation_timer.stop()
        # Qt automatically disconnects signals when QObjects are destroyed
        self._is_active = False
        self.statusChanged.emit("Animation controller shutdown")

    # ============================================================================
    # ANIMATION CONTROL (Will be implemented in Step 4.2-4.3)
    # ============================================================================

    def start_animation(self) -> bool:
        """
        Start animation playback using current FPS settings.
        Returns success status.
        """
        if not self._is_active or not self._sprite_model:
            return False

        # Validate that we have frames to animate
        if not self._sprite_model.sprite_frames:
            self.errorOccurred.emit("No sprite frames available for animation")
            return False

        # Calculate timer interval based on FPS
        interval_ms = self._calculate_timer_interval()

        # Start animation timer
        self._animation_timer.start(interval_ms)
        self._is_playing = True

        # Notify components
        self.animationStarted.emit()
        self.playbackStateChanged.emit(True)
        self.statusChanged.emit(f"Animation started at {self._current_fps} FPS")

        return True

    def pause_animation(self) -> None:
        """Pause animation playback, preserving current frame."""
        if self._is_playing:
            self._animation_timer.stop()
            self._is_playing = False

            # Notify components
            self.animationPaused.emit()
            self.playbackStateChanged.emit(False)
            self.statusChanged.emit("Animation paused")

    def stop_animation(self) -> None:
        """Stop animation and reset to first frame."""
        if self._is_playing:
            self._animation_timer.stop()
            self._is_playing = False

            # Reset to first frame via model
            if self._sprite_model:
                self._sprite_model.first_frame()

            # Notify components
            self.animationStopped.emit()
            self.playbackStateChanged.emit(False)
            self.statusChanged.emit("Animation stopped")

    def toggle_playback(self) -> bool:
        """Toggle between play and pause states. Returns new playing state."""
        if self._is_playing:
            self.pause_animation()
        else:
            self.start_animation()
        return self._is_playing

    # ============================================================================
    # TIMING CONFIGURATION (Will be implemented in Step 4.3)
    # ============================================================================

    def set_fps(self, fps: int) -> bool:
        """
        Set animation frame rate with validation.
        Updates timer interval if currently playing.
        Returns success status.
        """
        # Validate input type
        if fps is None or not isinstance(fps, (int, float)):
            self.errorOccurred.emit(f"FPS must be a number, received: {type(fps).__name__}")
            return False

        # Check for special float values
        if isinstance(fps, float) and (fps != fps or fps == float("inf") or fps == float("-inf")):
            self.errorOccurred.emit(f"FPS must be a valid number, not {fps}")
            return False

        # Convert to int if float
        try:
            fps = int(fps)
        except (ValueError, OverflowError):
            self.errorOccurred.emit(f"FPS value too large or invalid: {fps}")
            return False

        # Validate FPS range
        if not (Config.Animation.MIN_FPS <= fps <= Config.Animation.MAX_FPS):
            self.errorOccurred.emit(
                f"FPS must be between {Config.Animation.MIN_FPS} and {Config.Animation.MAX_FPS}"
            )
            return False

        self._current_fps = fps

        # Sync change to model
        self._sync_state_to_model()

        # Update timer interval if currently playing
        if self._is_playing:
            interval_ms = self._calculate_timer_interval()
            self._animation_timer.setInterval(interval_ms)

        # Notify components
        self.fpsChanged.emit(fps)
        self.statusChanged.emit(f"Animation speed set to {fps} FPS")

        return True

    def set_loop_mode(self, enabled: bool) -> None:
        """Set animation loop mode and update model."""
        self._loop_enabled = enabled

        # Sync change to model
        self._sync_state_to_model()

        # Notify components
        self.loopModeChanged.emit(enabled)
        mode_text = "enabled" if enabled else "disabled"
        self.statusChanged.emit(f"Animation loop {mode_text}")

    def _calculate_timer_interval(self) -> int:
        """
        Calculate precise timer interval in milliseconds for current FPS.
        Uses integer division with rounding for best timing accuracy.
        """
        # Validate FPS to prevent division by zero or invalid intervals
        if self._current_fps <= 0:
            self._current_fps = Config.Animation.DEFAULT_FPS
            self.errorOccurred.emit("Invalid FPS detected, reset to default")

        # Calculate interval with rounding for better accuracy
        # Formula: interval_ms = 1000ms / fps
        interval_ms = round(Config.Animation.TIMER_BASE / self._current_fps)

        # Clamp to reasonable bounds to prevent extreme intervals
        min_interval = Config.Animation.TIMER_BASE // Config.Animation.MAX_FPS
        max_interval = Config.Animation.TIMER_BASE // Config.Animation.MIN_FPS

        if interval_ms < min_interval:
            interval_ms = min_interval
        elif interval_ms > max_interval:
            interval_ms = max_interval

        # Store precision tracking for performance analysis
        self._timer_precision = Config.Animation.TIMER_BASE / interval_ms - self._current_fps

        return interval_ms

    def get_actual_fps(self) -> float:
        """
        Get the actual FPS based on calculated timer interval.
        May differ slightly from target FPS due to integer rounding.
        """
        interval_ms = self._calculate_timer_interval()
        return Config.Animation.TIMER_BASE / interval_ms if interval_ms > 0 else 0.0

    def get_timing_precision(self) -> float:
        """
        Get timing precision indicator.
        Returns difference between target and actual FPS.
        """
        return abs(self._timer_precision)

    # ============================================================================
    # TIMER EVENT HANDLING
    # ============================================================================

    def _on_timer_timeout(self) -> None:
        """
        Handle animation timer timeout - advance to next frame.
        """
        if not self._sprite_model or not self._is_playing:
            return

        try:
            # Advance frame using model logic
            frame_index, should_continue = self._sprite_model.next_frame()

            # Emit frame advanced signal
            self.frameAdvanced.emit(frame_index)

            # Handle animation completion (non-looping)
            if not should_continue:
                self.pause_animation()
                self.animationCompleted.emit()
                self.statusChanged.emit("Animation completed")

        except Exception as e:
            self.errorOccurred.emit(f"Animation error: {e!s}")
            self.pause_animation()

    # ============================================================================
    # SIGNAL COORDINATION (Will be implemented in Step 4.4-4.5)
    # ============================================================================

    def _connect_model_signals(self) -> None:
        """Connect to SpriteModel signals for data synchronization."""
        if not self._sprite_model:
            return

        # Model state changes that affect animation
        self._sprite_model.dataLoaded.connect(self._on_model_data_loaded)
        self._sprite_model.extractionCompleted.connect(self._on_model_extraction_completed)
        self._sprite_model.frameChanged.connect(self._on_model_frame_changed)
        self._sprite_model.errorOccurred.connect(self._on_model_error)

    def _connect_view_signals(self) -> None:
        """
        Connect to SpriteViewer signals for user interaction.
        Sets up bidirectional communication between View and Controller.
        """
        if not self._sprite_viewer:
            return

        # Connect view's status requests to controller
        # Note: Some signals like playPauseClicked are already connected directly
        # to controller methods in SpriteViewer._connect_signals()

        # Connect to view lifecycle signals if they exist
        if hasattr(self._sprite_viewer, "aboutToClose"):
            self._sprite_viewer.aboutToClose.connect(self._on_view_closing)  # type: ignore[union-attr]

        self.statusChanged.emit("View ↔ Controller signal communication established")

    def _sync_state_from_model(self) -> None:
        """
        Synchronize controller state with model state.
        Ensures controller settings match model configuration.
        """
        if not self._sprite_model:
            return

        # Sync animation settings from model
        self._current_fps = self._sprite_model.fps
        self._loop_enabled = self._sprite_model.loop_enabled

        # Validate synced settings
        if not (Config.Animation.MIN_FPS <= self._current_fps <= Config.Animation.MAX_FPS):
            self._current_fps = Config.Animation.DEFAULT_FPS
            self.errorOccurred.emit("Invalid FPS in model, reset to default")

        # Log successful synchronization
        self.statusChanged.emit(
            f"Controller synced: {self._current_fps} FPS, loop {'enabled' if self._loop_enabled else 'disabled'}"
        )

    def _sync_state_to_model(self) -> None:
        """
        Synchronize controller state changes to model.
        Ensures model settings match controller configuration.
        """
        if not self._sprite_model:
            return

        # Update model with controller settings
        self._sprite_model.set_fps(self._current_fps)
        self._sprite_model.set_loop_enabled(self._loop_enabled)

        self.statusChanged.emit("Model updated with controller settings")

    # ============================================================================
    # MODEL EVENT HANDLERS (Implemented in Step 4.4)
    # ============================================================================

    def _on_model_data_loaded(self, file_path: str) -> None:
        """
        Handle new sprite data loaded in model.
        Resets animation state and prepares for new sprite sheet.
        """
        self.statusChanged.emit(f"New sprite data loaded: {file_path}")

        # Stop current animation if playing
        if self._is_playing:
            self.stop_animation()

        # Sync state with newly loaded model
        self._sync_state_from_model()

        # Notify that controller is ready for new sprite data
        self.statusChanged.emit("Animation controller ready for new sprite sheet")

    def _on_model_extraction_completed(self, frame_count: int) -> None:
        """
        Handle frame extraction completion in model.
        Updates controller state for animation readiness.
        """
        self.statusChanged.emit(
            f"Frame extraction completed: {frame_count} frames ready for animation"
        )

        # Validate that we have animatable frames
        if frame_count == 0:
            self.statusChanged.emit("No frames available for animation")
            if self._is_playing:
                self.pause_animation()
        elif frame_count == 1:
            self.statusChanged.emit("Single frame detected - animation not applicable")
            if self._is_playing:
                self.pause_animation()
        else:
            self.statusChanged.emit(
                f"Animation ready: {frame_count} frames at {self._current_fps} FPS"
            )

    def _on_model_frame_changed(self, current_frame: int, total_frames: int) -> None:
        """
        Handle frame change in model.
        Distinguishes between timer-driven and manual frame changes.
        """
        # Check if this is a manual frame change (not timer-driven)
        if self._is_playing and not self._animation_timer.isActive():
            # Timer is not active but we're supposed to be playing - this is manual
            self.pause_animation()
            self.statusChanged.emit(
                f"Animation paused - manual frame change to {current_frame + 1}/{total_frames}"
            )

        # Emit frame advanced signal for UI synchronization
        self.frameAdvanced.emit(current_frame)

    def _on_model_error(self, error_message: str) -> None:
        """
        Handle errors from sprite model.
        Pauses animation and propagates error information.
        """
        # Always pause animation on model errors
        if self._is_playing:
            self.pause_animation()

        # Propagate error with controller context
        controller_error = f"Sprite model error: {error_message}"
        self.errorOccurred.emit(controller_error)
        self.statusChanged.emit("Animation paused due to model error")

    def _on_view_closing(self) -> None:
        """Handle view closing signal - stop animation and cleanup."""
        if self._is_playing:
            self.stop_animation()
        self.statusChanged.emit("View closing, animation stopped")

    # ============================================================================
    # PROPERTIES & STATUS
    # ============================================================================

    @property
    def is_active(self) -> bool:
        """Check if controller is initialized and active."""
        return self._is_active

    @property
    def is_playing(self) -> bool:
        """Check if animation is currently playing."""
        return self._is_playing

    @property
    def current_fps(self) -> int:
        """Get current animation FPS setting."""
        return self._current_fps

    @property
    def loop_enabled(self) -> bool:
        """Get current loop mode setting."""
        return self._loop_enabled

    def get_status_info(self) -> dict:
        """Get controller status information."""
        return {
            "is_active": self._is_active,
            "is_playing": self._is_playing,
            "current_fps": self._current_fps,
            "actual_fps": self.get_actual_fps(),
            "loop_enabled": self._loop_enabled,
            "timer_interval_ms": self._calculate_timer_interval(),
            "has_model": self._sprite_model is not None,
            "has_view": self._sprite_viewer is not None,
        }


# Export for easy importing
__all__ = ["AnimationController"]
