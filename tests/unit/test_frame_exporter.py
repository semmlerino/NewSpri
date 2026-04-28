"""
Unit tests for FrameExporter functionality.
Tests the frame export system including various export modes and formats.
"""

from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

from export.core.frame_exporter import (
    ExportConfig,
    ExportFormat,
    ExportMode,
    FrameExporter,
    _ExportTask,
    get_frame_exporter,
)


class TestExportFormat:
    """Test ExportFormat enum functionality."""

    def test_export_format_values(self):
        """Test that export formats have correct values."""
        assert ExportFormat.PNG.value == "PNG"
        assert ExportFormat.JPG.value == "JPG"
        assert ExportFormat.BMP.value == "BMP"

    def test_export_format_extension(self):
        """Test that export formats return correct extensions."""
        assert ExportFormat.PNG.extension == ".png"
        assert ExportFormat.JPG.extension == ".jpg"
        assert ExportFormat.BMP.extension == ".bmp"

    def test_export_format_from_string(self):
        """Test creating export format from string."""
        assert ExportFormat.from_string("png") == ExportFormat.PNG
        assert ExportFormat.from_string("PNG") == ExportFormat.PNG
        assert ExportFormat.from_string("jpg") == ExportFormat.JPG
        assert ExportFormat.from_string("JPG") == ExportFormat.JPG

        with pytest.raises(ValueError):
            ExportFormat.from_string("invalid")


class TestExportTask:
    """Test ExportTask class."""

    def test_export_task_creation(self):
        """Test creating an export task."""
        mock_frame = MagicMock()
        frames = [mock_frame]
        output_dir = Path("/tmp/test")

        task = _ExportTask(
            frames=frames,
            output_dir=output_dir,
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )

        assert task.frames == frames
        assert task.output_dir == output_dir
        assert task.base_name == "test"
        assert task.format == ExportFormat.PNG
        assert task.mode == ExportMode.INDIVIDUAL_FRAMES
        assert task.scale_factor == pytest.approx(1.0)

    def test_export_task_validation(self):
        """Test export task validation."""
        output_dir = Path("/tmp/test")

        # Test empty frames
        with pytest.raises(ValueError, match="No frames to export"):
            _ExportTask(
                frames=[],
                output_dir=output_dir,
                base_name="test",
                format=ExportFormat.PNG,
                mode=ExportMode.INDIVIDUAL_FRAMES,
            )

        # Test invalid scale factor
        with pytest.raises(ValueError, match="Scale factor must be positive"):
            _ExportTask(
                frames=[MagicMock()],
                output_dir=output_dir,
                base_name="test",
                format=ExportFormat.PNG,
                mode=ExportMode.INDIVIDUAL_FRAMES,
                scale_factor=0,
            )


