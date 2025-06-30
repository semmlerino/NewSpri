"""
Unit tests for SpriteViewer initialization.
Tests that SpriteViewer initializes without AttributeError using REAL components.
"""

import pytest
import sys
import os
from unittest.mock import patch


class TestSpriteViewerInitialization:
    """Test SpriteViewer initialization order and dependencies with real components."""
    
    def test_sprite_viewer_init_no_attribute_error(self, qtbot):
        """Test that SpriteViewer initializes without AttributeError using real components."""
        from sprite_viewer import SpriteViewer
        
        # Test REAL initialization - no mocking of internal methods
        try:
            # This should not raise any AttributeError
            viewer = SpriteViewer()
            qtbot.addWidget(viewer)
            
            # Verify that the status manager was created
            assert hasattr(viewer, '_status_manager')
            assert viewer._status_manager is not None
            
            # Verify that status bar was created and is the right type
            from enhanced_status_bar import EnhancedStatusBar
            assert hasattr(viewer, '_status_manager')
            assert viewer._status_manager is not None
            assert isinstance(viewer.statusBar(), EnhancedStatusBar)
            
            # Verify that other essential components exist and are real objects
            assert hasattr(viewer, '_settings_manager')
            assert hasattr(viewer, '_recent_files')
            assert hasattr(viewer, '_sprite_model')
            assert hasattr(viewer, '_animation_controller')
            
            # Test the objects are actually the right types
            from settings_manager import SettingsManager
            from recent_files_manager import RecentFilesManager
            from sprite_model import SpriteModel
            from animation_controller import AnimationController
            
            assert isinstance(viewer._settings_manager, SettingsManager)
            assert isinstance(viewer._recent_files, RecentFilesManager)
            assert isinstance(viewer._sprite_model, SpriteModel)
            assert isinstance(viewer._animation_controller, AnimationController)
            
        except AttributeError as e:
            pytest.fail(f"SpriteViewer initialization failed with AttributeError: {e}")
        except Exception as e:
            pytest.fail(f"SpriteViewer initialization failed with unexpected error: {e}")
    
    def test_status_manager_api_exists(self, qtbot):
        """Test that status manager has required methods after initialization."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Test that status manager has the methods that caused failures
        status_manager = viewer._status_manager
        
        # These methods must exist (they were missing and caused errors)
        assert hasattr(status_manager, 'show_message')
        assert hasattr(status_manager, 'update_mouse_position')
        assert hasattr(status_manager, 'connect_to_sprite_model')
        assert hasattr(status_manager, 'connect_to_animation_controller') 
        assert hasattr(status_manager, 'connect_to_canvas')
        
        # Test that these methods are actually callable
        assert callable(status_manager.show_message)
        assert callable(status_manager.update_mouse_position)
        assert callable(status_manager.connect_to_sprite_model)
        assert callable(status_manager.connect_to_animation_controller)
        assert callable(status_manager.connect_to_canvas)
        
        # Test actual method calls work (these were failing before)
        status_manager.show_message("Test message")
        status_manager.update_mouse_position(100, 200)
    
    def test_animation_controller_api_contract(self, qtbot):
        """Test that AnimationController has the correct API contract."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        controller = viewer._animation_controller
        
        # Test that is_playing is a property, not a method (this was failing)
        assert hasattr(controller, 'is_playing')
        
        # Test that accessing is_playing doesn't raise TypeError
        try:
            is_playing = controller.is_playing  # Should not be callable
            assert isinstance(is_playing, bool)
        except TypeError as e:
            pytest.fail(f"is_playing should be a property, not method: {e}")
        
        # Test that initialize method exists and can be called
        assert hasattr(controller, 'initialize')
        assert callable(controller.initialize)
    
    def test_canvas_signal_connections(self, qtbot):
        """Test that canvas has the correct signals for connections."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        canvas = viewer._canvas
        
        # Test that canvas has the signals we connect to (these were wrong)
        assert hasattr(canvas, 'zoomChanged')  # This was correct
        assert hasattr(canvas, 'mouseMoved')   # This was mousePositionChanged (wrong)
        
        # Test that frame extractor has correct signals
        frame_extractor = viewer._frame_extractor
        assert hasattr(frame_extractor, 'settingsChanged')  # This was extractionRequested (wrong)
    
    def test_manager_api_contracts(self, qtbot):
        """Test that managers have the correct API contracts."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Test SettingsManager API (these methods were wrong)
        settings = viewer._settings_manager
        assert hasattr(settings, 'restore_window_geometry')  # Not get_window_geometry
        assert callable(settings.restore_window_geometry)
        
        # Test RecentFilesManager API (this method name was wrong)
        recent_files = viewer._recent_files
        assert hasattr(recent_files, 'add_file_to_recent')  # Not add_recent_file
        assert callable(recent_files.add_file_to_recent)
        
        # Test SpriteCanvas API (this method name was wrong)
        canvas = viewer._canvas
        assert hasattr(canvas, 'reset_view')  # Not reset_zoom
        assert callable(canvas.reset_view)
    
    def test_component_integration_real_calls(self, qtbot):
        """Test that components can actually call each other's methods."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Test real method calls that were failing
        try:
            # These should all work now
            viewer._canvas.reset_view()  # Was reset_zoom
            viewer._recent_files.add_file_to_recent('/test/file.png')  # Was add_recent_file
            viewer._settings_manager.restore_window_geometry(viewer)  # Was get_window_geometry
            
            is_playing = viewer._animation_controller.is_playing  # Was is_playing()
            assert isinstance(is_playing, bool)
            
            viewer._status_manager.show_message("Test")  # Was missing
            viewer._status_manager.update_mouse_position(0, 0)  # Was missing
            
        except AttributeError as e:
            pytest.fail(f"Component integration failed: {e}")
        except TypeError as e:
            pytest.fail(f"API contract violation: {e}")
    
    @pytest.mark.integration
    def test_sprite_viewer_full_initialization(self, qtbot):
        """Integration test: Full SpriteViewer initialization without mocking."""
        from sprite_viewer import SpriteViewer
        
        # Test COMPLETE initialization with NO mocking
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # If we reach this point, initialization succeeded
        assert viewer is not None
        
        # Test that all previously failing integration points now work
        assert viewer._status_manager is not None
        assert viewer._animation_controller.is_playing is not None  # Property access
        assert hasattr(viewer._canvas, 'mouseMoved')  # Correct signal name
        assert hasattr(viewer._frame_extractor, 'settingsChanged')  # Correct signal name
        assert hasattr(viewer._recent_files, 'add_file_to_recent')  # Correct method name
        assert hasattr(viewer._canvas, 'reset_view')  # Correct method name
        assert hasattr(viewer._status_manager, 'show_message')  # Previously missing
        assert hasattr(viewer._status_manager, 'update_mouse_position')  # Previously missing


if __name__ == '__main__':
    pytest.main([__file__, '-v'])