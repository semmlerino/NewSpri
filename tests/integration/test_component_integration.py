"""
Component Integration Tests
Tests the integration between different components of the sprite viewer system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import QApplication

from sprite_viewer import SpriteViewer
from sprite_model import SpriteModel
from core.animation_controller import AnimationController
from core.auto_detection_controller import AutoDetectionController
from ui.sprite_canvas import SpriteCanvas
from ui.playback_controls import PlaybackControls
from ui.frame_extractor import FrameExtractor
from managers import StatusManager, RecentFilesManager, ShortcutManager
from export import ExportDialog
from export.frame_exporter import FrameExporter


class TestModelViewControllerIntegration:
    """Test MVC component integration."""
    
    @pytest.mark.integration
    def test_model_view_sync(self, qtbot):
        """Test that model changes properly update all views."""
        # Create components
        model = SpriteModel()
        canvas = SpriteCanvas()
        playback = PlaybackControls()
        
        qtbot.addWidget(canvas)
        qtbot.addWidget(playback)
        
        # Connect model to views
        model.frameChanged.connect(canvas.set_current_frame)
        model.frameChanged.connect(playback.update_frame_info)
        model.dataLoaded.connect(canvas.update)
        
        # Load sprites
        sprites = [QPixmap(32, 32) for _ in range(10)]
        for i, sprite in enumerate(sprites):
            sprite.fill(QColor.fromHsv(i * 36, 200, 200))
        
        model.sprite_frames = sprites
        model.frameChanged.emit(0, 10)
        
        # Verify views updated
        assert canvas._sprite_pixmap is not None
        assert playback._frame_label.text() == "Frame 1/10"
        
        # Change frame
        model.set_current_frame(5)
        
        # Verify synchronization
        assert canvas._current_frame == 5
        assert "Frame 6/10" in playback._frame_label.text()
    
    @pytest.mark.integration
    def test_controller_coordination(self, qtbot):
        """Test coordination between different controllers."""
        model = SpriteModel()
        animation_controller = AnimationController(model)
        detection_controller = AutoDetectionController(model)
        
        # Load test sprites
        sprites = []
        for i in range(16):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 22, 200, 200))
            sprites.append(pixmap)
        
        model.sprite_frames = sprites
        
        # Test animation controller
        animation_controller.start_animation()
        assert animation_controller.is_playing is True
        
        # Animation should update model
        initial_frame = model.current_frame
        qtbot.wait(200)  # Wait for timer
        assert model.current_frame != initial_frame
        
        animation_controller.stop_animation()
        
        # Test detection controller
        with patch.object(detection_controller, '_analyze_sprite_sheet') as mock_analyze:
            mock_analyze.return_value = {
                'frame_width': 32,
                'frame_height': 32,
                'cols': 4,
                'rows': 4
            }
            
            result = detection_controller.detect_frames(QPixmap(128, 128))
            assert result['frame_width'] == 32
    
    @pytest.mark.integration
    def test_signal_propagation_chain(self, qtbot):
        """Test complex signal propagation chains."""
        # Create full component hierarchy
        model = SpriteModel()
        canvas = SpriteCanvas()
        playback = PlaybackControls()
        extractor = FrameExtractor()
        status_manager = StatusManager()
        
        qtbot.addWidget(canvas)
        qtbot.addWidget(playback)
        qtbot.addWidget(extractor)
        
        # Set up signal connections
        model.frameChanged.connect(canvas.set_current_frame)
        model.frameChanged.connect(playback.update_frame_info)
        model.frameChanged.connect(status_manager.update_frame_info)
        
        canvas.zoomChanged.connect(status_manager.update_zoom_level)
        extractor.settingsChanged.connect(model.update_extraction_settings)
        
        # Test signal chain
        signal_received = {'frame': False, 'zoom': False, 'extraction': False}
        
        def on_frame_change(current, total):
            signal_received['frame'] = True
        
        def on_zoom_change(zoom):
            signal_received['zoom'] = True
        
        def on_extraction_change():
            signal_received['extraction'] = True
        
        # Connect test receivers
        model.frameChanged.connect(on_frame_change)
        canvas.zoomChanged.connect(on_zoom_change)
        extractor.settingsChanged.connect(on_extraction_change)
        
        # Trigger signals
        model.set_current_frame(5)
        canvas.zoom_in()
        extractor.frame_width_spin.setValue(64)
        
        # Verify all signals propagated
        assert all(signal_received.values())


class TestManagerIntegration:
    """Test integration of manager components."""
    
    @pytest.mark.integration
    def test_status_manager_integration(self, qtbot):
        """Test StatusManager integrates with all components."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        status = viewer._status_manager
        
        # Test model integration
        viewer._sprite_model.sprite_frames = [QPixmap(32, 32) for _ in range(10)]
        viewer._sprite_model.frameChanged.emit(5, 10)
        
        # Status should show frame info
        assert "Frame" in status._status_bar.currentMessage()
        
        # Test canvas integration
        viewer._canvas.set_zoom(2.0)
        viewer._canvas.zoomChanged.emit(2.0)
        
        # Status should show zoom
        assert "200%" in status._zoom_label.text()
        
        # Test animation integration
        viewer._animation_controller.fps_changed.emit(15)
        
        # Status should show FPS
        assert "15" in status._fps_label.text()
    
    @pytest.mark.integration
    def test_recent_files_integration(self, qtbot):
        """Test RecentFilesManager integration with menu system."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        recent_files = viewer._recent_files
        
        # Add some files
        test_files = [
            "/path/to/sprite1.png",
            "/path/to/sprite2.png",
            "/path/to/sprite3.png"
        ]
        
        for file_path in test_files:
            recent_files.add_file_to_recent(file_path)
        
        # Check menu updated
        recent_menu = viewer._file_menu.actions()[0].menu()  # Assuming first submenu
        if recent_menu and recent_menu.title() == "Recent Files":
            actions = recent_menu.actions()
            assert len(actions) >= len(test_files)
    
    @pytest.mark.integration
    def test_shortcut_manager_integration(self, qtbot):
        """Test ShortcutManager properly connects to actions."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        shortcuts = viewer._shortcut_manager
        
        # Test shortcut registration
        test_action = Mock()
        shortcuts.register_shortcut("test_action", "Ctrl+T", test_action)
        
        # Verify shortcut exists
        assert "test_action" in shortcuts._shortcuts
        
        # Test shortcut conflict detection
        conflict = shortcuts.check_conflicts("Ctrl+T")
        assert conflict is not None


