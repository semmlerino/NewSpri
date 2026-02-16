"""
Tests for ExportCoordinator.

Tests progress dialog lifecycle management, validation, and error handling
to ensure the dialog is always cleaned up properly.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QObject
from PySide6.QtGui import QImage

from core.export_coordinator import ExportCoordinator


@pytest.fixture
def mock_sprite_model():
    """Create a mock sprite model with frames."""
    model = MagicMock()
    # Create some dummy frames
    model.sprite_frames = [QImage(10, 10, QImage.Format.Format_ARGB32) for _ in range(5)]
    return model


@pytest.fixture
def mock_segment_manager():
    """Create a mock segment manager."""
    manager = MagicMock()
    # Mock segment
    segment = MagicMock()
    segment.name = "Walk"
    segment.start_frame = 0
    segment.end_frame = 3
    manager.get_all_segments.return_value = [segment]
    return manager


@pytest.fixture
def mock_exporter():
    """Create a mock frame exporter with signals."""
    exporter = MagicMock()
    # Create mock signals that support connect/disconnect
    exporter.exportProgress = MagicMock()
    exporter.exportProgress.connect = MagicMock()
    exporter.exportProgress.disconnect = MagicMock()
    exporter.exportFinished = MagicMock()
    exporter.exportFinished.connect = MagicMock()
    exporter.exportFinished.disconnect = MagicMock()
    exporter.exportError = MagicMock()
    exporter.exportError.connect = MagicMock()
    exporter.exportError.disconnect = MagicMock()
    exporter.export_frames = MagicMock(return_value=True)
    return exporter


@pytest.fixture
def basic_settings() -> dict[str, Any]:
    """Create basic export settings."""
    return {
        "output_dir": "/tmp/export",
        "base_name": "test",
        "format": "png",
        "mode": "individual",
        "scale_factor": 1.0,
    }


# -------------------------------------------------------------------------
# Validation Tests
# -------------------------------------------------------------------------


def test_validate_export_settings_missing_key(mock_sprite_model, mock_exporter):
    """Missing required settings returns False and shows error."""
    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    with patch.object(coordinator, "_show_error") as mock_error:
        result = coordinator._validate_export_settings({"output_dir": "/tmp"})

    assert result is False
    mock_error.assert_called_once()
    assert "Missing required setting" in mock_error.call_args[0][0]


def test_validate_export_settings_no_frames(mock_exporter):
    """No frames available returns False and shows error."""
    model = MagicMock()
    model.sprite_frames = []
    coordinator = ExportCoordinator(model, None, mock_exporter)

    settings = {
        "output_dir": "/tmp",
        "base_name": "test",
        "format": "png",
        "mode": "individual",
        "scale_factor": 1.0,
    }

    with patch.object(coordinator, "_show_error") as mock_error:
        result = coordinator._validate_export_settings(settings)

    assert result is False
    mock_error.assert_called_once_with("No frames available to export.")


def test_validate_export_settings_valid(mock_sprite_model, mock_exporter, basic_settings):
    """Valid settings returns True."""
    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    result = coordinator._validate_export_settings(basic_settings)

    assert result is True


# -------------------------------------------------------------------------
# Mode Precondition Tests
# -------------------------------------------------------------------------


def test_validate_mode_preconditions_segments_no_manager(
    mock_sprite_model, mock_exporter, basic_settings
):
    """segments_sheet mode with no segment_manager returns error."""
    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    settings = basic_settings.copy()
    settings["mode"] = "segments_sheet"

    valid, message = coordinator._validate_mode_preconditions(settings)

    assert valid is False
    assert message == "Segment manager not available."


def test_validate_mode_preconditions_segments_no_segments(
    mock_sprite_model, mock_exporter, basic_settings
):
    """segments_sheet mode with no segments returns error."""
    manager = MagicMock()
    manager.get_all_segments.return_value = []
    coordinator = ExportCoordinator(mock_sprite_model, manager, mock_exporter)

    settings = basic_settings.copy()
    settings["mode"] = "segments_sheet"

    valid, message = coordinator._validate_mode_preconditions(settings)

    assert valid is False
    assert message == "No animation segments defined."


def test_validate_mode_preconditions_selected_empty_indices(
    mock_sprite_model, mock_exporter, basic_settings
):
    """Mode with empty selected_indices returns error."""
    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    settings = basic_settings.copy()
    settings["selected_indices"] = []

    valid, message = coordinator._validate_mode_preconditions(settings)

    # Empty list is valid - precondition only fails if indices exist but are all invalid
    assert valid is True


def test_validate_mode_preconditions_selected_invalid_indices(
    mock_sprite_model, mock_exporter, basic_settings
):
    """Mode with all invalid selected_indices returns error."""
    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    settings = basic_settings.copy()
    # Model has 5 frames, indices 10, 20 are invalid
    settings["selected_indices"] = [10, 20]

    valid, message = coordinator._validate_mode_preconditions(settings)

    assert valid is False
    assert message == "No valid frames selected for export."


def test_validate_mode_preconditions_selected_some_valid_indices(
    mock_sprite_model, mock_exporter, basic_settings
):
    """Mode with some valid selected_indices succeeds."""
    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    settings = basic_settings.copy()
    # Model has 5 frames, indices 1, 2 are valid
    settings["selected_indices"] = [1, 2, 10]

    valid, message = coordinator._validate_mode_preconditions(settings)

    assert valid is True
    assert message == ""


def test_validate_mode_preconditions_valid_settings(
    mock_sprite_model, mock_segment_manager, mock_exporter, basic_settings
):
    """Valid settings for all modes succeed."""
    coordinator = ExportCoordinator(mock_sprite_model, mock_segment_manager, mock_exporter)

    # Test individual mode
    valid, message = coordinator._validate_mode_preconditions(basic_settings)
    assert valid is True
    assert message == ""

    # Test segments_sheet mode
    settings = basic_settings.copy()
    settings["mode"] = "segments_sheet"
    valid, message = coordinator._validate_mode_preconditions(settings)
    assert valid is True
    assert message == ""


# -------------------------------------------------------------------------
# Progress Dialog Lifecycle Tests
# -------------------------------------------------------------------------


@patch("core.export_coordinator.ExportProgressDialog")
def test_handle_export_request_no_dialog_on_validation_failure(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """Failed validation does not create progress dialog."""
    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    # Invalid settings (missing keys)
    with patch.object(coordinator, "_show_error"):
        coordinator.handle_export_request({"output_dir": "/tmp"})

    # Dialog should not be created
    mock_dialog_class.assert_not_called()


@patch("core.export_coordinator.ExportProgressDialog")
def test_handle_export_request_no_dialog_on_precondition_failure(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """Failed mode preconditions do not create progress dialog."""
    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    settings = basic_settings.copy()
    settings["mode"] = "segments_sheet"

    with patch.object(coordinator, "_show_warning"):
        coordinator.handle_export_request(settings)

    # Dialog should not be created
    mock_dialog_class.assert_not_called()


@patch("core.export_coordinator.ExportProgressDialog")
def test_handle_export_request_creates_dialog_on_valid_settings(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """Valid settings create progress dialog."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    coordinator.handle_export_request(basic_settings)

    # Dialog should be created
    mock_dialog_class.assert_called_once()
    mock_dialog.show.assert_called_once()


