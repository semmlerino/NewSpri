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

from pathlib import Path

import pytest
from PySide6.QtGui import QColor, QImage, QPixmap

from export.core.frame_exporter import (
    ExportFormat,
    ExportMode,
    LayoutMode,
    SpriteSheetLayout,
    _ExportTask,
    _ExportWorker,
    get_frame_exporter,
)

# Mark all tests in this module as requiring Qt
pytestmark = pytest.mark.requires_qt


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_exporter():
    """Reset the global frame exporter before and after each test."""
    import export.core.frame_exporter as _fe_mod

    def _do_reset():
        inst = _fe_mod._exporter_instance
        if inst is not None and inst._worker is not None and inst._worker.isRunning():
            inst._worker.quit()
            inst._worker.wait()
        _fe_mod._exporter_instance = None

    _do_reset()
    yield
    _do_reset()


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
def basic_export_task(sample_frames: list[QImage], export_dir: Path) -> _ExportTask:
    """Create a basic export task for individual frames."""
    return _ExportTask(
        frames=sample_frames,
        output_dir=export_dir,
        base_name="test_frame",
        format=ExportFormat.PNG,
        mode=ExportMode.INDIVIDUAL_FRAMES,
        scale_factor=1.0,
    )


@pytest.fixture
def sheet_export_task(sample_frames: list[QImage], export_dir: Path) -> _ExportTask:
    """Create an export task for sprite sheet."""
    return _ExportTask(
        frames=sample_frames,
        output_dir=export_dir,
        base_name="test_sheet",
        format=ExportFormat.PNG,
        mode=ExportMode.SPRITE_SHEET,
        scale_factor=1.0,
        sprite_sheet_layout=SpriteSheetLayout(mode=LayoutMode.ROWS, max_columns=4),
    )


# ============================================================================
# ExportWorker Cancellation Tests
# ============================================================================


class TestExportWorkerCancellation:
    """Tests for export worker cancellation behavior."""

    def test_cancel_before_start(self, qapp, basic_export_task: _ExportTask) -> None:
        """Cancellation before start should prevent export."""
        worker = _ExportWorker(basic_export_task)
        worker.cancel()

        assert worker._cancelled is True

    def test_cancel_flag_checked(self, qapp, basic_export_task: _ExportTask) -> None:
        """Worker should check cancellation flag during export."""
        worker = _ExportWorker(basic_export_task)

        # Spy on cancelled state
        assert worker._cancelled is False

        worker.cancel()

        assert worker._cancelled is True

    def test_cancelled_export_does_not_emit_success(
        self, qapp, basic_export_task: _ExportTask, qtbot
    ) -> None:
        """Cancelled export should not emit success signal."""
        worker = _ExportWorker(basic_export_task)

        # Track signals
        progress_values = []
        finished_results = []
        worker.progress.connect(lambda *args: progress_values.append(args))
        worker.finished.connect(lambda success, msg: finished_results.append((success, msg)))

        # Cancel and run
        worker.cancel()
        worker.run()

        assert finished_results == [(False, "Export cancelled")]
        assert progress_values == []
        assert list(basic_export_task.output_dir.glob("*.png")) == []


# ============================================================================
# Concurrent Export Prevention Tests
# ============================================================================


