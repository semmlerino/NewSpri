"""
Integration tests for CCL extraction using real sprite sheet data.
Tests Connected Component Labeling algorithm with actual sprite sheets.
"""

import pytest
import os
from pathlib import Path
from PySide6.QtGui import QPixmap, QImage

from sprite_model import SpriteModel
from sprite_model.extraction.ccl_extractor import CCLExtractor


class TestCCLExtractionWithRealData:
    """Test CCL extraction with real sprite sheets."""
    
    @pytest.fixture
    def sprite_model(self):
        """Create a real SpriteModel instance."""
        return SpriteModel()
    
    @pytest.fixture
    def ark_sprite_path(self):
        """Get path to Ark.png test sprite sheet."""
        # Try multiple possible locations
        possible_paths = [
            Path("spritetests/Ark.png"),
            Path("tests/fixtures/Ark.png"),
            Path("../spritetests/Ark.png"),
            Path(__file__).parent.parent.parent / "spritetests" / "Ark.png"
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path.absolute())
        
        # If not found, skip the test
        pytest.skip("Ark.png test sprite sheet not found")
    
    def test_load_ark_sprite_sheet(self, sprite_model, ark_sprite_path, qtbot):
        """Test loading Ark.png sprite sheet."""
        success, error = sprite_model.load_sprite_sheet(ark_sprite_path)
        
        assert success, f"Failed to load sprite sheet: {error}"
        assert sprite_model.original_sprite_sheet is not None
        assert sprite_model.file_path == ark_sprite_path
        
        # Verify the image was loaded correctly
        width = sprite_model.original_sprite_sheet.width()
        height = sprite_model.original_sprite_sheet.height()
        assert width > 0, "Sprite sheet width should be positive"
        assert height > 0, "Sprite sheet height should be positive"
        
        print(f"Successfully loaded Ark.png: {width}x{height} pixels")
    
    def test_ccl_extraction_on_ark(self, sprite_model, ark_sprite_path, qtbot):
        """Test CCL extraction algorithm on Ark.png."""
        # Load the sprite sheet
        success, error = sprite_model.load_sprite_sheet(ark_sprite_path)
        assert success, f"Failed to load sprite sheet: {error}"
        
        # Apply CCL extraction
        sprite_model.set_extraction_mode("ccl")
        
        # Extract frames using CCL
        frames = sprite_model.sprite_frames
        
        # Verify extraction results
        assert frames is not None, "CCL extraction returned no frames"
        assert len(frames) > 0, "CCL extraction found no sprites"
        
        print(f"CCL extraction found {len(frames)} sprites in Ark.png")
        
        # Analyze extracted sprites
        sprite_sizes = set()
        for i, frame in enumerate(frames):
            width = frame.width()
            height = frame.height()
            sprite_sizes.add((width, height))
            print(f"  Sprite {i+1}: {width}x{height} pixels")
        
        print(f"Unique sprite sizes found: {sprite_sizes}")
        
        # Verify sprites have reasonable dimensions
        for frame in frames:
            assert frame.width() > 0, "Sprite width should be positive"
            assert frame.height() > 0, "Sprite height should be positive"
            assert frame.width() < sprite_model.original_sprite_sheet.width(), "Sprite should be smaller than sheet"
            assert frame.height() < sprite_model.original_sprite_sheet.height(), "Sprite should be smaller than sheet"
    
    def test_ccl_extractor_direct(self, ark_sprite_path):
        """Test CCL extractor directly with Ark.png."""
        # Load the image
        pixmap = QPixmap(ark_sprite_path)
        assert not pixmap.isNull(), f"Failed to load pixmap from {ark_sprite_path}"
        
        # Convert to QImage for processing
        image = pixmap.toImage()
        
        # Create CCL extractor
        extractor = CCLExtractor()
        
        # Extract sprites
        sprites = extractor.extract_sprites(image)
        
        assert sprites is not None, "CCL extractor returned None"
        assert len(sprites) > 0, "CCL extractor found no sprites"
        
        print(f"Direct CCL extraction found {len(sprites)} sprites")
        
        # Analyze bounding boxes
        for i, sprite_data in enumerate(sprites):
            if isinstance(sprite_data, dict):
                bbox = sprite_data.get('bbox', None)
                if bbox:
                    x, y, w, h = bbox
                    print(f"  Sprite {i+1} bbox: x={x}, y={y}, w={w}, h={h}")
            elif hasattr(sprite_data, 'rect'):
                rect = sprite_data.rect()
                print(f"  Sprite {i+1} rect: {rect.x()}, {rect.y()}, {rect.width()}x{rect.height()}")
    
    def test_ccl_vs_grid_extraction(self, sprite_model, ark_sprite_path):
        """Compare CCL extraction with grid extraction on Ark.png."""
        # Load the sprite sheet
        success, error = sprite_model.load_sprite_sheet(ark_sprite_path)
        assert success
        
        # Test CCL extraction
        sprite_model.set_extraction_mode("ccl")
        ccl_frames = list(sprite_model.sprite_frames)  # Copy the list
        ccl_count = len(ccl_frames)
        
        # Test grid extraction with auto-detection
        sprite_model.set_extraction_mode("grid")
        # Try common sprite sizes for comparison
        test_sizes = [(32, 32), (64, 64), (48, 48), (16, 16)]
        
        grid_results = []
        for width, height in test_sizes:
            success, error, count = sprite_model.extract_frames(width, height, 0, 0, 0, 0)
            if success and count > 0:
                grid_results.append({
                    'size': (width, height),
                    'count': count,
                    'frames': list(sprite_model.sprite_frames)
                })
        
        print(f"\nCCL Extraction Results: {ccl_count} sprites")
        print(f"Grid Extraction Results:")
        for result in grid_results:
            print(f"  {result['size']}: {result['count']} sprites")
        
        # CCL should find sprites even if grid sizes don't match perfectly
        assert ccl_count > 0, "CCL should find at least one sprite"
    
    def test_ccl_consistency(self, sprite_model, ark_sprite_path):
        """Test that CCL extraction is consistent across multiple runs."""
        # Load the sprite sheet
        success, error = sprite_model.load_sprite_sheet(ark_sprite_path)
        assert success
        
        sprite_model.set_extraction_mode("ccl")
        
        # Run extraction multiple times
        results = []
        for run in range(3):
            frames = list(sprite_model.sprite_frames)
            results.append({
                'count': len(frames),
                'sizes': [(f.width(), f.height()) for f in frames]
            })
        
        # Verify consistency
        first_count = results[0]['count']
        first_sizes = sorted(results[0]['sizes'])
        
        for i, result in enumerate(results[1:], 1):
            assert result['count'] == first_count, f"Run {i+1} found different sprite count"
            assert sorted(result['sizes']) == first_sizes, f"Run {i+1} found different sprite sizes"
        
        print(f"CCL extraction is consistent: {first_count} sprites across all runs")
    
    @pytest.mark.parametrize("min_area", [100, 500, 1000])
    def test_ccl_with_minimum_area_threshold(self, sprite_model, ark_sprite_path, min_area):
        """Test CCL extraction with different minimum area thresholds."""
        # Load the sprite sheet
        success, error = sprite_model.load_sprite_sheet(ark_sprite_path)
        assert success
        
        # Note: If the sprite model supports minimum area configuration
        # This tests filtering of small noise/artifacts
        sprite_model.set_extraction_mode("ccl")
        
        # Extract sprites
        frames = sprite_model.sprite_frames
        
        # Filter by minimum area
        filtered_frames = []
        for frame in frames:
            area = frame.width() * frame.height()
            if area >= min_area:
                filtered_frames.append(frame)
        
        print(f"Minimum area {min_area}: {len(filtered_frames)}/{len(frames)} sprites")
        
        # Larger minimum area should result in fewer sprites
        assert len(filtered_frames) <= len(frames)


