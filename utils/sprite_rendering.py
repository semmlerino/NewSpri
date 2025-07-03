"""
Sprite Rendering Utilities
Common utilities for properly rendering sprites without edge cutoff.
"""

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QPixmap, QPainter


def draw_pixmap_safe(painter: QPainter, target_rect: QRect, pixmap: QPixmap, 
                    preserve_pixel_perfect: bool = True):
    """
    Draw a pixmap safely without edge cutoff.
    
    This function ensures that sprites are rendered completely without
    edge pixels being cut off due to rounding or scaling issues.
    
    Args:
        painter: The QPainter to draw with
        target_rect: The target rectangle to draw into
        pixmap: The pixmap to draw
        preserve_pixel_perfect: Whether to preserve pixel-perfect rendering
    """
    if not pixmap or pixmap.isNull():
        return
    
    # Save painter state
    old_hints = painter.renderHints()
    old_clip = painter.hasClipping()
    
    # Temporarily disable clipping to ensure edges aren't cut
    painter.setClipping(False)
    
    if preserve_pixel_perfect:
        # Keep pixel-perfect scaling
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        # But use antialiasing for edges
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw the pixmap directly without any offset adjustments
        painter.drawPixmap(target_rect, pixmap)
    else:
        # For smooth scaling, use standard approach
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawPixmap(target_rect, pixmap)
    
    # Restore painter state
    painter.setClipping(old_clip)
    painter.setRenderHints(old_hints)


def scale_pixmap_safe(pixmap: QPixmap, width: int, height: int, 
                     preserve_aspect: bool = True) -> QPixmap:
    """
    Scale a pixmap safely without edge cutoff.
    
    Args:
        pixmap: The pixmap to scale
        width: Target width
        height: Target height
        preserve_aspect: Whether to preserve aspect ratio
        
    Returns:
        Scaled pixmap with all edges preserved
    """
    if not pixmap or pixmap.isNull():
        return pixmap
    
    # Create a pixmap with transparent padding
    padded_pixmap = QPixmap(pixmap.width() + 2, pixmap.height() + 2)
    padded_pixmap.fill(Qt.transparent)
    
    # Draw original pixmap centered
    painter = QPainter(padded_pixmap)
    painter.drawPixmap(1, 1, pixmap)
    painter.end()
    
    # Scale with padding included
    if preserve_aspect:
        scaled = padded_pixmap.scaled(width, height, 
                                     Qt.KeepAspectRatio, 
                                     Qt.SmoothTransformation)
    else:
        scaled = padded_pixmap.scaled(width, height,
                                     Qt.IgnoreAspectRatio,
                                     Qt.SmoothTransformation)
    
    return scaled