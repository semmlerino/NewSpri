"""
Common Test Fixtures
Reusable fixtures for sprite viewer tests.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

from PySide6.QtGui import QPixmap, QColor, QPainter, QFont
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from sprite_model import SpriteModel
from export import ExportPreset
from export.core.frame_exporter import BackgroundMode, ExportMode, LayoutMode, SpriteSheetLayout


# Sprite Creation Fixtures
@pytest.fixture
def simple_sprites():
    """Create simple colored sprites for testing."""
    sprites = []
    for i in range(16):
        pixmap = QPixmap(32, 32)
        color = QColor.fromHsv(int(i * 360 / 16), 200, 200)
        pixmap.fill(color)
        sprites.append(pixmap)
    return sprites


@pytest.fixture
def numbered_sprites():
    """Create sprites with numbers drawn on them."""
    sprites = []
    for i in range(16):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw colored background
        color = QColor.fromHsv(int(i * 360 / 16), 150, 200)
        painter.fillRect(8, 8, 48, 48, color)
        
        # Draw number
        painter.setPen(Qt.white)
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, str(i + 1))
        
        painter.end()
        sprites.append(pixmap)
    
    return sprites


@pytest.fixture
def large_sprites():
    """Create larger sprites for performance testing."""
    sprites = []
    for i in range(100):
        pixmap = QPixmap(128, 128)
        color = QColor.fromHsv(int(i * 360 / 100), 180, 220)
        pixmap.fill(color)
        sprites.append(pixmap)
    return sprites


@pytest.fixture
def varied_size_sprites():
    """Create sprites with different sizes."""
    sizes = [(32, 32), (64, 64), (48, 48), (32, 64), (64, 32)]
    sprites = []
    
    for i, (width, height) in enumerate(sizes * 3):  # 15 sprites
        pixmap = QPixmap(width, height)
        color = QColor.fromHsv(int(i * 24), 200, 200)
        pixmap.fill(color)
        sprites.append(pixmap)
    
    return sprites


# Model Fixtures
@pytest.fixture
def sprite_model_with_data(simple_sprites):
    """Create a sprite model populated with test data."""
    model = SpriteModel()
    model.sprite_frames = simple_sprites.copy()
    model.current_frame = 0
    model.sprite_path = "/test/sprites.png"
    return model


@pytest.fixture
def empty_sprite_model():
    """Create an empty sprite model."""
    return SpriteModel()


# Directory Fixtures
@pytest.fixture
def temp_export_dir():
    """Create a temporary directory for export testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_sprite_files(temp_export_dir, simple_sprites):
    """Create actual sprite files in a temp directory."""
    sprite_dir = temp_export_dir / "sprites"
    sprite_dir.mkdir()
    
    files = []
    for i, sprite in enumerate(simple_sprites[:5]):
        filepath = sprite_dir / f"sprite_{i:03d}.png"
        sprite.save(str(filepath))
        files.append(filepath)
    
    return files


# Export Preset Fixtures
@pytest.fixture
def mock_individual_preset():
    """Create a mock individual frames export preset."""
    return ExportPreset(
        name="individual_frames",
        display_name="Individual Frames",
        icon="📁",
        description="Export frames as separate files",
        mode=ExportMode.INDIVIDUAL_FRAMES,
        format="PNG",
        scale=1.0,
        default_pattern="{name}_{index:03d}",
        tooltip="Export each frame as a separate file",
        use_cases=["Frame editing", "Video production"],
        short_description="Perfect for editing"
    )


@pytest.fixture
def mock_sprite_sheet_preset():
    """Create a mock sprite sheet export preset."""
    return ExportPreset(
        name="sprite_sheet",
        display_name="Sprite Sheet",
        icon="📋",
        description="Combine all frames into one image",
        mode=ExportMode.SPRITE_SHEET,
        format="PNG",
        scale=1.0,
        default_pattern="{name}_sheet",
        tooltip="Create a sprite sheet for game engines",
        use_cases=["Game development", "Web animations"],
        sprite_sheet_layout=SpriteSheetLayout(
            mode=LayoutMode.AUTO,
            spacing=0,
            padding=0,
            background_mode=BackgroundMode.TRANSPARENT
        ),
        short_description="Optimized for games"
    )


@pytest.fixture
def mock_gif_preset():
    """Create a mock animated GIF export preset."""
    return ExportPreset(
        name="animation_gif",
        display_name="Animated GIF",
        icon="🎬",
        description="Create an animated GIF",
        mode=ExportMode.INDIVIDUAL_FRAMES,
        format="PNG",
        scale=1.0,
        default_pattern="{name}_animation",
        tooltip="Export as animated GIF for sharing",
        use_cases=["Social media", "Documentation"],
        short_description="Share-ready animation"
    )


