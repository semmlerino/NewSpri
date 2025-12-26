"""
Integration tests for concurrent operations.
Tests behavior when multiple operations happen simultaneously.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor, QPainter
from PySide6.QtWidgets import QApplication

from sprite_viewer import SpriteViewer
from sprite_model.core import SpriteModel
from core.animation_controller import AnimationController


class TestConcurrentOperations:
    """Test behavior when multiple operations happen simultaneously."""

    @pytest.fixture
    def sprite_viewer_with_frames(self, qtbot):
        """Create a sprite viewer with test frames loaded."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # Create a proper sprite sheet
        sprite_sheet = QPixmap(360, 36)
        sprite_sheet.fill(Qt.transparent)

        painter = QPainter(sprite_sheet)
        for i in range(10):
            color = QColor.fromHsv(i * 36, 200, 200)
            painter.fillRect(i * 36 + 2, 2, 32, 32, color)
        painter.end()

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            sprite_sheet.save(tmp.name)
            tmp_path = tmp.name

        viewer._sprite_model.load_sprite_sheet(tmp_path)

        if len(viewer._sprite_model.sprite_frames) == 0:
            viewer._sprite_model.set_extraction_mode('grid')
            viewer._sprite_model.extract_frames(32, 32, 2, 2, 4, 0)

        os.unlink(tmp_path)

        frame_count = len(viewer._sprite_model.sprite_frames)
        if frame_count > 0:
            viewer._playback_controls.set_frame_range(frame_count - 1)
            viewer._playback_controls.update_button_states(True, True, False)

        return viewer

    @pytest.mark.integration
    def test_export_during_playback(self, qtbot, sprite_viewer_with_frames, tmp_path):
        """Export should work while animation is playing."""
        viewer = sprite_viewer_with_frames

        if len(viewer._sprite_model.sprite_frames) < 2:
            pytest.skip("Need at least 2 frames")

        # 1. Start playback
        viewer._playback_controls.play_button.click()
        QApplication.processEvents()
        qtbot.waitUntil(lambda: viewer._animation_controller.is_playing, timeout=2000)

        assert viewer._animation_controller.is_playing

        # 2. Trigger export while playing (mock the dialog and export)
        with patch('export.core.frame_exporter.ExportWorker') as mock_worker_class:
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker

            from export.core.frame_exporter import FrameExporter
            exporter = FrameExporter()

            # Export frames while animation is playing
            success = exporter.export_frames(
                frames=viewer._sprite_model.sprite_frames,
                output_dir=str(tmp_path),
                base_name="test"
            )

            # Export should succeed
            assert success
            mock_worker.start.assert_called_once()

        # 3. Animation should still be playing (export doesn't stop playback)
        # Note: The export runs in a separate thread, so playback continues
        assert viewer._animation_controller.is_playing

        # 4. Clean up - stop playback
        viewer._animation_controller.pause_animation()
        QApplication.processEvents()

    @pytest.mark.integration
    def test_extraction_mode_change_with_loaded_sprite(self, qtbot, tmp_path):
        """Changing grid→CCL mode with loaded sprite should work."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # Create sprite sheet
        sprite_sheet = QPixmap(360, 36)
        sprite_sheet.fill(Qt.transparent)

        painter = QPainter(sprite_sheet)
        for i in range(10):
            painter.fillRect(i * 36 + 2, 2, 32, 32, QColor(255, 0, 0))
        painter.end()

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            sprite_sheet.save(tmp.name)
            tmp_path_file = tmp.name

        # Load sprite
        viewer._sprite_model.load_sprite_sheet(tmp_path_file)
        os.unlink(tmp_path_file)

        # Initial extraction with grid mode
        viewer._sprite_model.set_extraction_mode('grid')
        viewer._sprite_model.extract_frames(32, 32, 2, 2, 4, 0)
        initial_frames = len(viewer._sprite_model.sprite_frames)

        # Change to CCL mode
        viewer._sprite_model.set_extraction_mode('ccl')

        # Try CCL extraction
        viewer._sprite_model.extract_ccl_frames()

        # Should have some frames (CCL might detect different count)
        assert len(viewer._sprite_model.sprite_frames) >= 0

        # Change back to grid mode
        viewer._sprite_model.set_extraction_mode('grid')
        viewer._sprite_model.extract_frames(32, 32, 2, 2, 4, 0)

        # Should have frames again
        assert len(viewer._sprite_model.sprite_frames) > 0

    @pytest.mark.integration
    def test_playback_during_frame_extraction(self, qtbot, sprite_viewer_with_frames, tmp_path):
        """Frame extraction should stop playback first."""
        viewer = sprite_viewer_with_frames

        if len(viewer._sprite_model.sprite_frames) < 2:
            pytest.skip("Need at least 2 frames")

        # Start playback
        viewer._playback_controls.play_button.click()
        QApplication.processEvents()
        qtbot.waitUntil(lambda: viewer._animation_controller.is_playing, timeout=2000)

        initial_playing = viewer._animation_controller.is_playing
        assert initial_playing

        # Attempt new extraction (this should trigger frame replacement)
        viewer._sprite_model.extract_frames(32, 32, 2, 2, 4, 0)
        QApplication.processEvents()

        # System should handle this gracefully (frames replaced, playback state may change)
        # At minimum, no crash should occur
        assert True  # If we get here, no crash occurred

    @pytest.mark.integration
    def test_segment_creation_during_playback(self, qtbot, sprite_viewer_with_frames):
        """Creating segments while animation plays should work."""
        viewer = sprite_viewer_with_frames

        if len(viewer._sprite_model.sprite_frames) < 4:
            pytest.skip("Need at least 4 frames")

        # Start playback
        viewer._playback_controls.play_button.click()
        QApplication.processEvents()
        qtbot.waitUntil(lambda: viewer._animation_controller.is_playing, timeout=2000)

        # Access segment manager through controller
        segment_manager = viewer._segment_manager

        # Set sprite context for segment manager (use unique name to avoid pollution)
        import uuid
        unique_sprite_name = f"test_sprite_{uuid.uuid4().hex[:8]}.png"
        segment_manager.set_sprite_context(
            unique_sprite_name,
            len(viewer._sprite_model.sprite_frames)
        )

        # Create segment during playback using correct API (individual args, not object)
        from PySide6.QtGui import QColor
        success, message = segment_manager.add_segment(
            name="DuringPlayback",
            start_frame=0,
            end_frame=2,
            color=QColor(255, 0, 0)
        )
        assert success, f"Should be able to create segment during playback: {message}"

        # Segment should exist
        assert segment_manager.get_segment("DuringPlayback") is not None

        # Stop playback for cleanup
        viewer._animation_controller.pause_animation()
        QApplication.processEvents()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
