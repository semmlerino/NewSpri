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
    
    if preserve_pixel_perfect:
        # For pixel-perfect rendering, we need to be careful about coordinates
        # Use QRectF for sub-pixel accuracy during calculation
        # then round to ensure we're on pixel boundaries
        
        # Ensure antialiasing is on to prevent edge cutoff
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Keep pixel-perfect scaling
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        
        # Draw with slight inset to ensure edges are visible
        # This compensates for Qt's pixel boundary handling
        source_rect = QRectF(0.5, 0.5, pixmap.width() - 1, pixmap.height() - 1)
        target_rect_f = QRectF(target_rect.x() + 0.5, target_rect.y() + 0.5,
                              target_rect.width() - 1, target_rect.height() - 1)
        
        painter.drawPixmap(target_rect_f, pixmap, source_rect)
    else:
        # For smooth scaling, use standard approach
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawPixmap(target_rect, pixmap)
    
    # Restore painter state
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
    
    # Create a slightly larger pixmap to ensure edges aren't cut
    temp_pixmap = QPixmap(pixmap.size().width() + 2, pixmap.size().height() + 2)
    temp_pixmap.fill(Qt.transparent)
    
    # Draw original pixmap centered in temp pixmap
    painter = QPainter(temp_pixmap)
    painter.drawPixmap(1, 1, pixmap)
    painter.end()
    
    # Scale the temp pixmap
    if preserve_aspect:
        scaled = temp_pixmap.scaled(width + 2, height + 2, 
                                   Qt.KeepAspectRatio, 
                                   Qt.FastTransformation)
    else:
        scaled = temp_pixmap.scaled(width + 2, height + 2,
                                   Qt.IgnoreAspectRatio,
                                   Qt.FastTransformation)
    
    # Extract the center portion
    final_width = min(width, scaled.width() - 2)
    final_height = min(height, scaled.height() - 2)
    
    return scaled.copy(1, 1, final_width, final_height)