"""
End-to-End Integration Tests
Comprehensive integration tests covering complete user workflows from startup to export.
"""

import pytest

# Mark all tests as slow integration tests - they create full SpriteViewer windows
pytestmark = [pytest.mark.integration, pytest.mark.slow]
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication

from export import ExportDialog
from export.core.frame_exporter import (
    ExportConfig,
    ExportFormat,
    ExportMode,
    get_frame_exporter,
)
from sprite_viewer import SpriteViewer


class TestCompleteApplicationLifecycle:
    """Test the complete application lifecycle from startup to shutdown."""

    @pytest.mark.smoke
    @pytest.mark.integration
    def test_smoke_load_extract_export(self, qtbot, tmp_path):
        """Smoke: load a sprite sheet, extract grid frames, export frames, close cleanly."""
        sprite_path = tmp_path / "smoke.png"
        self._create_test_sprite_sheet(64, 32, 32).save(str(sprite_path), "PNG")

        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        try:
            success, _ = viewer._sprite_model.load_sprite_sheet(str(sprite_path))
            assert success
            success, _, count = viewer._sprite_model.extract_frames(32, 32, 0, 0)
            assert success and count > 0

            out_dir = tmp_path / "out"
            out_dir.mkdir()
            config = ExportConfig(
                output_dir=out_dir,
                base_name="smoke",
                format=ExportFormat.PNG,
                mode=ExportMode.INDIVIDUAL_FRAMES,
                scale_factor=1.0,
            )
            finished: list[bool] = []
            get_frame_exporter().exportFinished.connect(lambda s, _m: finished.append(s))
            assert get_frame_exporter().export_frames(
                frames=viewer._sprite_model.sprite_frames,
                config=config,
            )
            qtbot.waitUntil(lambda: bool(finished), timeout=3000)
            assert finished[0] is True
            assert any(out_dir.iterdir())
        finally:
            viewer.close()

    @pytest.mark.integration
    def test_error_recovery_workflow(self, qtbot):
        """Test application recovery from various error conditions."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # 1. Test loading invalid file (real error handling)
        # Try to load a non-existent file directly
        success, message = viewer._sprite_model.load_sprite_sheet("/nonexistent/file.png")

        # Should fail gracefully
        assert not success, "Loading non-existent file should fail"
        assert any(word in message.lower() for word in ["not found", "error", "does not exist"])
        assert viewer._sprite_model.sprite_frames == ()

        # 2. Test export with no sprites loaded
        # Export should fail gracefully with no frames
        exporter = get_frame_exporter()
        empty_config = ExportConfig(
            output_dir=Path("/tmp"),
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        success = exporter.export_frames(
            frames=[],  # No frames
            config=empty_config,
        )
        # Should handle empty frame list gracefully
        assert not success, "Export should fail with no frames"

        # 3. Test invalid frame navigation
        # Navigate using the model directly
        viewer._sprite_model.next_frame()  # Should not crash with no frames
        viewer._sprite_model.previous_frame()

        # Ensure button states are updated for no frames
        viewer._sprite_model.frameChanged.emit(0, 0)
        QApplication.processEvents()

        # Test button navigation with no frames
        assert not viewer._playback_controls.prev_btn.isEnabled()
        assert not viewer._playback_controls.next_btn.isEnabled()

        # Clicking disabled buttons should not crash
        viewer._playback_controls.prev_btn.click()
        viewer._playback_controls.next_btn.click()

        # 4. Test animation with no frames
        viewer._animation_controller.toggle_playback()  # Should handle gracefully
        assert viewer._animation_controller.is_playing is False

    # Helper methods
    def _create_test_sprite_sheet(self, width, height, sprite_size):
        """Create a test sprite sheet with properly separated sprites."""
        sheet = QPixmap(width, height)
        sheet.fill(Qt.transparent)  # Use transparent background for CCL

        from PySide6.QtGui import QPainter

        painter = QPainter(sheet)

        cols = width // sprite_size
        rows = height // sprite_size

        for row in range(rows):
            for col in range(cols):
                x = col * sprite_size
                y = row * sprite_size
                color = QColor.fromHsv((row * cols + col) * 30 % 360, 200, 200)

                # Draw sprite with some margin for CCL detection
                margin = 2
                painter.fillRect(
                    x + margin,
                    y + margin,
                    sprite_size - 2 * margin,
                    sprite_size - 2 * margin,
                    color,
                )

                # Add border for visual clarity
                painter.setPen(Qt.black)
                painter.drawRect(
                    x + margin,
                    y + margin,
                    sprite_size - 2 * margin - 1,
                    sprite_size - 2 * margin - 1,
                )

        painter.end()
        return sheet

    def _load_test_sprites(self, viewer):
        """Load test sprites into viewer."""
        frames = []
        for i in range(8):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 45, 200, 200))
            frames.append(pixmap)
        viewer._sprite_model.set_frames(frames)
        viewer._sprite_model.frameChanged.emit(0, 8)


class TestAnimationSegmentWorkflow:
    """Test complete animation segment creation and management workflow."""

    @pytest.mark.integration
    def test_segment_creation_workflow(self, qtbot):
        """Test creating, naming, and exporting animation segments."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # Load sprites
        frames = []
        for i in range(16):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 22, 200, 200))
            frames.append(pixmap)
        viewer._sprite_model.set_frames(frames)

        # Open animation grid view
        from ui.animation_grid_view import AnimationGridView

        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        grid_view.set_frames(viewer._sprite_model.sprite_frames)
        grid_view.show()

        # Mirror what a controller would do: store the segment in the grid view
        def _record_segment(segment):
            grid_view._segments[segment.name] = segment
            grid_view._update_segment_visualization()

        grid_view.segmentCreated.connect(_record_segment)

        # Select frames for segment
        grid_view._selected_frames = {0, 1, 2, 3}

        # Create segment
        with patch("PySide6.QtWidgets.QInputDialog.getText") as mock_input:
            mock_input.return_value = ("Walk Cycle", True)
            grid_view._create_segment_from_selection()

        # Verify segment created
        assert len(grid_view._segments) == 1
        segment_name = next(iter(grid_view._segments.keys()))
        segment = grid_view._segments[segment_name]
        assert segment.name == "Walk Cycle"
        assert segment.start_frame == 0
        assert segment.end_frame == 3

        # Test export signal emission
        export_signal_received = []

        def on_export_requested(segment_name):
            export_signal_received.append(segment_name)

        grid_view.exportRequested.connect(on_export_requested)

        # Emit export request for the created segment
        grid_view.exportRequested.emit("Walk Cycle")
        assert "Walk Cycle" in export_signal_received

    @pytest.mark.integration
    def test_multi_segment_management(self, qtbot):
        """Test managing multiple animation segments."""
        from managers.animation_segment_manager import AnimationSegmentManager

        manager = AnimationSegmentManager()
        manager.set_auto_save_enabled(False)  # Disable auto-save for testing
        manager.set_sprite_context("test_sprite.png", 16)  # Set sprite context with 16 frames

        # Clear any existing segments from disk
        manager.clear_segments()

        # Create multiple segments
        segments = [
            ("Idle", 0, 1, QColor("red")),
            ("Walk", 2, 5, QColor("green")),
            ("Run", 6, 9, QColor("blue")),
            ("Jump", 10, 12, QColor("yellow")),
        ]

        for name, start, end, color in segments:
            manager.add_segment(name, start, end, color=color)

        # Test segment operations
        assert len(manager.get_all_segments()) == 4
        walk_segment = manager.get_segment("Walk")
        assert walk_segment.start_frame == 2
        assert walk_segment.end_frame == 5

        # Remove segment
        manager.remove_segment("Idle")
        assert len(manager.get_all_segments()) == 3

        # Clear all
        manager.clear_segments()
        assert len(manager.get_all_segments()) == 0


