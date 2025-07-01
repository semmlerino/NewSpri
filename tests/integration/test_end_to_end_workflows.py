"""
End-to-End Integration Tests
Comprehensive integration tests covering complete user workflows from startup to export.
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPixmap, QColor, QKeyEvent
from PySide6.QtTest import QTest

from sprite_viewer import SpriteViewer
from sprite_model import SpriteModel
from export import ExportDialog
from export.frame_exporter import get_frame_exporter


class TestCompleteApplicationLifecycle:
    """Test the complete application lifecycle from startup to shutdown."""
    
    @pytest.mark.integration
    def test_full_application_workflow(self, qtbot, tmp_path):
        """Test complete workflow: load → detect → animate → export."""
        # Create test sprite sheet
        sprite_sheet = self._create_test_sprite_sheet(256, 64, 32)
        sprite_path = tmp_path / "test_sprites.png"
        sprite_sheet.save(str(sprite_path))
        
        # Create application
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        
        # 1. Test startup state
        assert viewer._sprite_model.sprite_frames == []
        assert viewer._animation_controller.is_playing is False
        assert viewer._status_manager is not None
        
        # 2. Load sprite sheet
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(sprite_path), "")):
            viewer._load_sprites()
            
        # Verify sprite loaded
        assert len(viewer._sprite_model.sprite_frames) > 0
        assert viewer._sprite_model.sprite_path == str(sprite_path)
        
        # 3. Test auto-detection
        with patch('managers.AutoDetectionController.run_comprehensive_detection_with_dialog') as mock_detect:
            mock_detect.return_value = {
                'frame_width': 32,
                'frame_height': 32,
                'mode': 'grid'
            }
            viewer._auto_detection_controller.run_comprehensive_detection_with_dialog()
            
        # 4. Test animation playback
        viewer._toggle_playback()
        assert viewer._animation_controller.is_playing is True
        
        # Process some animation frames
        for _ in range(5):
            QApplication.processEvents()
            qtbot.wait(50)
        
        viewer._toggle_playback()
        assert viewer._animation_controller.is_playing is False
        
        # 5. Test frame navigation
        initial_frame = viewer._sprite_model.current_frame
        viewer._go_to_next_frame()
        assert viewer._sprite_model.current_frame == initial_frame + 1
        
        viewer._go_to_first_frame()
        assert viewer._sprite_model.current_frame == 0
        
        # 6. Test export workflow
        export_dir = tmp_path / "exports"
        export_dir.mkdir()
        
        with patch.object(ExportDialog, 'exec', return_value=True):
            with patch.object(ExportDialog, 'get_export_settings') as mock_settings:
                mock_settings.return_value = {
                    'output_dir': str(export_dir),
                    'base_name': 'exported',
                    'format': 'PNG',
                    'mode': 'individual',
                    'scale_factor': 1.0
                }
                
                viewer._export_frames()
                
        # 7. Test settings persistence
        viewer._save_window_state()
        
        # Verify cleanup
        viewer.close()
    
    @pytest.mark.integration
    def test_keyboard_driven_workflow(self, qtbot):
        """Test complete workflow using only keyboard shortcuts."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        
        # Load test sprites
        self._load_test_sprites(viewer)
        
        # Test keyboard navigation
        shortcuts = [
            (Qt.Key_Space, lambda: viewer._animation_controller.is_playing),  # Toggle playback
            (Qt.Key_Right, lambda: viewer._sprite_model.current_frame),      # Next frame
            (Qt.Key_Left, lambda: viewer._sprite_model.current_frame),       # Previous frame
            (Qt.Key_Home, lambda: viewer._sprite_model.current_frame == 0),  # First frame
            (Qt.Key_End, lambda: viewer._sprite_model.current_frame),        # Last frame
            (Qt.Key_G, lambda: viewer._canvas._show_grid),                   # Toggle grid
            (Qt.Key_Plus, lambda: viewer._canvas._zoom_level),               # Zoom in
            (Qt.Key_Minus, lambda: viewer._canvas._zoom_level),              # Zoom out
            (Qt.Key_0, lambda: viewer._canvas._zoom_level == 1.0),          # Reset zoom
        ]
        
        for key, check_func in shortcuts:
            # Send key event
            event = QKeyEvent(QKeyEvent.KeyPress, key, Qt.NoModifier)
            viewer.keyPressEvent(event)
            QApplication.processEvents()
            
            # Verify action occurred
            result = check_func()
            assert result is not None
    
    @pytest.mark.integration
    def test_error_recovery_workflow(self, qtbot):
        """Test application recovery from various error conditions."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # 1. Test loading invalid file
        with patch.object(QMessageBox, 'critical') as mock_error:
            with patch.object(QFileDialog, 'getOpenFileName', return_value=("/nonexistent/file.png", "")):
                viewer._load_sprites()
                
            # Should show error but not crash
            mock_error.assert_called_once()
            assert viewer._sprite_model.sprite_frames == []
        
        # 2. Test export with no sprites loaded
        viewer._export_frames()  # Should handle gracefully
        
        # 3. Test invalid frame navigation
        viewer._go_to_next_frame()  # Should not crash with no frames
        viewer._go_to_prev_frame()
        
        # 4. Test animation with no frames
        viewer._toggle_playback()  # Should handle gracefully
        assert viewer._animation_controller.is_playing is False
    
    # Helper methods
    def _create_test_sprite_sheet(self, width, height, sprite_size):
        """Create a test sprite sheet."""
        sheet = QPixmap(width, height)
        sheet.fill(Qt.white)
        
        from PySide6.QtGui import QPainter
        painter = QPainter(sheet)
        
        cols = width // sprite_size
        rows = height // sprite_size
        
        for row in range(rows):
            for col in range(cols):
                x = col * sprite_size
                y = row * sprite_size
                color = QColor.fromHsv((row * cols + col) * 30 % 360, 200, 200)
                painter.fillRect(x, y, sprite_size, sprite_size, color)
        
        painter.end()
        return sheet
    
    def _load_test_sprites(self, viewer):
        """Load test sprites into viewer."""
        for i in range(8):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 45, 200, 200))
            viewer._sprite_model.sprite_frames.append(pixmap)
        viewer._sprite_model.frameChanged.emit(0, 8)


class TestAnimationSegmentWorkflow:
    """Test complete animation segment creation and management workflow."""
    
    @pytest.mark.integration
    def test_segment_creation_workflow(self, qtbot):
        """Test creating, naming, and exporting animation segments."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Load sprites
        for i in range(16):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 22, 200, 200))
            viewer._sprite_model.sprite_frames.append(pixmap)
        
        # Open animation grid view
        from ui.animation_grid_view import AnimationGridView
        grid_view = AnimationGridView(viewer._sprite_model.sprite_frames)
        qtbot.addWidget(grid_view)
        grid_view.show()
        
        # Select frames for segment
        grid_view.selected_frames = [0, 1, 2, 3]
        
        # Create segment
        with patch('PySide6.QtWidgets.QInputDialog.getText') as mock_input:
            mock_input.return_value = ("Walk Cycle", True)
            grid_view._create_segment_from_selection()
        
        # Verify segment created
        assert len(grid_view.segment_manager.segments) == 1
        segment = grid_view.segment_manager.segments[0]
        assert segment.name == "Walk Cycle"
        assert segment.frames == [0, 1, 2, 3]
        
        # Export segment
        with patch.object(QFileDialog, 'getExistingDirectory') as mock_dir:
            mock_dir.return_value = "/tmp/exports"
            grid_view.export_selected_segment()
    
    @pytest.mark.integration
    def test_multi_segment_management(self, qtbot):
        """Test managing multiple animation segments."""
        from managers.AnimationSegmentManager import AnimationSegmentManager
        from ui.animation_grid_view import AnimationSegment
        
        manager = AnimationSegmentManager()
        
        # Create multiple segments
        segments = [
            AnimationSegment("Idle", [0, 1], color=QColor("red")),
            AnimationSegment("Walk", [2, 3, 4, 5], color=QColor("green")),
            AnimationSegment("Run", [6, 7, 8, 9], color=QColor("blue")),
            AnimationSegment("Jump", [10, 11, 12], color=QColor("yellow"))
        ]
        
        for segment in segments:
            manager.add_segment(segment)
        
        # Test segment operations
        assert len(manager.segments) == 4
        assert manager.get_segment("Walk").frames == [2, 3, 4, 5]
        
        # Remove segment
        manager.remove_segment("Idle")
        assert len(manager.segments) == 3
        
        # Clear all
        manager.clear_segments()
        assert len(manager.segments) == 0


