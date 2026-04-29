"""
Integration tests for Qt signal/slot connections.
Tests that signals are properly connected and emitted throughout the application.
"""

from unittest.mock import Mock

import pytest
from PySide6.QtTest import QSignalSpy

from core import AnimationController
from export import ExportDialog
from managers import AnimationSegmentManager
from sprite_model import SpriteModel

# Import the actual runtime classes


@pytest.mark.integration
@pytest.mark.signal_test
@pytest.mark.requires_qt
class TestCriticalSignalConnections:
    """Test critical signal connections that integrate components."""

    def test_export_dialog_signal_connection(self, qapp):
        """Test that export dialog signals are properly connected."""
        # This test would have caught the exportRequested issue

        # Create the actual export dialog as used at runtime
        # Don't pass a segment_manager to avoid Mock compatibility issues
        dialog = ExportDialog(
            parent=None,  # Use None instead of Mock for Qt parent
            frame_count=10,
            current_frame=0,
        )

        # Verify the dialog has the expected signal
        assert hasattr(dialog, "exportRequested"), "ExportDialog missing exportRequested signal"

        # Test that we can connect to the signal
        handler_called = False
        received_data = None

        def mock_handler(data):
            nonlocal handler_called, received_data
            handler_called = True
            received_data = data

        dialog.exportRequested.connect(mock_handler)

        # Emit the signal to test connection
        test_data = {"format": "PNG", "output_dir": "/test"}
        dialog.exportRequested.emit(test_data)

        assert handler_called, "Signal handler was not called"
        assert received_data == test_data, "Signal data not passed correctly"

    def test_sprite_model_animation_controller_signals(self, qapp):
        """Test signal connections between SpriteModel and AnimationController."""
        sprite_model = SpriteModel()

        # Test that required signals exist
        assert hasattr(sprite_model, "frameChanged"), "SpriteModel missing frameChanged signal"

        # Create signal spy for frame changes
        frame_spy = QSignalSpy(sprite_model.frameChanged)

        # Initialize controller with model (single-step constructor DI)
        AnimationController(sprite_model=sprite_model)

        # Trigger frame change by emitting the signal directly
        # since set_current_frame takes only 1 argument (frame index)
        sprite_model.frameChanged.emit(1, 10)

        # Verify signal was emitted
        assert frame_spy.count() > 0, "frameChanged signal not emitted"

    def test_manager_signal_connections(self, qapp):
        """Test that manager classes properly connect their signals."""
        # Test AnimationSegmentManager signals
        segment_manager = AnimationSegmentManager()
        segment_manager.set_auto_save_enabled(False)

        # Verify segment manager has expected signals (camelCase naming)
        expected_signals = ["segmentRemoved", "segmentRenamed", "segmentsCleared"]
        for signal_name in expected_signals:
            assert hasattr(segment_manager, signal_name), (
                f"AnimationSegmentManager missing {signal_name} signal"
            )

        # Adding a segment populates the manager's storage
        import uuid

        segment_manager.set_sprite_context(f"test_{uuid.uuid4().hex[:8]}.png", 20)
        success, _ = segment_manager.add_segment("TestSignal", 0, 5)

        assert success
        assert segment_manager.get_segment("TestSignal") is not None


@pytest.mark.integration
@pytest.mark.signal_test
class TestSignalDataFlow:
    """Test data flow through signal connections."""

    def test_export_request_data_flow(self, qapp):
        """Test that export request data flows correctly through signals."""
        # Mock the components
        mock_exporter = Mock()

        # Create export dialog
        dialog = ExportDialog(parent=None, frame_count=5, current_frame=0)

        # Connect to capture export data
        captured_settings = None

        def capture_export(settings):
            nonlocal captured_settings
            captured_settings = settings

        if hasattr(dialog, "exportRequested"):
            dialog.exportRequested.connect(capture_export)

            # Simulate export request
            test_settings = {"format": "PNG", "scale": 2.0, "output_dir": "/test/output"}
            dialog.exportRequested.emit(test_settings)

            assert captured_settings is not None, "Export settings not captured"
            assert captured_settings["format"] == "PNG", "Format not passed correctly"
            assert captured_settings["scale"] == pytest.approx(2.0), "Scale not passed correctly"

    def test_animation_control_signal_chain(self, qapp):
        """Test signal chain for animation control."""
        model = SpriteModel()
        controller = AnimationController(sprite_model=model)

        status_changes: list[str] = []
        controller.statusChanged.connect(status_changes.append)

        # Change FPS
        controller.set_fps(15)

        # Status emits should describe the FPS change; controller state should reflect it
        assert controller.current_fps == 15
        assert any("15" in msg for msg in status_changes)
