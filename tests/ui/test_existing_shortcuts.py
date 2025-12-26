"""
Smoke test for keyboard shortcuts - verifies core shortcuts work without crashing.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent


class TestKeyboardShortcutsSmoke:
    """Smoke test that core keyboard shortcuts don't crash."""

    def test_core_shortcuts_execute_without_crash(self, qtbot):
        """Verify all core keyboard shortcuts can be invoked without error."""
        from sprite_viewer import SpriteViewer

        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        # Core shortcuts to test
        test_keys = [
            (Qt.Key_Space, Qt.NoModifier, "toggle playback"),
            (Qt.Key_G, Qt.NoModifier, "toggle grid"),
            (Qt.Key_Left, Qt.NoModifier, "prev frame"),
            (Qt.Key_Right, Qt.NoModifier, "next frame"),
            (Qt.Key_Home, Qt.NoModifier, "first frame"),
            (Qt.Key_End, Qt.NoModifier, "last frame"),
            (Qt.Key_Plus, Qt.NoModifier, "zoom in"),
            (Qt.Key_Minus, Qt.NoModifier, "zoom out"),
            (Qt.Key_0, Qt.NoModifier, "reset zoom"),
            (Qt.Key_1, Qt.NoModifier, "fit to window"),
        ]

        for key, modifier, description in test_keys:
            event = QKeyEvent(QKeyEvent.KeyPress, key, modifier)
            try:
                viewer.keyPressEvent(event)
            except Exception as e:
                pytest.fail(f"Shortcut '{description}' ({key}) crashed: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
