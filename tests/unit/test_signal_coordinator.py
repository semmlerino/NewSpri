"""Unit tests for coordinators/signal_coordinator.py."""

from unittest.mock import MagicMock

import pytest


def create_mock_signal():
    """Create a mock Qt signal with connect/disconnect methods."""
    signal = MagicMock()
    signal.connect = MagicMock()
    signal.disconnect = MagicMock()
    return signal


@pytest.fixture
def mock_sprite_model():
    """Mock SpriteModel with all required signals."""
    model = MagicMock()
    model.frameChanged = create_mock_signal()
    model.dataLoaded = create_mock_signal()
    model.extractionCompleted = create_mock_signal()
    model.set_current_frame = MagicMock()
    model.previous_frame = MagicMock()
    model.next_frame = MagicMock()
    model.first_frame = MagicMock()
    model.last_frame = MagicMock()
    return model


@pytest.fixture
def mock_animation_controller():
    """Mock AnimationController with all required signals."""
    controller = MagicMock()
    controller.animationStarted = create_mock_signal()
    controller.animationPaused = create_mock_signal()
    controller.animationStopped = create_mock_signal()
    controller.animationCompleted = create_mock_signal()
    controller.errorOccurred = create_mock_signal()
    controller.statusChanged = create_mock_signal()
    controller.toggle_playback = MagicMock()
    controller.set_fps = MagicMock()
    controller.set_loop_mode = MagicMock()
    return controller


@pytest.fixture
def mock_auto_detection_controller():
    """Mock AutoDetectionController with all required signals."""
    controller = MagicMock()
    controller.frameSettingsDetected = create_mock_signal()
    controller.statusUpdate = create_mock_signal()
    controller.run_comprehensive_detection_with_dialog = MagicMock()
    controller.run_frame_detection = MagicMock()
    controller.run_margin_detection = MagicMock()
    controller.run_spacing_detection = MagicMock()
    return controller


@pytest.fixture
def mock_segment_controller():
    """Mock AnimationSegmentController."""
    controller = MagicMock()
    controller.create_segment = MagicMock()
    controller.delete_segment = MagicMock()
    controller.rename_segment = MagicMock()
    controller.select_segment = MagicMock()
    controller.preview_segment = MagicMock()
    return controller


@pytest.fixture
def mock_canvas():
    """Mock SpriteCanvas with all required signals."""
    canvas = MagicMock()
    canvas.zoomChanged = create_mock_signal()
    canvas.mouseMoved = create_mock_signal()
    canvas.fit_to_window = MagicMock()
    canvas.reset_view = MagicMock()
    return canvas


@pytest.fixture
def mock_playback_controls():
    """Mock PlaybackControls with all required signals."""
    controls = MagicMock()
    controls.playPauseClicked = create_mock_signal()
    controls.fpsChanged = create_mock_signal()
    controls.loopToggled = create_mock_signal()
    controls.frameChanged = create_mock_signal()
    controls.prevFrameClicked = create_mock_signal()
    controls.nextFrameClicked = create_mock_signal()
    return controls


@pytest.fixture
def mock_frame_extractor():
    """Mock FrameExtractor with all required signals and buttons."""
    extractor = MagicMock()
    extractor.settingsChanged = create_mock_signal()
    extractor.modeChangedEnum = create_mock_signal()

    # Mock auto-detection buttons
    extractor.comprehensive_auto_btn = MagicMock()
    extractor.comprehensive_auto_btn.clicked = create_mock_signal()
    extractor.auto_btn = MagicMock()
    extractor.auto_btn.clicked = create_mock_signal()
    extractor.auto_margins_btn = MagicMock()
    extractor.auto_margins_btn.clicked = create_mock_signal()
    extractor.auto_spacing_btn = MagicMock()
    extractor.auto_spacing_btn.clicked = create_mock_signal()

    return extractor


@pytest.fixture
def mock_grid_view():
    """Mock AnimationGridView with all required signals."""
    grid_view = MagicMock()
    grid_view.frameSelected = create_mock_signal()
    grid_view.framePreviewRequested = create_mock_signal()
    grid_view.segmentCreated = create_mock_signal()
    grid_view.segmentDeleted = create_mock_signal()
    grid_view.segmentRenameRequested = create_mock_signal()
    grid_view.segmentSelected = create_mock_signal()
    grid_view.segmentPreviewRequested = create_mock_signal()
    return grid_view


