#!/usr/bin/env python3
"""Visual demo to show the difference between widget zoom and content zoom."""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt


def create_demo_sprite():
    """Create a demo sprite with text to show scaling."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw background
    painter.fillRect(0, 0, 64, 64, QColor("#FF6B6B"))
    
    # Draw border
    painter.setPen(QColor("#C92A2A"))
    painter.drawRect(0, 0, 63, 63)
    
    # Draw text
    painter.setPen(Qt.white)
    font = QFont("Arial", 20, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "A")
    
    painter.end()
    return pixmap


class ZoomComparisonDemo(QMainWindow):
    """Demo showing widget zoom vs content zoom."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zoom Comparison Demo")
        self.setGeometry(100, 100, 600, 400)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Title
        title = QLabel("<h2>Widget Zoom vs Content Zoom</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Create comparison layout
        comparison_layout = QHBoxLayout()
        
        # Left side: Widget zoom (old behavior)
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setAlignment(Qt.AlignCenter)
        
        left_title = QLabel("<b>Widget Zoom (Old)</b>")
        left_title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(left_title)
        
        left_desc = QLabel("Entire widget changes size")
        left_desc.setAlignment(Qt.AlignCenter)
        left_desc.setStyleSheet("color: #666; font-size: 10px;")
        left_layout.addWidget(left_desc)
        
        # Create widget zoom examples
        for zoom in [0.5, 1.0, 1.5]:
            widget_label = QLabel()
            size = int(120 * zoom)
            widget_label.setFixedSize(size, size)
            widget_label.setAlignment(Qt.AlignCenter)
            widget_label.setStyleSheet("""
                QLabel {
                    border: 1px solid #DDD;
                    background-color: white;
                    border-radius: 4px;
                }
            """)
            
            # Scale the pixmap to fit
            sprite = create_demo_sprite()
            scaled_size = int(120 * zoom)
            scaled = sprite.scaled(scaled_size, scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            widget_label.setPixmap(scaled)
            
            zoom_label = QLabel(f"{int(zoom * 100)}%")
            zoom_label.setAlignment(Qt.AlignCenter)
            
            left_layout.addWidget(widget_label)
            left_layout.addWidget(zoom_label)
            left_layout.addSpacing(10)
        
        comparison_layout.addWidget(left_container)
        
        # Right side: Content zoom (new behavior)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setAlignment(Qt.AlignCenter)
        
        right_title = QLabel("<b>Content Zoom (New)</b>")
        right_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(right_title)
        
        right_desc = QLabel("Only sprite content scales")
        right_desc.setAlignment(Qt.AlignCenter)
        right_desc.setStyleSheet("color: #666; font-size: 10px;")
        right_layout.addWidget(right_desc)
        
        # Create content zoom examples
        for zoom in [0.5, 1.0, 1.5]:
            content_label = QLabel()
            content_label.setFixedSize(120, 120)  # Always same size
            content_label.setAlignment(Qt.AlignCenter)
            content_label.setStyleSheet("""
                QLabel {
                    border: 1px solid #DDD;
                    background-color: white;
                    border-radius: 4px;
                }
            """)
            
            # Scale only the content
            sprite = create_demo_sprite()
            scaled_size = int(120 * zoom)
            scaled = sprite.scaled(scaled_size, scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            content_label.setPixmap(scaled)
            
            zoom_label = QLabel(f"{int(zoom * 100)}%")
            zoom_label.setAlignment(Qt.AlignCenter)
            
            right_layout.addWidget(content_label)
            right_layout.addWidget(zoom_label)
            right_layout.addSpacing(10)
        
        comparison_layout.addWidget(right_container)
        
        layout.addLayout(comparison_layout)
        
        # Benefits explanation
        benefits = QLabel(
            "<p><b>Benefits of Content Zoom:</b></p>"
            "<ul>"
            "<li>Layout remains consistent</li>"
            "<li>More segments fit on screen when zoomed out</li>"
            "<li>UI elements stay the same size</li>"
            "<li>Better for comparing multiple animations</li>"
            "</ul>"
        )
        benefits.setWordWrap(True)
        layout.addWidget(benefits)


def main():
    """Run the demo."""
    app = QApplication(sys.argv)
    
    demo = ZoomComparisonDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()