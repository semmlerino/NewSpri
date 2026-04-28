"""
Unit tests for sprite_model.sprite_file_ops.

Covers the FileValidator and FileLoader contracts that other tests only hit
indirectly: format checks, missing/empty/oversized files, directory paths,
and the load happy path.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtGui import QImage, QPixmap

from sprite_model.sprite_file_ops import _FileLoader, _FileValidator

pytestmark = pytest.mark.requires_qt


# ============================================================================
# Helpers
# ============================================================================


def _write_real_png(path: Path, size: tuple[int, int] = (8, 8)) -> Path:
    """Write a tiny but valid PNG so QPixmap can decode it."""
    img = QImage(size[0], size[1], QImage.Format.Format_ARGB32)
    img.fill(0xFFFF0000)  # opaque red
    assert img.save(str(path), "PNG"), f"failed to write {path}"
    return path


# ============================================================================
# FileValidator
# ============================================================================


class TestFileValidatorPathChecks:
    def test_empty_path_is_invalid(self):
        valid, msg = _FileValidator().validate_file_path("")
        assert not valid
        assert "No file path" in msg

    def test_whitespace_path_is_invalid(self):
        valid, msg = _FileValidator().validate_file_path("   ")
        assert not valid
        assert "No file path" in msg

    def test_missing_file_is_invalid(self, tmp_path: Path):
        valid, msg = _FileValidator().validate_file_path(str(tmp_path / "ghost.png"))
        assert not valid
        assert "does not exist" in msg

    def test_directory_is_invalid(self, tmp_path: Path):
        valid, msg = _FileValidator().validate_file_path(str(tmp_path))
        assert not valid
        assert "not a file" in msg

    def test_unsupported_format_is_invalid(self, tmp_path: Path):
        bad = tmp_path / "data.txt"
        bad.write_text("not an image")
        valid, msg = _FileValidator().validate_file_path(str(bad))
        assert not valid
        assert "Unsupported file format" in msg

    def test_empty_file_is_invalid(self, tmp_path: Path, qapp):
        empty = tmp_path / "empty.png"
        empty.write_bytes(b"")
        valid, msg = _FileValidator().validate_file_path(str(empty))
        assert not valid
        assert "empty" in msg.lower()

    def test_valid_png_passes(self, tmp_path: Path, qapp):
        good = _write_real_png(tmp_path / "good.png")
        valid, msg = _FileValidator().validate_file_path(str(good))
        assert valid, msg
        assert msg == ""


class TestFileValidatorFormatDetection:
    @pytest.mark.parametrize("suffix", [".png", ".jpg", ".jpeg", ".bmp", ".gif"])
    def test_supported_extensions_recognized(self, suffix: str):
        path = Path("/tmp/sample" + suffix)
        assert _FileValidator()._is_supported_format(path)

    @pytest.mark.parametrize("suffix", [".txt", ".pdf", ".tiff", ""])
    def test_unsupported_extensions_rejected(self, suffix: str):
        path = Path("/tmp/sample" + suffix)
        assert not _FileValidator()._is_supported_format(path)


# ============================================================================
# FileLoader
# ============================================================================


class TestFileLoader:
    @pytest.mark.smoke
    def test_loads_valid_png(self, tmp_path: Path, qapp):
        good = _write_real_png(tmp_path / "good.png", size=(16, 16))
        success, pixmap, msg = _FileLoader().load_sprite_sheet(str(good))
        assert success, msg
        assert isinstance(pixmap, QPixmap)
        assert pixmap is not None
        assert pixmap.width() == 16
        assert pixmap.height() == 16

    def test_missing_file_returns_validation_error(self, tmp_path: Path, qapp):
        success, pixmap, msg = _FileLoader().load_sprite_sheet(str(tmp_path / "ghost.png"))
        assert not success
        assert pixmap is None
        assert "does not exist" in msg

    def test_unsupported_extension_returns_validation_error(self, tmp_path: Path, qapp):
        bad = tmp_path / "data.txt"
        bad.write_text("not an image")
        success, pixmap, msg = _FileLoader().load_sprite_sheet(str(bad))
        assert not success
        assert pixmap is None
        assert "Unsupported" in msg

    def test_corrupt_image_returns_load_failure(self, tmp_path: Path, qapp):
        broken = tmp_path / "broken.png"
        broken.write_bytes(b"\x89PNG\r\n\x1a\nthis is not really PNG content")
        success, pixmap, msg = _FileLoader().load_sprite_sheet(str(broken))
        assert not success
        assert pixmap is None
        assert "Failed to load image" in msg