@pytest.fixture
def mock_status_manager():
    """Mock StatusBarManager."""
    manager = MagicMock()
    manager.show_message = MagicMock()
    manager.update_mouse_position = MagicMock()
    return manager


@pytest.fixture
def mock_segment_manager():
    """Mock AnimationSegmentManager."""
    return MagicMock()


@pytest.fixture
def mock_actions():
    """Mock actions dictionary with QAction mocks."""
    actions = {}
    action_names = [
        "file_export_frames",
        "file_export_current",
        "toolbar_export",
        "view_zoom_fit",
        "view_zoom_reset",
        "animation_toggle",
        "animation_prev_frame",
        "animation_next_frame",
        "animation_first_frame",
        "animation_last_frame",
    ]
    for name in action_names:
        action = MagicMock()
        action.triggered = create_mock_signal()
        actions[name] = action
    return actions


@pytest.fixture
def mock_handlers():
    """Mock handler callback functions."""
    return {
        "on_frame_changed": MagicMock(),
        "on_sprite_loaded": MagicMock(),
        "on_extraction_completed": MagicMock(),
        "on_playback_started": MagicMock(),
        "on_playback_paused": MagicMock(),
        "on_playback_stopped": MagicMock(),
        "on_playback_completed": MagicMock(),
        "on_animation_error": MagicMock(),
        "on_frame_settings_detected": MagicMock(),
        "on_extraction_mode_changed": MagicMock(),
        "on_update_frame_slicing": MagicMock(),
        "on_grid_frame_preview": MagicMock(),
        "on_export_frames_requested": MagicMock(),
        "on_export_current_frame_requested": MagicMock(),
        "on_zoom_changed": MagicMock(),
    }


@pytest.fixture
def signal_coordinator(
    mock_sprite_model,
    mock_animation_controller,
    mock_auto_detection_controller,
    mock_segment_controller,
    mock_canvas,
    mock_playback_controls,
    mock_frame_extractor,
    mock_grid_view,
    mock_status_manager,
    mock_segment_manager,
    mock_actions,
    mock_handlers,
):
    """Create a SignalCoordinator with all mocked dependencies."""
    from coordinators.signal_coordinator import SignalCoordinator

    coordinator = SignalCoordinator(
        sprite_model=mock_sprite_model,
        animation_controller=mock_animation_controller,
        auto_detection_controller=mock_auto_detection_controller,
        segment_controller=mock_segment_controller,
        canvas=mock_canvas,
        playback_controls=mock_playback_controls,
        frame_extractor=mock_frame_extractor,
        grid_view=mock_grid_view,
        status_manager=mock_status_manager,
        segment_manager=mock_segment_manager,
        actions=mock_actions,
        on_frame_changed=mock_handlers["on_frame_changed"],
        on_sprite_loaded=mock_handlers["on_sprite_loaded"],
        on_extraction_completed=mock_handlers["on_extraction_completed"],
        on_playback_started=mock_handlers["on_playback_started"],
        on_playback_paused=mock_handlers["on_playback_paused"],
        on_playback_stopped=mock_handlers["on_playback_stopped"],
        on_playback_completed=mock_handlers["on_playback_completed"],
        on_animation_error=mock_handlers["on_animation_error"],
        on_frame_settings_detected=mock_handlers["on_frame_settings_detected"],
        on_extraction_mode_changed=mock_handlers["on_extraction_mode_changed"],
        on_update_frame_slicing=mock_handlers["on_update_frame_slicing"],
        on_grid_frame_preview=mock_handlers["on_grid_frame_preview"],
        on_export_frames_requested=mock_handlers["on_export_frames_requested"],
        on_export_current_frame_requested=mock_handlers["on_export_current_frame_requested"],
        on_zoom_changed=mock_handlers["on_zoom_changed"],
    )

    return coordinator


