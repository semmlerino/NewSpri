"""
Test sprite sheet fixtures and generators.
Provides reusable test data for sprite testing.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt


class SpriteSheetGenerator:
    """Generate test sprite sheets programmatically."""
    
    @staticmethod
    def create_test_sprite_sheet(
        frame_width: int,
        frame_height: int,
        rows: int,
        cols: int,
        spacing: int = 0,
        margin: int = 0,
        colors: Optional[List[QColor]] = None
    ) -> QPixmap:
        """
        Create a test sprite sheet with specified parameters.
        
        Args:
            frame_width: Width of each frame
            frame_height: Height of each frame  
            rows: Number of rows
            cols: Number of columns
            spacing: Spacing between frames
            margin: Margin around the entire sheet
            colors: List of colors to use for frames (cycles if needed)
        
        Returns:
            QPixmap containing the generated sprite sheet
        """
        if colors is None:
            colors = [
                QColor(255, 0, 0),    # Red
                QColor(0, 255, 0),    # Green
                QColor(0, 0, 255),    # Blue
                QColor(255, 255, 0),  # Yellow
                QColor(255, 0, 255),  # Magenta
                QColor(0, 255, 255),  # Cyan
            ]
        
        # Calculate total dimensions
        total_width = margin * 2 + cols * frame_width + (cols - 1) * spacing
        total_height = margin * 2 + rows * frame_height + (rows - 1) * spacing
        
        # Create pixmap and painter
        pixmap = QPixmap(total_width, total_height)
        pixmap.fill(Qt.white)
        
        painter = QPainter(pixmap)
        
        # Draw frames
        for row in range(rows):
            for col in range(cols):
                # Calculate frame position
                x = margin + col * (frame_width + spacing)
                y = margin + row * (frame_height + spacing)
                
                # Select color (cycle through available colors)
                color_index = (row * cols + col) % len(colors)
                color = colors[color_index]
                
                # Draw frame
                painter.fillRect(x, y, frame_width, frame_height, color)
                
                # Add frame number text
                painter.setPen(Qt.black)
                frame_number = row * cols + col + 1
                painter.drawText(x + 5, y + 15, str(frame_number))
        
        painter.end()
        return pixmap
    
    @staticmethod
    def create_character_animation_sheet() -> QPixmap:
        """Create a test character animation sprite sheet."""
        return SpriteSheetGenerator.create_test_sprite_sheet(
            frame_width=32,
            frame_height=48,
            rows=4,
            cols=8,
            spacing=2,
            margin=4,
            colors=[
                QColor(220, 180, 140),  # Skin tone
                QColor(139, 69, 19),    # Brown hair
                QColor(100, 100, 255),  # Blue shirt
                QColor(50, 150, 50),    # Green pants
            ]
        )
    
    @staticmethod
    def create_tile_sheet() -> QPixmap:
        """Create a test tile sprite sheet."""
        return SpriteSheetGenerator.create_test_sprite_sheet(
            frame_width=64,
            frame_height=64,
            rows=3,
            cols=3,
            spacing=0,
            margin=0,
            colors=[
                QColor(34, 139, 34),    # Forest green
                QColor(139, 69, 19),    # Saddle brown  
                QColor(70, 130, 180),   # Steel blue
                QColor(255, 140, 0),    # Dark orange
            ]
        )
    
    @staticmethod
    def create_irregular_spacing_sheet() -> QPixmap:
        """Create a sprite sheet with irregular spacing for testing detection."""
        return SpriteSheetGenerator.create_test_sprite_sheet(
            frame_width=24,
            frame_height=32,
            rows=5,
            cols=6,
            spacing=3,
            margin=8,
            colors=[QColor(i * 40 % 255, i * 60 % 255, i * 80 % 255) for i in range(12)]
        )


class TestSpriteData:
    """Container for test sprite sheet data and metadata."""
    
    def __init__(self, name: str, pixmap: QPixmap, metadata: Dict):
        self.name = name
        self.pixmap = pixmap
        self.metadata = metadata
    
    @property
    def frame_width(self) -> int:
        return self.metadata.get('frame_width', 32)
    
    @property 
    def frame_height(self) -> int:
        return self.metadata.get('frame_height', 32)
    
    @property
    def expected_frames(self) -> int:
        return self.metadata.get('expected_frames', 1)
    
    @property
    def margin_x(self) -> int:
        return self.metadata.get('margin_x', 0)
    
    @property
    def margin_y(self) -> int:
        return self.metadata.get('margin_y', 0)
    
    @property
    def spacing_x(self) -> int:
        return self.metadata.get('spacing_x', 0)
    
    @property
    def spacing_y(self) -> int:
        return self.metadata.get('spacing_y', 0)


def get_test_sprite_collection() -> Dict[str, TestSpriteData]:
    """Get a collection of test sprite sheets for various test scenarios."""
    
    collection = {}
    
    # Basic square sprites
    collection['basic_square'] = TestSpriteData(
        name='basic_square',
        pixmap=SpriteSheetGenerator.create_test_sprite_sheet(32, 32, 2, 4),
        metadata={
            'frame_width': 32,
            'frame_height': 32,
            'expected_frames': 8,
            'margin_x': 0,
            'margin_y': 0,
            'spacing_x': 0,
            'spacing_y': 0,
        }
    )
    
    # Character animation
    collection['character_anim'] = TestSpriteData(
        name='character_anim',
        pixmap=SpriteSheetGenerator.create_character_animation_sheet(),
        metadata={
            'frame_width': 32,
            'frame_height': 48,
            'expected_frames': 32,
            'margin_x': 4,
            'margin_y': 4,
            'spacing_x': 2,
            'spacing_y': 2,
        }
    )
    
    # Tile sheet
    collection['tiles'] = TestSpriteData(
        name='tiles',
        pixmap=SpriteSheetGenerator.create_tile_sheet(),
        metadata={
            'frame_width': 64,
            'frame_height': 64,
            'expected_frames': 9,
            'margin_x': 0,
            'margin_y': 0,
            'spacing_x': 0,
            'spacing_y': 0,
        }
    )
    
    # Irregular spacing
    collection['irregular'] = TestSpriteData(
        name='irregular',
        pixmap=SpriteSheetGenerator.create_irregular_spacing_sheet(),
        metadata={
            'frame_width': 24,
            'frame_height': 32,
            'expected_frames': 30,
            'margin_x': 8,
            'margin_y': 8,
            'spacing_x': 3,
            'spacing_y': 3,
        }
    )
    
    # Large frames
    collection['large_frames'] = TestSpriteData(
        name='large_frames',
        pixmap=SpriteSheetGenerator.create_test_sprite_sheet(128, 128, 2, 2),
        metadata={
            'frame_width': 128,
            'frame_height': 128,
            'expected_frames': 4,
            'margin_x': 0,
            'margin_y': 0,
            'spacing_x': 0,
            'spacing_y': 0,
        }
    )
    
    # Single frame
    collection['single_frame'] = TestSpriteData(
        name='single_frame',
        pixmap=SpriteSheetGenerator.create_test_sprite_sheet(96, 96, 1, 1),
        metadata={
            'frame_width': 96,
            'frame_height': 96,
            'expected_frames': 1,
            'margin_x': 0,
            'margin_y': 0,
            'spacing_x': 0,
            'spacing_y': 0,
        }
    )
    
    return collection


def get_detection_test_cases() -> List[Dict]:
    """Get test cases specifically for detection algorithm testing."""
    
    return [
        {
            'name': 'perfect_grid',
            'frame_size': (32, 32),
            'grid_size': (4, 4),
            'spacing': (0, 0),
            'margin': (0, 0),
            'difficulty': 'easy'
        },
        {
            'name': 'with_spacing',
            'frame_size': (24, 32),
            'grid_size': (6, 4),
            'spacing': (2, 3),
            'margin': (0, 0),
            'difficulty': 'medium'
        },
        {
            'name': 'with_margin',
            'frame_size': (48, 48),
            'grid_size': (3, 3),
            'spacing': (0, 0),
            'margin': (8, 8),
            'difficulty': 'medium'
        },
        {
            'name': 'complex_layout',
            'frame_size': (20, 28),
            'grid_size': (8, 5),
            'spacing': (4, 2),
            'margin': (12, 6),
            'difficulty': 'hard'
        },
        {
            'name': 'rectangular_frames',
            'frame_size': (16, 48),
            'grid_size': (10, 2),
            'spacing': (1, 4),
            'margin': (5, 10),
            'difficulty': 'medium'
        },
    ]


def save_test_sprites_to_files(output_dir: Path) -> Dict[str, Path]:
    """
    Save generated test sprites to files for debugging or external testing.
    
    Args:
        output_dir: Directory to save files to
        
    Returns:
        Dictionary mapping sprite names to file paths
    """
    output_dir.mkdir(exist_ok=True)
    
    collection = get_test_sprite_collection()
    saved_files = {}
    
    for name, sprite_data in collection.items():
        file_path = output_dir / f"test_{name}.png"
        sprite_data.pixmap.save(str(file_path))
        saved_files[name] = file_path
    
    return saved_files


# Export main functions and classes
__all__ = [
    'SpriteSheetGenerator',
    'TestSpriteData', 
    'get_test_sprite_collection',
    'get_detection_test_cases',
    'save_test_sprites_to_files'
]