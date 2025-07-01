#!/usr/bin/env python3
"""
Animation Controller for Sprite Viewer
Manages animation timing, state coordination, and UI/Model synchronization.
Complete MVC Controller implementation for sprite animation.
"""

from typing import Optional
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication

from config import Config


class AnimationController(QObject):
    """
    Centralized animation controller implementing the Controller layer of MVC.
    Coordinates animation timing between SpriteModel (data) and SpriteViewer (UI).
    """
    
    # ============================================================================
    # CONTROLLER SIGNALS FOR COORDINATION
    # ============================================================================
    
    # Timing & State Signals
    animationStarted = Signal()             # Animation playback began
    animationPaused = Signal()              # Animation playback paused 
    animationStopped = Signal()             # Animation playback stopped
    animationCompleted = Signal()           # Animation completed (non-looping)
    
    # Frame Control Signals
    frameAdvanced = Signal(int)             # Frame advanced to index
    playbackStateChanged = Signal(bool)     # Playing state changed
    
    # Configuration Signals
    fpsChanged = Signal(int)                # Animation speed changed
    loopModeChanged = Signal(bool)          # Loop mode toggled
    
    # Error & Status Signals
    errorOccurred = Signal(str)             # Error in animation processing
    statusChanged = Signal(str)             # Status message updates
    
    def __init__(self):
        super().__init__()
        
        # ============================================================================
        # TIMER MANAGEMENT
        # ============================================================================
        
        self._animation_timer: QTimer = QTimer()
        self._animation_timer.timeout.connect(self._on_timer_timeout)
        self._animation_timer.setSingleShot(False)  # Repeating timer
        
        # ============================================================================
        # ANIMATION STATE
        # ============================================================================
        
        self._is_active: bool = False           # Controller is managing animation
        self._is_playing: bool = False          # Animation is currently playing
        self._current_fps: int = Config.Animation.DEFAULT_FPS
        self._loop_enabled: bool = True
        
        # ============================================================================
        # CONNECTED COMPONENTS
        # ============================================================================
        
        self._sprite_model: Optional[object] = None    # SpriteModel reference
        self._sprite_viewer: Optional[object] = None   # SpriteViewer reference
        
        # ============================================================================
        # PERFORMANCE TRACKING & OPTIMIZATION
        # ============================================================================
        
        self._frame_count: int = 0
        self._timer_precision: float = 0.0
        self._last_frame_time: float = 0.0
        self._frame_timing_history: list = []
        self._max_timing_history: int = 60  # Track last 60 frames for FPS analysis
        
        # UI Update Optimization
        self._last_ui_update_frame: int = -1
        self._ui_update_batch_pending: bool = False
        self._pending_status_messages: list = []
        
        # Memory Management
        self._signal_batch_timer: Optional[object] = None  # For batching UI updates
    
    # ============================================================================
    # CONTROLLER LIFECYCLE
    # ============================================================================
    
    def initialize(self, sprite_model, sprite_viewer) -> bool:
        """
        Initialize controller with Model and View components.
        Sets up all signal connections and prepares for animation control.
        Returns success status.
        """
        try:
            # Store component references
            self._sprite_model = sprite_model
            self._sprite_viewer = sprite_viewer
            
            # Connect to Model signals
            self._connect_model_signals()
            
            # Connect to View signals  
            self._connect_view_signals()
            
            # Initialize state from model
            self._sync_state_from_model()
            
            self._is_active = True
            self.statusChanged.emit("Animation controller initialized")
            return True
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to initialize controller: {str(e)}")
            return False
    
    def shutdown(self) -> None:
        """Clean shutdown of animation controller."""
        if self._is_playing:
            self.stop_animation()
        
        self._animation_timer.stop()
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
        
        # Reset performance tracking for new animation session
        self._reset_performance_tracking()
        
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
        # Validate FPS range
        if not (Config.Animation.MIN_FPS <= fps <= Config.Animation.MAX_FPS):
            self.errorOccurred.emit(f"FPS must be between {Config.Animation.MIN_FPS} and {Config.Animation.MAX_FPS}")
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
    # PERFORMANCE OPTIMIZATION METHODS (Step 4.7)
    # ============================================================================
    
    def _track_frame_timing(self) -> None:
        """
        Track frame timing for performance analysis.
        Maintains rolling window of frame timing data.
        """
        import time
        current_time = time.time()
        
        if self._last_frame_time > 0:
            frame_duration = current_time - self._last_frame_time
            self._frame_timing_history.append(frame_duration)
            
            # Maintain rolling window
            if len(self._frame_timing_history) > self._max_timing_history:
                self._frame_timing_history.pop(0)
        
        self._last_frame_time = current_time
    
    def get_actual_performance_fps(self) -> float:
        """
        Get actual FPS based on measured frame timing.
        More accurate than calculated FPS for performance monitoring.
        """
        if len(self._frame_timing_history) < 2:
            return 0.0
        
        avg_duration = sum(self._frame_timing_history) / len(self._frame_timing_history)
        return 1.0 / avg_duration if avg_duration > 0 else 0.0
    
    def get_performance_metrics(self) -> dict:
        """
        Get comprehensive performance metrics for monitoring.
        """
        return {
            "target_fps": self._current_fps,
            "calculated_fps": self.get_actual_fps(),
            "measured_fps": self.get_actual_performance_fps(),
            "timing_precision": self.get_timing_precision(),
            "frame_timing_samples": len(self._frame_timing_history),
            "total_frames_processed": self._frame_count,
            "average_frame_duration_ms": (sum(self._frame_timing_history) / len(self._frame_timing_history) * 1000) if self._frame_timing_history else 0
        }
    
    def _optimize_ui_updates(self, frame_index: int) -> bool:
        """
        Optimize UI updates to prevent unnecessary redraws.
        Returns True if UI update should proceed.
        """
        # Skip redundant updates for same frame
        if frame_index == self._last_ui_update_frame:
            return False
        
        self._last_ui_update_frame = frame_index
        return True
    
    def _batch_status_message(self, message: str) -> None:
        """
        Batch status messages to prevent UI flooding.
        Groups multiple rapid status updates.
        """
        self._pending_status_messages.append(message)
        
        # If not already pending, schedule batch update
        if not self._ui_update_batch_pending and self._signal_batch_timer:
            self._ui_update_batch_pending = True
            self._signal_batch_timer.start(50)  # 50ms batch window
    
    def _flush_batched_status_messages(self) -> None:
        """
        Flush batched status messages to UI.
        Sends only the most recent relevant messages.
        """
        if self._pending_status_messages:
            # Send only the last message to avoid spam
            latest_message = self._pending_status_messages[-1]
            self.statusChanged.emit(latest_message)
            self._pending_status_messages.clear()
        
        self._ui_update_batch_pending = False
    
    def _reset_performance_tracking(self) -> None:
        """Reset performance tracking for new animation session."""
        self._frame_timing_history.clear()
        self._last_frame_time = 0.0
        self._frame_count = 0
        self._last_ui_update_frame = -1
    
    # ============================================================================
    # TIMER EVENT HANDLING (Implemented in Step 4.2, Enhanced in Step 4.7)
    # ============================================================================
    
    def _on_timer_timeout(self) -> None:
        """
        Handle animation timer timeout - advance to next frame.
        Core animation advancement logic with performance optimization.
        """
        if not self._sprite_model or not self._is_playing:
            return
        
        try:
            # Track frame timing for performance analysis
            self._track_frame_timing()
            
            # Advance frame using model logic
            frame_index, should_continue = self._sprite_model.next_frame()
            
            # Optimize UI updates - only emit if frame actually changed
            if self._optimize_ui_updates(frame_index):
                self.frameAdvanced.emit(frame_index)
            
            # Handle animation completion (non-looping)
            if not should_continue:
                self.pause_animation()
                self.animationCompleted.emit()
                # Use batched status for completion message
                self._batch_status_message("Animation completed")
            
            # Track performance
            self._frame_count += 1
            
            # Periodic performance reporting (every 60 frames)
            if self._frame_count % 60 == 0:
                metrics = self.get_performance_metrics()
                if metrics["measured_fps"] > 0:
                    performance_msg = f"Performance: {metrics['measured_fps']:.1f} FPS (target: {metrics['target_fps']})"
                    self._batch_status_message(performance_msg)
            
        except Exception as e:
            self.errorOccurred.emit(f"Animation error: {str(e)}")
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
        if hasattr(self._sprite_viewer, 'aboutToClose'):
            self._sprite_viewer.aboutToClose.connect(self._on_view_closing)
        
        # Connect to canvas frame change signals for UI synchronization
        if hasattr(self._sprite_viewer, '_canvas') and hasattr(self._sprite_viewer._canvas, 'frameChanged'):
            self._sprite_viewer._canvas.frameChanged.connect(self._on_view_frame_display_changed)
        
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
        self.statusChanged.emit(f"Controller synced: {self._current_fps} FPS, loop {'enabled' if self._loop_enabled else 'disabled'}")
    
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
        
        # Reset frame counting for new data
        self._frame_count = 0
        
        # Sync state with newly loaded model
        self._sync_state_from_model()
        
        # Notify that controller is ready for new sprite data
        self.statusChanged.emit("Animation controller ready for new sprite sheet")
    
    def _on_model_extraction_completed(self, frame_count: int) -> None:
        """
        Handle frame extraction completion in model.
        Updates controller state for animation readiness.
        """
        self.statusChanged.emit(f"Frame extraction completed: {frame_count} frames ready for animation")
        
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
            self.statusChanged.emit(f"Animation ready: {frame_count} frames at {self._current_fps} FPS")
    
    def _on_model_frame_changed(self, current_frame: int, total_frames: int) -> None:
        """
        Handle frame change in model.
        Distinguishes between timer-driven and manual frame changes.
        """
        # Check if this is a manual frame change (not timer-driven)
        if self._is_playing and not self._animation_timer.isActive():
            # Timer is not active but we're supposed to be playing - this is manual
            self.pause_animation()
            self.statusChanged.emit(f"Animation paused - manual frame change to {current_frame + 1}/{total_frames}")
        
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
    
    # ============================================================================
    # VIEW EVENT HANDLERS (Implemented in Step 4.5)
    # ============================================================================
    
    def _on_view_closing(self) -> None:
        """
        Handle view closing event.
        Ensures clean shutdown of animation controller.
        """
        self.statusChanged.emit("View closing - shutting down animation controller")
        self.shutdown()
    
    def _on_view_frame_display_changed(self, current: int, total: int) -> None:
        """
        Handle frame display change from view canvas.
        Provides feedback for UI synchronization.
        """
        # This can be used for performance monitoring or sync validation
        # Typically no action needed as controller drives frame changes
        pass
    
    def handle_user_interaction(self, interaction_type: str, **kwargs) -> bool:
        """
        Generic handler for user interactions from view.
        Centralizes user action processing in controller.
        """
        try:
            if interaction_type == "manual_frame_seek":
                # User manually seeks to specific frame
                frame_index = kwargs.get("frame_index", 0)
                if self._is_playing:
                    self.pause_animation()
                    self.statusChanged.emit(f"Animation paused - user seek to frame {frame_index + 1}")
                return True
                
            elif interaction_type == "speed_change_request":
                # User requests FPS change
                new_fps = kwargs.get("fps", self._current_fps)
                return self.set_fps(new_fps)
                
            elif interaction_type == "loop_toggle_request":
                # User toggles loop mode
                enabled = kwargs.get("enabled", not self._loop_enabled)
                self.set_loop_mode(enabled)
                return True
                
            elif interaction_type == "animation_control_request":
                # User requests play/pause/stop
                action = kwargs.get("action", "toggle")
                if action == "play":
                    return self.start_animation()
                elif action == "pause":
                    self.pause_animation()
                    return True
                elif action == "stop":
                    self.stop_animation()
                    return True
                elif action == "toggle":
                    return self.toggle_playback()
                    
            else:
                self.statusChanged.emit(f"Unknown user interaction: {interaction_type}")
                return False
                
        except Exception as e:
            self.errorOccurred.emit(f"Error handling user interaction '{interaction_type}': {str(e)}")
            return False
    
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
    
    @property
    def frame_count(self) -> int:
        """Get total frames processed since initialization."""
        return self._frame_count
    
    def get_view_status_info(self) -> dict:
        """
        Get status information specifically formatted for view display.
        Returns user-friendly status data for UI components.
        """
        measured_fps = self.get_actual_performance_fps()
        return {
            "animation_state": "Playing" if self._is_playing else "Paused",
            "fps_display": f"{self._current_fps} FPS",
            "actual_fps_display": f"{self.get_actual_fps():.1f} actual FPS",
            "measured_fps_display": f"{measured_fps:.1f} measured FPS" if measured_fps > 0 else "No data",
            "loop_mode": "Loop enabled" if self._loop_enabled else "Play once",
            "timing_quality": "Precise" if self.get_timing_precision() < 0.1 else "Standard",
            "performance_quality": "Excellent" if abs(measured_fps - self._current_fps) < 2 else "Good" if abs(measured_fps - self._current_fps) < 5 else "Fair" if measured_fps > 0 else "Unknown",
            "frame_count_processed": self._frame_count,
            "controller_status": "Active" if self._is_active else "Inactive",
            "can_animate": self._sprite_model is not None and len(self._sprite_model.sprite_frames) > 1 if self._sprite_model else False
        }
    
    def get_status_info(self) -> dict:
        """Get comprehensive controller status information."""
        return {
            "is_active": self._is_active,
            "is_playing": self._is_playing,
            "current_fps": self._current_fps,
            "actual_fps": self.get_actual_fps(),
            "timing_precision": self.get_timing_precision(),
            "loop_enabled": self._loop_enabled,
            "frame_count": self._frame_count,
            "timer_interval_ms": self._calculate_timer_interval(),
            "has_model": self._sprite_model is not None,
            "has_view": self._sprite_viewer is not None
        }


# Export for easy importing
__all__ = ['AnimationController']