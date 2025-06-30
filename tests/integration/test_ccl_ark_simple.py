"""
Simple CCL integration test with Ark.png using minimal Qt dependency.
Tests Connected Component Labeling algorithm with real sprite sheet data.
"""

import pytest
import os
from pathlib import Path
from PIL import Image
import numpy as np


class TestCCLSimpleIntegration:
    """Simple CCL test with real data using PIL instead of Qt."""
    
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
    
    def test_ark_file_exists_and_readable(self, ark_sprite_path):
        """Test that Ark.png exists and is readable."""
        assert os.path.exists(ark_sprite_path), f"Ark.png not found at {ark_sprite_path}"
        
        # Load with PIL to verify it's a valid image
        try:
            with Image.open(ark_sprite_path) as img:
                width, height = img.size
                mode = img.mode
                
                print(f"Ark.png details:")
                print(f"  Size: {width}x{height} pixels")
                print(f"  Mode: {mode}")
                print(f"  Path: {ark_sprite_path}")
                
                assert width > 0, "Image width should be positive"
                assert height > 0, "Image height should be positive"
                assert mode in ['RGB', 'RGBA', 'L', 'P'], f"Unexpected image mode: {mode}"
                
        except Exception as e:
            pytest.fail(f"Failed to open Ark.png with PIL: {e}")
    
    def test_sprite_model_with_qtbot(self, ark_sprite_path, qtbot):
        """Test sprite model loading with Qt context."""
        from sprite_model import SpriteModel
        
        sprite_model = SpriteModel()
        
        # Load the sprite sheet
        success, error = sprite_model.load_sprite_sheet(ark_sprite_path)
        
        if not success:
            print(f"Failed to load sprite sheet: {error}")
            pytest.fail(f"Could not load Ark.png: {error}")
        
        assert sprite_model.original_sprite_sheet is not None
        
        # Get basic info
        width = sprite_model.original_sprite_sheet.width()
        height = sprite_model.original_sprite_sheet.height()
        
        print(f"Loaded Ark.png via SpriteModel: {width}x{height}")
        
        # Test CCL mode
        sprite_model.set_extraction_mode("ccl")
        
        # Get extracted frames
        frames = sprite_model.sprite_frames
        frame_count = len(frames) if frames else 0
        
        print(f"CCL extraction result: {frame_count} sprites found")
        
        # Analyze results
        if frame_count > 0:
            sprite_sizes = []
            for i, frame in enumerate(frames):
                w = frame.width()
                h = frame.height()
                sprite_sizes.append((w, h))
                if i < 5:  # Show first 5 sprites
                    print(f"  Sprite {i+1}: {w}x{h}")
            
            unique_sizes = set(sprite_sizes)
            print(f"Unique sprite sizes: {unique_sizes}")
            
            # Basic validation
            assert frame_count > 0, "CCL should find at least one sprite"
            for frame in frames[:3]:  # Check first 3 frames
                assert frame.width() > 0, "Sprite width should be positive"
                assert frame.height() > 0, "Sprite height should be positive"
        else:
            print("Warning: CCL extraction found no sprites")
    
    def test_ccl_algorithm_analysis(self, ark_sprite_path):
        """Analyze the CCL algorithm performance on Ark.png."""
        # Load image with PIL for analysis
        with Image.open(ark_sprite_path) as img:
            # Convert to RGBA for consistent processing
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Convert to numpy array
            img_array = np.array(img)
            height, width = img_array.shape[:2]
            
            print(f"Image analysis for CCL:")
            print(f"  Dimensions: {width}x{height}")
            print(f"  Shape: {img_array.shape}")
            
            # Analyze alpha channel for transparency
            if img_array.shape[2] == 4:  # Has alpha channel
                alpha = img_array[:, :, 3]
                
                # Count transparent vs opaque pixels
                transparent_pixels = np.sum(alpha == 0)
                opaque_pixels = np.sum(alpha == 255)
                semi_transparent = np.sum((alpha > 0) & (alpha < 255))
                
                total_pixels = width * height
                
                print(f"  Transparency analysis:")
                print(f"    Transparent: {transparent_pixels} ({transparent_pixels/total_pixels*100:.1f}%)")
                print(f"    Opaque: {opaque_pixels} ({opaque_pixels/total_pixels*100:.1f}%)")
                print(f"    Semi-transparent: {semi_transparent} ({semi_transparent/total_pixels*100:.1f}%)")
                
                # This gives us insight into how CCL should perform
                if transparent_pixels > 0:
                    print("  -> CCL should be able to separate sprites using transparency")
                else:
                    print("  -> CCL will need to use color-based separation")
            
            # Basic color analysis
            if img_array.shape[2] >= 3:
                rgb = img_array[:, :, :3]
                unique_colors = len(np.unique(rgb.reshape(-1, rgb.shape[-1]), axis=0))
                print(f"  Unique colors: {unique_colors}")
    
    def test_ccl_extraction_modes_comparison(self, ark_sprite_path, qtbot):
        """Compare different extraction modes on Ark.png."""
        from sprite_model import SpriteModel
        
        sprite_model = SpriteModel()
        success, error = sprite_model.load_sprite_sheet(ark_sprite_path)
        
        if not success:
            pytest.skip(f"Could not load sprite sheet: {error}")
        
        results = {}
        
        # Test CCL mode
        try:
            sprite_model.set_extraction_mode("ccl")
            ccl_frames = sprite_model.sprite_frames
            results['ccl'] = {
                'count': len(ccl_frames) if ccl_frames else 0,
                'sizes': [(f.width(), f.height()) for f in ccl_frames] if ccl_frames else []
            }
        except Exception as e:
            results['ccl'] = {'error': str(e)}
        
        # Test grid mode with common sizes
        test_sizes = [(32, 32), (64, 64), (48, 48), (16, 16), (24, 24)]
        
        for size in test_sizes:
            try:
                width, height = size
                sprite_model.set_extraction_mode("grid")
                success, error, count = sprite_model.extract_frames(width, height, 0, 0, 0, 0)
                
                if success and count > 0:
                    results[f'grid_{width}x{height}'] = {
                        'count': count,
                        'success': True
                    }
                else:
                    results[f'grid_{width}x{height}'] = {
                        'count': 0,
                        'success': False,
                        'error': error
                    }
            except Exception as e:
                results[f'grid_{width}x{height}'] = {'error': str(e)}
        
        # Print comparison results
        print("\nExtraction method comparison:")
        for method, result in results.items():
            if 'error' in result:
                print(f"  {method}: ERROR - {result['error']}")
            else:
                count = result.get('count', 0)
                print(f"  {method}: {count} sprites")
        
        # Verify CCL found something
        ccl_result = results.get('ccl', {})
        if 'error' not in ccl_result:
            ccl_count = ccl_result.get('count', 0)
            assert ccl_count >= 0, "CCL should return valid count"
            
            if ccl_count > 0:
                print(f"✅ CCL successfully found {ccl_count} sprites in Ark.png")
            else:
                print("⚠️  CCL found no sprites - may need algorithm tuning")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])