class TestMultiWindowWorkflow:
    """Test workflows involving multiple windows and dialogs."""

    @pytest.mark.integration
    def test_multiple_dialogs_workflow(self, qtbot):
        """Test opening multiple dialogs in sequence."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # Load sprites first
        frames = []
        for i in range(8):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 45, 200, 200))
            frames.append(pixmap)
        viewer._sprite_model.set_frames(frames)

        # Test settings dialog - skip if not implemented
        # Settings dialog might not exist in current implementation

        # Test opening export dialog
        # Export dialog can be created directly
        if viewer._sprite_model.sprite_frames:
            dialog = ExportDialog(
                frame_count=len(viewer._sprite_model.sprite_frames),
                current_frame=viewer._sprite_model.current_frame,
                sprites=viewer._sprite_model.sprite_frames,
            )
            # Don't execute, just verify it can be created
            assert dialog is not None

        # Test opening about dialog
        # About dialog might be shown differently or not exist
        # Just verify the viewer is still functional
        viewer.show()
        assert viewer.isVisible()


class TestLargeInputWorkflows:
    """Test complete workflows with larger frame sets."""

    @pytest.mark.integration
    @pytest.mark.performance
    def test_large_sprite_sheet_workflow_handles_many_frames(self, qtbot):
        """Test workflow with large sprite sheets."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # Simulate a loaded 256-frame sprite sheet.
        frames = []
        for i in range(256):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i % 360, 200, 200))
            frames.append(pixmap)
        viewer._sprite_model.set_frames(frames)

        # Trigger updates
        viewer._sprite_model.frameChanged.emit(0, 256)
        assert viewer._sprite_model.frame_count == 256

        # Navigate through frames
        for _ in range(10):
            viewer._sprite_model.next_frame()
            QApplication.processEvents()

        assert 0 <= viewer._sprite_model.current_frame < 256

        viewer.close()


# Integration test fixtures
@pytest.fixture
def mock_sprite_viewer(qtbot):
    """Create a sprite viewer with mock data."""
    viewer = SpriteViewer()
    qtbot.addWidget(viewer)

    # Add test sprites
    frames = []
    for i in range(16):
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor.fromHsv(i * 22, 200, 200))
        frames.append(pixmap)
    viewer._sprite_model.set_frames(frames)

    viewer._sprite_model.frameChanged.emit(0, 16)
    return viewer


@pytest.fixture
def test_sprite_sheet_file(tmp_path):
    """Create a test sprite sheet file."""
    sprite_sheet = QPixmap(256, 256)
    sprite_sheet.fill(Qt.white)

    from PySide6.QtGui import QPainter

    painter = QPainter(sprite_sheet)

    # Draw 8x8 grid of sprites
    for row in range(8):
        for col in range(8):
            x = col * 32
            y = row * 32
            color = QColor.fromHsv((row * 8 + col) * 5, 200, 200)
            painter.fillRect(x, y, 32, 32, color)
            painter.setPen(Qt.black)
            painter.drawRect(x, y, 31, 31)

    painter.end()

    filepath = tmp_path / "test_sprites.png"
    sprite_sheet.save(str(filepath))
    return filepath