class TestSignalCoordinatorConstruction:
    """Test SignalCoordinator construction."""

    def test_can_construct_with_all_mocked_params(self, signal_coordinator):
        """Coordinator can be constructed with all mocked parameters."""
        assert signal_coordinator is not None
        assert not signal_coordinator._connected

    def test_construction_with_none_grid_view(
        self,
        mock_sprite_model,
        mock_animation_controller,
        mock_auto_detection_controller,
        mock_segment_controller,
        mock_canvas,
        mock_playback_controls,
        mock_frame_extractor,
        mock_status_manager,
        mock_segment_manager,
        mock_actions,
        mock_handlers,
    ):
        """Coordinator can be constructed with grid_view=None."""
        from coordinators.signal_coordinator import SignalCoordinator

        coordinator = SignalCoordinator(
            sprite_model=mock_sprite_model,
            animation_controller=mock_animation_controller,
            auto_detection_controller=mock_auto_detection_controller,
            segment_controller=mock_segment_controller,
            canvas=mock_canvas,
            playback_controls=mock_playback_controls,
            frame_extractor=mock_frame_extractor,
            grid_view=None,
            status_manager=mock_status_manager,
            segment_manager=mock_segment_manager,
            actions=mock_actions,
            on_frame_changed=mock_handlers["on_frame_changed"],
            on_sprite_loaded=mock_handlers["on_sprite_loaded"],
            on_extraction_completed=mock_handlers["on_extraction_completed"],
            on_playback_started=mock_handlers["on_playback_started"],
            on_playback_paused=mock_handlers["on_playback_paused"],
            on_playback_stopped=mock_handlers["on_playback_stopped"],
            on_playback_completed=mock_handlers["on_playback_completed"],
            on_animation_error=mock_handlers["on_animation_error"],
            on_frame_settings_detected=mock_handlers["on_frame_settings_detected"],
            on_extraction_mode_changed=mock_handlers["on_extraction_mode_changed"],
            on_update_frame_slicing=mock_handlers["on_update_frame_slicing"],
            on_grid_frame_preview=mock_handlers["on_grid_frame_preview"],
            on_export_frames_requested=mock_handlers["on_export_frames_requested"],
            on_export_current_frame_requested=mock_handlers["on_export_current_frame_requested"],
            on_zoom_changed=mock_handlers["on_zoom_changed"],
        )

        assert coordinator is not None
        assert coordinator._grid_view is None

    def test_construction_with_none_status_manager(
        self,
        mock_sprite_model,
        mock_animation_controller,
        mock_auto_detection_controller,
        mock_segment_controller,
        mock_canvas,
        mock_playback_controls,
        mock_frame_extractor,
        mock_grid_view,
        mock_segment_manager,
        mock_actions,
        mock_handlers,
    ):
        """Coordinator can be constructed with status_manager=None."""
        from coordinators.signal_coordinator import SignalCoordinator

        coordinator = SignalCoordinator(
            sprite_model=mock_sprite_model,
            animation_controller=mock_animation_controller,
            auto_detection_controller=mock_auto_detection_controller,
            segment_controller=mock_segment_controller,
            canvas=mock_canvas,
            playback_controls=mock_playback_controls,
            frame_extractor=mock_frame_extractor,
            grid_view=mock_grid_view,
            status_manager=None,
            segment_manager=mock_segment_manager,
            actions=mock_actions,
            on_frame_changed=mock_handlers["on_frame_changed"],
            on_sprite_loaded=mock_handlers["on_sprite_loaded"],
            on_extraction_completed=mock_handlers["on_extraction_completed"],
            on_playback_started=mock_handlers["on_playback_started"],
            on_playback_paused=mock_handlers["on_playback_paused"],
            on_playback_stopped=mock_handlers["on_playback_stopped"],
            on_playback_completed=mock_handlers["on_playback_completed"],
            on_animation_error=mock_handlers["on_animation_error"],
            on_frame_settings_detected=mock_handlers["on_frame_settings_detected"],
            on_extraction_mode_changed=mock_handlers["on_extraction_mode_changed"],
            on_update_frame_slicing=mock_handlers["on_update_frame_slicing"],
            on_grid_frame_preview=mock_handlers["on_grid_frame_preview"],
            on_export_frames_requested=mock_handlers["on_export_frames_requested"],
            on_export_current_frame_requested=mock_handlers["on_export_current_frame_requested"],
            on_zoom_changed=mock_handlers["on_zoom_changed"],
        )

        assert coordinator is not None
        assert coordinator._status_manager is None


