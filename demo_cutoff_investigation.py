#!/usr/bin/env python3
"""Demo to investigate the underlying sprite cutoff issue across different views."""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QLabel, QHBoxLayout, QGridLayout, QPushButton)
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtCore import Qt, QRect


def create_test_sprite_with_full_edges():
    """Create a test sprite with content at all edges."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    
    # Fill with solid color
    painter.fillRect(0, 0, 64, 64, QColor("#FF6B6B"))
    
    # Draw thick border that touches all edges
    painter.setPen(QPen(Qt.black, 4))
    painter.drawRect(0, 0, 63, 63)
    
    # Draw distinctive corner markers
    painter.setPen(QPen(Qt.yellow, 6))
    # Top-left
    painter.drawLine(0, 0, 15, 0)
    painter.drawLine(0, 0, 0, 15)
    # Top-right
    painter.drawLine(48, 0, 63, 0)
    painter.drawLine(63, 0, 63, 15)
    # Bottom-left
    painter.drawLine(0, 48, 0, 63)
    painter.drawLine(0, 63, 15, 63)
    # Bottom-right
    painter.drawLine(48, 63, 63, 63)
    painter.drawLine(63, 48, 63, 63)
    
    # Draw edge lines
    painter.setPen(QPen(Qt.green, 2))
    # Top edge
    painter.drawLine(20, 0, 43, 0)
    # Bottom edge
    painter.drawLine(20, 63, 43, 63)
    # Left edge
    painter.drawLine(0, 20, 0, 43)
    # Right edge
    painter.drawLine(63, 20, 63, 43)
    
    painter.end()
    return pixmap


class TestCanvas(QLabel):
    """Test canvas with different rendering approaches."""
    
    def __init__(self, title, render_mode):
        super().__init__()
        self.title = title
        self.render_mode = render_mode
        self.pixmap = None
        self.zoom = 1.0
        self.setFixedSize(200, 200)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #333;
                background-color: #f0f0f0;
            }
        """)
    
    def set_sprite(self, pixmap):
        """Set the sprite to display."""
        self.pixmap = pixmap
        self.update()
    
    def set_zoom(self, zoom):
        """Set zoom level."""
        self.zoom = zoom
        self.update()
    
    def paintEvent(self, event):
        """Paint the sprite with specified render mode."""
        painter = QPainter(self)
        
        # Draw background grid
        painter.setPen(QColor(200, 200, 200))
        for i in range(0, 200, 20):
            painter.drawLine(i, 0, i, 200)
            painter.drawLine(0, i, 200, i)
        
        if not self.pixmap:
            return
        
        # Apply render mode settings
        if self.render_mode == "default":
            # Default Qt rendering
            pass
        elif self.render_mode == "no_smooth":
            painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        elif self.render_mode == "antialiased":
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        elif self.render_mode == "smooth":
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        elif self.render_mode == "all_hints":
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
        
        # Calculate scaled size
        scaled_width = int(self.pixmap.width() * self.zoom)
        scaled_height = int(self.pixmap.height() * self.zoom)
        
        # Center the sprite
        x = (200 - scaled_width) // 2
        y = (200 - scaled_height) // 2
        
        # Draw pixmap
        target_rect = QRect(x, y, scaled_width, scaled_height)
        painter.drawPixmap(target_rect, self.pixmap)
        
        # Draw info
        painter.setPen(Qt.black)
        painter.drawText(5, 15, self.title)
        painter.drawText(5, 195, f"Zoom: {self.zoom:.1f}x")


class CutoffInvestigationDemo(QMainWindow):
    """Demo to investigate sprite cutoff issues."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sprite Cutoff Investigation")
        self.setGeometry(100, 100, 1200, 700)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Title
        title = QLabel("<h2>Sprite Edge Cutoff Investigation</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "<p>This demo shows how sprites are rendered with different settings.</p>"
            "<p>The test sprite has:</p>"
            "<ul>"
            "<li>Black border (4px) at the very edge</li>"
            "<li>Yellow corner markers (should form perfect corners)</li>"
            "<li>Green edge markers (should touch the edge)</li>"
            "</ul>"
            "<p>If rendering is correct, all edge content should be visible.</p>"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Create test sprite
        self.test_sprite = create_test_sprite_with_full_edges()
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Zoom:")
        zoom_layout.addWidget(zoom_label)
        
        self.zoom_buttons = []
        for zoom in [0.5, 1.0, 1.5, 2.0, 3.0]:
            btn = QPushButton(f"{zoom}x")
            btn.clicked.connect(lambda checked, z=zoom: self.set_zoom(z))
            zoom_layout.addWidget(btn)
            self.zoom_buttons.append(btn)
        
        zoom_layout.addStretch()
        layout.addLayout(zoom_layout)
        
        # Canvas grid
        canvas_container = QWidget()
        canvas_layout = QGridLayout(canvas_container)
        
        # Create canvases with different render modes
        self.canvases = []
        modes = [
            ("Default", "default"),
            ("No Smooth", "no_smooth"),
            ("Antialiased", "antialiased"),
            ("Smooth", "smooth"),
            ("All Hints", "all_hints"),
        ]
        
        for i, (title, mode) in enumerate(modes):
            canvas = TestCanvas(title, mode)
            canvas.set_sprite(self.test_sprite)
            canvas_layout.addWidget(canvas, i // 3, i % 3)
            self.canvases.append(canvas)
        
        layout.addWidget(canvas_container)
        
        # Observations
        obs = QLabel(
            "<p><b>Expected Results:</b></p>"
            "<ul>"
            "<li>All yellow corners should form perfect right angles</li>"
            "<li>Green edge markers should be fully visible</li>"
            "<li>Black border should be visible on all sides</li>"
            "</ul>"
            "<p><b>Common Issues:</b></p>"
            "<ul>"
            "<li>Top/left edges may be cut off by 1-2 pixels</li>"
            "<li>Scaling may introduce artifacts at edges</li>"
            "<li>Different render hints may affect edge visibility</li>"
            "</ul>"
        )
        obs.setWordWrap(True)
        layout.addWidget(obs)
        
        # Set initial zoom
        self.set_zoom(1.0)
    
    def set_zoom(self, zoom):
        """Set zoom on all canvases."""
        for canvas in self.canvases:
            canvas.set_zoom(zoom)


def main():
    """Run the demo."""
    app = QApplication(sys.argv)
    
    demo = CutoffInvestigationDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()