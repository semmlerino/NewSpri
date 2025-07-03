"""
Performance and stress tests for Phase 4: Enhanced Live Preview System
Tests performance characteristics, memory usage, and handling of edge cases.
"""

import pytest

# Mark all tests in this file as performance tests
pytestmark = [
    pytest.mark.phase4,
    pytest.mark.preview_performance,
    pytest.mark.performance,
    pytest.mark.ui,
    pytest.mark.requires_display,
    pytest.mark.slow
]

import sys
import os
import time
import gc
from unittest.mock import Mock, patch
from typing import List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Qt imports
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QColor

# Project imports
from export.widgets.sprite_preview_widget import SpriteSheetPreviewCanvas, SpriteSheetPreviewWidget
from export.core.frame_exporter import SpriteSheetLayout
from config import Config


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def create_test_sprites(count: int, width: int = 32, height: int = 32) -> List[QPixmap]:
    """Create test sprites for performance testing."""
    sprites = []
    for i in range(count):
        pixmap = QPixmap(width, height)
        # Use different colors to ensure sprites are distinct
        color = QColor(
            (i * 37) % 255,
            (i * 73) % 255,
            (i * 109) % 255
        )
        pixmap.fill(color)
        sprites.append(pixmap)
    return sprites


class TestUpdatePerformance:
    """Test performance of preview updates."""
    
    def test_small_sprite_count_performance(self, qapp):
        """Test performance with small sprite count (typical use case)."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(16, 32, 32)
        layout = SpriteSheetLayout(mode='auto', spacing=4, padding=8)
        
        # Measure update time
        start_time = time.time()
        
        canvas.set_sprites(sprites)
        canvas.set_layout(layout)
        canvas._generate_preview()  # Force immediate generation
        
        end_time = time.time()
        update_time = end_time - start_time
        
        # Should complete quickly for small sprite count
        assert update_time < 0.5, f"Update took too long: {update_time:.3f}s for 16 sprites"
        
    def test_medium_sprite_count_performance(self, qapp):
        """Test performance with medium sprite count."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(64, 32, 32)
        layout = SpriteSheetLayout(mode='auto', spacing=2, padding=4)
        
        start_time = time.time()
        
        canvas.set_sprites(sprites)
        canvas.set_layout(layout)
        canvas._generate_preview()
        
        end_time = time.time()
        update_time = end_time - start_time
        
        # Should still be reasonable for medium count
        assert update_time < 2.0, f"Update took too long: {update_time:.3f}s for 64 sprites"
        
    def test_large_sprite_count_performance(self, qapp):
        """Test performance with large sprite count (stress test)."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(144, 32, 32)  # 12x12 grid
        layout = SpriteSheetLayout(mode='square', spacing=1, padding=2)
        
        start_time = time.time()
        
        canvas.set_sprites(sprites)
        canvas.set_layout(layout)
        canvas._generate_preview()
        
        end_time = time.time()
        update_time = end_time - start_time
        
        # Should handle large count within reasonable time
        assert update_time < 5.0, f"Update took too long: {update_time:.3f}s for 144 sprites"
        
    def test_very_large_sprite_performance(self, qapp):
        """Test performance with very large sprites."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(16, 128, 128)  # Large individual sprites
        layout = SpriteSheetLayout(mode='auto', spacing=4, padding=8)
        
        start_time = time.time()
        
        canvas.set_sprites(sprites)
        canvas.set_layout(layout)
        canvas._generate_preview()
        
        end_time = time.time()
        update_time = end_time - start_time
        
        # Large sprites should still be handled efficiently
        assert update_time < 3.0, f"Update took too long: {update_time:.3f}s for 16 large sprites"