class TestConnectAll:
    """Test connect_all behavior."""

    def test_connect_all_sets_connected_flag(self, signal_coordinator):
        """connect_all sets _connected flag to True."""
        assert not signal_coordinator._connected
        signal_coordinator.connect_all()
        assert signal_coordinator._connected

    def test_connect_all_is_idempotent(self, signal_coordinator, mock_sprite_model):
        """Calling connect_all twice doesn't double-connect signals."""
        signal_coordinator.connect_all()
        first_call_count = mock_sprite_model.frameChanged.connect.call_count

        signal_coordinator.connect_all()
        second_call_count = mock_sprite_model.frameChanged.connect.call_count

        assert first_call_count == second_call_count


class TestDisconnectAll:
    """Test disconnect_all behavior."""

    def test_disconnect_all_clears_flag(self, signal_coordinator):
        """disconnect_all clears _connected flag."""
        signal_coordinator.connect_all()
        assert signal_coordinator._connected

        signal_coordinator.disconnect_all()
        assert not signal_coordinator._connected

    def test_disconnect_all_without_connect_is_safe(self, signal_coordinator):
        """disconnect_all is safe to call without prior connect_all."""
        assert not signal_coordinator._connected
        signal_coordinator.disconnect_all()
        assert not signal_coordinator._connected


class TestModelSignalConnections:
    """Test SpriteModel signal connections."""

    def test_model_frame_changed_connected(self, signal_coordinator, mock_sprite_model, mock_handlers):
        """SpriteModel.frameChanged is connected to handler."""
        signal_coordinator.connect_all()
        mock_sprite_model.frameChanged.connect.assert_called_once_with(
            mock_handlers["on_frame_changed"]
        )

    def test_model_data_loaded_connected(self, signal_coordinator, mock_sprite_model, mock_handlers):
        """SpriteModel.dataLoaded is connected to handler."""
        signal_coordinator.connect_all()
        mock_sprite_model.dataLoaded.connect.assert_called_once_with(
            mock_handlers["on_sprite_loaded"]
        )

    def test_model_extraction_completed_connected(
        self, signal_coordinator, mock_sprite_model, mock_handlers
    ):
        """SpriteModel.extractionCompleted is connected to handler."""
        signal_coordinator.connect_all()
        mock_sprite_model.extractionCompleted.connect.assert_called_once_with(
            mock_handlers["on_extraction_completed"]
        )


class TestAnimationControllerSignalConnections:
    """Test AnimationController signal connections."""

    def test_animation_started_connected(
        self, signal_coordinator, mock_animation_controller, mock_handlers
    ):
        """AnimationController.animationStarted is connected."""
        signal_coordinator.connect_all()
        mock_animation_controller.animationStarted.connect.assert_called_once_with(
            mock_handlers["on_playback_started"]
        )

    def test_animation_paused_connected(
        self, signal_coordinator, mock_animation_controller, mock_handlers
    ):
        """AnimationController.animationPaused is connected."""
        signal_coordinator.connect_all()
        mock_animation_controller.animationPaused.connect.assert_called_once_with(
            mock_handlers["on_playback_paused"]
        )

    def test_animation_stopped_connected(
        self, signal_coordinator, mock_animation_controller, mock_handlers
    ):
        """AnimationController.animationStopped is connected."""
        signal_coordinator.connect_all()
        mock_animation_controller.animationStopped.connect.assert_called_once_with(
            mock_handlers["on_playback_stopped"]
        )

    def test_animation_completed_connected(
        self, signal_coordinator, mock_animation_controller, mock_handlers
    ):
        """AnimationController.animationCompleted is connected."""
        signal_coordinator.connect_all()
        mock_animation_controller.animationCompleted.connect.assert_called_once_with(
            mock_handlers["on_playback_completed"]
        )

    def test_error_occurred_connected(
        self, signal_coordinator, mock_animation_controller, mock_handlers
    ):
        """AnimationController.errorOccurred is connected."""
        signal_coordinator.connect_all()
        mock_animation_controller.errorOccurred.connect.assert_called_once_with(
            mock_handlers["on_animation_error"]
        )

    def test_status_changed_connected_to_status_manager(
        self, signal_coordinator, mock_animation_controller, mock_status_manager
    ):
        """AnimationController.statusChanged is connected to status manager."""
        signal_coordinator.connect_all()
        mock_animation_controller.statusChanged.connect.assert_called_once_with(
            mock_status_manager.show_message
        )


