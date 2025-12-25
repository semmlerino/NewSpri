"""
Animation Coordinator for SpriteViewer refactoring.
Handles animation navigation, playback state management, and UI updates.
"""

from PySide6.QtWidgets import QMessageBox

from .base import CoordinatorBase


class AnimationCoordinator(CoordinatorBase):
    """
    Coordinator responsible for animation operations.
    
    Manages frame navigation, playback state updates, and coordination
    between animation controller, playback controls, and sprite model.
    Extracts animation logic from SpriteViewer.
    """
    
    def __init__(self, main_window):
        """Initialize animation coordinator."""
        super().__init__(main_window)

        # Component references
        self.sprite_model = None
        self.animation_controller = None
        self.playback_controls = None
        self.action_manager = None
        self.status_manager = None
        self.shortcut_manager = None

    def initialize(self, dependencies):
        """
        Initialize coordinator with required dependencies.

        Args:
            dependencies: Dict containing:
                - sprite_model: SpriteModel instance
                - animation_controller: AnimationController instance
                - playback_controls: PlaybackControls instance
                - action_manager: ActionManager instance
                - status_manager: StatusBarManager instance
                - shortcut_manager: ShortcutManager instance
        """
        self.sprite_model = dependencies['sprite_model']
        self.animation_controller = dependencies['animation_controller']
        self.playback_controls = dependencies['playback_controls']
        self.action_manager = dependencies.get('action_manager')
        self.status_manager = dependencies.get('status_manager')
        self.shortcut_manager = dependencies.get('shortcut_manager')

        self._initialized = True
    
    def cleanup(self):
        """Clean up resources."""
        # No specific cleanup needed for animation coordinator
        pass
    
    # ============================================================================
    # FRAME NAVIGATION
    # ============================================================================
    
    def go_to_prev_frame(self):
        """Navigate to previous frame."""
        if self.sprite_model:
            self.sprite_model.previous_frame()
    
    def go_to_next_frame(self):
        """Navigate to next frame."""
        if self.sprite_model:
            self.sprite_model.next_frame()
    
    def go_to_first_frame(self):
        """Navigate to first frame."""
        if self.sprite_model:
            self.sprite_model.first_frame()
    
    def go_to_last_frame(self):
        """Navigate to last frame."""
        if self.sprite_model:
            self.sprite_model.last_frame()
    
    def go_to_frame(self, frame_index: int):
        """
        Navigate to specific frame.
        
        Args:
            frame_index: Index of frame to navigate to
        """
        if self.sprite_model:
            self.sprite_model.set_current_frame(frame_index)
    
    def restart_animation(self):
        """Restart animation from first frame."""
        if self.sprite_model:
            self.sprite_model.set_current_frame(0)
            if self.status_manager:
                self.status_manager.show_message("Animation restarted")
    
    # ============================================================================
    # PLAYBACK CONTROL
    # ============================================================================
    
    def toggle_playback(self):
        """Toggle animation playback."""
        if self.animation_controller:
            self.animation_controller.toggle_playback()
    
    def start_playback(self):
        """Start animation playback."""
        if self.animation_controller:
            self.animation_controller.start_playback()
    
    def pause_playback(self):
        """Pause animation playback."""
        if self.animation_controller:
            self.animation_controller.pause_playback()
    
    def stop_playback(self):
        """Stop animation playback."""
        if self.animation_controller:
            self.animation_controller.stop_playback()
    
    # ============================================================================
    # PLAYBACK STATE HANDLERS
    # ============================================================================
    
    def on_playback_started(self):
        """Handle playback start."""
        if self.playback_controls:
            self.playback_controls.update_button_states(False, True, True)
        self._update_context()
    
    def on_playback_paused(self):
        """Handle playback pause."""
        if self.playback_controls:
            self.playback_controls.update_button_states(True, True, True)
        self._update_context()
    
    def on_playback_stopped(self):
        """Handle playback stop."""
        if self.playback_controls:
            self.playback_controls.update_button_states(True, True, False)
        self._update_context()
    
    def on_playback_completed(self):
        """Handle playback completion."""
        if self.playback_controls:
            self.playback_controls.update_button_states(True, True, False)
        self._update_context()
    
    def on_frame_advanced(self, frame_index: int):
        """
        Handle frame advancement from animation controller.
        
        Args:
            frame_index: New frame index
        """
        # Frame advancement is handled by the animation controller
        # UI updates happen through sprite model frameChanged signal
        pass
    
    def on_animation_error(self, error_message: str):
        """
        Handle animation controller error.
        
        Args:
            error_message: Error message to display
        """
        QMessageBox.warning(self.main_window, "Animation Error", error_message)
    
    # ============================================================================
    # FRAME EXTRACTION UPDATES
    # ============================================================================
    
    def on_extraction_completed(self, frame_count: int):
        """
        Handle extraction completion - update playback controls.
        
        Args:
            frame_count: Number of frames extracted
        """
        if not self.playback_controls:
            return
            
        if frame_count > 0:
            self.playback_controls.set_frame_range(frame_count - 1)
            self.playback_controls.update_button_states(True, True, False)
        else:
            self.playback_controls.set_frame_range(0)
            self.playback_controls.update_button_states(False, False, False)
    
    # ============================================================================
    # PLAYBACK SETTINGS
    # ============================================================================
    
    def set_fps(self, fps: float):
        """
        Set animation FPS.
        
        Args:
            fps: Frames per second
        """
        if self.animation_controller:
            self.animation_controller.set_fps(fps)
    
    def set_loop_mode(self, loop: bool):
        """
        Set loop mode.
        
        Args:
            loop: Whether to loop animation
        """
        if self.animation_controller:
            self.animation_controller.set_loop_mode(loop)
    
    # ============================================================================
    # STATE QUERIES
    # ============================================================================
    
    def is_playing(self) -> bool:
        """Check if animation is currently playing."""
        if self.animation_controller:
            return self.animation_controller.is_playing
        return False
    
    def get_current_frame(self) -> int:
        """Get current frame index."""
        if self.sprite_model:
            return self.sprite_model.current_frame
        return 0
    
    def get_frame_count(self) -> int:
        """Get total number of frames."""
        if self.sprite_model and self.sprite_model.sprite_frames:
            return len(self.sprite_model.sprite_frames)
        return 0
    
    def decrease_animation_speed(self):
        """Decrease animation speed by one step."""
        if self.animation_controller:
            current_fps = self.animation_controller._current_fps
            # Define speed steps
            speed_steps = [1, 2, 4, 6, 8, 10, 12, 15, 20, 24, 30, 60]
            # Find current step and go to previous
            for i in range(len(speed_steps) - 1, -1, -1):
                if current_fps > speed_steps[i]:
                    self.animation_controller.set_fps(speed_steps[i])
                    return
            # If we're at or below the lowest, set to lowest
            if current_fps > speed_steps[0]:
                self.animation_controller.set_fps(speed_steps[0])
    
    def increase_animation_speed(self):
        """Increase animation speed by one step."""
        if self.animation_controller:
            current_fps = self.animation_controller._current_fps
            # Define speed steps
            speed_steps = [1, 2, 4, 6, 8, 10, 12, 15, 20, 24, 30, 60]
            # Find current step and go to next
            for i in range(len(speed_steps)):
                if current_fps < speed_steps[i]:
                    self.animation_controller.set_fps(speed_steps[i])
                    return
            # If we're at or above the highest, set to highest
            if current_fps < speed_steps[-1]:
                self.animation_controller.set_fps(speed_steps[-1])
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _update_context(self):
        """Update manager context based on animation state."""
        if not self.action_manager:
            return
            
        has_frames = bool(self.sprite_model and self.sprite_model.sprite_frames)
        is_playing = self.is_playing()

        # Update both managers if available
        if self.shortcut_manager:
            self.shortcut_manager.update_context(
                has_frames=has_frames,
                is_playing=is_playing
            )

        if self.action_manager:
            self.action_manager.update_context(
                has_frames=has_frames,
                is_playing=is_playing
            )