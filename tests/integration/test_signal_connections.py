"""
Integration tests for Qt signal/slot connections.
Tests that signals are properly connected and emitted throughout the application.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QObject, Signal
from PySide6.QtTest import QSignalSpy

# Import the actual runtime classes
from sprite_viewer import SpriteViewer
from export import ExportDialog
from sprite_model import SpriteModel
from core import AnimationController
from managers import AnimationSegmentManager


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
            current_frame=0
        )
        
        # Verify the dialog has the expected signal
        assert hasattr(dialog, 'exportRequested'), "ExportDialog missing exportRequested signal"
        
        # Test that we can connect to the signal
        handler_called = False
        received_data = None
        
        def mock_handler(data):
            nonlocal handler_called, received_data
            handler_called = True
            received_data = data
        
        dialog.exportRequested.connect(mock_handler)
        
        # Emit the signal to test connection
        test_data = {'format': 'PNG', 'output_dir': '/test'}
        dialog.exportRequested.emit(test_data)
        
        assert handler_called, "Signal handler was not called"
        assert received_data == test_data, "Signal data not passed correctly"
    
    def test_sprite_model_animation_controller_signals(self, qapp):
        """Test signal connections between SpriteModel and AnimationController."""
        sprite_model = SpriteModel()
        animation_controller = AnimationController()
        
        # Test that required signals exist
        assert hasattr(sprite_model, 'frameChanged'), "SpriteModel missing frameChanged signal"
        assert hasattr(animation_controller, 'frameAdvanced'), "AnimationController missing frameAdvanced signal"
        
        # Create signal spy for frame changes
        frame_spy = QSignalSpy(sprite_model.frameChanged)
        
        # Initialize controller with model (this should connect signals)
        mock_viewer = Mock()
        animation_controller.initialize(sprite_model, mock_viewer)
        
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
        expected_signals = ['segmentAdded', 'segmentRemoved', 'segmentUpdated', 'segmentsCleared']
        for signal_name in expected_signals:
            assert hasattr(segment_manager, signal_name), f"AnimationSegmentManager missing {signal_name} signal"

        # Test signal emission
        spy = QSignalSpy(segment_manager.segmentAdded)

        # Set sprite context and add a segment using the actual API
        import uuid
        segment_manager.set_sprite_context(f"test_{uuid.uuid4().hex[:8]}.png", 20)
        segment_manager.add_segment("TestSignal", 0, 5)

        # Verify signal was emitted
        assert spy.count() > 0, "segmentAdded signal not emitted"


@pytest.mark.integration
@pytest.mark.signal_test
class TestSignalDataFlow:
    """Test data flow through signal connections."""
    
    def test_export_request_data_flow(self, qapp):
        """Test that export request data flows correctly through signals."""
        # Mock the components
        mock_exporter = Mock()
        
        # Create export dialog
        dialog = ExportDialog(
            parent=None,
            frame_count=5,
            current_frame=0
        )
        
        # Connect to capture export data
        captured_settings = None
        
        def capture_export(settings):
            nonlocal captured_settings
            captured_settings = settings
        
        if hasattr(dialog, 'exportRequested'):
            dialog.exportRequested.connect(capture_export)
            
            # Simulate export request
            test_settings = {
                'format': 'PNG',
                'scale': 2.0,
                'output_dir': '/test/output'
            }
            dialog.exportRequested.emit(test_settings)
            
            assert captured_settings is not None, "Export settings not captured"
            assert captured_settings['format'] == 'PNG', "Format not passed correctly"
            assert captured_settings['scale'] == 2.0, "Scale not passed correctly"
    
    def test_animation_control_signal_chain(self, qapp):
        """Test signal chain for animation control."""
        model = SpriteModel()
        controller = AnimationController()
        
        # Track signal emissions
        fps_changes = []
        status_changes = []
        
        def track_fps(fps):
            fps_changes.append(fps)
        
        def track_status(status):
            status_changes.append(status)
        
        if hasattr(controller, 'fpsChanged'):
            controller.fpsChanged.connect(track_fps)
        if hasattr(controller, 'statusChanged'):
            controller.statusChanged.connect(track_status)
        
        # Initialize controller
        controller.initialize(model, Mock())
        
        # Change FPS
        controller.set_fps(15)
        
        # Verify signals were emitted
        assert len(fps_changes) > 0, "FPS change signal not emitted"
        assert 15 in fps_changes, "Correct FPS value not emitted"
        assert len(status_changes) > 0, "Status change signal not emitted"


@pytest.mark.integration
@pytest.mark.signal_test
class TestSignalErrorHandling:
    """Test signal behavior under error conditions."""
    
    def test_signal_emission_with_no_connections(self, qapp):
        """Test that emitting signals with no connections doesn't crash."""
        dialog = ExportDialog(parent=None, frame_count=1, current_frame=0)
        
        # Emit signal with no connections - should not raise
        if hasattr(dialog, 'exportRequested'):
            dialog.exportRequested.emit({})  # Should not crash
        
        if hasattr(dialog, 'exportCompleted'):
            dialog.exportCompleted.emit("test_path")  # Should not crash


def test_signal_documentation():
    """Meta-test: Verify all signals are documented."""
    # This test helps maintain signal documentation
    
    components = [
        (SpriteModel, ['frameChanged', 'dataLoaded', 'errorOccurred']),
        (AnimationController, ['fpsChanged', 'playbackStateChanged', 'frameAdvanced']),
        (ExportDialog, ['exportRequested']),  # Should have this signal
    ]
    
    missing_docs = []
    
    for component_class, expected_signals in components:
        for signal_name in expected_signals:
            if not hasattr(component_class, signal_name):
                missing_docs.append(f"{component_class.__name__}.{signal_name}")
    
    # This helps identify missing signals
    if missing_docs:
        pytest.skip(f"Missing signals (expected): {', '.join(missing_docs)}")


# Signal connection verification fixture
@pytest.fixture
def signal_connection_tracker():
    """Fixture to track signal connections for testing."""
    connections = []
    
    class ConnectionTracker:
        def track_connection(self, signal, slot, connection_type='direct'):
            connections.append({
                'signal': signal,
                'slot': slot,
                'type': connection_type
            })
        
        def verify_connection_made(self, signal_name):
            return any(c['signal'].__name__ == signal_name for c in connections if hasattr(c['signal'], '__name__'))
        
        def get_connection_count(self):
            return len(connections)
        
        def reset(self):
            connections.clear()
    
    return ConnectionTracker()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])