class TestAutoDetectionSignalConnections:
    """Test AutoDetectionController signal connections."""

    def test_frame_settings_detected_connected(
        self, signal_coordinator, mock_auto_detection_controller, mock_handlers
    ):
        """AutoDetectionController.frameSettingsDetected is connected."""
        signal_coordinator.connect_all()
        mock_auto_detection_controller.frameSettingsDetected.connect.assert_called_once_with(
            mock_handlers["on_frame_settings_detected"]
        )

    def test_status_update_connected_to_status_manager(
        self, signal_coordinator, mock_auto_detection_controller, mock_status_manager
    ):
        """AutoDetectionController.statusUpdate is connected to status manager."""
        signal_coordinator.connect_all()
        mock_auto_detection_controller.statusUpdate.connect.assert_called_once_with(
            mock_status_manager.show_message
        )


class TestCanvasSignalConnections:
    """Test SpriteCanvas signal connections."""

    def test_zoom_changed_connected(self, signal_coordinator, mock_canvas, mock_handlers):
        """SpriteCanvas.zoomChanged is connected."""
        signal_coordinator.connect_all()
        mock_canvas.zoomChanged.connect.assert_called_once_with(mock_handlers["on_zoom_changed"])

    def test_mouse_moved_connected_to_status_manager(
        self, signal_coordinator, mock_canvas, mock_status_manager
    ):
        """SpriteCanvas.mouseMoved is connected to status manager."""
        signal_coordinator.connect_all()
        mock_canvas.mouseMoved.connect.assert_called_once_with(
            mock_status_manager.update_mouse_position
        )


class TestFrameExtractorSignalConnections:
    """Test FrameExtractor signal connections."""

    def test_settings_changed_connected(
        self, signal_coordinator, mock_frame_extractor, mock_handlers
    ):
        """FrameExtractor.settingsChanged is connected."""
        signal_coordinator.connect_all()
        mock_frame_extractor.settingsChanged.connect.assert_called_once_with(
            mock_handlers["on_update_frame_slicing"]
        )

    def test_mode_changed_connected(self, signal_coordinator, mock_frame_extractor, mock_handlers):
        """FrameExtractor.modeChangedEnum is connected when available."""
        signal_coordinator.connect_all()
        mock_frame_extractor.modeChangedEnum.connect.assert_called_once_with(
            mock_handlers["on_extraction_mode_changed"]
        )

    def test_comprehensive_auto_btn_connected(
        self, signal_coordinator, mock_frame_extractor, mock_auto_detection_controller
    ):
        """FrameExtractor comprehensive auto button is connected."""
        signal_coordinator.connect_all()
        mock_frame_extractor.comprehensive_auto_btn.clicked.connect.assert_called_once_with(
            mock_auto_detection_controller.run_comprehensive_detection_with_dialog
        )

    def test_auto_btn_connected(
        self, signal_coordinator, mock_frame_extractor, mock_auto_detection_controller
    ):
        """FrameExtractor auto button is connected."""
        signal_coordinator.connect_all()
        mock_frame_extractor.auto_btn.clicked.connect.assert_called_once_with(
            mock_auto_detection_controller.run_frame_detection
        )

    def test_auto_margins_btn_connected(
        self, signal_coordinator, mock_frame_extractor, mock_auto_detection_controller
    ):
        """FrameExtractor auto margins button is connected."""
        signal_coordinator.connect_all()
        mock_frame_extractor.auto_margins_btn.clicked.connect.assert_called_once_with(
            mock_auto_detection_controller.run_margin_detection
        )

    def test_auto_spacing_btn_connected(
        self, signal_coordinator, mock_frame_extractor, mock_auto_detection_controller
    ):
        """FrameExtractor auto spacing button is connected."""
        signal_coordinator.connect_all()
        mock_frame_extractor.auto_spacing_btn.clicked.connect.assert_called_once_with(
            mock_auto_detection_controller.run_spacing_detection
        )


