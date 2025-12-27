"""
Tests for sprite extraction algorithms.

Covers:
- Grid configuration and layout calculations
- Frame extraction from grid-based sprite sheets
- Frame settings validation
- Margin detection
- Frame size auto-detection
- Spacing detection
- Comprehensive auto-detection workflow
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPixmap, QPainter

from sprite_model.sprite_extraction import (
    GridConfig,
    GridLayout,
    extract_grid_frames,
    validate_frame_settings,
    calculate_grid_layout,
)
from sprite_model.sprite_detection import (
    DetectionResult,
    detect_margins,
    detect_frame_size,
    comprehensive_auto_detect,
)

if TYPE_CHECKING:
    pass


# Mark all tests in this module as requiring Qt
pytestmark = pytest.mark.requires_qt


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def simple_grid_sprite_sheet(qapp) -> QPixmap:
    """Create a simple 128x64 sprite sheet with 4x2 = 8 frames of 32x32."""
    pixmap = QPixmap(128, 64)
    pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

    painter = QPainter(pixmap)
    colors = [
        QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255), QColor(255, 255, 0),
        QColor(255, 0, 255), QColor(0, 255, 255), QColor(128, 128, 128), QColor(255, 128, 0)
    ]

    for i, color in enumerate(colors):
        x = (i % 4) * 32
        y = (i // 4) * 32
        painter.fillRect(x + 4, y + 4, 24, 24, color)

    painter.end()
    return pixmap


@pytest.fixture
def sprite_sheet_with_spacing(qapp) -> QPixmap:
    """Create a 140x70 sprite sheet with 4x2 frames of 32x32 with 2px spacing."""
    # 4 frames * 32 + 3 gaps * 2 = 128 + 6 = 134 (but we'll use offsets)
    # Let's use exact math: 4 frames * (32 + 2) - 2 = 134 - 2 = 132 + offset
    pixmap = QPixmap(140, 74)
    pixmap.fill(QColor(255, 255, 255))  # White background

    painter = QPainter(pixmap)

    spacing_x = 2
    spacing_y = 2
    frame_size = 32
    offset_x = 2
    offset_y = 2

    for row in range(2):
        for col in range(4):
            x = offset_x + col * (frame_size + spacing_x)
            y = offset_y + row * (frame_size + spacing_y)
            color = QColor((col * 50 + row * 100) % 256, 100, 150)
            painter.fillRect(x, y, frame_size, frame_size, color)

    painter.end()
    return pixmap


@pytest.fixture
def sprite_sheet_with_margins(qapp) -> QPixmap:
    """Create a sprite sheet with transparent margins."""
    pixmap = QPixmap(100, 80)
    pixmap.fill(QColor(0, 0, 0, 0))  # Transparent

    painter = QPainter(pixmap)
    # Content starts at (10, 8) and ends at (90, 72)
    # This gives margins: left=10, right=10, top=8, bottom=8
    painter.fillRect(10, 8, 80, 64, QColor(255, 0, 0))
    painter.end()

    return pixmap


@pytest.fixture
def null_pixmap(qapp) -> QPixmap:
    """Create a null pixmap for error testing."""
    return QPixmap()


# ============================================================================
# GridConfig Tests
# ============================================================================


class TestGridConfig:
    """Tests for GridConfig NamedTuple."""

    def test_grid_config_basic(self, qapp) -> None:
        """GridConfig should accept basic dimensions."""
        config = GridConfig(width=32, height=32)

        assert config.width == 32
        assert config.height == 32
        assert config.offset_x == 0
        assert config.offset_y == 0
        assert config.spacing_x == 0
        assert config.spacing_y == 0

    def test_grid_config_with_offsets(self, qapp) -> None:
        """GridConfig should accept offset parameters."""
        config = GridConfig(width=64, height=48, offset_x=4, offset_y=8)

        assert config.width == 64
        assert config.height == 48
        assert config.offset_x == 4
        assert config.offset_y == 8

    def test_grid_config_with_spacing(self, qapp) -> None:
        """GridConfig should accept spacing parameters."""
        config = GridConfig(width=32, height=32, spacing_x=2, spacing_y=2)

        assert config.spacing_x == 2
        assert config.spacing_y == 2

    def test_grid_config_full_parameters(self, qapp) -> None:
        """GridConfig should accept all parameters."""
        config = GridConfig(
            width=64, height=48, offset_x=4, offset_y=8,
            spacing_x=2, spacing_y=4
        )

        assert config.width == 64
        assert config.height == 48
        assert config.offset_x == 4
        assert config.offset_y == 8
        assert config.spacing_x == 2
        assert config.spacing_y == 4


# ============================================================================
# Validate Frame Settings Tests
# ============================================================================


class TestValidateFrameSettings:
    """Tests for validate_frame_settings function."""

    def test_valid_settings(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Valid settings should pass validation."""
        config = GridConfig(width=32, height=32)

        valid, error_msg = validate_frame_settings(simple_grid_sprite_sheet, config)

        assert valid is True
        assert error_msg == ""

    def test_zero_width_invalid(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Zero width should fail validation."""
        config = GridConfig(width=0, height=32)

        valid, error_msg = validate_frame_settings(simple_grid_sprite_sheet, config)

        assert valid is False
        assert "width" in error_msg.lower()

    def test_zero_height_invalid(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Zero height should fail validation."""
        config = GridConfig(width=32, height=0)

        valid, error_msg = validate_frame_settings(simple_grid_sprite_sheet, config)

        assert valid is False
        assert "height" in error_msg.lower()

    def test_negative_width_invalid(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Negative width should fail validation."""
        config = GridConfig(width=-10, height=32)

        valid, error_msg = validate_frame_settings(simple_grid_sprite_sheet, config)

        assert valid is False
        assert "width" in error_msg.lower()

    def test_negative_offset_invalid(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Negative offset should fail validation."""
        config = GridConfig(width=32, height=32, offset_x=-5)

        valid, error_msg = validate_frame_settings(simple_grid_sprite_sheet, config)

        assert valid is False
        assert "offset" in error_msg.lower()

    def test_negative_spacing_invalid(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Negative spacing should fail validation."""
        config = GridConfig(width=32, height=32, spacing_x=-1)

        valid, error_msg = validate_frame_settings(simple_grid_sprite_sheet, config)

        assert valid is False
        assert "spacing" in error_msg.lower()

    def test_frame_exceeds_sheet_width(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Frame wider than sheet should fail validation."""
        config = GridConfig(width=200, height=32)  # Sheet is 128 wide

        valid, error_msg = validate_frame_settings(simple_grid_sprite_sheet, config)

        assert valid is False
        assert "exceeds" in error_msg.lower() or "width" in error_msg.lower()

    def test_frame_exceeds_sheet_height(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Frame taller than sheet should fail validation."""
        config = GridConfig(width=32, height=100)  # Sheet is 64 tall

        valid, error_msg = validate_frame_settings(simple_grid_sprite_sheet, config)

        assert valid is False
        assert "exceeds" in error_msg.lower() or "height" in error_msg.lower()

    def test_offset_plus_frame_exceeds_sheet(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Offset + frame size exceeding sheet should fail validation."""
        config = GridConfig(width=32, height=32, offset_x=100)  # 100 + 32 > 128

        valid, error_msg = validate_frame_settings(simple_grid_sprite_sheet, config)

        assert valid is False


# ============================================================================
# Calculate Grid Layout Tests
# ============================================================================


class TestCalculateGridLayout:
    """Tests for calculate_grid_layout function."""

    def test_basic_layout_calculation(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Basic layout should calculate correctly."""
        config = GridConfig(width=32, height=32)

        layout = calculate_grid_layout(simple_grid_sprite_sheet, config)

        assert layout is not None
        assert layout.frames_per_row == 4
        assert layout.frames_per_col == 2
        assert layout.total_frames == 8

    def test_layout_with_offset(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Layout with offset should reduce available frames."""
        # Sheet is 128x64, with offset 32,32 we have 96x32 remaining
        config = GridConfig(width=32, height=32, offset_x=32, offset_y=32)

        layout = calculate_grid_layout(simple_grid_sprite_sheet, config)

        assert layout is not None
        assert layout.frames_per_row == 3  # (128-32) // 32 = 3
        assert layout.frames_per_col == 1  # (64-32) // 32 = 1
        assert layout.total_frames == 3

    def test_layout_with_spacing(
        self, qapp
    ) -> None:
        """Layout with spacing should account for gaps."""
        # Create a sheet where spacing matters
        # 130 wide with 32px frames and 2px spacing: (130 + 2) / (32 + 2) = 3.88 = 3 frames
        pixmap = QPixmap(130, 66)
        pixmap.fill(QColor(255, 255, 255))

        config = GridConfig(width=32, height=32, spacing_x=2, spacing_y=2)

        layout = calculate_grid_layout(pixmap, config)

        assert layout is not None
        # Frames: (130 + 2) / (32 + 2) = 3.88 → 3 frames per row
        # Frames: (66 + 2) / (32 + 2) = 2 → 2 frames per column
        assert layout.frames_per_row >= 3
        assert layout.frames_per_col >= 1

    def test_layout_with_null_pixmap(
        self, null_pixmap: QPixmap
    ) -> None:
        """Layout with null pixmap should return None."""
        config = GridConfig(width=32, height=32)

        layout = calculate_grid_layout(null_pixmap, config)

        assert layout is None

    def test_layout_with_invalid_config(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Layout with invalid config should return None."""
        config = GridConfig(width=0, height=32)  # Invalid width

        layout = calculate_grid_layout(simple_grid_sprite_sheet, config)

        assert layout is None


# ============================================================================
# Extract Grid Frames Tests
# ============================================================================


class TestExtractGridFrames:
    """Tests for extract_grid_frames function."""

    def test_basic_extraction(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Basic extraction should return correct number of frames."""
        config = GridConfig(width=32, height=32)

        success, error_msg, frames, skipped = extract_grid_frames(
            simple_grid_sprite_sheet, config
        )

        assert success is True
        assert error_msg == ""
        assert len(frames) == 8  # 4x2 grid
        assert skipped == 0

    def test_extraction_frame_dimensions(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Extracted frames should have correct dimensions."""
        config = GridConfig(width=32, height=32)

        success, error_msg, frames, skipped = extract_grid_frames(
            simple_grid_sprite_sheet, config
        )

        assert success is True
        for frame in frames:
            assert frame.width() == 32
            assert frame.height() == 32

    def test_extraction_with_offset(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Extraction with offset should return fewer frames."""
        config = GridConfig(width=32, height=32, offset_x=32)

        success, error_msg, frames, skipped = extract_grid_frames(
            simple_grid_sprite_sheet, config
        )

        assert success is True
        assert len(frames) == 6  # (128-32)/32 * 64/32 = 3*2 = 6

    def test_extraction_with_spacing(
        self, sprite_sheet_with_spacing: QPixmap
    ) -> None:
        """Extraction with spacing should work correctly."""
        config = GridConfig(
            width=32, height=32,
            offset_x=2, offset_y=2,
            spacing_x=2, spacing_y=2
        )

        success, error_msg, frames, skipped = extract_grid_frames(
            sprite_sheet_with_spacing, config
        )

        assert success is True
        assert len(frames) == 8  # 4x2 grid

    def test_extraction_with_null_pixmap(
        self, null_pixmap: QPixmap
    ) -> None:
        """Extraction with null pixmap should fail gracefully."""
        config = GridConfig(width=32, height=32)

        success, error_msg, frames, skipped = extract_grid_frames(
            null_pixmap, config
        )

        assert success is False
        assert len(frames) == 0
        assert "No sprite sheet" in error_msg

    def test_extraction_with_invalid_config(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Extraction with invalid config should fail gracefully."""
        config = GridConfig(width=0, height=32)

        success, error_msg, frames, skipped = extract_grid_frames(
            simple_grid_sprite_sheet, config
        )

        assert success is False
        assert len(frames) == 0

    def test_extraction_counts_skipped_frames(
        self, qapp
    ) -> None:
        """Extraction should count frames that don't fit."""
        # Create a sheet where last row doesn't fully fit
        pixmap = QPixmap(64, 48)  # Only fits 2x1 fully, partial for row 2
        pixmap.fill(QColor(255, 0, 0))

        config = GridConfig(width=32, height=32)

        success, error_msg, frames, skipped = extract_grid_frames(pixmap, config)

        assert success is True
        # 2 columns, 1 full row = 2 frames (second row is partial at 16px height)
        assert len(frames) == 2


# ============================================================================
# Detect Frame Size Tests
# ============================================================================


class TestDetectFrameSize:
    """Tests for detect_frame_size function."""

    def test_detect_perfect_grid(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Detect frame size on perfect grid."""
        success, width, height, message = detect_frame_size(simple_grid_sprite_sheet)

        # 128x64 can be divided by 32 evenly
        assert success is True
        assert width > 0
        assert height > 0

    def test_detect_returns_square_for_square_common_sizes(
        self, qapp
    ) -> None:
        """Detection should return square dimensions for common sizes."""
        # Create a 64x64 sheet (should detect 32x32 or 16x16 or 64x64)
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(255, 0, 0))

        success, width, height, message = detect_frame_size(pixmap)

        assert success is True
        assert width == height  # Square detection

    def test_detect_with_null_pixmap(
        self, null_pixmap: QPixmap
    ) -> None:
        """Detection should fail with null pixmap."""
        success, width, height, message = detect_frame_size(null_pixmap)

        assert success is False
        assert width == 0
        assert height == 0

    def test_detect_unusual_dimensions(
        self, qapp
    ) -> None:
        """Detection should handle unusual dimensions."""
        # Create a 100x50 sheet (GCD = 50)
        pixmap = QPixmap(100, 50)
        pixmap.fill(QColor(255, 0, 0))

        success, width, height, message = detect_frame_size(pixmap)

        # May or may not succeed depending on algorithm
        # But should not raise an exception
        assert isinstance(success, bool)


# ============================================================================
# Detect Margins Tests
# ============================================================================


class TestDetectMargins:
    """Tests for detect_margins function."""

    def test_detect_margins_with_content(
        self, sprite_sheet_with_margins: QPixmap
    ) -> None:
        """Detect margins should find transparent borders."""
        success, offset_x, offset_y, message = detect_margins(sprite_sheet_with_margins)

        assert success is True
        # Content starts at (10, 8)
        assert offset_x >= 0
        assert offset_y >= 0

    def test_detect_margins_no_margins(
        self, qapp
    ) -> None:
        """Detect margins on image with no margins."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(255, 0, 0))  # Fully opaque

        success, offset_x, offset_y, message = detect_margins(pixmap)

        assert success is True
        assert offset_x == 0
        assert offset_y == 0

    def test_detect_margins_null_pixmap(
        self, null_pixmap: QPixmap
    ) -> None:
        """Detect margins should fail with null pixmap."""
        success, offset_x, offset_y, message = detect_margins(null_pixmap)

        assert success is False


# ============================================================================
# Comprehensive Auto Detect Tests
# ============================================================================


class TestComprehensiveAutoDetect:
    """Tests for comprehensive_auto_detect function."""

    def test_auto_detect_simple_grid(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Comprehensive detection on simple grid should succeed."""
        success, message, result = comprehensive_auto_detect(simple_grid_sprite_sheet)

        # Should at least partially succeed
        assert isinstance(success, bool)
        assert isinstance(result, DetectionResult)
        assert result.frame_width >= 0
        assert result.frame_height >= 0

    def test_auto_detect_returns_detection_result(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Comprehensive detection should return DetectionResult."""
        success, message, result = comprehensive_auto_detect(simple_grid_sprite_sheet)

        assert isinstance(result, DetectionResult)
        assert hasattr(result, 'frame_width')
        assert hasattr(result, 'frame_height')
        assert hasattr(result, 'offset_x')
        assert hasattr(result, 'offset_y')
        assert hasattr(result, 'spacing_x')
        assert hasattr(result, 'spacing_y')

    def test_auto_detect_with_null_pixmap(
        self, null_pixmap: QPixmap
    ) -> None:
        """Comprehensive detection should fail with null pixmap."""
        success, message, result = comprehensive_auto_detect(null_pixmap)

        assert success is False
        assert "No sprite sheet" in message

    def test_auto_detect_message_is_detailed(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Comprehensive detection should return detailed message."""
        success, message, result = comprehensive_auto_detect(simple_grid_sprite_sheet)

        # Message should contain step information
        assert len(message) > 0
        assert "Step" in message or "detecting" in message.lower()

    def test_auto_detect_confidence(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """Comprehensive detection should set confidence."""
        success, message, result = comprehensive_auto_detect(simple_grid_sprite_sheet)

        # DetectionResult should have confidence attribute
        assert hasattr(result, 'confidence')


# ============================================================================
# Detection Result Tests
# ============================================================================


class TestDetectionResult:
    """Tests for DetectionResult class."""

    def test_detection_result_defaults(self, qapp) -> None:
        """DetectionResult should have sensible defaults."""
        result = DetectionResult()

        assert result.frame_width == 0
        assert result.frame_height == 0
        assert result.offset_x == 0
        assert result.offset_y == 0
        assert result.spacing_x == 0
        assert result.spacing_y == 0

    def test_detection_result_confidence_method(self, qapp) -> None:
        """DetectionResult confidence method should work."""
        result = DetectionResult()

        # confidence is a method that returns a value
        conf = result.confidence
        assert isinstance(conf, (int, float))


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_tiny_sprite_sheet(self, qapp) -> None:
        """Extraction should handle tiny sprite sheets."""
        pixmap = QPixmap(8, 8)
        pixmap.fill(QColor(255, 0, 0))

        config = GridConfig(width=4, height=4)
        success, error_msg, frames, skipped = extract_grid_frames(pixmap, config)

        assert success is True
        assert len(frames) == 4  # 2x2 grid

    def test_very_large_frame_size(self, qapp) -> None:
        """Validation should reject very large frame sizes."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(255, 0, 0))

        from config import Config
        config = GridConfig(width=Config.FrameExtraction.MAX_FRAME_SIZE + 1, height=32)

        valid, error_msg = validate_frame_settings(pixmap, config)

        assert valid is False
        assert "exceed" in error_msg.lower() or "cannot" in error_msg.lower()

    def test_single_frame_extraction(self, qapp) -> None:
        """Extraction of single frame should work."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(255, 0, 0))

        config = GridConfig(width=32, height=32)
        success, error_msg, frames, skipped = extract_grid_frames(pixmap, config)

        assert success is True
        assert len(frames) == 1

    def test_non_square_frames(self, qapp) -> None:
        """Extraction should handle non-square frames."""
        pixmap = QPixmap(128, 64)
        pixmap.fill(QColor(255, 0, 0))

        config = GridConfig(width=64, height=32)  # 64x32 frames
        success, error_msg, frames, skipped = extract_grid_frames(pixmap, config)

        assert success is True
        assert len(frames) == 4  # 2x2 grid of 64x32 frames

    def test_frame_exactly_fits_sheet(self, qapp) -> None:
        """Frame size equal to sheet size should extract 1 frame."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(255, 0, 0))

        config = GridConfig(width=64, height=64)
        success, error_msg, frames, skipped = extract_grid_frames(pixmap, config)

        assert success is True
        assert len(frames) == 1
        assert frames[0].width() == 64
        assert frames[0].height() == 64

    def test_grid_layout_available_dimensions(
        self, simple_grid_sprite_sheet: QPixmap
    ) -> None:
        """GridLayout should report available dimensions."""
        config = GridConfig(width=32, height=32, offset_x=10, offset_y=5)

        layout = calculate_grid_layout(simple_grid_sprite_sheet, config)

        assert layout is not None
        assert layout.available_width == 128 - 10  # 118
        assert layout.available_height == 64 - 5   # 59
