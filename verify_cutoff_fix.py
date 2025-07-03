#!/usr/bin/env python3
"""Quick verification that the sprite cutoff fix is working."""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt

# Import the components we fixed
from ui.sprite_canvas import SpriteCanvas
from ui.animation_grid_view import FrameThumbnail
from ui.animation_segment_preview import SegmentPreviewItem


def create_test_sprite():
    """Create a sprite with visible edges for testing."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.white)
    
    painter = QPainter(pixmap)
    
    # Draw red background
    painter.fillRect(1, 1, size-2, size-2, Qt.red)
    
    # Draw black border at the very edge (should be visible)
    painter.setPen(QPen(Qt.black, 2))
    painter.drawRect(0, 0, size-1, size-1)
    
    # Draw yellow corners (should form perfect right angles)
    painter.setPen(QPen(Qt.yellow, 4))
    painter.drawLine(0, 0, 10, 0)
    painter.drawLine(0, 0, 0, 10)
    painter.drawLine(size-11, 0, size-1, 0)
    painter.drawLine(size-1, 0, size-1, 10)
    painter.drawLine(0, size-11, 0, size-1)
    painter.drawLine(0, size-1, 10, size-1)
    painter.drawLine(size-11, size-1, size-1, size-1)
    painter.drawLine(size-1, size-11, size-1, size-1)
    
    painter.end()
    return pixmap


def main():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Sprite Cutoff Fix Verification")
    window.setGeometry(100, 100, 800, 600)
    
    layout = QVBoxLayout(window)
    
    # Title
    title = QLabel("<h2>Sprite Edge Cutoff Fix Verification</h2>")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)
    
    info = QLabel(
        "All three views should show:\n"
        "• Complete black borders\n"
        "• Yellow corners forming perfect right angles\n"
        "• No edge pixels cut off"
    )
    layout.addWidget(info)
    
    test_sprite = create_test_sprite()
    
    # Test 1: Sprite Canvas
    canvas_label = QLabel("<b>1. Sprite Canvas (main view):</b>")
    layout.addWidget(canvas_label)
    
    canvas = SpriteCanvas()
    canvas.setMinimumHeight(150)
    canvas.set_pixmap(test_sprite, auto_fit=False)
    canvas.set_zoom(2.0)
    layout.addWidget(canvas)
    
    # Test 2: Animation Grid Thumbnail
    grid_label = QLabel("<b>2. Animation Grid Thumbnail:</b>")
    layout.addWidget(grid_label)
    
    thumbnail = FrameThumbnail(0, test_sprite, thumbnail_size=80)
    thumbnail.set_selected(True)  # Add border to test edge handling
    layout.addWidget(thumbnail)
    
    # Test 3: Animation Segment Preview
    segment_label = QLabel("<b>3. Animation Segment Preview:</b>")
    layout.addWidget(segment_label)
    
    frames = [test_sprite] * 4
    segment_preview = SegmentPreviewItem("Test", QColor("#FF0000"), frames)
    layout.addWidget(segment_preview)
    
    layout.addStretch()
    
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()