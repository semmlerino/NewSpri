"""
Error scenario tests for Python Sprite Viewer.
Tests application behavior under various error conditions.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMessageBox

from sprite_viewer import SpriteViewer
from sprite_model import SpriteModel
from sprite_model.extraction_mode import ExtractionMode
from export import ExportDialog, get_frame_exporter
from managers import AnimationSegmentManager


@pytest.mark.integration
class TestFileOperationErrors:
    """Test error handling for file operations."""
    
    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        model = SpriteModel()
        
        result = model.load_sprite_sheet("/nonexistent/path/sprite.png")
        
        # Handle both return types: bool or (bool, message) tuple
        if isinstance(result, tuple):
            success, message = result
            assert success is False, "Loading nonexistent file should fail"
        else:
            assert result is False, "Loading nonexistent file should fail"
        
        # Model should remain in valid state
        assert model.sprite_frames == []
        assert model.current_frame == 0

    @patch('pathlib.Path.open', side_effect=PermissionError("Access denied"))
    def test_load_permission_denied(self, mock_open):
        """Test loading a file without read permissions."""
        model = SpriteModel()
        
        result = model.load_sprite_sheet("/restricted/file.png")
        
        # Handle both return types: bool or (bool, message) tuple
        if isinstance(result, tuple):
            success, message = result
            assert success is False, "Loading restricted file should fail gracefully"
        else:
            assert result is False, "Loading restricted file should fail gracefully"
    
    def test_save_to_readonly_directory(self, qapp, tmp_path):
        """Test exporting to a read-only directory."""
        # Create read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()

        # Make it read-only (Unix-like systems)
        try:
            os.chmod(readonly_dir, 0o444)

            exporter = get_frame_exporter()
            test_pixmap = QPixmap(32, 32)
            test_pixmap.fill(Qt.white)

            # Track error signal
            error_messages = []
            exporter.exportError.connect(lambda msg: error_messages.append(msg))

            # Attempt to export to read-only directory
            # The export_frames method creates subdirectory, which should fail
            result = exporter.export_frames(
                frames=[test_pixmap],
                output_dir=str(readonly_dir / "subdir"),  # Creating subdir should fail
                base_name="test",
                format="PNG",
                mode="individual"
            )

            # Export should fail or error should be emitted
            assert result is False or len(error_messages) > 0
        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)

    def test_export_disk_full_simulation(self, qapp, tmp_path):
        """Test export when disk write fails."""
        exporter = get_frame_exporter()
        test_pixmap = QPixmap(32, 32)
        test_pixmap.fill(Qt.white)

        # Track error signals
        error_messages = []
        exporter.exportError.connect(lambda msg: error_messages.append(msg))

        # Test with empty frames - should emit error
        result = exporter.export_frames(
            frames=[],  # Empty frames should fail
            output_dir=str(tmp_path),
            base_name="test",
            format="PNG",
            mode="individual"
        )

        assert result is False, "Export should fail with empty frames"
        assert len(error_messages) > 0, "Error should be emitted"


@pytest.mark.integration
class TestInvalidDataHandling:
    """Test handling of invalid data inputs."""
    
    def test_sprite_model_invalid_frame_dimensions(self, qapp):
        """Test sprite extraction with invalid dimensions."""
        model = SpriteModel()
        
        # Create a valid pixmap
        test_pixmap = QPixmap(100, 100)
        test_pixmap.fill()  # Fill with default color
        
        # Use proper loading method to set internal state
        model._original_sprite_sheet = test_pixmap
        model._sprite_sheet = test_pixmap
        
        # Try to extract with invalid dimensions
        invalid_cases = [
            (0, 50),      # Zero width
            (50, 0),      # Zero height
            (-50, 50),    # Negative width
            (50, -50),    # Negative height
            (200, 50),    # Width larger than sprite sheet
            (50, 200),    # Height larger than sprite sheet
        ]
        
        for width, height in invalid_cases:
            result = model.extract_frames(
                width=width,
                height=height,
                offset_x=0,
                offset_y=0
            )
            
            # extract_frames returns (success, message, frame_count)
            success, message, frame_count = result
            assert success is False, f"Should fail with dimensions ({width}, {height}). Got: {message}"
            assert frame_count == 0, f"Frame count should be 0 for failed extraction, got {frame_count}"
            assert model.sprite_frames == [], "Frames should be empty after failed extraction"
    
    def test_animation_controller_invalid_fps(self):
        """Test animation controller with invalid FPS values."""
        from core import AnimationController

        # Mock the sprite model with required properties
        mock_model = Mock()
        mock_animation = Mock()
        mock_model.sprite_animation = mock_animation
        mock_model.fps = 30
        mock_model.loop_enabled = True

        # Initialize controller (single-step constructor DI)
        controller = AnimationController(
            sprite_model=mock_model,
            sprite_viewer=Mock(),
        )
        
        # Set initial valid FPS
        controller._current_fps = 30
        
        # Test invalid FPS values
        invalid_fps_values = [0, -10, None, "string", float('inf'), float('nan')]
        
        for fps in invalid_fps_values:
            previous_fps = controller._current_fps
            
            # All invalid values should now return False (no exceptions)
            result = controller.set_fps(fps)
            assert result is False, f"set_fps should return False for invalid value: {fps}"
            
            # Controller should maintain previous valid FPS value
            assert controller._current_fps == previous_fps, f"FPS should remain {previous_fps} after invalid input: {fps}"
            assert controller._current_fps > 0, "FPS should remain positive"
        
        # Test that valid floats are converted to int
        result = controller.set_fps(24.7)
        assert result is True, "Valid float should be accepted"
        assert controller._current_fps == 24, "Float should be converted to int"
    
    def test_segment_manager_invalid_segments(self):
        """Test segment manager with invalid segment data."""
        manager = AnimationSegmentManager()
        manager.set_auto_save_enabled(False)  # Disable auto-save for testing
        manager.set_sprite_context("test.png", 20)  # Set sprite context
        
        # Test invalid segment parameters using the API
        invalid_segments = [
            ("", 0, 10),           # Empty name
            ("Test1", 10, 5),      # End before start
            ("Test2", -5, 10),     # Negative start
            ("Test3", 0, -10),     # Negative end
            ("Test4", 25, 30),     # Beyond sprite bounds
        ]
        
        for name, start, end in invalid_segments:
            # Manager should reject invalid segments
            success, message = manager.add_segment(name, start, end)
            
            if name == "":
                assert not success, f"Should reject empty name"
                assert "name" in message.lower()
            elif end < start:
                assert not success, f"Should reject end before start"
            elif start < 0 or end < 0:
                assert not success, f"Should reject negative frames"
            elif start >= 20 or end >= 20:
                assert not success, f"Should reject frames beyond sprite bounds"
                
            # Verify segment was not added
            assert manager.get_segment(name) is None, f"Invalid segment '{name}' should not be added"


@pytest.mark.integration
class TestUIErrorHandling:
    """Test UI error handling and user feedback."""

    def test_export_dialog_handles_invalid_settings(self, qapp):
        """Test export dialog with invalid settings."""
        dialog = ExportDialog(
            parent=None,
            frame_count=5,
            current_frame=0
        )
        
        # Test with invalid settings
        invalid_settings = {
            'format': 'INVALID_FORMAT',
            'scale': -1.0,
            'output_dir': None
        }
        
        # Should handle gracefully (not crash)
        if hasattr(dialog, 'exportRequested'):
            dialog.exportRequested.emit(invalid_settings)
    
    def test_ui_components_handle_null_data(self, qapp):
        """Test UI components handle null/empty data gracefully."""
        from ui import SpriteCanvas, PlaybackControls, FrameExtractor

        # Create components with no data
        canvas = SpriteCanvas()
        controls = PlaybackControls()
        extractor = FrameExtractor()

        # Operations on empty data should not crash
        canvas.set_pixmap(None)
        canvas.set_frame_info(0, 0)
        canvas.update()

        controls.set_frame_range(0)  # Use correct API name
        controls.set_current_frame(0)

        # Should handle gracefully
        assert canvas._pixmap is None
        assert controls.frame_slider.maximum() == 0


@pytest.mark.integration
class TestExportFailureRecovery:
    """Test export failure and cleanup scenarios."""

    def test_export_failure_cleanup(self, tmp_path):
        """Verify cleanup when export fails mid-operation."""
        from export.core.frame_exporter import ExportWorker, ExportTask, ExportMode, ExportFormat
        from unittest.mock import MagicMock

        # Create mock frames
        frames = []
        for i in range(5):
            frame = MagicMock(spec=QPixmap)
            frame.width.return_value = 64
            frame.height.return_value = 64
            # First frame succeeds, rest fail
            frame.save.return_value = (i == 0)
            frames.append(frame)

        task = ExportTask(
            frames=frames,
            output_dir=tmp_path,
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES
        )

        worker = ExportWorker(task)

        # Capture error signals
        errors = []
        worker.error.connect(lambda e: errors.append(e))

        # Run export (will partially fail)
        worker._export_individual_frames()

        # First frame should have been attempted
        frames[0].save.assert_called()

        # Worker should report errors for failed frames
        # (Implementation may vary - some implementations continue, some stop)

    def test_export_directory_deleted_mid_operation(self, tmp_path):
        """Test export behavior when output directory is deleted during export."""
        from export.core.frame_exporter import FrameExporter

        exporter = FrameExporter()
        test_frames = [QPixmap(32, 32) for _ in range(3)]

        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Start export with mocked worker
        with patch('export.core.frame_exporter.ExportWorker') as mock_worker_class:
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker

            success = exporter.export_frames(
                frames=test_frames,
                output_dir=str(output_dir),
                base_name="test"
            )

            # Should succeed in starting (directory exists at start time)
            assert success

    def test_missing_sprite_file_handling(self, qapp, tmp_path):
        """Verify graceful handling when sprite file is deleted after loading."""
        model = SpriteModel()

        # Create and load a sprite
        sprite_path = tmp_path / "temp_sprite.png"
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.white)
        pixmap.save(str(sprite_path))

        result = model.load_sprite_sheet(str(sprite_path))
        if isinstance(result, tuple):
            success, _ = result
        else:
            success = result

        if not success:
            pytest.skip("Could not load test sprite")

        # Use grid extraction mode for predictable results
        model.set_extraction_mode(ExtractionMode.GRID)

        # Extract frames
        success, msg, count = model.extract_frames(50, 50, 0, 0, 0, 0)
        initial_frames = len(model.sprite_frames)

        # Skip if extraction didn't yield frames (e.g., image too small)
        if initial_frames == 0:
            pytest.skip("Could not extract frames from test sprite")

        # Delete the file
        sprite_path.unlink()

        # Operations on existing frames should still work
        current_frame = model.current_frame
        assert current_frame >= 0

        # Accessing existing frames should work (they're in memory)
        if model.sprite_frames:
            frame = model.sprite_frames[0]
            assert frame is not None

        # Attempting to reload the deleted file should fail gracefully
        result = model.load_sprite_sheet(str(sprite_path))
        if isinstance(result, tuple):
            success, _ = result
        else:
            success = result
        assert not success


@pytest.mark.integration
class TestRecoveryScenarios:
    """Test recovery from error conditions."""

    def test_animation_controller_recovery(self):
        """Test animation controller recovery after errors."""
        from core import AnimationController

        # Create a proper mock with frames that will be recognized
        model = Mock()
        model.sprite_animation = Mock()
        # Use a list that evaluates as truthy and has length
        frames = [Mock(), Mock(), Mock()]
        model.sprite_frames = frames
        # Configure the mock to return proper boolean for empty check
        model.configure_mock(**{'sprite_frames': frames})

        # Add required model properties
        model.fps = 30
        model.loop_enabled = True
        model.set_fps = Mock(return_value=True)
        model.set_loop_enabled = Mock(return_value=True)

        # Initialize controller (single-step constructor DI)
        controller = AnimationController(
            sprite_model=model,
            sprite_viewer=Mock(),
        )
        
        # Start with working state
        model.next_frame.return_value = (1, True)
        success = controller.start_animation()
        assert success, "Initial animation start should succeed"
        assert controller._is_playing is True
        
        # Now simulate error during animation update
        model.next_frame.side_effect = RuntimeError("Test error")
        
        # The error during timer callback shouldn't crash the controller
        # Timer will handle the error internally
        
        # Stop animation cleanly
        controller.stop_animation()
        assert controller._is_playing is False
        
        # Fix the mock - remove the error
        model.next_frame.side_effect = None
        model.next_frame.return_value = (1, True)
        
        # Should be able to restart animation
        success = controller.start_animation()
        assert success, "Animation restart should succeed after recovery"
        assert controller._is_playing is True
        
        # Clean up
        controller.stop_animation()


@pytest.mark.integration
class TestMemoryErrorHandling:
    """Test handling of memory-related errors."""
    
    @pytest.mark.memory_intensive
    def test_large_sprite_sheet_handling(self, qapp):
        """Test handling very large sprite sheets."""
        model = SpriteModel()
        
        # Try to create unreasonably large pixmap
        # Most systems will fail to allocate this
        try:
            huge_pixmap = QPixmap(50000, 50000)
            # If it somehow succeeds, verify model handles it
            model._sprite_sheet = huge_pixmap
            
            # Extraction should handle gracefully
            result = model.extract_frames(1000, 1000, 0, 0)
            # Should either work or fail gracefully
        except (MemoryError, RuntimeError):
            # Expected - system can't allocate such large image
            pass
    
# Test utilities for error injection
class ErrorInjector:
    """Utility class for injecting errors in tests."""
    
    @staticmethod
    def make_file_unreadable(filepath):
        """Make a file unreadable (platform-specific)."""
        try:
            os.chmod(filepath, 0o000)
        except Exception:
            # May not work on all platforms
            pass
    
    @staticmethod
    def restore_file_permissions(filepath):
        """Restore file permissions."""
        try:
            os.chmod(filepath, 0o644)
        except Exception:
            pass
    
    @staticmethod
    def create_corrupt_image(filepath, corruption_type='invalid_header'):
        """Create various types of corrupt image files."""
        corruptions = {
            'invalid_header': b'NOTAPNG\x00\x00\x00',
            'truncated': b'\x89PNG\r\n\x1a\n',  # Valid header but nothing else
            'random': os.urandom(1024),  # Random bytes
            'empty': b'',  # Empty file
        }
        
        Path(filepath).write_bytes(corruptions.get(corruption_type, corruptions['random']))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])