# Mock Objects Fixtures
@pytest.fixture
def mock_exporter():
    """Create a mock frame exporter."""
    exporter = Mock()
    exporter.export_frames = Mock(return_value=True)
    exporter.exportStarted = Mock()
    exporter.exportProgress = Mock()
    exporter.exportFinished = Mock()
    exporter.exportError = Mock()
    return exporter


@pytest.fixture
def mock_segment_manager():
    """Create a mock animation segment manager."""
    manager = Mock()
    manager.segments = []
    manager.get_segment = Mock(return_value=None)
    manager.add_segment = Mock()
    manager.remove_segment = Mock()
    manager.clear_segments = Mock()
    return manager


# NOTE: qapp fixture is defined in tests/conftest.py - do not duplicate here


# Window Geometry Fixtures
@pytest.fixture
def default_window_geometry():
    """Default window geometry for testing."""
    return {
        'x': 100,
        'y': 100,
        'width': 800,
        'height': 600
    }


@pytest.fixture
def large_window_geometry():
    """Large window geometry for testing."""
    return {
        'x': 50,
        'y': 50,
        'width': 1200,
        'height': 900
    }


# Performance Testing Fixtures
@pytest.fixture
def performance_timer():
    """Simple performance timer context manager."""
    import time
    
    class Timer:
        def __init__(self):
            self.elapsed = 0
        
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        
        def __exit__(self, *args):
            self.elapsed = time.perf_counter() - self.start
    
    return Timer


# Test Data Fixtures
@pytest.fixture
def sample_export_settings():
    """Sample export settings dictionary."""
    return {
        'output_dir': '/tmp/sprites',
        'base_name': 'test_sprite',
        'format': 'PNG',
        'mode': 'individual',
        'scale_factor': 1.0,
        'pattern': '{name}_{index:03d}',
        'preset_name': 'individual_frames'
    }


@pytest.fixture
def sample_sprite_sheet_settings():
    """Sample sprite sheet export settings."""
    return {
        'output_dir': '/tmp/sprites',
        'base_name': 'spritesheet',
        'format': 'PNG',
        'mode': 'sheet',
        'scale_factor': 1.0,
        'pattern': '{name}',
        'preset_name': 'sprite_sheet',
        'sprite_sheet_layout': SpriteSheetLayout(
            mode=LayoutMode.AUTO,
            spacing=2,
            padding=4,
            background_mode=BackgroundMode.TRANSPARENT
        )
    }


# Validation Fixtures
@pytest.fixture
def valid_filenames():
    """List of valid filenames for testing."""
    return [
        "sprite",
        "my_sprite",
        "sprite123",
        "sprite-name",
        "SPRITE",
        "sprite.test",
        "sprite_v2"
    ]


@pytest.fixture
def invalid_filenames():
    """List of invalid filenames for testing."""
    return [
        "",
        " ",
        "sprite/name",
        "sprite\\name",
        "sprite:name",
        "sprite*name",
        "sprite?name",
        "sprite<name>",
        "sprite|name"
    ]


# Mock UI Components
@pytest.fixture
def mock_directory_selector():
    """Mock directory selector widget."""
    selector = Mock()
    selector.get_directory = Mock(return_value="/tmp/sprites")
    selector.set_directory = Mock()
    selector.is_valid = Mock(return_value=True)
    selector.directoryChanged = Mock()
    selector.validationChanged = Mock()
    return selector


@pytest.fixture
def mock_filename_edit():
    """Mock filename edit widget."""
    edit = Mock()
    edit.text = Mock(return_value="sprite")
    edit.setText = Mock()
    edit.is_valid = Mock(return_value=True)
    edit.textChanged = Mock()
    return edit


# Utility Functions
def create_test_sprite_sheet(width=256, height=256, sprite_size=32):
    """Create a test sprite sheet with grid pattern."""
    sheet = QPixmap(width, height)
    sheet.fill(Qt.white)
    
    painter = QPainter(sheet)
    cols = width // sprite_size
    rows = height // sprite_size
    
    for row in range(rows):
        for col in range(cols):
            x = col * sprite_size
            y = row * sprite_size
            color = QColor.fromHsv((row * cols + col) * 30 % 360, 200, 200)
            painter.fillRect(x, y, sprite_size, sprite_size, color)
            
            # Draw border
            painter.setPen(Qt.black)
            painter.drawRect(x, y, sprite_size - 1, sprite_size - 1)
    
    painter.end()
    return sheet


def compare_pixmaps(pixmap1, pixmap2):
    """Compare two pixmaps for equality."""
    if pixmap1.size() != pixmap2.size():
        return False
    
    # Convert to images for comparison
    img1 = pixmap1.toImage()
    img2 = pixmap2.toImage()
    
    # Simple pixel comparison (could be optimized)
    for x in range(img1.width()):
        for y in range(img1.height()):
            if img1.pixel(x, y) != img2.pixel(x, y):
                return False
    
    return True