"""
Factory for creating real test images (QPixmap) for use in integration tests.
Provides authentic image data instead of mocks.
"""

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont, QPainter, QPixmap

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


class RealImageFactory:
    """Factory for creating real test images and sprite sheets."""

    @staticmethod
    def create_solid_color_frame(width=64, height=64, color=Qt.red):
        """Create a solid color frame."""
        pixmap = QPixmap(width, height)
        pixmap.fill(color)
        return pixmap

    @staticmethod
    def create_numbered_frame(width=64, height=64, number=0, bg_color=Qt.red, text_color=Qt.white):
        """Create a frame with a number overlay for identification."""
        pixmap = QPixmap(width, height)
        pixmap.fill(bg_color)

        painter = QPainter(pixmap)
        painter.setPen(text_color)
        font = QFont()
        font.setPointSize(max(8, min(width, height) // 8))
        painter.setFont(font)

        # Center the text
        text = str(number)
        text_rect = painter.fontMetrics().boundingRect(text)
        x = (width - text_rect.width()) // 2
        y = (height + text_rect.height()) // 2

        painter.drawText(x, y, text)
        painter.end()

        return pixmap

    @staticmethod
    def create_sprite_sheet(
        frame_count=8,
        frame_size=(32, 32),
        layout="horizontal",
        colors=None,
        spacing=0,
        margin=0,
    ):
        """Create a real sprite sheet with multiple frames."""
        frame_width, frame_height = frame_size

        if colors is None:
            colors = [
                Qt.red,
                Qt.green,
                Qt.blue,
                Qt.yellow,
                Qt.cyan,
                Qt.magenta,
                Qt.darkRed,
                Qt.darkGreen,
                Qt.darkBlue,
                Qt.darkYellow,
            ]

        if layout == "horizontal":
            sheet_width = frame_count * frame_width + (frame_count - 1) * spacing + 2 * margin
            sheet_height = frame_height + 2 * margin
        elif layout == "vertical":
            sheet_width = frame_width + 2 * margin
            sheet_height = frame_count * frame_height + (frame_count - 1) * spacing + 2 * margin
        else:  # grid layout
            cols = int(frame_count**0.5)
            if cols * cols < frame_count:
                cols += 1
            rows = (frame_count + cols - 1) // cols
            sheet_width = cols * frame_width + (cols - 1) * spacing + 2 * margin
            sheet_height = rows * frame_height + (rows - 1) * spacing + 2 * margin

        sprite_sheet = QPixmap(sheet_width, sheet_height)
        sprite_sheet.fill(Qt.white)

        painter = QPainter(sprite_sheet)

        for i in range(frame_count):
            if layout == "horizontal":
                x = margin + i * (frame_width + spacing)
                y = margin
            elif layout == "vertical":
                x = margin
                y = margin + i * (frame_height + spacing)
            else:  # grid
                col = i % cols
                row = i // cols
                x = margin + col * (frame_width + spacing)
                y = margin + row * (frame_height + spacing)

            # Draw colored frame background
            color = colors[i % len(colors)]
            painter.fillRect(x, y, frame_width, frame_height, color)

            # Add frame number
            painter.setPen(Qt.white)
            font = QFont()
            font.setPointSize(max(8, min(frame_width, frame_height) // 8))
            painter.setFont(font)

            text = str(i)
            text_rect = painter.fontMetrics().boundingRect(text)
            text_x = x + (frame_width - text_rect.width()) // 2
            text_y = y + (frame_height + text_rect.height()) // 2

            painter.drawText(text_x, text_y, text)

        painter.end()
        return sprite_sheet

    @staticmethod
    def create_ccl_test_sprite():
        """Create a sprite sheet specifically for CCL testing."""
        # Create a sheet with isolated sprites for CCL to detect
        sheet = QPixmap(200, 100)
        sheet.fill(Qt.transparent)

        painter = QPainter(sheet)

        # Create separate colored rectangles for CCL to find
        sprite_rects = [
            (10, 10, 30, 30, Qt.red),
            (50, 10, 25, 35, Qt.green),
            (85, 15, 20, 25, Qt.blue),
            (115, 5, 35, 40, Qt.yellow),
            (160, 20, 30, 25, Qt.cyan),
        ]

        for x, y, w, h, color in sprite_rects:
            painter.fillRect(x, y, w, h, color)
            # Add small border to make sprites distinct
            painter.setPen(Qt.black)
            painter.drawRect(x, y, w, h)

        painter.end()
        return sheet

    @staticmethod
    def save_to_temp_file(pixmap, temp_dir, filename="test_sprite.png"):
        """Save real image to temporary file and return path."""
        file_path = temp_dir / filename
        success = pixmap.save(str(file_path))
        return str(file_path) if success else None

    @staticmethod
    def create_animation_frames(count=6, size=(48, 48), animation_type="rotate"):
        """Create frames for animation testing."""
        frames = []
        width, height = size

        for i in range(count):
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            if animation_type == "rotate":
                # Rotating square animation
                angle = (360 / count) * i
                painter.translate(width // 2, height // 2)
                painter.rotate(angle)
                painter.fillRect(-10, -10, 20, 20, Qt.red)
            elif animation_type == "scale":
                # Scaling circle animation
                scale = 0.5 + 0.5 * (i / count)
                radius = int(min(width, height) * 0.3 * scale)
                center_x, center_y = width // 2, height // 2
                painter.setBrush(Qt.blue)
                painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
            elif animation_type == "move":
                # Moving dot animation
                x = int((width - 20) * (i / (count - 1)))
                y = height // 2 - 10
                painter.fillRect(x, y, 20, 20, Qt.green)

            painter.end()
            frames.append(pixmap)

        return frames