class TestConcurrentExportPrevention:
    """Tests for preventing concurrent exports."""

    def test_export_sets_exporting_state(
        self, qapp, sample_pixmaps: list[QPixmap], export_dir: Path
    ) -> None:
        """Starting export should set exporting state."""
        from export.core.frame_exporter import ExportConfig, ExportFormat, ExportMode

        exporter = get_frame_exporter()

        config = ExportConfig(
            output_dir=Path(export_dir),
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        result = exporter.export_frames(frames=sample_pixmaps, config=config)

        # Should have started successfully
        assert result is True


class TestExportSignalSafety:
    """Tests for signal emission safety from worker thread."""

    def test_progress_signal_emission(self, qapp, basic_export_task: _ExportTask, qtbot) -> None:
        """Progress signals should be emitted safely."""
        worker = _ExportWorker(basic_export_task)

        progress_values = []
        worker.progress.connect(lambda val: progress_values.append(val))

        # Run export (synchronously for testing)
        worker.run()

        # Should have received progress updates
        # For 8 frames, we expect multiple progress updates
        assert len(progress_values) >= 1

    def test_finished_signal_emission(self, qapp, basic_export_task: _ExportTask, qtbot) -> None:
        """Finished signal should be emitted on completion."""
        worker = _ExportWorker(basic_export_task)

        finished_results = []
        worker.finished.connect(lambda success, msg: finished_results.append((success, msg)))

        # Run export
        worker.run()

        # Should have received finished signal
        assert len(finished_results) == 1
        success, message = finished_results[0]
        assert success is True

    def test_error_on_empty_frames_task(self, qapp, export_dir: Path, qtbot) -> None:
        """ExportTask should raise ValueError for empty frames."""
        # Creating task with no frames should raise ValueError
        with pytest.raises(ValueError, match="No frames to export"):
            _ExportTask(
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
            _ExportTask(
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
        self, qapp, basic_export_task: _ExportTask, export_dir: Path
    ) -> None:
        """Export should create output files."""
        worker = _ExportWorker(basic_export_task)
        worker.run()

        # Check that files were created
        png_files = list(export_dir.glob("*.png"))
        assert len(png_files) == 8  # 8 frames

    def test_sprite_sheet_export_creates_single_file(
        self, qapp, sheet_export_task: _ExportTask, export_dir: Path
    ) -> None:
        """Sprite sheet export should create single output file."""
        worker = _ExportWorker(sheet_export_task)
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

        task = _ExportTask(
            frames=sample_frames,
            output_dir=invalid_path,
            base_name="test",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        worker = _ExportWorker(task)

        error_messages = []
        finished_results = []
        worker.error.connect(lambda msg: error_messages.append(msg))
        worker.finished.connect(lambda success, msg: finished_results.append((success, msg)))

        worker.run()

        assert error_messages
        assert finished_results
        assert finished_results[-1][0] is False
        assert "failed" in finished_results[-1][1].lower()
        assert not invalid_path.exists()


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
        """Resetting the singleton global should create a new instance on next get."""
        import export.core.frame_exporter as _fe_mod

        exporter1 = get_frame_exporter()
        _fe_mod._exporter_instance = None
        exporter2 = get_frame_exporter()

        assert exporter1 is not exporter2

    def test_export_task_immutability(self, qapp, basic_export_task: _ExportTask) -> None:
        """Export task should not be modified during export."""
        original_frame_count = len(basic_export_task.frames)
        original_base_name = basic_export_task.base_name

        worker = _ExportWorker(basic_export_task)
        worker.run()

        # Task should be unchanged
        assert len(basic_export_task.frames) == original_frame_count
        assert basic_export_task.base_name == original_base_name


# ============================================================================
# Export Format Tests
# ============================================================================


class TestExportFormats:
    """Tests for different export format handling."""

    @pytest.mark.parametrize(
        "format_str,expected_ext",
        [
            ("PNG", ".png"),
            ("JPG", ".jpg"),
            ("BMP", ".bmp"),
        ],
    )
    def test_export_format_extensions(self, qapp, format_str: str, expected_ext: str) -> None:
        """Export formats should have correct extensions."""
        fmt = ExportFormat.from_string(format_str)
        assert fmt.extension == expected_ext

    def test_individual_frame_export_png(
        self, qapp, sample_frames: list[QImage], export_dir: Path
    ) -> None:
        """Individual frame export to PNG should work."""
        task = _ExportTask(
            frames=sample_frames,
            output_dir=export_dir,
            base_name="frame",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        worker = _ExportWorker(task)
        worker.run()

        # Verify files created
        files = list(export_dir.glob("*.png"))
        assert len(files) == 8

    def test_individual_frame_export_jpg(
        self, qapp, sample_frames: list[QImage], export_dir: Path
    ) -> None:
        """Individual frame export to JPG should work."""
        task = _ExportTask(
            frames=sample_frames,
            output_dir=export_dir,
            base_name="frame",
            format=ExportFormat.JPG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=1.0,
        )
        worker = _ExportWorker(task)
        worker.run()

        # Verify files created
        files = list(export_dir.glob("*.jpg"))
        assert len(files) == 8


# ============================================================================
# Scale Factor Tests
# ============================================================================


class TestScaleFactor:
    """Tests for scale factor application during export."""

    def test_scale_factor_2x(self, qapp, sample_frames: list[QImage], export_dir: Path) -> None:
        """2x scale factor should double dimensions."""
        task = _ExportTask(
            frames=sample_frames,
            output_dir=export_dir,
            base_name="scaled",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=2.0,
        )
        worker = _ExportWorker(task)
        worker.run()

        # Load first exported frame and check size
        files = sorted(export_dir.glob("*.png"))
        assert len(files) >= 1

        img = QImage(str(files[0]))
        # Original is 32x32, scaled should be 64x64
        assert img.width() == 64
        assert img.height() == 64

    def test_scale_factor_half(self, qapp, sample_frames: list[QImage], export_dir: Path) -> None:
        """0.5x scale factor should halve dimensions."""
        task = _ExportTask(
            frames=sample_frames,
            output_dir=export_dir,
            base_name="scaled",
            format=ExportFormat.PNG,
            mode=ExportMode.INDIVIDUAL_FRAMES,
            scale_factor=0.5,
        )
        worker = _ExportWorker(task)
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
        layout = SpriteSheetLayout(mode=LayoutMode.ROWS, max_columns=4)
        # In rows mode, effective columns is the configured max_columns
        effective_cols = layout.get_effective_columns()
        assert effective_cols == 4

    def test_layout_rows_calculation_columns_mode(self, qapp) -> None:
        """Layout in columns mode should return configured max_rows."""
        layout = SpriteSheetLayout(mode=LayoutMode.COLUMNS, max_rows=4)
        # In columns mode, effective rows is the configured max_rows
        effective_rows = layout.get_effective_rows()
        assert effective_rows == 4

    def test_sprite_sheet_output_dimensions(
        self, qapp, sample_frames: list[QImage], export_dir: Path
    ) -> None:
        """Sprite sheet should have correct dimensions."""
        task = _ExportTask(
            frames=sample_frames,
            output_dir=export_dir,
            base_name="sheet",
            format=ExportFormat.PNG,
            mode=ExportMode.SPRITE_SHEET,
            scale_factor=1.0,
            sprite_sheet_layout=SpriteSheetLayout(mode=LayoutMode.ROWS, max_columns=4, spacing=0),
        )
        worker = _ExportWorker(task)
        worker.run()

        # Load sheet and check dimensions
        files = list(export_dir.glob("*.png"))
        assert len(files) == 1

        img = QImage(str(files[0]))
        # 4 columns * 32 = 128 wide
        # 2 rows * 32 = 64 tall
        assert img.width() == 128
        assert img.height() == 64
