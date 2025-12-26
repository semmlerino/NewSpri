"""
UI tests for menu actions.
Tests that menu actions trigger their corresponding methods.
"""

import pytest

from sprite_viewer import SpriteViewer


class TestMenuStructureSmoke:
    """Smoke test for menu structure."""

    def test_expected_menus_exist(self, qtbot):
        """Smoke test: all expected menus exist."""
        from sprite_viewer import SpriteViewer

        viewer = SpriteViewer()
        qtbot.addWidget(viewer)

        menu_names = [a.text() for a in viewer.menuBar().actions()]

        assert "File" in menu_names
        assert "View" in menu_names
        assert "Help" in menu_names


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
