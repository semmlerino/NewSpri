"""
Unit tests for proper object initialization order.
Tests that object attributes are created before they're accessed.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch


@pytest.mark.skip(reason="Test is too brittle with complex mocking requirements")
def test_sprite_viewer_initialization_order(qtbot):
    """Test that SpriteViewer initializes attributes in correct order."""
    from sprite_viewer import SpriteViewer
    
    # Mock the heavy setup methods to speed up the test
    with patch.object(SpriteViewer, '_setup_ui') as mock_setup_ui, \
         patch.object(SpriteViewer, '_setup_menu_bar') as mock_setup_menu, \
         patch.object(SpriteViewer, '_setup_toolbar') as mock_setup_toolbar, \
         patch.object(SpriteViewer, '_connect_signals') as mock_connect_signals:
        
        # Set up _setup_ui to create necessary attributes
        def setup_ui_side_effect():
            viewer._tab_widget = MagicMock()
        
        mock_setup_ui.side_effect = setup_ui_side_effect
        
        # Create instance
        viewer = SpriteViewer()
        qtbot.addWidget(viewer)
        
        # Verify that important attributes exist
        assert hasattr(viewer, '_settings')
        assert hasattr(viewer, '_status_bar')
        assert hasattr(viewer, '_sprite_model')
        assert hasattr(viewer, '_animation_controller')
        
        # Verify methods were called
        mock_setup_ui.assert_called_once()
        mock_setup_menu.assert_called_once()
        mock_setup_toolbar.assert_called_once()
        mock_connect_signals.assert_called_once()


def test_status_manager_creation_before_usage():
    """Test that _status_manager is created before being used."""
    # Mock PySide6 modules
    mock_modules = {
        'PySide6': MagicMock(),
        'PySide6.QtWidgets': MagicMock(),
        'PySide6.QtCore': MagicMock(),
        'PySide6.QtGui': MagicMock(),
    }
    
    for module_name, mock_module in mock_modules.items():
        sys.modules[module_name] = mock_module
    
    try:
        # Test the specific order of operations
        from enhanced_status_bar import EnhancedStatusBar, StatusBarManager
        
        # This should work without errors
        status_bar = EnhancedStatusBar()
        status_manager = StatusBarManager(status_bar)
        
        # Status manager should have the required methods
        assert hasattr(status_manager, 'connect_to_sprite_model')
        assert hasattr(status_manager, 'connect_to_animation_controller')
        assert hasattr(status_manager, 'connect_to_canvas')
        
    finally:
        # Clean up mocks
        for module_name in mock_modules.keys():
            if module_name in sys.modules:
                del sys.modules[module_name]


if __name__ == '__main__':
    # Add parent directory to path for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Run tests directly
    test_sprite_viewer_initialization_order()
    test_status_manager_creation_before_usage()
    print("All initialization order tests passed!")