class TestFrameExporter:
    """Test FrameExporter class."""

    def test_singleton_instance(self):
        """Test that get_frame_exporter returns singleton instance."""
        exporter1 = get_frame_exporter()
        exporter2 = get_frame_exporter()
        assert exporter1 is exporter2

    def test_export_frames_validation(self):
        """Test export_frames validation."""
        from pathlib import Path

        exporter = FrameExporter()

        # Test with no frames
        config = ExportConfig(
            output_dir=Path("/tmp/test"),
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        success = exporter.export_frames(frames=[], config=config)
        assert not success

    @patch("export.core.frame_exporter._ExportWorker")
    @patch("pathlib.Path.mkdir")
    def test_export_frames_creates_directory(self, mock_mkdir, mock_worker_class):
        """Test that export creates output directory if needed."""
        # Mock the worker to avoid actual thread creation
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker

        exporter = FrameExporter()

        # Create mock QPixmap that returns a valid QImage when toImage() is called
        mock_pixmap = MagicMock(spec=QPixmap)
        mock_image = MagicMock(spec=QImage)
        mock_image.isNull.return_value = False
        mock_pixmap.toImage.return_value = mock_image

        frames = [mock_pixmap]
        config = ExportConfig(
            output_dir=Path("/tmp/test_export"),
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        exporter.export_frames(frames=frames, config=config)

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_worker.start.assert_called_once()

    def test_cancel_export_is_cooperative_and_non_blocking(self):
        """Cancellation should not block the UI thread waiting for worker shutdown."""
        exporter = FrameExporter()
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = True
        exporter._worker = mock_worker

        exporter.cancel_export()

        mock_worker.cancel.assert_called_once_with()
        mock_worker.wait.assert_not_called()
        mock_worker.terminate.assert_not_called()


class TestExportWorker:
    """Test ExportWorker functionality."""

    @pytest.fixture
    def mock_frames(self):
        """Create mock QImage frames for testing (ExportTask now uses QImage)."""
        frames = []
        for _i in range(3):
            frame = MagicMock(spec=QImage)
            frame.width.return_value = 64
            frame.height.return_value = 64
            frame.save.return_value = True
            frames.append(frame)
        return frames

    def test_individual_frames_export(self, mock_frames, tmp_path):
        """Test exporting individual frames."""
        from export.core.frame_exporter import _ExportWorker

        task = _ExportTask(
            frames=mock_frames,
            output_dir=tmp_path,
            base_name="frame",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            pattern="{name}_{index:03d}",
        )

        worker = _ExportWorker(task)

        # Mock the progress signal
        progress_calls = []
        worker.progress.connect(lambda c, t, m: progress_calls.append((c, t, m)))

        # Run the export (directly call the method for testing)
        worker._export_individual_frames()

        # Check that save was called for each frame (Qt infers format from extension)
        for i, frame in enumerate(mock_frames):
            expected_filename = f"frame_{i:03d}.png"
            frame.save.assert_called_with(str(tmp_path / expected_filename))

        # Check progress signals
        assert len(progress_calls) == len(mock_frames)

    def test_sprite_sheet_export(self, mock_frames, tmp_path):
        """Test exporting as sprite sheet."""
        from export.core.frame_exporter import _ExportWorker

        task = _ExportTask(
            frames=mock_frames,
            output_dir=tmp_path,
            base_name="sprites",
            format=ExportFormat.PNG,
            mode=ExportMode.SPRITE_SHEET,
        )

        worker = _ExportWorker(task)

        # Mock QImage creation for sprite sheet (now uses thread-safe QImage)
        with patch("export.core.frame_exporter.QImage") as mock_image_class:
            mock_sheet = MagicMock()
            mock_sheet.save.return_value = True
            mock_image_class.return_value = mock_sheet

            # Mock QPainter
            with patch("export.core.frame_exporter.QPainter"):
                worker._export_sprite_sheet()

                # Verify sprite sheet was created with correct size
                # 3 frames in 1x3 grid = 64x192 pixels (auto layout chooses 1x3 for 3 frames)
                # QImage constructor takes (width, height, format)
                # Use ANY for format since patching QImage also patches Format enum
                mock_image_class.assert_called_with(64, 192, ANY)

                # Verify save was called (Qt infers format from extension)
                expected_filename = "sprites_sheet.png"
                mock_sheet.save.assert_called_with(str(tmp_path / expected_filename))

    def test_scale_factor_application(self, mock_frames, tmp_path):
        """Test that scale factor is applied correctly."""
        from export.core.frame_exporter import _ExportWorker

        # Mock scaled return
        for frame in mock_frames:
            scaled_frame = MagicMock()
            scaled_frame.save.return_value = True
            frame.scaled.return_value = scaled_frame

        task = _ExportTask(
            frames=mock_frames,
            output_dir=tmp_path,
            base_name="scaled",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=2.0,
        )

        worker = _ExportWorker(task)
        worker._export_individual_frames()

        # Check that scaling was called with correct parameters
        # Use Qt enum values instead of integers
        for frame in mock_frames:
            frame.scaled.assert_called_once_with(
                128,
                128,  # 64 * 2.0
                aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
                mode=Qt.TransformationMode.SmoothTransformation,
            )

    def test_export_cancellation(self, mock_frames, tmp_path):
        """Test export cancellation."""
        from export.core.frame_exporter import _ExportWorker

        task = _ExportTask(
            frames=mock_frames,
            output_dir=tmp_path,
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
        )

        worker = _ExportWorker(task)
        worker.cancel()

        assert worker._cancelled


class TestExportIntegration:
    """Integration tests for export functionality."""

    @patch("export.core.frame_exporter._ExportWorker")
    def test_full_export_workflow(self, mock_worker_class, qtbot):
        """Test complete export workflow."""
        exporter = FrameExporter()

        # Mock worker
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker

        # Track signals
        started = []
        progress = []
        finished = []
        errors = []

        exporter.exportStarted.connect(lambda: started.append(True))
        exporter.exportProgress.connect(lambda c, t, m: progress.append((c, t, m)))
        exporter.exportFinished.connect(lambda s, m: finished.append((s, m)))
        exporter.exportError.connect(lambda e: errors.append(e))

        # Start export - mock QPixmap with working toImage()
        mock_pixmap = MagicMock(spec=QPixmap)
        mock_image = MagicMock(spec=QImage)
        mock_image.isNull.return_value = False
        mock_pixmap.toImage.return_value = mock_image
        frames = [mock_pixmap]
        config = ExportConfig(
            output_dir=Path("/tmp/test"),
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        success = exporter.export_frames(frames=frames, config=config)

        assert success
        assert len(started) == 1
        mock_worker.start.assert_called_once()
