"""
Signal Coordinator - centralized signal connection management.

Extracts all inter-component signal wiring from SpriteViewer into a
single, self-documenting class. Makes signal dependencies explicit
and simplifies adding new component connections.
"""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject

if TYPE_CHECKING:
    from PySide6.QtGui import QAction

    from core import AnimationController, AnimationSegmentController, AutoDetectionController
    from sprite_model import SpriteModel
    from ui import (
        AnimationGridView,
        EnhancedStatusBar,
        FrameExtractor,
        PlaybackControls,
        SpriteCanvas,
    )


logger = logging.getLogger(__name__)


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
        # Status bar
        status_bar: EnhancedStatusBar | None,
        # Actions dict
        actions: dict[str, QAction],
        # Handler callbacks (from SpriteViewer)
        on_frame_changed: object,
        on_sprite_loaded: object,
        on_extraction_completed: object,
        on_playback_started: object,
        on_playback_paused: object,
        on_playback_ended: object,
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
        self._status_bar = status_bar
        self._actions = actions

        # Store handler callbacks
        self._on_frame_changed = on_frame_changed
        self._on_sprite_loaded = on_sprite_loaded
        self._on_extraction_completed = on_extraction_completed
        self._on_playback_started = on_playback_started
        self._on_playback_paused = on_playback_paused
        self._on_playback_ended = on_playback_ended
        self._on_animation_error = on_animation_error
        self._on_frame_settings_detected = on_frame_settings_detected
        self._on_extraction_mode_changed = on_extraction_mode_changed
        self._on_update_frame_slicing = on_update_frame_slicing
        self._on_grid_frame_preview = on_grid_frame_preview
        self._on_export_frames_requested = on_export_frames_requested
        self._on_export_current_frame_requested = on_export_current_frame_requested
        self._on_zoom_changed = on_zoom_changed

        self._connected = False
        self._connections: list[tuple[Any, Any]] = []

    def connect_all(self) -> None:
        """Connect all inter-component signals."""
        if self._connected:
            return

        self._connect_model_signals()
        self._connect_animation_controller_signals()
        self._connect_auto_detection_signals()
        self._connect_segment_controller_signals()
        self._connect_canvas_signals()
        self._connect_frame_extractor_signals()
        self._connect_playback_controls_signals()
        self._connect_grid_view_signals()
        self._connect_action_callbacks()

        self._connected = True

    def disconnect_all(self) -> None:
        """Disconnect all signal-slot connections created by this coordinator."""
        if not self._connected and not self._connections:
            return

        for signal, slot in reversed(self._connections):
            with contextlib.suppress(RuntimeError, TypeError):
                signal.disconnect(slot)
        self._connections.clear()
        self._connected = False

    def _connect(self, signal: Any, slot: Any) -> None:
        """Connect a Qt signal and remember the exact slot for later disconnection."""
        signal.connect(slot)
        self._connections.append((signal, slot))

    # =========================================================================
    # SIGNAL CONNECTION GROUPS
    # =========================================================================

    def _connect_model_signals(self) -> None:
        """Connect SpriteModel signals to handlers."""
        self._connect(self._sprite_model.frameChanged, self._on_frame_changed)
        self._connect(self._sprite_model.dataLoaded, self._on_sprite_loaded)
        self._connect(self._sprite_model.extractionCompleted, self._on_extraction_completed)

    def _connect_animation_controller_signals(self) -> None:
        """Connect AnimationController signals to handlers."""
        self._connect(self._animation_controller.animationStarted, self._on_playback_started)
        self._connect(self._animation_controller.animationPaused, self._on_playback_paused)
        self._connect(self._animation_controller.animationStopped, self._on_playback_ended)
        self._connect(self._animation_controller.animationCompleted, self._on_playback_ended)
        self._connect(self._animation_controller.errorOccurred, self._on_animation_error)

        if self._status_bar is not None:
            self._connect(self._animation_controller.statusChanged, self._status_bar.show_message)

    def _connect_auto_detection_signals(self) -> None:
        """Connect AutoDetectionController signals to handlers."""
        self._connect(
            self._auto_detection_controller.frameSettingsDetected,
            self._on_frame_settings_detected,
        )
        self._connect(
            self._auto_detection_controller.marginSettingsDetected,
            self._on_margin_settings_detected,
        )
        self._connect(
            self._auto_detection_controller.spacingSettingsDetected,
            self._on_spacing_settings_detected,
        )
        self._connect(
            self._auto_detection_controller.buttonConfidenceUpdate,
            self._frame_extractor.update_auto_button_confidence,
        )

        def log_detection_failed(wf: str, msg: str) -> None:
            logger.warning("Detection failed (%s): %s", wf, msg)

        self._connect(self._auto_detection_controller.detectionFailed, log_detection_failed)
        self._connect(
            self._auto_detection_controller.detectionResultsReady,
            self._on_detection_results_ready,
        )

        if self._status_bar is not None:
            status_bar = self._status_bar
            self._connect(
                self._auto_detection_controller.statusUpdate,
                status_bar.show_message,
            )

            def show_detection_failed(_wf: str, msg: str) -> None:
                status_bar.show_message(f"Detection failed: {msg}")

            self._connect(self._auto_detection_controller.detectionFailed, show_detection_failed)

    def _on_margin_settings_detected(self, offset_x: int, offset_y: int) -> None:
        """Update margin spin boxes when auto-detection finds margin values."""
        self._frame_extractor.set_offset(offset_x, offset_y)

    def _on_spacing_settings_detected(self, spacing_x: int, spacing_y: int) -> None:
        """Update spacing spin boxes when auto-detection finds spacing values."""
        self._frame_extractor.set_spacing(spacing_x, spacing_y)

    def _on_detection_results_ready(self, success: bool, summary: str, details: str) -> None:
        """Show detection results dialog."""
        from PySide6.QtWidgets import QMessageBox

        dialog = QMessageBox()
        dialog.setWindowTitle("Comprehensive Auto-Detection Results")
        dialog.setIcon(QMessageBox.Icon.Information if success else QMessageBox.Icon.Warning)
        dialog.setText(summary)
        dialog.setDetailedText(details)
        dialog.exec()

    def _connect_canvas_signals(self) -> None:
        """Connect SpriteCanvas signals to handlers."""
        self._connect(self._canvas.zoomChanged, self._on_zoom_changed)

        if self._status_bar is not None:
            self._connect(self._canvas.mouseMoved, self._status_bar.update_mouse_position)

    def _connect_frame_extractor_signals(self) -> None:
        """Connect FrameExtractor signals to handlers."""
        self._connect(self._frame_extractor.settingsChanged, self._on_update_frame_slicing)
        self._connect(self._frame_extractor.modeChangedEnum, self._on_extraction_mode_changed)

        # Auto-detect button connections
        self._connect(
            self._frame_extractor.comprehensive_auto_btn.clicked,
            self._auto_detection_controller.run_comprehensive_detection_with_dialog,
        )
        self._connect(
            self._frame_extractor.auto_btn.clicked,
            self._auto_detection_controller.run_frame_detection,
        )
        self._connect(
            self._frame_extractor.auto_margins_btn.clicked,
            self._auto_detection_controller.run_margin_detection,
        )
        self._connect(
            self._frame_extractor.auto_spacing_btn.clicked,
            self._auto_detection_controller.run_spacing_detection,
        )

    def _connect_playback_controls_signals(self) -> None:
        """Connect PlaybackControls signals to controllers/model."""
        # Direct connections to animation controller
        self._connect(
            self._playback_controls.playPauseClicked, self._animation_controller.toggle_playback
        )
        self._connect(self._playback_controls.fpsChanged, self._animation_controller.set_fps)
        self._connect(self._playback_controls.loopToggled, self._animation_controller.set_loop_mode)

        # Direct connections to sprite model
        self._connect(self._playback_controls.frameChanged, self._sprite_model.set_current_frame)
        self._connect(self._playback_controls.prevFrameClicked, self._sprite_model.previous_frame)
        self._connect(self._playback_controls.nextFrameClicked, self._sprite_model.next_frame)

    def _connect_grid_view_signals(self) -> None:
        """Connect AnimationGridView signals to segment controller."""
        if not self._grid_view:
            return

        # Frame selection feedback
        def show_selected_frame(idx: int) -> None:
            if self._status_bar:
                self._status_bar.show_message(f"Selected frame {idx}")

        self._connect(self._grid_view.frameSelected, show_selected_frame)

        # Frame preview (double-click)
        self._connect(self._grid_view.framePreviewRequested, self._on_grid_frame_preview)

        # Segment operations -> segment controller
        self._connect(self._grid_view.segmentCreated, self._segment_controller.create_segment)
        self._connect(self._grid_view.segmentDeleted, self._segment_controller.delete_segment)
        self._connect(
            self._grid_view.segmentRenameRequested, self._segment_controller.rename_segment
        )
        self._connect(self._grid_view.segmentSelected, self._segment_controller.select_segment)
        self._connect(
            self._grid_view.segmentPreviewRequested, self._segment_controller.preview_segment
        )

        # Note: exportRequested is already connected internally by AnimationSegmentController

    def _connect_segment_controller_signals(self) -> None:
        """Forward segment controller status messages to the status bar."""
        if self._status_bar is not None:
            self._connect(self._segment_controller.statusMessage, self._status_bar.show_message)

    def _connect_action_callbacks(self) -> None:
        """Connect QAction triggers to handlers."""
        # Export actions
        if "file_export_frames" in self._actions:
            self._connect(
                self._actions["file_export_frames"].triggered, self._on_export_frames_requested
            )
        if "file_export_current" in self._actions:
            self._connect(
                self._actions["file_export_current"].triggered,
                self._on_export_current_frame_requested,
            )
        if "toolbar_export" in self._actions:
            self._connect(
                self._actions["toolbar_export"].triggered, self._on_export_frames_requested
            )

        # View actions (need canvas)
        if "view_zoom_fit" in self._actions:
            self._connect(self._actions["view_zoom_fit"].triggered, self._canvas.fit_to_window)
        if "view_zoom_reset" in self._actions:
            self._connect(self._actions["view_zoom_reset"].triggered, self._canvas.reset_view)

        # Animation actions (need animation_controller and sprite_model)
        if "animation_toggle" in self._actions:
            self._connect(
                self._actions["animation_toggle"].triggered,
                self._animation_controller.toggle_playback,
            )
        if "animation_prev_frame" in self._actions:
            self._connect(
                self._actions["animation_prev_frame"].triggered,
                self._sprite_model.previous_frame,
            )
        if "animation_next_frame" in self._actions:
            self._connect(
                self._actions["animation_next_frame"].triggered, self._sprite_model.next_frame
            )
        if "animation_first_frame" in self._actions:
            self._connect(
                self._actions["animation_first_frame"].triggered, self._sprite_model.first_frame
            )
        if "animation_last_frame" in self._actions:
            self._connect(
                self._actions["animation_last_frame"].triggered, self._sprite_model.last_frame
            )


__all__ = ["SignalCoordinator"]