@patch("core.export_coordinator.ExportProgressDialog")
def test_handle_export_request_cleanup_on_success(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """Successful export cleans up progress dialog."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    coordinator.handle_export_request(basic_settings)

    # Simulate export completion
    with patch("core.export_coordinator.QMessageBox"):
        coordinator._on_export_finished(True, "Export complete")

    # Dialog should be cleaned up
    assert coordinator._progress_dialog is None
    mock_dialog.close.assert_called_once()


@patch("core.export_coordinator.ExportProgressDialog")
def test_handle_export_request_cleanup_on_error(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """Export error cleans up progress dialog."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    coordinator.handle_export_request(basic_settings)

    # Simulate export error
    with patch("core.export_coordinator.QMessageBox"):
        coordinator._on_export_error("Export failed")

    # Dialog should be cleaned up
    assert coordinator._progress_dialog is None
    mock_dialog.close.assert_called_once()


@patch("core.export_coordinator.ExportProgressDialog")
def test_cleanup_progress_dialog_idempotent(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """Calling cleanup twice does not crash."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    coordinator.handle_export_request(basic_settings)

    # Clean up once
    coordinator._cleanup_progress_dialog()
    assert coordinator._progress_dialog is None

    # Clean up again - should not crash
    coordinator._cleanup_progress_dialog()
    assert coordinator._progress_dialog is None


@patch("core.export_coordinator.ExportProgressDialog")
def test_cleanup_handles_disconnection_errors(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """Cleanup handles RuntimeError when signals already disconnected."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    # Make disconnect raise RuntimeError
    mock_exporter.exportProgress.disconnect.side_effect = RuntimeError("Already disconnected")

    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    coordinator.handle_export_request(basic_settings)

    # Cleanup should handle the error gracefully
    coordinator._cleanup_progress_dialog()
    assert coordinator._progress_dialog is None


# -------------------------------------------------------------------------
# Exception Safety Test
# -------------------------------------------------------------------------


@patch("core.export_coordinator.ExportProgressDialog")
def test_handle_export_request_cleanup_on_unexpected_exception(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """Unexpected exception in export method still cleans up dialog."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    # Make export_frames raise an exception
    mock_exporter.export_frames.side_effect = ValueError("Unexpected error")

    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    # Should raise the exception but still clean up
    with pytest.raises(ValueError, match="Unexpected error"):
        coordinator.handle_export_request(basic_settings)

    # Dialog should be cleaned up despite exception
    assert coordinator._progress_dialog is None
    mock_dialog.close.assert_called_once()


# -------------------------------------------------------------------------
# Export Logic Tests
# -------------------------------------------------------------------------


@patch("core.export_coordinator.ExportProgressDialog")
def test_export_frames_calls_exporter(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """_export_frames calls exporter with correct arguments."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    coordinator.handle_export_request(basic_settings)

    # Verify exporter was called
    mock_exporter.export_frames.assert_called_once()
    call_kwargs = mock_exporter.export_frames.call_args[1]
    assert call_kwargs["output_dir"] == "/tmp/export"
    assert call_kwargs["base_name"] == "test"
    assert call_kwargs["format"] == "png"
    assert call_kwargs["mode"] == "individual"
    assert call_kwargs["scale_factor"] == 1.0


@patch("core.export_coordinator.ExportProgressDialog")
def test_export_segments_per_row_calls_exporter(
    mock_dialog_class, mock_sprite_model, mock_segment_manager, mock_exporter, basic_settings
):
    """_export_segments_per_row calls exporter with segment info."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    coordinator = ExportCoordinator(mock_sprite_model, mock_segment_manager, mock_exporter)

    settings = basic_settings.copy()
    settings["mode"] = "segments_sheet"

    coordinator.handle_export_request(settings)

    # Verify exporter was called with segment info
    mock_exporter.export_frames.assert_called_once()
    call_kwargs = mock_exporter.export_frames.call_args[1]
    assert call_kwargs["mode"] == "segments_sheet"
    assert "segment_info" in call_kwargs
    segment_info = call_kwargs["segment_info"]
    assert len(segment_info) == 1
    assert segment_info[0]["name"] == "Walk"


@patch("core.export_coordinator.ExportProgressDialog")
def test_export_frames_with_selected_indices(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """_export_frames handles selected_indices correctly."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    settings = basic_settings.copy()
    settings["selected_indices"] = [1, 2]

    coordinator.handle_export_request(settings)

    # Verify mode changed to individual and indices passed
    mock_exporter.export_frames.assert_called_once()
    call_kwargs = mock_exporter.export_frames.call_args[1]
    assert call_kwargs["mode"] == "individual"
    assert call_kwargs["selected_indices"] == [1, 2]


@patch("core.export_coordinator.ExportProgressDialog")
@patch("core.export_coordinator.QMessageBox")
def test_export_frames_shows_info_on_invalid_indices(
    mock_messagebox, mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """_export_frames shows info when some indices are invalid."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    settings = basic_settings.copy()
    # Model has 5 frames, index 10 is invalid
    settings["selected_indices"] = [1, 2, 10]

    coordinator.handle_export_request(settings)

    # Info message should be shown
    mock_messagebox.information.assert_called_once()
    args = mock_messagebox.information.call_args[0]
    assert "2 frames" in args[2]  # message text
    assert "1 invalid" in args[2]


@patch("core.export_coordinator.ExportProgressDialog")
def test_export_frames_export_failure_shows_error(
    mock_dialog_class, mock_sprite_model, mock_exporter, basic_settings
):
    """_export_frames shows error when export_frames returns False."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    mock_exporter.export_frames.return_value = False

    coordinator = ExportCoordinator(mock_sprite_model, None, mock_exporter)

    with patch.object(coordinator, "_show_error") as mock_error:
        coordinator.handle_export_request(basic_settings)

    mock_error.assert_called_once_with("Failed to start export.")


@patch("core.export_coordinator.ExportProgressDialog")
def test_export_segments_per_row_export_failure_shows_error(
    mock_dialog_class, mock_sprite_model, mock_segment_manager, mock_exporter, basic_settings
):
    """_export_segments_per_row shows error when export_frames returns False."""
    mock_dialog = MagicMock()
    mock_dialog.cancelled = MagicMock()
    mock_dialog.cancelled.connect = MagicMock()
    mock_dialog_class.return_value = mock_dialog

    mock_exporter.export_frames.return_value = False

    coordinator = ExportCoordinator(mock_sprite_model, mock_segment_manager, mock_exporter)

    settings = basic_settings.copy()
    settings["mode"] = "segments_sheet"

    with patch.object(coordinator, "_show_error") as mock_error:
        coordinator.handle_export_request(settings)

    mock_error.assert_called_once_with("Failed to start segments per row export.")
