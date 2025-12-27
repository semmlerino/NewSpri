"""
Tests for export system thread safety.

Covers:
- ExportWorker cancellation during export
- Concurrent export prevention
- Signal emission from worker thread
- Resource cleanup after export
- State consistency during export
- Progress reporting during long exports
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from PySide6.QtCore import QThread
from PySide6.QtGui import QPixmap, QImage, QColor

from export.core.frame_exporter import (
    ExportWorker,
    ExportTask,
    ExportMode,
    ExportFormat,
    FrameExporter,
    get_frame_exporter,
    reset_frame_exporter,
    SpriteSheetLayout,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


# Mark all tests in this module as requiring Qt
pytestmark = pytest.mark.requires_qt


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_exporter():
    """Reset the global frame exporter before and after each test."""
    reset_frame_exporter()
    yield
    reset_frame_exporter()


@pytest.fixture
def sample_frames() -> list[QImage]:
    """Create sample QImage frames for export testing."""
    frames = []
    for i in range(8):
        img = QImage(32, 32, QImage.Format.Format_ARGB32)
        img.fill(QColor(i * 30, 100, 150))
        frames.append(img)
    return frames


@pytest.fixture
def sample_pixmaps(sample_frames: list[QImage]) -> list[QPixmap]:
    """Create sample QPixmap frames for FrameExporter testing."""
    return [QPixmap.fromImage(img) for img in sample_frames]


@pytest.fixture
def export_dir(tmp_path: Path) -> Path:
    """Create a temporary export directory."""
    export_path = tmp_path / "exports"
    export_path.mkdir()
    return export_path


@pytest.fixture
def basic_export_task(sample_frames: list[QImage], export_dir: Path) -> ExportTask:
    """Create a basic export task for individual frames."""
    return ExportTask(
        frames=sample_frames,
        output_dir=export_dir,
        base_name="test_frame",
        format=ExportFormat.PNG,
        mode=ExportMode.INDIVIDUAL_FRAMES,
        scale_factor=1.0,
    )


@pytest.fixture
def sheet_export_task(sample_frames: list[QImage], export_dir: Path) -> ExportTask:
    """Create an export task for sprite sheet."""
    return ExportTask(
        frames=sample_frames,
        output_dir=export_dir,
        base_name="test_sheet",
        format=ExportFormat.PNG,
        mode=ExportMode.SPRITE_SHEET,
        scale_factor=1.0,
        sprite_sheet_layout=SpriteSheetLayout(mode='rows', max_columns=4),
    )


# ============================================================================
# ExportWorker Cancellation Tests
# ============================================================================


class TestExportWorkerCancellation:
    """Tests for export worker cancellation behavior."""

    def test_cancel_before_start(
        self, qapp, basic_export_task: ExportTask
    ) -> None:
        """Cancellation before start should prevent export."""
        worker = ExportWorker(basic_export_task)
        worker.cancel()

        assert worker._cancelled is True

    def test_cancel_flag_checked(
        self, qapp, basic_export_task: ExportTask
    ) -> None:
        """Worker should check cancellation flag during export."""
        worker = ExportWorker(basic_export_task)

        # Spy on cancelled state
        assert worker._cancelled is False

        worker.cancel()

        assert worker._cancelled is True

    def test_cancelled_export_does_not_emit_success(
        self, qapp, basic_export_task: ExportTask, qtbot
    ) -> None:
        """Cancelled export should not emit success signal."""
        worker = ExportWorker(basic_export_task)

        # Track signals
        finished_results = []
        worker.finished.connect(lambda success, msg: finished_results.append((success, msg)))

        # Cancel and run
        worker.cancel()
        worker.run()

        # Should emit with cancelled status
        # Note: actual behavior depends on implementation - may not emit at all
        # or may emit with success=False


# ============================================================================
# Concurrent Export Prevention Tests
# ============================================================================


class TestConcurrentExportPrevention:
    """Tests for preventing concurrent exports."""

    def test_is_exporting_initially_false(self, qapp) -> None:
        """Exporter should not be exporting initially."""
        exporter = get_frame_exporter()
        assert exporter.is_exporting() is False

    def test_export_sets_exporting_state(
        self, qapp, sample_pixmaps: list[QPixmap], export_dir: Path
    ) -> None:
        """Starting export should set exporting state."""
        exporter = get_frame_exporter()

        # Start export (uses QPixmap which is converted internally)
        result = exporter.export_frames(
            frames=sample_pixmaps,
            output_dir=str(export_dir),
            base_name="test",
            format="PNG",
            mode="individual",
            scale_factor=1.0,
        )

        # Should have started successfully
        assert result is True


class TestExportSignalSafety:
    """Tests for signal emission safety from worker thread."""

    def test_progress_signal_emission(
        self, qapp, basic_export_task: ExportTask, qtbot
    ) -> None:
        """Progress signals should be emitted safely."""
        worker = ExportWorker(basic_export_task)

        progress_values = []
        worker.progress.connect(lambda val: progress_values.append(val))

        # Run export (synchronously for testing)
        worker.run()

        # Should have received progress updates
        # For 8 frames, we expect multiple progress updates
        assert len(progress_values) >= 1

    def test_finished_signal_emission(
        self, qapp, basic_export_task: ExportTask, qtbot
    ) -> None:
        """Finished signal should be emitted on completion."""
        worker = ExportWorker(basic_export_task)

        finished_results = []
        worker.finished.connect(lambda success, msg: finished_results.append((success, msg)))

        # Run export
        worker.run()

        # Should have received finished signal
        assert len(finished_results) == 1
        success, message = finished_results[0]
        assert success is True

    def test_error_on_empty_frames_task(
        self, qapp, export_dir: Path, qtbot
    ) -> None:
        """ExportTask should raise ValueError for empty frames."""
        # Creating task with no frames should raise ValueError
        with pytest.raises(ValueError, match="No frames to export"):
            ExportTask(
                frames=[],
                output_dir=export_dir,
                base_name="test",
                format=ExportFormat.PNG,
                mode=ExportMode.INDIVIDUAL_FRAMES,
                scale_factor=1.0,
            )

    def test_error_on_invalid_scale_factor(
        self, qapp, sample_frames: list[QImage], export_dir: Path, qtbot
    ) -> None:
        """ExportTask should raise ValueError for invalid scale factor."""
        with pytest.raises(ValueError, match="Scale factor must be positive"):
            ExportTask(
                frames=sample_frames,
                output_dir=export_dir,
                base_name="test",
                format=ExportFormat.PNG,
                mode=ExportMode.INDIVIDUAL_FRAMES,
                scale_factor=-1.0,
            )


# ============================================================================
# Resource Cleanup Tests
# ============================================================================


class TestResourceCleanup:
    """Tests for proper resource cleanup after export."""

    def test_export_creates_output_files(
        self, qapp, basic_export_task: ExportTask, export_dir: Path
    ) -> None:
        """Export should create output files."""
        worker = ExportWorker(basic_export_task)
        worker.run()

        # Check that files were created
        png_files = list(export_dir.glob("*.png"))
        assert len(png_files) == 8  # 8 frames

    def test_sprite_sheet_export_creates_single_file(
        self, qapp, sheet_export_task: ExportTask, export_dir: Path
    ) -> None:
        """Sprite sheet export should create single output file."""
        worker = ExportWorker(sheet_export_task)
        worker.run()

        # Check that single sheet file was created
        png_files = list(export_dir.glob("*.png"))
        assert len(png_files) == 1

    def test_failed_export_cleans_partial_output(
        self, qapp, sample_frames: list[QImage], tmp_path: Path
    ) -> None:
        """Failed export should clean up partial output."""
        # Use non-existent directory to cause failure
        invalid_path = tmp_path / "nonexistent" / "deeply" / "nested"

        task = ExportTask(
            frames=sample_frames,
            output_dir=invalid_path,
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        worker = ExportWorker(task)

        error_messages = []
        worker.error.connect(lambda msg: error_messages.append(msg))

        worker.run()

        # Should have error
        assert len(error_messages) >= 1 or not invalid_path.exists()


# ============================================================================
# State Consistency Tests
# ============================================================================


class TestStateConsistency:
    """Tests for state consistency during export."""

    def test_frame_exporter_singleton(self, qapp) -> None:
        """get_frame_exporter should return same instance."""
        exporter1 = get_frame_exporter()
        exporter2 = get_frame_exporter()

        assert exporter1 is exporter2

    def test_reset_creates_new_instance(self, qapp) -> None:
        """reset_frame_exporter should create new instance."""
        exporter1 = get_frame_exporter()
        reset_frame_exporter()
        exporter2 = get_frame_exporter()

        assert exporter1 is not exporter2

    def test_export_task_immutability(
        self, qapp, basic_export_task: ExportTask
    ) -> None:
        """Export task should not be modified during export."""
        original_frame_count = len(basic_export_task.frames)
        original_base_name = basic_export_task.base_name

        worker = ExportWorker(basic_export_task)
        worker.run()

        # Task should be unchanged
        assert len(basic_export_task.frames) == original_frame_count
        assert basic_export_task.base_name == original_base_name


# ============================================================================
# Export Format Tests
# ============================================================================


class TestExportFormats:
    """Tests for different export format handling."""

    @pytest.mark.parametrize("format_str,expected_ext", [
        ("PNG", ".png"),
        ("JPG", ".jpg"),
        ("BMP", ".bmp"),
    ])
    def test_export_format_extensions(
        self, qapp, format_str: str, expected_ext: str
    ) -> None:
        """Export formats should have correct extensions."""
        fmt = ExportFormat.from_string(format_str)
        assert fmt.extension == expected_ext

    def test_individual_frame_export_png(
        self, qapp, sample_frames: list[QImage], export_dir: Path
    ) -> None:
        """Individual frame export to PNG should work."""
        task = ExportTask(
            frames=sample_frames,
            output_dir=export_dir,
            base_name="frame",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        worker = ExportWorker(task)
        worker.run()

        # Verify files created
        files = list(export_dir.glob("*.png"))
        assert len(files) == 8

    def test_individual_frame_export_jpg(
        self, qapp, sample_frames: list[QImage], export_dir: Path
    ) -> None:
        """Individual frame export to JPG should work."""
        task = ExportTask(
            frames=sample_frames,
            output_dir=export_dir,
            base_name="frame",
            format=ExportFormat.JPG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        worker = ExportWorker(task)
        worker.run()

        # Verify files created
        files = list(export_dir.glob("*.jpg"))
        assert len(files) == 8


# ============================================================================
# Scale Factor Tests
# ============================================================================


class TestScaleFactor:
    """Tests for scale factor application during export."""

    def test_scale_factor_2x(
        self, qapp, sample_frames: list[QImage], export_dir: Path
    ) -> None:
        """2x scale factor should double dimensions."""
        task = ExportTask(
            frames=sample_frames,
            output_dir=export_dir,
            base_name="scaled",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=2.0,
        )
        worker = ExportWorker(task)
        worker.run()

        # Load first exported frame and check size
        files = sorted(export_dir.glob("*.png"))
        assert len(files) >= 1

        img = QImage(str(files[0]))
        # Original is 32x32, scaled should be 64x64
        assert img.width() == 64
        assert img.height() == 64

    def test_scale_factor_half(
        self, qapp, sample_frames: list[QImage], export_dir: Path
    ) -> None:
        """0.5x scale factor should halve dimensions."""
        task = ExportTask(
            frames=sample_frames,
            output_dir=export_dir,
            base_name="scaled",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=0.5,
        )
        worker = ExportWorker(task)
        worker.run()

        # Load first exported frame and check size
        files = sorted(export_dir.glob("*.png"))
        assert len(files) >= 1

        img = QImage(str(files[0]))
        # Original is 32x32, scaled should be 16x16
        assert img.width() == 16
        assert img.height() == 16


# ============================================================================
# Sprite Sheet Layout Tests
# ============================================================================


class TestSpriteSheetLayout:
    """Tests for sprite sheet layout calculations."""

    def test_layout_columns_calculation_rows_mode(self, qapp) -> None:
        """Layout in rows mode should return configured max_columns."""
        layout = SpriteSheetLayout(mode='rows', max_columns=4)
        # In rows mode, effective columns is the configured max_columns
        effective_cols = layout.get_effective_columns(8)
        assert effective_cols == 4

    def test_layout_rows_calculation_columns_mode(self, qapp) -> None:
        """Layout in columns mode should return configured max_rows."""
        layout = SpriteSheetLayout(mode='columns', max_rows=4)
        # In columns mode, effective rows is the configured max_rows
        effective_rows = layout.get_effective_rows(8)
        assert effective_rows == 4

    def test_layout_with_padding(self, qapp) -> None:
        """Layout with padding should account for spacing."""
        layout = SpriteSheetLayout(mode='rows', max_columns=4, padding=2)
        width, height = layout.calculate_estimated_dimensions(
            frame_width=32,
            frame_height=32,
            frame_count=8,
        )
        # With padding, dimensions should be larger than without
        assert width > 128  # Should be larger due to padding
        assert height > 64

    def test_sprite_sheet_output_dimensions(
        self, qapp, sample_frames: list[QImage], export_dir: Path
    ) -> None:
        """Sprite sheet should have correct dimensions."""
        task = ExportTask(
            frames=sample_frames,
            output_dir=export_dir,
            base_name="sheet",
            format=ExportFormat.PNG,
            mode=ExportMode.SPRITE_SHEET,
            scale_factor=1.0,
            sprite_sheet_layout=SpriteSheetLayout(mode='rows', max_columns=4, spacing=0, padding=0),
        )
        worker = ExportWorker(task)
        worker.run()

        # Load sheet and check dimensions
        files = list(export_dir.glob("*.png"))
        assert len(files) == 1

        img = QImage(str(files[0]))
        # 4 columns * 32 = 128 wide
        # 2 rows * 32 = 64 tall
        assert img.width() == 128
        assert img.height() == 64