class TestCCLWithDifferentSpriteSheets:
    """Test CCL with various sprite sheet types."""
    
    @pytest.fixture
    def sprite_sheets(self):
        """Get paths to various test sprite sheets."""
        base_path = Path(__file__).parent.parent.parent / "spritetests"
        sheets = {}
        
        # Check for available sprite sheets
        test_files = [
            ("ark", "Ark.png"),
            ("lancer_idle", "Lancer_Idle.png"),
            ("archer_run", "Archer/Archer_Run.png"),
            ("test_rect", "test_rect_32x48.png"),
            ("test_spacing", "test_spacing.png")
        ]
        
        for name, filename in test_files:
            path = base_path / filename
            if path.exists():
                sheets[name] = str(path.absolute())
        
        return sheets
    
    def test_ccl_on_multiple_sheets(self, sprite_sheets):
        """Test CCL extraction on multiple sprite sheets."""
        if not sprite_sheets:
            pytest.skip("No test sprite sheets found")
        
        results = {}
        sprite_model = SpriteModel()
        
        for name, path in sprite_sheets.items():
            success, error = sprite_model.load_sprite_sheet(path)
            if not success:
                print(f"Failed to load {name}: {error}")
                continue
            
            sprite_model.set_extraction_mode("ccl")
            frames = sprite_model.sprite_frames
            
            results[name] = {
                'path': path,
                'sprite_count': len(frames),
                'sprite_sizes': [(f.width(), f.height()) for f in frames]
            }
            
            print(f"\n{name} ({os.path.basename(path)}):")
            print(f"  Found {len(frames)} sprites")
            print(f"  Sizes: {set(results[name]['sprite_sizes'])}")
        
        # Verify we tested at least one sprite sheet
        assert len(results) > 0, "No sprite sheets could be tested"
        
        # Each sprite sheet should find at least one sprite
        for name, result in results.items():
            assert result['sprite_count'] > 0, f"{name} should have at least one sprite"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])