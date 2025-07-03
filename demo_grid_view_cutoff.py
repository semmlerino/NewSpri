#!/usr/bin/env python3
"""Demo to show the animation grid view frame display fix for cutoff issues."""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QGridLayout
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from PySide6.QtCore import Qt
from ui.animation_grid_view import FrameThumbnail, AnimationSegment


def create_test_sprite_with_edges():
    """Create a test sprite with visible edges to show cutoff."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Fill with gradient
    painter.fillRect(0, 0, 64, 64, QColor("#FF6B6B"))
    
    # Draw thick border to make cutoff obvious
    pen = QPen(Qt.black, 3)
    painter.setPen(pen)
    painter.drawRect(0, 0, 63, 63)
    
    # Draw corner markers
    painter.setPen(QPen(Qt.yellow, 5))
    # Top-left corner
    painter.drawLine(0, 0, 10, 0)
    painter.drawLine(0, 0, 0, 10)
    # Top-right corner
    painter.drawLine(53, 0, 63, 0)
    painter.drawLine(63, 0, 63, 10)
    # Bottom-left corner
    painter.drawLine(0, 53, 0, 63)
    painter.drawLine(0, 63, 10, 63)
    # Bottom-right corner
    painter.drawLine(53, 63, 63, 63)
    painter.drawLine(63, 53, 63, 63)
    
    # Draw text
    painter.setPen(Qt.white)
    font = QFont("Arial", 24, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "F")
    
    painter.end()
    return pixmap


class GridViewCutoffDemo(QMainWindow):
    """Demo showing the grid view cutoff fix."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Animation Grid View - Frame Display Fix Demo")
        self.setGeometry(100, 100, 800, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Title
        title = QLabel("<h2>Animation Grid View Frame Display</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "<p>This demo shows how frames are displayed in the animation grid view:</p>"
            "<ul>"
            "<li>Frames have visible black borders and yellow corner markers</li>"
            "<li>If corners are cut off, the yellow markers won't be fully visible</li>"
            "<li>The fix ensures proper padding to prevent any cutoff</li>"
            "</ul>"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Create grid layout for frames
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(10)
        
        # Create test sprite
        test_sprite = create_test_sprite_with_edges()
        
        # Add frames in different states
        states = [
            ("Normal", False, False, None),
            ("Selected", True, False, None),
            ("Segment", False, False, QColor("#E91E63")),
            ("Segment Start", False, True, QColor("#2196F3")),
        ]
        
        for i, (label_text, selected, is_segment_start, segment_color) in enumerate(states):
            # Label
            label = QLabel(f"<b>{label_text}:</b>")
            grid_layout.addWidget(label, i, 0, Qt.AlignRight)
            
            # Frame thumbnail
            thumbnail = FrameThumbnail(i, test_sprite, thumbnail_size=80)
            
            if selected:
                thumbnail.set_selected(True)
            
            if segment_color:
                thumbnail.set_segment_markers(
                    is_start=is_segment_start,
                    is_end=False,
                    color=segment_color
                )
            
            grid_layout.addWidget(thumbnail, i, 1, Qt.AlignLeft)
            
            # Description
            if i == 0:
                desc_text = "Standard frame with 1px border"
            elif i == 1:
                desc_text = "Selected frame with 3px green border"
            elif i == 2:
                desc_text = "Part of segment with 3px colored border"
            else:
                desc_text = "Segment start with 5px left border"
            
            desc_label = QLabel(desc_text)
            desc_label.setStyleSheet("color: #666;")
            grid_layout.addWidget(desc_label, i, 2)
        
        layout.addWidget(grid_container)
        
        # Technical details
        tech_details = QLabel(
            "<p><b>Technical Details:</b></p>"
            "<ul>"
            "<li>Widget size: 88x88 pixels (80 + 8 for borders)</li>"
            "<li>Margin: 2px on each side</li>"
            "<li>Padding: 2px on each side</li>"
            "<li>Border: 1-5px depending on state</li>"
            "<li>Content area: 74x74 pixels (80 - 6 for safety)</li>"
            "</ul>"
            "<p>The 6px reduction ensures content fits even with the thickest borders.</p>"
        )
        tech_details.setWordWrap(True)
        layout.addWidget(tech_details)
        
        layout.addStretch()


def main():
    """Run the demo."""
    app = QApplication(sys.argv)
    
    demo = GridViewCutoffDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()