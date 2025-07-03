#!/usr/bin/env python3
"""Demo script to showcase the frame hold features including 'Add Hold to All Frames'."""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt
from ui.animation_segment_preview import SegmentPreviewItem, AnimationSegmentPreview


def create_demo_frames(num_frames=8):
    """Create demo frames with different colors."""
    frames = []
    for i in range(num_frames):
        pixmap = QPixmap(64, 64)
        # Create a gradient of colors
        hue = int(i * 360 / num_frames)
        color = QColor.fromHsv(hue, 200, 200)
        pixmap.fill(color)
        frames.append(pixmap)
    return frames


class FrameHoldDemo(QMainWindow):
    """Demo window for frame hold features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Frame Hold Feature Demo")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Add instructions
        instructions = QLabel(
            "<h2>Frame Hold Demo</h2>"
            "<p>This demo shows the new frame hold features:</p>"
            "<ul>"
            "<li>Click 'Holds' button on any segment to access hold menu</li>"
            "<li><b>Add Frame Hold:</b> Add hold to a specific frame</li>"
            "<li><b>Add Hold to All Frames:</b> Apply same duration to all frames</li>"
            "<li><b>Clear All Holds:</b> Remove all frame holds</li>"
            "<li>Click existing holds in menu to edit them</li>"
            "</ul>"
            "<p>Try enabling 'Bounce' mode with frame holds for interesting effects!</p>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create animation segment preview
        self.preview_widget = AnimationSegmentPreview()
        layout.addWidget(self.preview_widget)
        
        # Create demo frames
        frames = create_demo_frames(8)
        self.preview_widget.set_frames(frames)
        
        # Add demo segments
        self.preview_widget.add_segment(
            "Normal Animation",
            0, 7,
            QColor("#FF0000"),
            bounce_mode=False,
            frame_holds={}
        )
        
        self.preview_widget.add_segment(
            "With Holds",
            0, 7,
            QColor("#00FF00"),
            bounce_mode=False,
            frame_holds={0: 3, 4: 2, 7: 3}  # Hold start, middle, and end
        )
        
        self.preview_widget.add_segment(
            "Bounce Mode",
            0, 7,
            QColor("#0000FF"),
            bounce_mode=True,
            frame_holds={}
        )
        
        self.preview_widget.add_segment(
            "Bounce + Holds",
            0, 7,
            QColor("#FF00FF"),
            bounce_mode=True,
            frame_holds={0: 2, 7: 2}  # Hold at bounce points
        )
        
        # Add button to demonstrate "Add Hold to All Frames"
        demo_button = QPushButton("Demo: Add 3-frame hold to all frames in first segment")
        demo_button.clicked.connect(self.demo_all_frames_hold)
        layout.addWidget(demo_button)
        
        # Connect signals to show changes
        self.preview_widget.segmentFrameHoldsChanged.connect(self.on_holds_changed)
    
    def demo_all_frames_hold(self):
        """Demonstrate adding holds to all frames programmatically."""
        if "Normal Animation" in self.preview_widget._preview_items:
            preview_item = self.preview_widget._preview_items["Normal Animation"]
            # Apply 3-frame hold to all frames
            for i in range(len(preview_item._frames)):
                preview_item._frame_holds[i] = 3
            preview_item._update_hold_button_text()
            preview_item.frameHoldsChanged.emit(preview_item.segment_name, preview_item._frame_holds)
            print("Applied 3-frame hold to all frames in 'Normal Animation' segment")
    
    def on_holds_changed(self, segment_name, holds):
        """Show when holds change."""
        print(f"Frame holds changed for '{segment_name}': {holds}")


def main():
    """Run the demo."""
    app = QApplication(sys.argv)
    
    demo = FrameHoldDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()