class TestExportSystemIntegration:
    """Test export system integration with main application."""
    
    @pytest.mark.integration
    def test_export_dialog_data_flow(self, qtbot):
        """Test data flows correctly through export system."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Load sprites
        sprites = []
        for i in range(8):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 45, 200, 200))
            sprites.append(pixmap)
        
        viewer._sprite_model.sprite_frames = sprites
        
        # Create export dialog
        dialog = ExportDialog(
            frame_count=len(sprites),
            current_frame=2,
            sprites=sprites
        )
        qtbot.addWidget(dialog)
        
        # Test wizard mode
        assert hasattr(dialog, 'wizard')
        assert hasattr(dialog, 'type_step')
        assert hasattr(dialog, 'settings_step')
        assert hasattr(dialog, 'preview_step')
        
        # Select export type
        dialog.type_step._selected_preset = Mock(
            name="individual_frames",
            mode="individual",
            format="PNG"
        )
        
        # Verify data propagation
        type_data = dialog.type_step.get_data()
        assert type_data['export_mode'] == "individual"
        
        # Configure settings
        dialog.wizard.current_step_index = 1
        dialog.settings_step._setup_for_preset(dialog.type_step._selected_preset)
        
        # Verify settings widgets created
        assert hasattr(dialog.settings_step, 'directory_selector')
        assert hasattr(dialog.settings_step, 'base_name_edit')
    
    @pytest.mark.integration
    def test_frame_exporter_integration(self, qtbot, tmp_path):
        """Test FrameExporter integrates with export dialog."""
        exporter = FrameExporter()
        
        # Create test sprites
        sprites = []
        for i in range(4):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 90, 200, 200))
            sprites.append(pixmap)
        
        # Test export with real file writing
        export_complete = {'done': False}
        
        def on_complete(success):
            export_complete['done'] = success
        
        exporter.exportFinished.connect(on_complete)
        
        # Export frames
        success = exporter.export_frames(
            sprites=sprites,
            output_dir=str(tmp_path),
            base_name="test",
            format="PNG",
            mode="individual"
        )
        
        # Verify files created
        exported_files = list(tmp_path.glob("*.png"))
        assert len(exported_files) == 4
        assert all(f.exists() for f in exported_files)


class TestUIComponentIntegration:
    """Test UI component integration."""
    
    @pytest.mark.integration
    def test_canvas_playback_integration(self, qtbot):
        """Test canvas and playback controls work together."""
        model = SpriteModel()
        canvas = SpriteCanvas()
        playback = PlaybackControls()
        controller = AnimationController(model)
        
        qtbot.addWidget(canvas)
        qtbot.addWidget(playback)
        
        # Connect components
        model.frameChanged.connect(canvas.set_current_frame)
        controller.animationStarted.connect(playback.on_animation_started)
        controller.animationStopped.connect(playback.on_animation_stopped)
        playback.play_clicked.connect(controller.start_animation)
        playback.pause_clicked.connect(controller.stop_animation)
        
        # Load sprites
        for i in range(8):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 45, 200, 200))
            model.sprite_frames.append(pixmap)
        
        # Test playback control
        playback._play_button.click()
        assert controller.is_playing is True
        assert playback._play_button.isVisible() is False
        assert playback._pause_button.isVisible() is True
        
        # Test frame updates during animation
        initial_frame = canvas._current_frame
        qtbot.wait(200)
        assert canvas._current_frame != initial_frame
        
        # Stop playback
        playback._pause_button.click()
        assert controller.is_playing is False
    
    @pytest.mark.integration
    def test_frame_extractor_model_sync(self, qtbot):
        """Test frame extractor syncs with model."""
        model = SpriteModel()
        extractor = FrameExtractor()
        qtbot.addWidget(extractor)
        
        # Connect extractor to model
        extractor.settingsChanged.connect(model.update_extraction_settings)
        
        # Change extraction settings
        settings_received = {'updated': False}
        
        def on_settings_update(settings):
            settings_received['updated'] = True
            settings_received['width'] = settings.get('frame_width')
            settings_received['height'] = settings.get('frame_height')
        
        model.update_extraction_settings = on_settings_update
        
        # Update extractor
        extractor.frame_width_spin.setValue(64)
        extractor.frame_height_spin.setValue(64)
        
        # Verify model received update
        assert settings_received['updated'] is True
        assert settings_received['width'] == 64
        assert settings_received['height'] == 64


class TestCrossComponentCommunication:
    """Test communication across multiple component boundaries."""
    
    @pytest.mark.integration
    def test_full_signal_flow(self, qtbot):
        """Test signals flow through entire component hierarchy."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Track signal flow
        signals_fired = []
        
        def track_signal(name):
            def handler(*args):
                signals_fired.append(name)
            return handler
        
        # Monitor key signals
        viewer._sprite_model.frameChanged.connect(track_signal('model.frameChanged'))
        viewer._canvas.zoomChanged.connect(track_signal('canvas.zoomChanged'))
        viewer._animation_controller.animationStarted.connect(track_signal('controller.started'))
        viewer._frame_extractor.settingsChanged.connect(track_signal('extractor.changed'))
        
        # Trigger actions that should cascade signals
        viewer._sprite_model.sprite_frames = [QPixmap(32, 32) for _ in range(5)]
        viewer._sprite_model.set_current_frame(2)
        viewer._canvas.zoom_in()
        viewer._animation_controller.start_animation()
        viewer._frame_extractor.frame_width_spin.setValue(48)
        
        # Verify signal cascade
        assert 'model.frameChanged' in signals_fired
        assert 'canvas.zoomChanged' in signals_fired
        assert 'controller.started' in signals_fired
        assert 'extractor.changed' in signals_fired
    
    @pytest.mark.integration
    def test_error_propagation(self, qtbot):
        """Test error handling across components."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        errors_caught = []
        
        # Mock error handler
        def on_error(error_msg):
            errors_caught.append(error_msg)
        
        # Connect error handlers
        if hasattr(viewer._sprite_model, 'errorOccurred'):
            viewer._sprite_model.errorOccurred.connect(on_error)
        
        # Trigger various errors
        with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical:
            # Invalid file load
            viewer._sprite_model.load_sprite_sheet("/nonexistent/file.png")
            
            # Invalid frame access
            viewer._sprite_model.set_current_frame(999)
            
            # Verify errors handled gracefully
            assert viewer._sprite_model.current_frame < len(viewer._sprite_model.sprite_frames)


class TestPerformanceIntegration:
    """Test performance across integrated components."""
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_large_sprite_integration_performance(self, qtbot, benchmark):
        """Test performance with large sprite counts across components."""
        def create_and_process_large_viewer():
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            # Create many sprites
            sprite_count = 200
            for i in range(sprite_count):
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor.fromHsv(i * 360 // sprite_count, 200, 200))
                viewer._sprite_model.sprite_frames.append(pixmap)
            
            # Trigger updates across components
            viewer._sprite_model.frameChanged.emit(0, sprite_count)
            viewer._canvas.update()
            viewer._playback_controls.update_frame_info(0, sprite_count)
            
            # Navigate frames
            for i in range(10):
                viewer._sprite_model.set_current_frame(i)
                QApplication.processEvents()
            
            return viewer
        
        # Should handle 200 sprites efficiently
        result = benchmark(create_and_process_large_viewer)
        assert result.stats['mean'] < 1.0  # Under 1 second
    
    @pytest.mark.integration
    def test_rapid_update_handling(self, qtbot):
        """Test handling of rapid updates across components."""
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Load sprites
        for i in range(50):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor.fromHsv(i * 7, 200, 200))
            viewer._sprite_model.sprite_frames.append(pixmap)
        
        # Rapid frame changes
        update_count = 0
        
        def count_updates():
            nonlocal update_count
            update_count += 1
        
        viewer._canvas.paintEvent = lambda e: count_updates()
        
        # Change frames rapidly
        for i in range(50):
            viewer._sprite_model.set_current_frame(i % 50)
            QApplication.processEvents()
        
        # Should batch updates efficiently
        assert update_count < 50  # Some updates should be batched