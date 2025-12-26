"""Unit tests for sprite rendering utilities."""

import pytest
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect
from utils.sprite_rendering import draw_pixmap_safe, scale_pixmap_safe


def create_edge_test_pixmap(size=64):
    """Create a pixmap with content at the very edges."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    
    # Fill with color
    painter.fillRect(0, 0, size, size, QColor("#FF0000"))
    
    # Draw border at the very edge
    painter.setPen(QPen(Qt.black, 1))
    painter.drawRect(0, 0, size - 1, size - 1)
    
    # Draw markers at corners
    painter.setPen(QPen(Qt.yellow, 3))
    painter.drawPoint(0, 0)
    painter.drawPoint(size - 1, 0)
    painter.drawPoint(0, size - 1)
    painter.drawPoint(size - 1, size - 1)
    
    painter.end()
    return pixmap


class TestSpriteRendering:
    """Test sprite rendering utilities."""
    
    @pytest.mark.unit
    def test_scale_pixmap_safe_preserves_edges(self, qtbot):
        """Test that safe scaling preserves edge content."""
        # Create test pixmap
        original = create_edge_test_pixmap(64)
        
        # Scale down
        scaled = scale_pixmap_safe(original, 32, 32, preserve_aspect=True)
        
        # The scaled pixmap should be approximately the target size
        assert 30 <= scaled.width() <= 32
        assert 30 <= scaled.height() <= 32
        
        # Scale up
        scaled_up = scale_pixmap_safe(original, 128, 128, preserve_aspect=True)
        assert 126 <= scaled_up.width() <= 128
        assert 126 <= scaled_up.height() <= 128
    
    @pytest.mark.unit
    def test_scale_pixmap_safe_non_square(self, qtbot):
        """Test scaling non-square pixmaps."""
        # Create rectangular pixmap
        pixmap = QPixmap(100, 50)
        pixmap.fill(QColor("#00FF00"))
        
        # Scale with aspect ratio preserved
        scaled = scale_pixmap_safe(pixmap, 50, 50, preserve_aspect=True)
        
        # Should maintain aspect ratio
        aspect_ratio = scaled.width() / scaled.height()
        original_ratio = 100 / 50
        assert abs(aspect_ratio - original_ratio) < 0.1
    
    def test_draw_pixmap_safe(self, qtbot):
        """Test safe pixmap drawing."""
        # Create a widget to draw on
        from PySide6.QtWidgets import QLabel
        label = QLabel()
        label.setFixedSize(200, 200)
        qtbot.addWidget(label)
        
        # Create test pixmap
        test_pixmap = create_edge_test_pixmap(64)
        
        # Create a pixmap to draw on
        canvas = QPixmap(200, 200)
        canvas.fill(Qt.white)
        
        painter = QPainter(canvas)
        target_rect = QRect(50, 50, 100, 100)
        
        # Draw using safe method
        draw_pixmap_safe(painter, target_rect, test_pixmap, preserve_pixel_perfect=True)
        
        painter.end()
        
        # Set the pixmap on the label
        label.setPixmap(canvas)
        
        # The drawing should have completed without errors
        assert not canvas.isNull()
    
    @pytest.mark.unit
    def test_null_pixmap_handling(self, qtbot):
        """Test handling of null pixmaps."""
        # Null pixmap should return null
        result = scale_pixmap_safe(QPixmap(), 100, 100)
        assert result.isNull()
        
        # Drawing null pixmap should not crash
        canvas = QPixmap(100, 100)
        painter = QPainter(canvas)
        draw_pixmap_safe(painter, QRect(0, 0, 100, 100), QPixmap())
        painter.end()