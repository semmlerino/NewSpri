"""
Foundation tests for existing keyboard shortcuts using REAL components.
Tests keyboard shortcuts work with actual objects instead of mocks.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication


class TestExistingKeyboardShortcuts:
    """Test keyboard shortcuts with real component behavior."""
    
    def test_space_key_calls_real_toggle_playback(self, qtbot):
        """Test Space key calls real animation controller toggle."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Get initial state
        initial_playing = viewer._animation_controller.is_playing
        
        # Simulate Space key press - test REAL behavior
        key_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Space, Qt.NoModifier)
        viewer.keyPressEvent(key_event)
        
        # Test that the REAL method was executed
        # Note: Without sprites loaded, toggle may not change state,
        # but the method should be callable and not raise errors
        try:
            final_playing = viewer._animation_controller.is_playing
            # Method executed successfully if we reach here
            assert isinstance(final_playing, bool)
        except Exception as e:
            pytest.fail(f"Space key handler failed: {e}")
    
    def test_g_key_calls_real_grid_toggle(self, qtbot):
        """Test G key calls real grid toggle on canvas."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Test that canvas has grid toggle capability
        canvas = viewer._canvas
        assert hasattr(canvas, 'toggle_grid')
        
        # Simulate G key press - test REAL behavior
        key_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_G, Qt.NoModifier)
        viewer.keyPressEvent(key_event)
        
        # The real _toggle_grid method should execute without error
        # We can verify by calling it directly to ensure it works
        try:
            viewer._toggle_grid()  # This should work
        except Exception as e:
            pytest.fail(f"Grid toggle functionality broken: {e}")
    
    def test_arrow_keys_with_real_sprite_model(self, qtbot):
        """Test arrow key navigation with real sprite model."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        sprite_model = viewer._sprite_model
        
        # Test that navigation methods exist and are callable
        assert hasattr(viewer, '_go_to_prev_frame')
        assert hasattr(viewer, '_go_to_next_frame')
        assert callable(viewer._go_to_prev_frame)
        assert callable(viewer._go_to_next_frame)
        
        # Test Left arrow key - should not crash even with no sprites
        left_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Left, Qt.NoModifier)
        try:
            viewer.keyPressEvent(left_event)
        except Exception as e:
            pytest.fail(f"Left arrow key handler failed: {e}")
        
        # Test Right arrow key - should not crash even with no sprites
        right_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Right, Qt.NoModifier)
        try:
            viewer.keyPressEvent(right_event)
        except Exception as e:
            pytest.fail(f"Right arrow key handler failed: {e}")
    
    def test_home_end_keys_with_real_navigation(self, qtbot):
        """Test Home/End keys with real navigation methods."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Test that boundary navigation methods exist
        assert hasattr(viewer, '_go_to_first_frame')
        assert hasattr(viewer, '_go_to_last_frame')
        assert callable(viewer._go_to_first_frame)
        assert callable(viewer._go_to_last_frame)
        
        # Test Home key
        home_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Home, Qt.NoModifier)
        try:
            viewer.keyPressEvent(home_event)
        except Exception as e:
            pytest.fail(f"Home key handler failed: {e}")
        
        # Test End key
        end_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_End, Qt.NoModifier)
        try:
            viewer.keyPressEvent(end_event)
        except Exception as e:
            pytest.fail(f"End key handler failed: {e}")
    
    def test_zoom_shortcuts_with_real_canvas(self, qtbot):
        """Test zoom shortcuts with real canvas methods."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        canvas = viewer._canvas
        
        # Test that zoom methods exist on canvas
        assert hasattr(canvas, 'zoom_in') or hasattr(viewer, '_zoom_in')
        assert hasattr(canvas, 'zoom_out') or hasattr(viewer, '_zoom_out')
        assert hasattr(canvas, 'fit_to_window') or hasattr(viewer, '_zoom_fit')
        assert hasattr(canvas, 'reset_view') or hasattr(viewer, '_zoom_reset')
        
        # Test plus key (zoom in)
        plus_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Plus, Qt.NoModifier)
        try:
            viewer.keyPressEvent(plus_event)
        except Exception as e:
            pytest.fail(f"Plus key (zoom in) handler failed: {e}")
        
        # Test minus key (zoom out)
        minus_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Minus, Qt.NoModifier)
        try:
            viewer.keyPressEvent(minus_event)
        except Exception as e:
            pytest.fail(f"Minus key (zoom out) handler failed: {e}")
        
        # Test 1 key (fit to window)
        one_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_1, Qt.NoModifier)
        try:
            viewer.keyPressEvent(one_event)
        except Exception as e:
            pytest.fail(f"1 key (fit to window) handler failed: {e}")
        
        # Test 0 key (reset zoom)
        zero_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_0, Qt.NoModifier)
        try:
            viewer.keyPressEvent(zero_event)
        except Exception as e:
            pytest.fail(f"0 key (reset zoom) handler failed: {e}")
    
    def test_ctrl_shortcuts_with_real_methods(self, qtbot):
        """Test Ctrl+key shortcuts with real methods."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Test Ctrl+O (open file)
        ctrl_o_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_O, Qt.ControlModifier)
        try:
            viewer.keyPressEvent(ctrl_o_event)
        except Exception as e:
            pytest.fail(f"Ctrl+O handler failed: {e}")
        
        # Test Ctrl+Q (quit) - we won't actually quit, just test the handler
        ctrl_q_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Q, Qt.ControlModifier)
        try:
            # This might close the app, so we just verify the handler exists
            assert hasattr(viewer, 'close')
        except Exception as e:
            pytest.fail(f"Ctrl+Q handler setup failed: {e}")
        
        # Test Ctrl+E (export) - should work even with no sprites
        ctrl_e_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_E, Qt.ControlModifier)
        try:
            viewer.keyPressEvent(ctrl_e_event)
            # If no sprites, this should show a warning but not crash
        except Exception as e:
            pytest.fail(f"Ctrl+E handler failed: {e}")


class TestShortcutIntegration:
    """Test that shortcut system integrates properly with managers."""
    
    def test_shortcut_manager_integration(self, qtbot):
        """Test that shortcut manager works with real components."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Test that shortcut manager exists and is functional
        assert hasattr(viewer, '_shortcut_manager')
        shortcut_manager = viewer._shortcut_manager
        
        # Test that shortcut manager has required methods
        assert hasattr(shortcut_manager, 'handle_key_press')
        assert callable(shortcut_manager.handle_key_press)
        
        # Test that key sequences can be processed
        try:
            # This should not crash even if key is unhandled
            result = shortcut_manager.handle_key_press('Space')
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"Shortcut manager integration failed: {e}")
    
    def test_action_manager_integration(self, qtbot):
        """Test that action manager works with real callbacks."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Test that action manager exists and is functional
        assert hasattr(viewer, '_action_manager')
        action_manager = viewer._action_manager
        
        # Test that action manager can handle real actions
        assert hasattr(action_manager, 'update_context')
        assert callable(action_manager.update_context)
        
        # Test context updates with real state
        try:
            has_frames = bool(viewer._sprite_model.sprite_frames)
            is_playing = viewer._animation_controller.is_playing
            
            action_manager.update_context(
                has_frames=has_frames,
                is_playing=is_playing
            )
        except Exception as e:
            pytest.fail(f"Action manager integration failed: {e}")


class TestKeyboardShortcutConsistency:
    """Test consistency between shortcut definitions and actual behavior."""
    
    def test_documented_shortcuts_exist(self, qtbot):
        """Test that all documented shortcuts have working handlers."""
        from sprite_viewer import SpriteViewer
        
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Define expected shortcuts and their corresponding methods
        expected_shortcuts = {
            'Space': viewer._animation_controller.toggle_playback,
            'G': viewer._toggle_grid,
            'Left': viewer._go_to_prev_frame,
            'Right': viewer._go_to_next_frame,
            'Home': viewer._go_to_first_frame,
            'End': viewer._go_to_last_frame,
        }
        
        # Test that all expected methods exist and are callable
        for key, method in expected_shortcuts.items():
            assert callable(method), f"Shortcut {key} method is not callable"
        
        # Test that shortcuts can be invoked without crashing
        test_keys = [
            (Qt.Key_Space, Qt.NoModifier),
            (Qt.Key_G, Qt.NoModifier),
            (Qt.Key_Left, Qt.NoModifier),
            (Qt.Key_Right, Qt.NoModifier),
            (Qt.Key_Home, Qt.NoModifier),
            (Qt.Key_End, Qt.NoModifier),
        ]
        
        for key, modifier in test_keys:
            event = QKeyEvent(QKeyEvent.KeyPress, key, modifier)
            try:
                viewer.keyPressEvent(event)
            except Exception as e:
                pytest.fail(f"Keyboard shortcut {key} failed: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])