class TestMemoryUsage:
    """Test memory usage and cleanup."""
    
    def test_memory_cleanup_after_sprite_change(self, qapp):
        """Test that memory is properly cleaned up when sprites change."""
        canvas = SpriteSheetPreviewCanvas()
        layout = SpriteSheetLayout(mode='auto')
        
        # Create initial sprites
        initial_sprites = create_test_sprites(50, 64, 64)
        canvas.set_sprites(initial_sprites)
        canvas.set_layout(layout)
        canvas._generate_preview()
        
        # Force garbage collection and measure
        gc.collect()
        
        # Replace with different sprites
        new_sprites = create_test_sprites(30, 32, 32)
        canvas.set_sprites(new_sprites)
        canvas._generate_preview()
        
        # Force cleanup
        gc.collect()
        
        # Should not accumulate excessive memory
        # This is a basic test - more sophisticated memory profiling would be better
        assert len(canvas.sprites) == 30, "Should have updated sprite count"
        
    def test_preview_pixmap_cleanup(self, qapp):
        """Test that preview pixmaps are properly managed."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(25, 48, 48)
        layout = SpriteSheetLayout(mode='square', spacing=3, padding=6)
        
        # Generate multiple previews
        for _ in range(10):
            canvas.set_sprites(sprites)
            canvas.set_layout(layout)
            canvas._generate_preview()
            
        # Should not accumulate pixmaps
        # Only one preview pixmap should be active
        assert canvas._preview_pixmap is not None, "Should have a preview pixmap"
        
    def test_large_sprite_count_memory(self, qapp):
        """Test memory usage with large sprite count."""
        canvas = SpriteSheetPreviewCanvas()
        
        # Test with progressively larger sprite counts
        for count in [50, 100, 200]:
            sprites = create_test_sprites(count, 32, 32)
            layout = SpriteSheetLayout(mode='auto', spacing=2, padding=4)
            
            canvas.set_sprites(sprites)
            canvas.set_layout(layout)
            canvas._generate_preview()
            
            # Should handle without crashing
            assert canvas._preview_pixmap is not None, f"Failed to generate preview for {count} sprites"
            
        # Cleanup
        canvas.set_sprites([])
        gc.collect()


class TestDebouncePerformance:
    """Test update debouncing performance."""
    
    def test_rapid_update_debouncing(self, qapp):
        """Test that rapid updates are properly debounced."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(20, 32, 32)
        layout = SpriteSheetLayout(mode='auto')
        
        canvas.set_sprites(sprites)
        canvas.set_layout(layout)
        
        # Mock the timer to count start calls
        start_calls = []
        original_start = canvas._update_timer.start
        
        def mock_start(interval):
            start_calls.append(interval)
            original_start(interval)
            
        canvas._update_timer.start = mock_start
        
        # Trigger multiple rapid updates
        for _ in range(10):
            canvas._invalidate_preview()
            
        # Should have debounced the updates
        assert len(start_calls) == 10, "Should have attempted to start timer for each invalidation"
        
        # All calls should use the same debounce interval
        assert all(call == 50 for call in start_calls), "All timer starts should use 50ms debounce"
        
    def test_debounce_timer_behavior(self, qapp):
        """Test debounce timer behavior under load."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(15, 32, 32)
        
        # Set up timer spy
        timer_starts = 0
        timer_stops = 0
        
        def count_start(interval):
            nonlocal timer_starts
            timer_starts += 1
            QTimer.start(canvas._update_timer, interval)
            
        def count_stop():
            nonlocal timer_stops  
            timer_stops += 1
            QTimer.stop(canvas._update_timer)
            
        canvas._update_timer.start = count_start
        canvas._update_timer.stop = count_stop
        
        # Simulate rapid changes
        canvas.set_sprites(sprites)
        for i in range(5):
            layout = SpriteSheetLayout(mode='auto', spacing=i, padding=i*2)
            canvas.set_layout(layout)
            
        # Should have started timer multiple times
        assert timer_starts > 0, "Timer should have been started"


class TestLayoutCalculationPerformance:
    """Test performance of layout calculations."""
    
    @pytest.mark.parametrize("sprite_count,mode", [
        (16, 'auto'),
        (25, 'square'), 
        (30, 'rows'),
        (40, 'columns'),
        (50, 'custom'),
        (100, 'auto'),
        (144, 'square')
    ])
    def test_layout_calculation_speed(self, qapp, sprite_count, mode):
        """Test layout calculation speed for different modes and counts."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(sprite_count, 32, 32)
        
        # Configure layout based on mode
        if mode == 'custom':
            layout = SpriteSheetLayout(mode=mode, custom_columns=8, custom_rows=8)
        elif mode == 'rows':
            layout = SpriteSheetLayout(mode=mode, max_columns=8)
        elif mode == 'columns':
            layout = SpriteSheetLayout(mode=mode, max_rows=8)
        else:
            layout = SpriteSheetLayout(mode=mode)
            
        canvas.sprites = sprites
        canvas.layout = layout
        
        # Measure calculation time
        start_time = time.time()
        
        # Run calculation multiple times to get average
        for _ in range(100):
            cols, rows = canvas._calculate_grid_layout()
            
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # Should be very fast
        assert avg_time < 0.001, f"Layout calculation too slow: {avg_time:.6f}s for {mode} with {sprite_count} sprites"
        
        # Verify calculation produces valid result
        assert cols > 0 and rows > 0, "Layout calculation should produce positive dimensions"
        assert cols * rows >= sprite_count, "Grid should have enough cells for all sprites"


