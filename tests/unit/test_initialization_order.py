"""
Unit tests for proper object initialization order.
Tests that object attributes are created before they're accessed.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch


def test_sprite_viewer_initialization_order():
    """Test that SpriteViewer initializes attributes in correct order."""
    # Mock PySide6 modules to avoid import errors
    mock_modules = {
        'PySide6': MagicMock(),
        'PySide6.QtWidgets': MagicMock(),
        'PySide6.QtCore': MagicMock(),
        'PySide6.QtGui': MagicMock(),
    }
    
    # Create mock classes that track instantiation
    mock_qmainwindow = MagicMock()
    mock_qapplication = MagicMock()
    
    # Mock the Qt classes we need
    mock_modules['PySide6.QtWidgets'].QMainWindow = mock_qmainwindow
    mock_modules['PySide6.QtWidgets'].QApplication = mock_qapplication
    mock_modules['PySide6.QtWidgets'].QWidget = MagicMock()
    mock_modules['PySide6.QtWidgets'].QVBoxLayout = MagicMock()
    mock_modules['PySide6.QtWidgets'].QHBoxLayout = MagicMock()
    mock_modules['PySide6.QtWidgets'].QLabel = MagicMock()
    mock_modules['PySide6.QtWidgets'].QPushButton = MagicMock()
    mock_modules['PySide6.QtWidgets'].QFileDialog = MagicMock()
    mock_modules['PySide6.QtWidgets'].QGroupBox = MagicMock()
    mock_modules['PySide6.QtWidgets'].QColorDialog = MagicMock()
    mock_modules['PySide6.QtWidgets'].QComboBox = MagicMock()
    mock_modules['PySide6.QtWidgets'].QStatusBar = MagicMock()
    mock_modules['PySide6.QtWidgets'].QToolBar = MagicMock()
    mock_modules['PySide6.QtWidgets'].QMessageBox = MagicMock()
    mock_modules['PySide6.QtWidgets'].QScrollArea = MagicMock()
    mock_modules['PySide6.QtWidgets'].QSplitter = MagicMock()
    mock_modules['PySide6.QtWidgets'].QSizePolicy = MagicMock()
    mock_modules['PySide6.QtWidgets'].QMenu = MagicMock()
    
    mock_modules['PySide6.QtCore'].Qt = MagicMock()
    mock_modules['PySide6.QtCore'].QSettings = MagicMock()
    mock_modules['PySide6.QtCore'].QByteArray = MagicMock()
    mock_modules['PySide6.QtCore'].QTimer = MagicMock()
    mock_modules['PySide6.QtCore'].QObject = MagicMock()
    mock_modules['PySide6.QtCore'].Signal = MagicMock()
    mock_modules['PySide6.QtCore'].QSize = MagicMock()
    
    mock_modules['PySide6.QtGui'].QPixmap = MagicMock()
    mock_modules['PySide6.QtGui'].QAction = MagicMock()
    mock_modules['PySide6.QtGui'].QDragEnterEvent = MagicMock()
    mock_modules['PySide6.QtGui'].QDropEvent = MagicMock()
    mock_modules['PySide6.QtGui'].QKeySequence = MagicMock()
    mock_modules['PySide6.QtGui'].QColor = MagicMock()
    
    # Apply mocks
    for module_name, mock_module in mock_modules.items():
        sys.modules[module_name] = mock_module
    
    try:
        # Import the module after mocking
        from sprite_viewer import SpriteViewer
        
        # This should not raise an AttributeError about missing _status_manager
        # We'll catch any AttributeError that indicates improper initialization order
        with patch.object(SpriteViewer, '_setup_ui'), \
             patch.object(SpriteViewer, '_setup_toolbar'), \
             patch.object(SpriteViewer, '_setup_menu'), \
             patch.object(SpriteViewer, '_connect_signals'), \
             patch.object(SpriteViewer, '_load_test_sprites'):
            
            viewer = SpriteViewer()
            
            # Verify that important attributes exist
            assert hasattr(viewer, '_settings')
            assert hasattr(viewer, '_recent_files')
            assert hasattr(viewer, '_status_bar')
            assert hasattr(viewer, '_status_manager')
            assert hasattr(viewer, '_sprite_model')
            assert hasattr(viewer, '_animation_controller')
            
    except AttributeError as e:
        if '_status_manager' in str(e):
            pytest.fail(f"Initialization order error: {e}")
        else:
            # Re-raise other AttributeErrors
            raise
    
    finally:
        # Clean up mocks
        for module_name in mock_modules.keys():
            if module_name in sys.modules:
                del sys.modules[module_name]


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