class TestPlaybackControlsSignalConnections:
    """Test PlaybackControls signal connections."""

    def test_play_pause_clicked_connected(
        self, signal_coordinator, mock_playback_controls, mock_animation_controller
    ):
        """PlaybackControls.playPauseClicked is connected to animation controller."""
        signal_coordinator.connect_all()
        mock_playback_controls.playPauseClicked.connect.assert_called_once_with(
            mock_animation_controller.toggle_playback
        )

    def test_fps_changed_connected(
        self, signal_coordinator, mock_playback_controls, mock_animation_controller
    ):
        """PlaybackControls.fpsChanged is connected to animation controller."""
        signal_coordinator.connect_all()
        mock_playback_controls.fpsChanged.connect.assert_called_once_with(
            mock_animation_controller.set_fps
        )

    def test_loop_toggled_connected(
        self, signal_coordinator, mock_playback_controls, mock_animation_controller
    ):
        """PlaybackControls.loopToggled is connected to animation controller."""
        signal_coordinator.connect_all()
        mock_playback_controls.loopToggled.connect.assert_called_once_with(
            mock_animation_controller.set_loop_mode
        )

    def test_frame_changed_connected(
        self, signal_coordinator, mock_playback_controls, mock_sprite_model
    ):
        """PlaybackControls.frameChanged is connected to sprite model."""
        signal_coordinator.connect_all()
        mock_playback_controls.frameChanged.connect.assert_called_once_with(
            mock_sprite_model.set_current_frame
        )

    def test_prev_frame_clicked_connected(
        self, signal_coordinator, mock_playback_controls, mock_sprite_model
    ):
        """PlaybackControls.prevFrameClicked is connected to sprite model."""
        signal_coordinator.connect_all()
        mock_playback_controls.prevFrameClicked.connect.assert_called_once_with(
            mock_sprite_model.previous_frame
        )

    def test_next_frame_clicked_connected(
        self, signal_coordinator, mock_playback_controls, mock_sprite_model
    ):
        """PlaybackControls.nextFrameClicked is connected to sprite model."""
        signal_coordinator.connect_all()
        mock_playback_controls.nextFrameClicked.connect.assert_called_once_with(
            mock_sprite_model.next_frame
        )


