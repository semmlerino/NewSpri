"""
Signal Coordinator - centralized signal connection management.

Extracts all inter-component signal wiring from SpriteViewer into a
single, self-documenting class. Makes signal dependencies explicit
and simplifies adding new component connections.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject

if TYPE_CHECKING:
    from PySide6.QtGui import QAction

    from core import AnimationController, AnimationSegmentController, AutoDetectionController
    from managers import AnimationSegmentManager
    from sprite_model import SpriteModel
    from ui import (
        AnimationGridView,
        FrameExtractor,
        PlaybackControls,
        SpriteCanvas,
        StatusBarManager,
    )


class SignalCoordinator(QObject):
    """
    Manages all signal-slot connections between application components.

    Responsibilities:
    - Connect signals between model, view, and controller layers
    - Provide clean connect/disconnect lifecycle
    - Document signal dependencies in one place

    Usage:
        coordinator = SignalCoordinator(
            sprite_model=model,
            animation_controller=anim_ctrl,
            ...
        )
        coordinator.connect_all()
        # ... on shutdown ...
        coordinator.disconnect_all()
    """

    def __init__(
        self,
        # Model layer
        sprite_model: SpriteModel,
        # Controllers
        animation_controller: AnimationController,
        auto_detection_controller: AutoDetectionController,
        segment_controller: AnimationSegmentController,
        # UI Components
        canvas: SpriteCanvas,
        playback_controls: PlaybackControls,
        frame_extractor: FrameExtractor,
        grid_view: AnimationGridView | None,
        # Managers
        status_manager: StatusBarManager | None,
        segment_manager: AnimationSegmentManager,
        # Actions dict
        actions: dict[str, QAction],
        # Handler callbacks (from SpriteViewer)
        on_frame_changed: object,
        on_sprite_loaded: object,
        on_extraction_completed: object,
        on_playback_started: object,
        on_playback_paused: object,
        on_playback_stopped: object,
        on_playback_completed: object,
        on_animation_error: object,
        on_frame_settings_detected: object,
        on_extraction_mode_changed: object,
        on_update_frame_slicing: object,
        on_grid_frame_preview: object,
        on_export_frames_requested: object,
        on_export_current_frame_requested: object,
        on_zoom_changed: object,
    ):
        super().__init__()

        # Store all component references
        self._sprite_model = sprite_model
        self._animation_controller = animation_controller
        self._auto_detection_controller = auto_detection_controller
        self._segment_controller = segment_controller
        self._canvas = canvas
        self._playback_controls = playback_controls
        self._frame_extractor = frame_extractor
        self._grid_view = grid_view
        self._status_manager = status_manager
        self._segment_manager = segment_manager
        self._actions = actions

        # Store handler callbacks
        self._on_frame_changed = on_frame_changed
        self._on_sprite_loaded = on_sprite_loaded
        self._on_extraction_completed = on_extraction_completed
        self._on_playback_started = on_playback_started
        self._on_playback_paused = on_playback_paused
        self._on_playback_stopped = on_playback_stopped
        self._on_playback_completed = on_playback_completed
        self._on_animation_error = on_animation_error
        self._on_frame_settings_detected = on_frame_settings_detected
        self._on_extraction_mode_changed = on_extraction_mode_changed
        self._on_update_frame_slicing = on_update_frame_slicing
        self._on_grid_frame_preview = on_grid_frame_preview
        self._on_export_frames_requested = on_export_frames_requested
        self._on_export_current_frame_requested = on_export_current_frame_requested
        self._on_zoom_changed = on_zoom_changed

        self._connected = False

    def connect_all(self) -> None:
        """Connect all inter-component signals."""
        if self._connected:
            return

        self._connect_model_signals()
        self._connect_animation_controller_signals()
        self._connect_auto_detection_signals()
        self._connect_canvas_signals()
        self._connect_frame_extractor_signals()
        self._connect_playback_controls_signals()
        self._connect_grid_view_signals()
        self._connect_action_callbacks()

        self._connected = True

    def disconnect_all(self) -> None:
        """Disconnect all signals for clean shutdown."""
        if not self._connected:
            return

        # Qt handles signal disconnection on object destruction,
        # but explicit disconnect is cleaner for lifecycle management.
        # Note: We don't disconnect here because Qt handles it automatically
        # and trying to disconnect already-destroyed objects can cause issues.

        self._connected = False

    # =========================================================================
    # SIGNAL CONNECTION GROUPS
    # =========================================================================

    def _connect_model_signals(self) -> None:
        """Connect SpriteModel signals to handlers."""
        self._sprite_model.frameChanged.connect(self._on_frame_changed)
        self._sprite_model.dataLoaded.connect(self._on_sprite_loaded)
        self._sprite_model.extractionCompleted.connect(self._on_extraction_completed)

    def _connect_animation_controller_signals(self) -> None:
        """Connect AnimationController signals to handlers."""
        self._animation_controller.animationStarted.connect(self._on_playback_started)
        self._animation_controller.animationPaused.connect(self._on_playback_paused)
        self._animation_controller.animationStopped.connect(self._on_playback_stopped)
        self._animation_controller.animationCompleted.connect(self._on_playback_completed)
        self._animation_controller.errorOccurred.connect(self._on_animation_error)

        if self._status_manager is not None:
            self._animation_controller.statusChanged.connect(self._status_manager.show_message)

    def _connect_auto_detection_signals(self) -> None:
        """Connect AutoDetectionController signals to handlers."""
        self._auto_detection_controller.frameSettingsDetected.connect(
            self._on_frame_settings_detected
        )
        self._auto_detection_controller.marginSettingsDetected.connect(
            self._on_margin_settings_detected
        )
        self._auto_detection_controller.spacingSettingsDetected.connect(
            self._on_spacing_settings_detected
        )
        self._auto_detection_controller.buttonConfidenceUpdate.connect(
            self._frame_extractor.update_auto_button_confidence
        )

        if self._status_manager is not None:
            self._auto_detection_controller.statusUpdate.connect(self._status_manager.show_message)

    def _on_margin_settings_detected(self, offset_x: int, offset_y: int) -> None:
        """Update margin spin boxes when auto-detection finds margin values."""
        self._frame_extractor.offset_x.setValue(offset_x)
        self._frame_extractor.offset_y.setValue(offset_y)

    def _on_spacing_settings_detected(self, spacing_x: int, spacing_y: int) -> None:
        """Update spacing spin boxes when auto-detection finds spacing values."""
        self._frame_extractor.spacing_x.setValue(spacing_x)
        self._frame_extractor.spacing_y.setValue(spacing_y)

    def _connect_canvas_signals(self) -> None:
        """Connect SpriteCanvas signals to handlers."""
        self._canvas.zoomChanged.connect(self._on_zoom_changed)

        if self._status_manager is not None:
            self._canvas.mouseMoved.connect(self._status_manager.update_mouse_position)

    def _connect_frame_extractor_signals(self) -> None:
        """Connect FrameExtractor signals to handlers."""
        self._frame_extractor.settingsChanged.connect(self._on_update_frame_slicing)
        self._frame_extractor.modeChangedEnum.connect(self._on_extraction_mode_changed)

        # Auto-detect button connections
        self._frame_extractor.comprehensive_auto_btn.clicked.connect(
            self._auto_detection_controller.run_comprehensive_detection_with_dialog
        )
        self._frame_extractor.auto_btn.clicked.connect(
            self._auto_detection_controller.run_frame_detection
        )
        self._frame_extractor.auto_margins_btn.clicked.connect(
            self._auto_detection_controller.run_margin_detection
        )
        self._frame_extractor.auto_spacing_btn.clicked.connect(
            self._auto_detection_controller.run_spacing_detection
        )

    def _connect_playback_controls_signals(self) -> None:
        """Connect PlaybackControls signals to controllers/model."""
        # Direct connections to animation controller
        self._playback_controls.playPauseClicked.connect(self._animation_controller.toggle_playback)
        self._playback_controls.fpsChanged.connect(self._animation_controller.set_fps)
        self._playback_controls.loopToggled.connect(self._animation_controller.set_loop_mode)

        # Direct connections to sprite model
        self._playback_controls.frameChanged.connect(self._sprite_model.set_current_frame)
        self._playback_controls.prevFrameClicked.connect(self._sprite_model.previous_frame)
        self._playback_controls.nextFrameClicked.connect(self._sprite_model.next_frame)

    def _connect_grid_view_signals(self) -> None:
        """Connect AnimationGridView signals to segment controller."""
        if not self._grid_view:
            return

        # Frame selection feedback
        self._grid_view.frameSelected.connect(
            lambda idx: self._status_manager.show_message(f"Selected frame {idx}")
            if self._status_manager
            else None
        )

        # Frame preview (double-click)
        self._grid_view.framePreviewRequested.connect(self._on_grid_frame_preview)

        # Segment operations -> segment controller
        self._grid_view.segmentCreated.connect(self._segment_controller.create_segment)
        self._grid_view.segmentDeleted.connect(self._segment_controller.delete_segment)
        self._grid_view.segmentRenameRequested.connect(self._segment_controller.rename_segment)
        self._grid_view.segmentSelected.connect(self._segment_controller.select_segment)
        self._grid_view.segmentPreviewRequested.connect(self._segment_controller.preview_segment)

        # Note: exportRequested is already connected internally by AnimationSegmentController

    def _connect_action_callbacks(self) -> None:
        """Connect QAction triggers to handlers."""
        # Export actions
        if "file_export_frames" in self._actions:
            self._actions["file_export_frames"].triggered.connect(self._on_export_frames_requested)
        if "file_export_current" in self._actions:
            self._actions["file_export_current"].triggered.connect(
                self._on_export_current_frame_requested
            )
        if "toolbar_export" in self._actions:
            self._actions["toolbar_export"].triggered.connect(self._on_export_frames_requested)

        # View actions (need canvas)
        if "view_zoom_fit" in self._actions:
            self._actions["view_zoom_fit"].triggered.connect(self._canvas.fit_to_window)
        if "view_zoom_reset" in self._actions:
            self._actions["view_zoom_reset"].triggered.connect(self._canvas.reset_view)

        # Animation actions (need animation_controller and sprite_model)
        if "animation_toggle" in self._actions:
            self._actions["animation_toggle"].triggered.connect(
                self._animation_controller.toggle_playback
            )
        if "animation_prev_frame" in self._actions:
            self._actions["animation_prev_frame"].triggered.connect(
                self._sprite_model.previous_frame
            )
        if "animation_next_frame" in self._actions:
            self._actions["animation_next_frame"].triggered.connect(self._sprite_model.next_frame)
        if "animation_first_frame" in self._actions:
            self._actions["animation_first_frame"].triggered.connect(self._sprite_model.first_frame)
        if "animation_last_frame" in self._actions:
            self._actions["animation_last_frame"].triggered.connect(self._sprite_model.last_frame)


__all__ = ["SignalCoordinator"]