class TestRenderingPerformance:
    """Test rendering performance."""
    
    def test_background_rendering_performance(self, qapp):
        """Test performance of different background rendering modes."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(25, 32, 32)
        
        background_modes = ['transparent', 'solid', 'checkerboard']
        
        for mode in background_modes:
            layout = SpriteSheetLayout(
                mode='auto',
                spacing=4,
                padding=8,
                background_mode=mode,
                background_color=(255, 255, 255, 255) if mode == 'solid' else (0, 0, 0, 0)
            )
            
            canvas.set_sprites(sprites)
            canvas.set_layout(layout)
            
            start_time = time.time()
            canvas._generate_preview()
            end_time = time.time()
            
            render_time = end_time - start_time
            
            # All background modes should render efficiently
            assert render_time < 2.0, f"Background rendering too slow for {mode}: {render_time:.3f}s"
            
    def test_grid_overlay_performance(self, qapp):
        """Test performance impact of grid overlays."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(36, 32, 32)
        layout = SpriteSheetLayout(mode='square', spacing=4, padding=8)
        
        # Test with grid overlay disabled
        canvas.preview_settings.show_grid = False
        canvas.set_sprites(sprites)
        canvas.set_layout(layout)
        
        start_time = time.time()
        canvas._generate_preview()
        time_without_grid = time.time() - start_time
        
        # Test with grid overlay enabled
        canvas.preview_settings.show_grid = True
        
        start_time = time.time()
        canvas._generate_preview()
        time_with_grid = time.time() - start_time
        
        # Grid overlay shouldn't add significant overhead
        overhead_ratio = time_with_grid / max(time_without_grid, 0.001)  # Avoid division by zero
        assert overhead_ratio < 3.0, f"Grid overlay adds too much overhead: {overhead_ratio:.2f}x slower"
        
    def test_scaling_performance(self, qapp):
        """Test performance of preview scaling."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(20, 64, 64)  # Larger sprites
        layout = SpriteSheetLayout(mode='auto', spacing=2, padding=4)
        
        # Set max preview size to force scaling
        canvas.preview_settings.max_preview_size = 200  # Small size to force scaling
        
        canvas.set_sprites(sprites)
        canvas.set_layout(layout)
        
        start_time = time.time()
        canvas._generate_preview()
        end_time = time.time()
        
        scaling_time = end_time - start_time
        
        # Scaling should not add excessive overhead
        assert scaling_time < 3.0, f"Preview scaling too slow: {scaling_time:.3f}s"
        
        # Verify scaling occurred
        if canvas._preview_pixmap:
            sheet_dimensions = layout.calculate_estimated_dimensions(64, 64, 20)
            max_expected_size = min(sheet_dimensions) 
            # Preview should be scaled down if original was larger than max_preview_size
            if max_expected_size > canvas.preview_settings.max_preview_size:
                assert (canvas._preview_pixmap.width() <= canvas.preview_settings.max_preview_size or 
                       canvas._preview_pixmap.height() <= canvas.preview_settings.max_preview_size), \
                       "Preview should be scaled down to max size"


class TestStressConditions:
    """Test system under stress conditions."""
    
    def test_maximum_sprite_count(self, qapp):
        """Test handling of maximum reasonable sprite count."""
        canvas = SpriteSheetPreviewCanvas()
        
        # Test with maximum practical sprite count (e.g., 20x20 = 400 sprites)
        max_sprites = 400
        sprites = create_test_sprites(max_sprites, 16, 16)  # Smaller sprites to be practical
        layout = SpriteSheetLayout(mode='auto', spacing=1, padding=2)
        
        try:
            canvas.set_sprites(sprites)
            canvas.set_layout(layout)
            
            start_time = time.time()
            canvas._generate_preview()
            end_time = time.time()
            
            # Should handle even large counts
            assert end_time - start_time < 10.0, f"Maximum sprite count handling too slow: {end_time - start_time:.3f}s"
            
            # Verify preview was generated
            assert canvas._preview_pixmap is not None, "Should generate preview even for maximum sprite count"
            
        except Exception as e:
            pytest.fail(f"Failed to handle maximum sprite count: {e}")
            
    def test_extreme_spacing_values(self, qapp):
        """Test handling of extreme spacing values."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(9, 32, 32)  # Small count for extreme spacing
        
        # Test maximum spacing
        layout = SpriteSheetLayout(
            mode='square',
            spacing=Config.Export.MAX_SPRITE_SPACING,  # Maximum allowed
            padding=Config.Export.MAX_SHEET_PADDING    # Maximum allowed
        )
        
        try:
            canvas.set_sprites(sprites)
            canvas.set_layout(layout)
            canvas._generate_preview()
            
            # Should handle extreme values without crashing
            assert canvas._preview_pixmap is not None, "Should handle extreme spacing values"
            
        except Exception as e:
            pytest.fail(f"Failed to handle extreme spacing values: {e}")
            
    def test_rapid_mode_switching(self, qapp):
        """Test rapid switching between layout modes."""
        canvas = SpriteSheetPreviewCanvas()
        sprites = create_test_sprites(16, 32, 32)
        
        modes = ['auto', 'rows', 'columns', 'square', 'custom']
        
        try:
            canvas.set_sprites(sprites)
            
            # Rapidly switch between modes
            for _ in range(20):  # Multiple cycles
                for mode in modes:
                    if mode == 'custom':
                        layout = SpriteSheetLayout(mode=mode, custom_columns=4, custom_rows=4)
                    elif mode == 'rows':
                        layout = SpriteSheetLayout(mode=mode, max_columns=6)
                    elif mode == 'columns':
                        layout = SpriteSheetLayout(mode=mode, max_rows=6)
                    else:
                        layout = SpriteSheetLayout(mode=mode)
                        
                    canvas.set_layout(layout)
                    # Don't wait for debounce - test rapid changes
                    
            # Final generation to verify system is still stable
            canvas._generate_preview()
            assert canvas._preview_pixmap is not None, "Should remain stable after rapid mode switching"
            
        except Exception as e:
            pytest.fail(f"Failed during rapid mode switching: {e}")


if __name__ == "__main__":
    # Run performance tests
    pytest.main([
        __file__,
        "-v",
        "-s",  # Don't capture output so we can see timing info
        "--tb=short"  # Shorter traceback format
    ])