class TestGridViewSignalConnections:
    """Test AnimationGridView signal connections."""

    def test_grid_view_none_handled_gracefully(
        self,
        mock_sprite_model,
        mock_animation_controller,
        mock_auto_detection_controller,
        mock_segment_controller,
        mock_canvas,
        mock_playback_controls,
        mock_frame_extractor,
        mock_status_manager,
        mock_segment_manager,
        mock_actions,
        mock_handlers,
    ):
        """Grid view connections are skipped when grid_view=None."""
        from coordinators.signal_coordinator import SignalCoordinator

        coordinator = SignalCoordinator(
            sprite_model=mock_sprite_model,
            animation_controller=mock_animation_controller,
            auto_detection_controller=mock_auto_detection_controller,
            segment_controller=mock_segment_controller,
            canvas=mock_canvas,
            playback_controls=mock_playback_controls,
            frame_extractor=mock_frame_extractor,
            grid_view=None,
            status_manager=mock_status_manager,
            segment_manager=mock_segment_manager,
            actions=mock_actions,
            on_frame_changed=mock_handlers["on_frame_changed"],
            on_sprite_loaded=mock_handlers["on_sprite_loaded"],
            on_extraction_completed=mock_handlers["on_extraction_completed"],
            on_playback_started=mock_handlers["on_playback_started"],
            on_playback_paused=mock_handlers["on_playback_paused"],
            on_playback_stopped=mock_handlers["on_playback_stopped"],
            on_playback_completed=mock_handlers["on_playback_completed"],
            on_animation_error=mock_handlers["on_animation_error"],
            on_frame_settings_detected=mock_handlers["on_frame_settings_detected"],
            on_extraction_mode_changed=mock_handlers["on_extraction_mode_changed"],
            on_update_frame_slicing=mock_handlers["on_update_frame_slicing"],
            on_grid_frame_preview=mock_handlers["on_grid_frame_preview"],
            on_export_frames_requested=mock_handlers["on_export_frames_requested"],
            on_export_current_frame_requested=mock_handlers["on_export_current_frame_requested"],
            on_zoom_changed=mock_handlers["on_zoom_changed"],
        )

        coordinator.connect_all()
        assert coordinator._connected

    def test_frame_selected_connected(self, signal_coordinator, mock_grid_view):
        """AnimationGridView.frameSelected is connected."""
        signal_coordinator.connect_all()
        mock_grid_view.frameSelected.connect.assert_called_once()

    def test_frame_preview_requested_connected(
        self, signal_coordinator, mock_grid_view, mock_handlers
    ):
        """AnimationGridView.framePreviewRequested is connected."""
        signal_coordinator.connect_all()
        mock_grid_view.framePreviewRequested.connect.assert_called_once_with(
            mock_handlers["on_grid_frame_preview"]
        )

    def test_segment_created_connected(
        self, signal_coordinator, mock_grid_view, mock_segment_controller
    ):
        """AnimationGridView.segmentCreated is connected to segment controller."""
        signal_coordinator.connect_all()
        mock_grid_view.segmentCreated.connect.assert_called_once_with(
            mock_segment_controller.create_segment
        )

    def test_segment_deleted_connected(
        self, signal_coordinator, mock_grid_view, mock_segment_controller
    ):
        """AnimationGridView.segmentDeleted is connected to segment controller."""
        signal_coordinator.connect_all()
        mock_grid_view.segmentDeleted.connect.assert_called_once_with(
            mock_segment_controller.delete_segment
        )

    def test_segment_rename_requested_connected(
        self, signal_coordinator, mock_grid_view, mock_segment_controller
    ):
        """AnimationGridView.segmentRenameRequested is connected to segment controller."""
        signal_coordinator.connect_all()
        mock_grid_view.segmentRenameRequested.connect.assert_called_once_with(
            mock_segment_controller.rename_segment
        )

    def test_segment_selected_connected(
        self, signal_coordinator, mock_grid_view, mock_segment_controller
    ):
        """AnimationGridView.segmentSelected is connected to segment controller."""
        signal_coordinator.connect_all()
        mock_grid_view.segmentSelected.connect.assert_called_once_with(
            mock_segment_controller.select_segment
        )

    def test_segment_preview_requested_connected(
        self, signal_coordinator, mock_grid_view, mock_segment_controller
    ):
        """AnimationGridView.segmentPreviewRequested is connected to segment controller."""
        signal_coordinator.connect_all()
        mock_grid_view.segmentPreviewRequested.connect.assert_called_once_with(
            mock_segment_controller.preview_segment
        )


