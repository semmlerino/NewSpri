"""
Integration Tests for Animation Segment Persistence
Tests that segments are properly saved and loaded across application restarts.
"""

import pytest
import tempfile
import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor, QPainter
from PySide6.QtWidgets import QApplication

from sprite_viewer import SpriteViewer
from managers.animation_segment_manager import AnimationSegmentManager
from ui.animation_grid_view import AnimationSegment


class TestSegmentPersistence:
    """Test segment persistence across application restarts."""
    
    @pytest.mark.integration
    def test_segments_persist_after_reload(self, qtbot, tmp_path):
        """Test that segments are automatically loaded when sprite sheet is reloaded."""
        # Create a sprite sheet file
        sprite_path = tmp_path / "test_sprite.png"
        sprite_sheet = self._create_test_sprite_sheet()
        sprite_sheet.save(str(sprite_path))
        
        # First session - create segments
        viewer1 = SpriteViewer()
        qtbot.addWidget(viewer1)
        
        # Load sprite sheet
        success, msg = viewer1._sprite_model.load_sprite_sheet(str(sprite_path))
        assert success, f"Failed to load sprite sheet: {msg}"
        
        # Extract frames
        viewer1._sprite_model.set_extraction_mode('grid')
        success, msg, count = viewer1._sprite_model.extract_frames(32, 32, 0, 0, 0, 0)
        assert success
        assert count == 8
        
        # Process Qt events to ensure extraction is fully complete
        QApplication.processEvents()
        
        # Create segments
        success1, msg1 = viewer1._segment_manager.add_segment("Walk", 0, 3)
        assert success1, f"Failed to create Walk segment: {msg1}"
        
        success2, msg2 = viewer1._segment_manager.add_segment("Run", 4, 7)
        assert success2, f"Failed to create Run segment: {msg2}"
        
        # Verify segments were created
        segments = viewer1._segment_manager.get_all_segments()
        assert len(segments) == 2
        
        # Check segments file was created
        segments_dir = sprite_path.parent / ".sprite_segments"
        segments_file = segments_dir / f"{sprite_path.stem}_segments.json"
        assert segments_file.exists(), "Segments file should be created"
        
        # Close first viewer
        viewer1.close()
        
        # Second session - verify segments are loaded
        viewer2 = SpriteViewer()
        qtbot.addWidget(viewer2)
        
        # Load the same sprite sheet
        success, msg = viewer2._sprite_model.load_sprite_sheet(str(sprite_path))
        assert success
        
        # Extract frames
        viewer2._sprite_model.set_extraction_mode('grid')
        success, msg, count = viewer2._sprite_model.extract_frames(32, 32, 0, 0, 0, 0)
        assert success
        assert count == 8
        
        # Process Qt events to ensure extraction is fully complete
        QApplication.processEvents()
        
        # Verify segments were loaded
        loaded_segments = viewer2._segment_manager.get_all_segments()
        assert len(loaded_segments) == 2, f"Expected 2 segments, got {len(loaded_segments)}"
        
        # Verify segment data
        segment_names = {seg.name for seg in loaded_segments}
        assert "Walk" in segment_names
        assert "Run" in segment_names
        
        # Verify grid view has segments
        grid_segments = viewer2._grid_view.get_segments()
        assert len(grid_segments) == 2
        
        # Clean up
        viewer2.close()
    
    @pytest.mark.integration
    def test_segment_manager_direct_persistence(self, tmp_path):
        """Test segment manager persistence directly without UI."""
        sprite_path = tmp_path / "test_sprite.png"
        # Create a dummy sprite file without using Qt
        sprite_path.write_bytes(b"PNG\x89\x50\x4E\x47\x0D\x0A\x1A\x0A")  # Minimal PNG header
        
        # Create first manager and add segments
        manager1 = AnimationSegmentManager()
        manager1.set_sprite_context(str(sprite_path), 10)
        
        # Add segments
        manager1.add_segment("Attack", 0, 4)
        manager1.add_segment("Defend", 5, 9)
        
        # Verify save
        segments_file = Path(manager1._get_segments_file_path())
        assert segments_file.exists()
        
        # Create second manager and verify automatic loading
        manager2 = AnimationSegmentManager()
        manager2.set_sprite_context(str(sprite_path), 10)
        
        # Check segments were loaded
        loaded_segments = manager2.get_all_segments()
        assert len(loaded_segments) == 2
        
        segment_names = {seg.name for seg in loaded_segments}
        assert "Attack" in segment_names
        assert "Defend" in segment_names
    
    @pytest.mark.integration
    def test_segments_cleared_when_switching_sprites(self, qtbot, tmp_path):
        """Test that segments are cleared when loading a different sprite."""
        # Create two different sprite sheets
        sprite1_path = tmp_path / "sprite1.png"
        sprite2_path = tmp_path / "sprite2.png"
        
        sprite1 = self._create_test_sprite_sheet()
        sprite1.save(str(sprite1_path))
        
        sprite2 = self._create_test_sprite_sheet()
        sprite2.save(str(sprite2_path))
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Load first sprite and create segments
        viewer._sprite_model.load_sprite_sheet(str(sprite1_path))
        viewer._sprite_model.set_extraction_mode('grid')
        success, msg, count = viewer._sprite_model.extract_frames(32, 32, 0, 0, 0, 0)
        assert success
        
        # Process Qt events to ensure extraction is fully complete
        QApplication.processEvents()

        viewer._segment_manager.add_segment("Sprite1_Segment", 0, 3)
        
        # Verify segment exists
        assert len(viewer._segment_manager.get_all_segments()) == 1
        
        
        # Load second sprite
        viewer._sprite_model.load_sprite_sheet(str(sprite2_path))
        viewer._sprite_model.set_extraction_mode('grid')
        success, msg, count = viewer._sprite_model.extract_frames(32, 32, 0, 0, 0, 0)
        assert success
        
        # Process Qt events to ensure extraction is fully complete
        QApplication.processEvents()

        # Verify segments were cleared
        assert len(viewer._segment_manager.get_all_segments()) == 0
        
        # Add segment for second sprite
        viewer._segment_manager.add_segment("Sprite2_Segment", 0, 3)
        
        # Load first sprite again
        viewer._sprite_model.load_sprite_sheet(str(sprite1_path))
        
        viewer._sprite_model.set_extraction_mode('grid')
        success, msg, count = viewer._sprite_model.extract_frames(32, 32, 0, 0, 0, 0)
        assert success
        
        # Process Qt events to ensure extraction is fully complete
        QApplication.processEvents()

        # Verify first sprite's segments are loaded
        segments = viewer._segment_manager.get_all_segments()
        assert len(segments) == 1
        assert segments[0].name == "Sprite1_Segment"
        
        viewer.close()
    
    def _create_test_sprite_sheet(self):
        """Create a test sprite sheet with 8 frames."""
        sheet = QPixmap(256, 32)
        sheet.fill(Qt.transparent)
        
        painter = QPainter(sheet)
        
        for i in range(8):
            x = i * 32
            color = QColor.fromHsv(i * 45, 200, 200)
            painter.fillRect(x + 2, 2, 28, 28, color)
        
        painter.end()
        return sheet

    @pytest.mark.integration
    def test_corrupted_segment_json_recovery(self, tmp_path):
        """Verify graceful handling of malformed .sprite_segments/ files."""
        sprite_path = tmp_path / "test_sprite.png"
        sprite_path.write_bytes(b"PNG\x89\x50\x4E\x47\x0D\x0A\x1A\x0A")  # Minimal PNG header

        # Create segments directory and write corrupted JSON
        segments_dir = sprite_path.parent / ".sprite_segments"
        segments_dir.mkdir(exist_ok=True)

        segments_file = segments_dir / f"{sprite_path.stem}_segments.json"
        with open(segments_file, 'w') as f:
            f.write("{ invalid json content }")

        # Create manager and set context (should not crash)
        manager = AnimationSegmentManager()

        # This should not raise an exception
        try:
            manager.set_sprite_context(str(sprite_path), frame_count=8)
        except json.JSONDecodeError:
            pytest.fail("Manager should handle corrupted JSON gracefully")

        # Manager should have no segments (corrupted file ignored)
        assert len(manager.get_all_segments()) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])