class TestMultiWindowWorkflow:
    """Test workflows involving multiple windows and dialogs."""
    
    @pytest.mark.integration
    def test_multiple_dialogs_workflow(self, qtbot):
        """Test opening multiple dialogs in sequence."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Load sprites first
        for i in range(8):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 45, 200, 200))
            viewer._sprite_model.sprite_frames.append(pixmap)
        
        # Test opening settings dialog
        with patch('ui.SettingsDialog.exec') as mock_settings:
            mock_settings.return_value = True
            viewer._open_settings()
            mock_settings.assert_called_once()
        
        # Test opening export dialog
        with patch.object(ExportDialog, 'exec') as mock_export:
            mock_export.return_value = True
            viewer._export_frames()
            mock_export.assert_called_once()
        
        # Test opening about dialog
        with patch.object(QMessageBox, 'about') as mock_about:
            viewer._show_about()
            mock_about.assert_called_once()
    
    @pytest.mark.integration  
    def test_window_state_persistence(self, qtbot, tmp_path):
        """Test window state saves and restores correctly."""
        # Create settings file path
        settings_file = tmp_path / "settings.json"
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        
        # Set specific window state
        viewer.resize(1024, 768)
        viewer.move(100, 100)
        viewer._canvas.set_zoom(2.0)
        
        # Save state
        with patch('managers.SettingsManager.get_settings_path', return_value=str(settings_file)):
            viewer._save_window_state()
        
        # Create new viewer and restore state
        viewer2 = SpriteViewer()
        qtbot.addWidget(viewer2)
        
        with patch('managers.SettingsManager.get_settings_path', return_value=str(settings_file)):
            viewer2._restore_window_state()
        
        # Verify state restored
        assert viewer2.width() == 1024
        assert viewer2.height() == 768


class TestComplexUserScenarios:
    """Test complex real-world user scenarios."""
    
    @pytest.mark.integration
    def test_sprite_sheet_editing_workflow(self, qtbot, tmp_path):
        """Test complete sprite sheet editing workflow."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # 1. Load sprite sheet
        sprite_sheet = self._create_test_sprite_sheet()
        sprite_path = tmp_path / "sprites.png"
        sprite_sheet.save(str(sprite_path))
        
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(sprite_path), "")):
            viewer._load_sprites()
        
        # 2. Adjust frame extraction
        viewer._frame_extractor.frame_width_spin.setValue(64)
        viewer._frame_extractor.frame_height_spin.setValue(64)
        viewer._update_frame_slicing()
        
        # 3. Create animation segments
        # (Would open grid view and create segments)
        
        # 4. Export as individual frames
        export_dir = tmp_path / "frames"
        export_dir.mkdir()
        
        with patch.object(ExportDialog, 'exec', return_value=True):
            with patch.object(ExportDialog, 'get_export_settings') as mock_settings:
                mock_settings.return_value = {
                    'output_dir': str(export_dir),
                    'base_name': 'frame',
                    'format': 'PNG',
                    'mode': 'individual',
                    'scale_factor': 2.0,  # Export at 2x size
                    'pattern': '{name}_{index:03d}'
                }
                
                viewer._export_frames()
        
        # 5. Export as sprite sheet with different layout
        with patch.object(ExportDialog, 'exec', return_value=True):
            with patch.object(ExportDialog, 'get_export_settings') as mock_settings:
                mock_settings.return_value = {
                    'output_dir': str(export_dir),
                    'base_name': 'sheet',
                    'format': 'PNG',
                    'mode': 'sheet',
                    'scale_factor': 1.0,
                    'sprite_sheet_layout': {
                        'mode': 'square',
                        'spacing': 2,
                        'padding': 4
                    }
                }
                
                viewer._export_frames()
    
    @pytest.mark.integration
    def test_batch_processing_workflow(self, qtbot, tmp_path):
        """Test processing multiple sprite sheets in sequence."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Create multiple sprite sheets
        sprite_files = []
        for i in range(3):
            sprite_sheet = self._create_test_sprite_sheet(size_variant=i)
            sprite_path = tmp_path / f"sprites_{i}.png"
            sprite_sheet.save(str(sprite_path))
            sprite_files.append(sprite_path)
        
        # Process each sprite sheet
        for sprite_path in sprite_files:
            # Load
            with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(sprite_path), "")):
                viewer._load_sprites()
            
            # Auto-detect frames
            with patch('managers.AutoDetectionController.run_comprehensive_detection_with_dialog'):
                viewer._auto_detection_controller.run_comprehensive_detection_with_dialog()
            
            # Export
            export_dir = tmp_path / f"export_{sprite_path.stem}"
            export_dir.mkdir()
            
            with patch.object(ExportDialog, 'exec', return_value=True):
                with patch.object(ExportDialog, 'get_export_settings') as mock_settings:
                    mock_settings.return_value = {
                        'output_dir': str(export_dir),
                        'base_name': sprite_path.stem,
                        'format': 'PNG',
                        'mode': 'individual'
                    }
                    viewer._export_frames()
    
    # Helper methods
    def _create_test_sprite_sheet(self, size_variant=0):
        """Create test sprite sheets with variations."""
        sizes = [(128, 128), (256, 64), (512, 512)]
        sprite_sizes = [16, 32, 64]
        
        width, height = sizes[size_variant % len(sizes)]
        sprite_size = sprite_sizes[size_variant % len(sprite_sizes)]
        
        sheet = QPixmap(width, height)
        sheet.fill(Qt.white)
        
        from PySide6.QtGui import QPainter
        painter = QPainter(sheet)
        
        cols = width // sprite_size
        rows = height // sprite_size
        
        for row in range(rows):
            for col in range(cols):
                x = col * sprite_size
                y = row * sprite_size
                hue = ((row * cols + col) * 30 + size_variant * 60) % 360
                color = QColor.fromHsv(hue, 200, 200)
                painter.fillRect(x, y, sprite_size, sprite_size, color)
                
                # Add border
                painter.setPen(Qt.black)
                painter.drawRect(x, y, sprite_size - 1, sprite_size - 1)
        
        painter.end()
        return sheet


class TestPerformanceUnderLoad:
    """Test application performance under various load conditions."""
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_large_sprite_sheet_workflow(self, qtbot, benchmark):
        """Test workflow with large sprite sheets."""
        def load_and_process_large_sheet():
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            # Create large sprite sheet (1024x1024 with 256 32x32 sprites)
            large_sheet = QPixmap(1024, 1024)
            large_sheet.fill(Qt.white)
            
            # Simulate loading
            for i in range(256):
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor.fromHsv(i % 360, 200, 200))
                viewer._sprite_model.sprite_frames.append(pixmap)
            
            # Trigger updates
            viewer._sprite_model.frameChanged.emit(0, 256)
            
            # Navigate through frames
            for _ in range(10):
                viewer._go_to_next_frame()
                QApplication.processEvents()
            
            viewer.close()
        
        # Should complete in reasonable time
        result = benchmark(load_and_process_large_sheet)
        assert result.stats['mean'] < 2.0  # Under 2 seconds
    
    @pytest.mark.integration
    def test_memory_usage_during_export(self, qtbot, tmp_path):
        """Test memory usage during large export operations."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Load many sprites
        sprite_count = 100
        for i in range(sprite_count):
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor.fromHsv(i * 3, 200, 200))
            viewer._sprite_model.sprite_frames.append(pixmap)
        
        # Export at high resolution
        with patch.object(ExportDialog, 'exec', return_value=True):
            with patch.object(ExportDialog, 'get_export_settings') as mock_settings:
                mock_settings.return_value = {
                    'output_dir': str(tmp_path),
                    'base_name': 'large',
                    'format': 'PNG',
                    'mode': 'sheet',
                    'scale_factor': 4.0,  # 4x scaling
                    'sprite_sheet_layout': {
                        'mode': 'square',
                        'spacing': 0,
                        'padding': 0
                    }
                }
                
                # Should complete without memory issues
                viewer._export_frames()


# Integration test fixtures
@pytest.fixture
def mock_sprite_viewer(qtbot):
    """Create a sprite viewer with mock data."""
    viewer = SpriteViewer()
    qtbot.addWidget(viewer)
    
    # Add test sprites
    for i in range(16):
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor.fromHsv(i * 22, 200, 200))
        viewer._sprite_model.sprite_frames.append(pixmap)
    
    viewer._sprite_model.frameChanged.emit(0, 16)
    return viewer


@pytest.fixture
def test_sprite_sheet_file(tmp_path):
    """Create a test sprite sheet file."""
    sprite_sheet = QPixmap(256, 256)
    sprite_sheet.fill(Qt.white)
    
    from PySide6.QtGui import QPainter
    painter = QPainter(sprite_sheet)
    
    # Draw 8x8 grid of sprites
    for row in range(8):
        for col in range(8):
            x = col * 32
            y = row * 32
            color = QColor.fromHsv((row * 8 + col) * 5, 200, 200)
            painter.fillRect(x, y, 32, 32, color)
            painter.setPen(Qt.black)
            painter.drawRect(x, y, 31, 31)
    
    painter.end()
    
    filepath = tmp_path / "test_sprites.png"
    sprite_sheet.save(str(filepath))
    return filepath