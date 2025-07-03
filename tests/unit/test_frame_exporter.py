"""
Unit tests for FrameExporter functionality.
Tests the frame export system including various export modes and formats.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from export.core.frame_exporter import (
    FrameExporter, ExportTask, ExportMode, ExportFormat,
    get_frame_exporter
)
from config import Config


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
        
        task = ExportTask(
            frames=frames,
            output_dir=output_dir,
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0
        )
        
        assert task.frames == frames
        assert task.output_dir == output_dir
        assert task.base_name == "test"
        assert task.format == ExportFormat.PNG
        assert task.mode == ExportMode.INDIVIDUAL_FRAMES
        assert task.scale_factor == 1.0
    
    def test_export_task_validation(self):
        """Test export task validation."""
        output_dir = Path("/tmp/test")
        
        # Test empty frames
        with pytest.raises(ValueError, match="No frames to export"):
            ExportTask(
                frames=[],
                output_dir=output_dir,
                base_name="test",
                format=ExportFormat.PNG,
                mode=ExportMode.INDIVIDUAL_FRAMES
            )
        
        # Test invalid scale factor
        with pytest.raises(ValueError, match="Scale factor must be positive"):
            ExportTask(
                frames=[MagicMock()],
                output_dir=output_dir,
                base_name="test",
                format=ExportFormat.PNG,
                mode=ExportMode.INDIVIDUAL_FRAMES,
                scale_factor=0
            )


class TestFrameExporter:
    """Test FrameExporter class."""
    
    def test_singleton_instance(self):
        """Test that get_frame_exporter returns singleton instance."""
        exporter1 = get_frame_exporter()
        exporter2 = get_frame_exporter()
        assert exporter1 is exporter2
    
    def test_supported_formats(self):
        """Test getting supported export formats."""
        exporter = FrameExporter()
        formats = exporter.get_supported_formats()
        
        assert "PNG" in formats
        assert "JPG" in formats
        assert "BMP" in formats
    
    def test_supported_modes(self):
        """Test getting supported export modes."""
        exporter = FrameExporter()
        modes = exporter.get_supported_modes()
        
        assert "individual" in modes
        assert "sheet" in modes
        # Note: 'selected' mode was consolidated into 'individual' with frame filtering
    
    def test_export_frames_validation(self):
        """Test export_frames validation."""
        exporter = FrameExporter()
        
        # Test with no frames
        success = exporter.export_frames(
            frames=[],
            output_dir="/tmp/test",
            base_name="test"
        )
        assert not success
    
    @patch('export.core.frame_exporter.ExportWorker')
    @patch('export.core.frame_exporter.Path.mkdir')
    def test_export_frames_creates_directory(self, mock_mkdir, mock_worker_class):
        """Test that export creates output directory if needed."""
        # Mock the worker to avoid actual thread creation
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        exporter = FrameExporter()
        
        frames = [MagicMock(spec=QPixmap)]
        success = exporter.export_frames(
            frames=frames,
            output_dir="/tmp/test_export",
            base_name="test"
        )
        
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_worker.start.assert_called_once()
    
    def test_is_exporting_state(self):
        """Test is_exporting state tracking."""
        exporter = FrameExporter()
        
        # Initially not exporting
        assert not exporter.is_exporting()
        
        # Would need to mock worker thread to test during export


class TestExportWorker:
    """Test ExportWorker functionality."""
    
    @pytest.fixture
    def mock_frames(self):
        """Create mock frames for testing."""
        frames = []
        for i in range(3):
            frame = MagicMock(spec=QPixmap)
            frame.width.return_value = 64
            frame.height.return_value = 64
            frame.save.return_value = True
            frames.append(frame)
        return frames
    
    def test_individual_frames_export(self, mock_frames, tmp_path):
        """Test exporting individual frames."""
        from export.core.frame_exporter import ExportWorker
        
        task = ExportTask(
            frames=mock_frames,
            output_dir=tmp_path,
            base_name="frame",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            pattern="{name}_{index:03d}"
        )
        
        worker = ExportWorker(task)
        
        # Mock the progress signal
        progress_calls = []
        worker.progress.connect(lambda c, t, m: progress_calls.append((c, t, m)))
        
        # Run the export (directly call the method for testing)
        worker._export_individual_frames()
        
        # Check that save was called for each frame
        for i, frame in enumerate(mock_frames):
            expected_filename = f"frame_{i:03d}.png"
            frame.save.assert_called_with(
                str(tmp_path / expected_filename),
                "PNG"
            )
        
        # Check progress signals
        assert len(progress_calls) == len(mock_frames)
    
    def test_sprite_sheet_export(self, mock_frames, tmp_path):
        """Test exporting as sprite sheet."""
        from export.core.frame_exporter import ExportWorker
        
        task = ExportTask(
            frames=mock_frames,
            output_dir=tmp_path,
            base_name="sprites",
            format=ExportFormat.PNG,
            mode=ExportMode.SPRITE_SHEET
        )
        
        worker = ExportWorker(task)
        
        # Mock QPixmap creation for sprite sheet
        with patch('export.core.frame_exporter.QPixmap') as mock_pixmap_class:
            mock_sheet = MagicMock()
            mock_sheet.save.return_value = True
            mock_pixmap_class.return_value = mock_sheet
            
            # Mock QPainter
            with patch('export.core.frame_exporter.QPainter'):
                worker._export_sprite_sheet()
                
                # Verify sprite sheet was created with correct size
                # 3 frames in 1x3 grid = 64x192 pixels (auto layout chooses 1x3 for 3 frames)
                mock_pixmap_class.assert_called_with(64, 192)
                
                # Verify save was called
                expected_filename = "sprites_sheet.png"
                mock_sheet.save.assert_called_with(
                    str(tmp_path / expected_filename),
                    "PNG"
                )
    
    def test_frame_filtering_workflow(self, mock_frames, tmp_path):
        """Test frame filtering workflow (replaces selected frames export)."""
        from export.core.frame_exporter import ExportWorker
        
        # Pre-filter frames like sprite_viewer.py does
        selected_indices = [0, 2]  # Select first and third frame
        filtered_frames = [mock_frames[i] for i in selected_indices]
        
        task = ExportTask(
            frames=filtered_frames,  # Pre-filtered frames
            output_dir=tmp_path,
            base_name="filtered",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,  # Use individual mode with filtered frames
            pattern="{name}_{index:03d}"
        )
        
        worker = ExportWorker(task)
        worker._export_individual_frames()
        
        # Check that filtered frames were saved
        # Note: These are now mock_frames[0] and mock_frames[2] as filtered_frames[0] and filtered_frames[1]
        assert len(filtered_frames) == 2
        for frame in filtered_frames:
            frame.save.assert_called_once()
    
    def test_scale_factor_application(self, mock_frames, tmp_path):
        """Test that scale factor is applied correctly."""
        from export.core.frame_exporter import ExportWorker
        
        # Mock scaled return
        for frame in mock_frames:
            scaled_frame = MagicMock()
            scaled_frame.save.return_value = True
            frame.scaled.return_value = scaled_frame
        
        task = ExportTask(
            frames=mock_frames,
            output_dir=tmp_path,
            base_name="scaled",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=2.0
        )
        
        worker = ExportWorker(task)
        worker._export_individual_frames()
        
        # Check that scaling was called with correct parameters
        for frame in mock_frames:
            frame.scaled.assert_called_once_with(
                128, 128,  # 64 * 2.0
                aspectMode=1,  # KeepAspectRatio
                mode=1  # SmoothTransformation
            )
    
    def test_export_cancellation(self, mock_frames, tmp_path):
        """Test export cancellation."""
        from export.core.frame_exporter import ExportWorker
        
        task = ExportTask(
            frames=mock_frames,
            output_dir=tmp_path,
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES
        )
        
        worker = ExportWorker(task)
        worker.cancel()
        
        assert worker._cancelled


class TestExportIntegration:
    """Integration tests for export functionality."""
    
    @patch('export.core.frame_exporter.ExportWorker')
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
        
        # Start export
        frames = [MagicMock(spec=QPixmap)]
        success = exporter.export_frames(
            frames=frames,
            output_dir="/tmp/test",
            base_name="test"
        )
        
        assert success
        assert len(started) == 1
        mock_worker.start.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])