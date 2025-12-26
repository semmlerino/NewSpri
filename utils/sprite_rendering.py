"""
Sprite rendering utilities.

Helper functions for rendering and manipulating sprite images.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap


def create_padded_pixmap(pixmap: QPixmap, padding: int = 1) -> QPixmap:
    """Create a padded pixmap to prevent edge cutoff during display.

    Adds transparent padding around the pixmap to ensure edges aren't
    clipped when displayed in widgets with borders or scaling.

    Args:
        pixmap: The source pixmap to pad
        padding: Pixels of padding to add on each side (default: 1)

    Returns:
        A new QPixmap with transparent padding around the original
    """
    if pixmap.isNull():
        return pixmap

    padded = QPixmap(pixmap.width() + padding * 2, pixmap.height() + padding * 2)
    padded.fill(Qt.GlobalColor.transparent)

    painter = QPainter(padded)
    painter.drawPixmap(padding, padding, pixmap)
    painter.end()

    return padded


__all__ = ['create_padded_pixmap']