class TestActionCallbackConnections:
    """Test QAction signal connections."""

    def test_file_export_frames_action_connected(
        self, signal_coordinator, mock_actions, mock_handlers
    ):
        """file_export_frames action is connected."""
        signal_coordinator.connect_all()
        mock_actions["file_export_frames"].triggered.connect.assert_called_once_with(
            mock_handlers["on_export_frames_requested"]
        )

    def test_file_export_current_action_connected(
        self, signal_coordinator, mock_actions, mock_handlers
    ):
        """file_export_current action is connected."""
        signal_coordinator.connect_all()
        mock_actions["file_export_current"].triggered.connect.assert_called_once_with(
            mock_handlers["on_export_current_frame_requested"]
        )

    def test_toolbar_export_action_connected(
        self, signal_coordinator, mock_actions, mock_handlers
    ):
        """toolbar_export action is connected."""
        signal_coordinator.connect_all()
        mock_actions["toolbar_export"].triggered.connect.assert_called_once_with(
            mock_handlers["on_export_frames_requested"]
        )

    def test_view_zoom_fit_action_connected(self, signal_coordinator, mock_actions, mock_canvas):
        """view_zoom_fit action is connected to canvas."""
        signal_coordinator.connect_all()
        mock_actions["view_zoom_fit"].triggered.connect.assert_called_once_with(
            mock_canvas.fit_to_window
        )

    def test_view_zoom_reset_action_connected(self, signal_coordinator, mock_actions, mock_canvas):
        """view_zoom_reset action is connected to canvas."""
        signal_coordinator.connect_all()
        mock_actions["view_zoom_reset"].triggered.connect.assert_called_once_with(
            mock_canvas.reset_view
        )

    def test_animation_toggle_action_connected(
        self, signal_coordinator, mock_actions, mock_animation_controller
    ):
        """animation_toggle action is connected to animation controller."""
        signal_coordinator.connect_all()
        mock_actions["animation_toggle"].triggered.connect.assert_called_once_with(
            mock_animation_controller.toggle_playback
        )

    def test_animation_prev_frame_action_connected(
        self, signal_coordinator, mock_actions, mock_sprite_model
    ):
        """animation_prev_frame action is connected to sprite model."""
        signal_coordinator.connect_all()
        mock_actions["animation_prev_frame"].triggered.connect.assert_called_once_with(
            mock_sprite_model.previous_frame
        )

    def test_animation_next_frame_action_connected(
        self, signal_coordinator, mock_actions, mock_sprite_model
    ):
        """animation_next_frame action is connected to sprite model."""
        signal_coordinator.connect_all()
        mock_actions["animation_next_frame"].triggered.connect.assert_called_once_with(
            mock_sprite_model.next_frame
        )

    def test_animation_first_frame_action_connected(
        self, signal_coordinator, mock_actions, mock_sprite_model
    ):
        """animation_first_frame action is connected to sprite model."""
        signal_coordinator.connect_all()
        mock_actions["animation_first_frame"].triggered.connect.assert_called_once_with(
            mock_sprite_model.first_frame
        )

    def test_animation_last_frame_action_connected(
        self, signal_coordinator, mock_actions, mock_sprite_model
    ):
        """animation_last_frame action is connected to sprite model."""
        signal_coordinator.connect_all()
        mock_actions["animation_last_frame"].triggered.connect.assert_called_once_with(
            mock_sprite_model.last_frame
        )


class TestOptionalComponents:
    """Test handling of optional components (None checks)."""

    def test_status_manager_none_skips_connections(
        self,
        mock_sprite_model,
        mock_animation_controller,
        mock_auto_detection_controller,
        mock_segment_controller,
        mock_canvas,
        mock_playback_controls,
        mock_frame_extractor,
        mock_grid_view,
        mock_segment_manager,
        mock_actions,
        mock_handlers,
    ):
        """When status_manager is None, status-related connections are skipped."""
        from coordinators.signal_coordinator import SignalCoordinator

        coordinator = SignalCoordinator(
            sprite_model=mock_sprite_model,
            animation_controller=mock_animation_controller,
            auto_detection_controller=mock_auto_detection_controller,
            segment_controller=mock_segment_controller,
            canvas=mock_canvas,
            playback_controls=mock_playback_controls,
            frame_extractor=mock_frame_extractor,
            grid_view=mock_grid_view,
            status_manager=None,
            segment_manager=mock_segment_manager,
            actions=mock_actions,
            on_frame_changed=mock_handlers["on_frame_changed"],
            on_sprite_loaded=mock_handlers["on_sprite_loaded"],
            on_extraction_completed=mock_handlers["on_extraction_completed"],
            on_playback_started=mock_handlers["on_playback_started"],
            on_playback_paused=mock_handlers["on_playback_paused"],
            on_playback_stopped=mock_handlers["on_playback_stopped"],
            on_playback_completed=mock_handlers["on_playback_completed"],
            on_animation_error=mock_handlers["on_animation_error"],
            on_frame_settings_detected=mock_handlers["on_frame_settings_detected"],
            on_extraction_mode_changed=mock_handlers["on_extraction_mode_changed"],
            on_update_frame_slicing=mock_handlers["on_update_frame_slicing"],
            on_grid_frame_preview=mock_handlers["on_grid_frame_preview"],
            on_export_frames_requested=mock_handlers["on_export_frames_requested"],
            on_export_current_frame_requested=mock_handlers["on_export_current_frame_requested"],
            on_zoom_changed=mock_handlers["on_zoom_changed"],
        )

        coordinator.connect_all()

        assert mock_animation_controller.statusChanged.connect.call_count == 0
        assert mock_auto_detection_controller.statusUpdate.connect.call_count == 0
        assert mock_canvas.mouseMoved.connect.call_count == 0
