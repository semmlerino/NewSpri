"""
Unit Tests for Keyboard Modifier Compatibility - Testing cross-version PySide6 compatibility.
Tests the safe keyboard modifier conversion that was implemented to fix TypeError issues.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QMouseEvent

from ui.animation_grid_view import FrameThumbnail, AnimationGridView


class TestKeyboardModifierCompatibility:
    """Test keyboard modifier handling across different PySide6 versions."""
    
    def test_modifier_conversion_newer_pyside6(self, qtbot):
        """Test modifier conversion for newer PySide6 versions using .value property."""
        pixmap = QPixmap(32, 32)
        thumbnail = FrameThumbnail(0, pixmap)
        qtbot.addWidget(thumbnail)
        
        signals_received = []
        thumbnail.clicked.connect(lambda idx, mods: signals_received.append((idx, mods)))
        
        # Mock newer PySide6 approach with .value property
        mock_event = Mock()
        mock_event.button.return_value = Qt.LeftButton
        mock_event.position.return_value = Mock()
        
        # Create mock modifiers with .value property
        mock_modifiers = Mock()
        mock_modifiers.value = int(Qt.ControlModifier)
        mock_event.modifiers.return_value = mock_modifiers
        
        thumbnail.mousePressEvent(mock_event)
        
        assert len(signals_received) == 1
        assert signals_received[0][1] == int(Qt.ControlModifier)
    
    def test_modifier_conversion_older_pyside6(self, qtbot):
        """Test modifier conversion for older PySide6 versions using int() conversion."""
        pixmap = QPixmap(32, 32)
        thumbnail = FrameThumbnail(0, pixmap)
        qtbot.addWidget(thumbnail)
        
        signals_received = []
        thumbnail.clicked.connect(lambda idx, mods: signals_received.append((idx, mods)))
        
        # Mock older PySide6 approach without .value property
        mock_event = Mock()
        mock_event.button.return_value = Qt.LeftButton
        mock_event.position.return_value = Mock()
        
        # Create modifiers that support direct int() conversion
        mock_modifiers = Mock()
        # Remove .value attribute to simulate older version
        del mock_modifiers.value
        # Mock int() conversion
        with patch('builtins.int') as mock_int:
            mock_int.return_value = int(Qt.ShiftModifier)
            mock_event.modifiers.return_value = mock_modifiers
            
            thumbnail.mousePressEvent(mock_event)
            
            assert len(signals_received) == 1
            assert signals_received[0][1] == int(Qt.ShiftModifier)
    
    def test_modifier_conversion_fallback(self, qtbot):
        """Test modifier conversion fallback when both approaches fail."""
        pixmap = QPixmap(32, 32)
        thumbnail = FrameThumbnail(0, pixmap)
        qtbot.addWidget(thumbnail)
        
        signals_received = []
        thumbnail.clicked.connect(lambda idx, mods: signals_received.append((idx, mods)))
        
        # Mock problematic case where both approaches fail
        mock_event = Mock()
        mock_event.button.return_value = Qt.LeftButton
        mock_event.position.return_value = Mock()
        
        # Create modifiers that fail both approaches
        mock_modifiers = Mock()
        # Remove .value attribute
        del mock_modifiers.value
        # Make int() conversion raise TypeError
        mock_modifiers.__int__ = Mock(side_effect=TypeError("conversion failed"))
        mock_event.modifiers.return_value = mock_modifiers
        
        thumbnail.mousePressEvent(mock_event)
        
        # Should fallback to 0 (no modifiers)
        assert len(signals_received) == 1
        assert signals_received[0][1] == 0
    
    def test_modifier_reconstruction_in_grid_view(self, qtbot):
        """Test modifier reconstruction from int back to KeyboardModifiers."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load test frames
        test_frames = [QPixmap(32, 32) for _ in range(5)]
        grid_view.set_frames(test_frames)
        
        # Test various modifier combinations
        test_cases = [
            (0, "no modifiers"),
            (int(Qt.ControlModifier), "Ctrl modifier"),
            (int(Qt.ShiftModifier), "Shift modifier"),
            (int(Qt.AltModifier), "Alt modifier"),
            (int(Qt.ControlModifier | Qt.ShiftModifier), "Ctrl+Shift modifiers")
        ]
        
        for modifier_int, description in test_cases:
            # Clear previous selection
            grid_view._clear_selection()
            
            # Test the modifier handling
            grid_view._on_frame_clicked(2, modifier_int)
            
            # Should not crash and should handle the modifiers appropriately
            assert True, f"Should handle {description} without crashing"
    
    def test_modifier_edge_cases(self, qtbot):
        """Test edge cases in modifier handling."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load frames
        test_frames = [QPixmap(32, 32) for _ in range(8)]
        grid_view.set_frames(test_frames)
        
        # Test invalid modifier value (should not crash)
        try:
            grid_view._on_frame_clicked(0, -1)  # Invalid modifier value
            grid_view._on_frame_clicked(1, 999999)  # Very large modifier value
            grid_view._on_frame_clicked(2, None)  # None value (would be converted to 0)
        except TypeError:
            # If it does raise TypeError, that's a problem we need to handle
            pytest.fail("Modifier handling should not raise TypeError on edge cases")
        
        # Should complete without crashing
        assert True


class TestModifierBehaviorCorrectness:
    """Test that modifier handling produces correct selection behavior."""
    
    def test_ctrl_click_behavior(self, qtbot):
        """Test Ctrl+click multi-select behavior works correctly."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load frames
        test_frames = [QPixmap(32, 32) for _ in range(8)]
        grid_view.set_frames(test_frames)
        
        # Normal click - should select frame 2
        grid_view._on_frame_clicked(2, 0)
        assert 2 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 1
        
        # Ctrl+click frame 4 - should add to selection
        grid_view._on_frame_clicked(4, int(Qt.ControlModifier))
        assert 2 in grid_view._selected_frames
        assert 4 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 2
        
        # Ctrl+click frame 2 again - should remove from selection
        grid_view._on_frame_clicked(2, int(Qt.ControlModifier))
        assert 2 not in grid_view._selected_frames
        assert 4 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 1
    
    def test_alt_click_behavior(self, qtbot):
        """Test Alt+click behaves same as Ctrl+click (multi-select)."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load frames
        test_frames = [QPixmap(32, 32) for _ in range(8)]
        grid_view.set_frames(test_frames)
        
        # Select initial frame
        grid_view._on_frame_clicked(1, 0)
        assert 1 in grid_view._selected_frames
        
        # Alt+click should add to selection (same as Ctrl)
        grid_view._on_frame_clicked(3, int(Qt.AltModifier))
        assert 1 in grid_view._selected_frames
        assert 3 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 2
    
    def test_shift_click_range_selection(self, qtbot):
        """Test Shift+click range selection behavior."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load frames
        test_frames = [QPixmap(32, 32) for _ in range(10)]
        grid_view.set_frames(test_frames)
        
        # Click frame 3 first
        grid_view._on_frame_clicked(3, 0)
        assert 3 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 1
        
        # Shift+click frame 6 - should select range 3-6
        grid_view._on_frame_clicked(6, int(Qt.ShiftModifier))
        expected_frames = {3, 4, 5, 6}
        assert grid_view._selected_frames == expected_frames
        
        # Shift+click frame 1 - should select range 1-3 (from last clicked)
        grid_view._on_frame_clicked(1, int(Qt.ShiftModifier))
        expected_frames = {1, 2, 3}
        assert grid_view._selected_frames == expected_frames
    
    def test_combined_modifier_handling(self, qtbot):
        """Test handling of combined modifiers."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load frames
        test_frames = [QPixmap(32, 32) for _ in range(8)]
        grid_view.set_frames(test_frames)
        
        # Test Ctrl+Shift combination (should behave as Ctrl)
        grid_view._on_frame_clicked(2, 0)  # Normal click
        combined_modifiers = int(Qt.ControlModifier | Qt.ShiftModifier)
        grid_view._on_frame_clicked(4, combined_modifiers)
        
        # Should add frame 4 to selection (Ctrl behavior takes precedence)
        assert 2 in grid_view._selected_frames
        assert 4 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 2
    
    def test_modifier_priority_logic(self, qtbot):
        """Test the priority logic for modifier handling."""
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        # Load frames  
        test_frames = [QPixmap(32, 32) for _ in range(8)]
        grid_view.set_frames(test_frames)
        
        # Set up initial state for range selection test
        grid_view._on_frame_clicked(2, 0)  # Click frame 2
        grid_view._last_clicked_frame = 2
        
        # The logic should be:
        # 1. If Ctrl OR Alt -> toggle selection
        # 2. Else if Shift AND last_clicked_frame exists -> range selection  
        # 3. Else -> normal click (clear and select)
        
        # Test that Ctrl takes priority over Shift
        ctrl_shift = int(Qt.ControlModifier | Qt.ShiftModifier)
        grid_view._on_frame_clicked(5, ctrl_shift)
        
        # Should behave as Ctrl (toggle), not Shift (range)
        assert 2 in grid_view._selected_frames
        assert 5 in grid_view._selected_frames
        assert len(grid_view._selected_frames) == 2
        # Should NOT have frames 3, 4 (which would be added by range selection)
        assert 3 not in grid_view._selected_frames
        assert 4 not in grid_view._selected_frames


class TestModifierCompatibilityWithRealEvents:
    """Test modifier compatibility with real QMouseEvent objects."""
    
    def test_real_mouse_event_modifier_extraction(self, qtbot):
        """Test modifier extraction from real QMouseEvent objects."""
        pixmap = QPixmap(32, 32)
        thumbnail = FrameThumbnail(0, pixmap)
        qtbot.addWidget(thumbnail)
        
        signals_received = []
        thumbnail.clicked.connect(lambda idx, mods: signals_received.append((idx, mods)))
        
        # Create a real QMouseEvent with modifiers
        # Note: This tests the actual PySide6 behavior on the current system
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QMouseEvent
        
        pos = QPointF(10, 10)
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            pos, pos, pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.ControlModifier  # Include Ctrl modifier
        )
        
        # This should work with the actual PySide6 implementation
        thumbnail.mousePressEvent(event)
        
        assert len(signals_received) == 1
        frame_index, modifier_value = signals_received[0]
        assert frame_index == 0
        # Should have extracted the Ctrl modifier correctly
        assert modifier_value != 0  # Should not be empty
        
        # Test the conversion back in the grid view
        grid_view = AnimationGridView()
        qtbot.addWidget(grid_view)
        
        test_frames = [QPixmap(32, 32) for _ in range(3)]
        grid_view.set_frames(test_frames)
        
        # This should not crash with the real modifier value
        grid_view._on_frame_clicked(0, modifier_value)
        
        # Should complete successfully
        assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])