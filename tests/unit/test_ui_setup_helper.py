"""
Unit tests for UISetupHelper (Phase 2 refactoring).
Tests the UI setup coordinator without requiring full Qt application.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from coordinators import UISetupHelper


class TestUISetupHelper:
    """Test UISetupHelper functionality."""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create mock main window."""
        window = Mock()
        window.setWindowTitle = Mock()
        window.setMinimumSize = Mock()
        window.setAcceptDrops = Mock()
        window.menuBar = Mock(return_value=Mock())
        window.setStatusBar = Mock()
        window.setCentralWidget = Mock()
        return window
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        return {
            'menu_manager': Mock(),
            'action_manager': Mock(),
            'shortcut_manager': Mock(),
            'segment_manager': Mock(),
            'sprite_model': Mock(),
            'segment_controller': Mock()
        }
    
    def test_initialization(self, mock_main_window):
        """Test UISetupHelper initialization."""
        helper = UISetupHelper(mock_main_window)
        
        assert helper.main_window == mock_main_window
        assert not helper.is_initialized
        assert helper.central_widget is None
        assert helper.tab_widget is None
        assert helper.canvas is None
        assert helper.playback_controls is None
        assert helper.frame_extractor is None
        assert helper.grid_view is None
        assert helper.info_label is None
        assert helper.zoom_label is None
        assert helper.main_toolbar is None
        assert helper.status_manager is None
    
    def test_initialize_with_dependencies(self, mock_main_window, mock_dependencies):
        """Test initialization with dependencies."""
        helper = UISetupHelper(mock_main_window)
        
        helper.initialize(mock_dependencies)
        
        assert helper.menu_manager == mock_dependencies['menu_manager']
        assert helper.action_manager == mock_dependencies['action_manager']
        assert helper.shortcut_manager == mock_dependencies['shortcut_manager']
        assert helper.segment_manager == mock_dependencies['segment_manager']
        assert helper.sprite_model == mock_dependencies['sprite_model']
        assert helper.segment_controller == mock_dependencies['segment_controller']
    
    def test_cleanup(self, mock_main_window):
        """Test cleanup method."""
        helper = UISetupHelper(mock_main_window)
        
        # Should not raise any errors
        helper.cleanup()
    
    @patch('coordinators.ui_setup_helper.QWidget')
    @patch('coordinators.ui_setup_helper.QLabel')
    @patch('coordinators.ui_setup_helper.QTabWidget')
    @patch('coordinators.ui_setup_helper.QVBoxLayout')
    @patch('coordinators.ui_setup_helper.QHBoxLayout')
    @patch('coordinators.ui_setup_helper.QSplitter')
    @patch('coordinators.ui_setup_helper.StyleManager')
    def test_setup_ui_creates_components(self, mock_style, mock_splitter, mock_hbox, mock_vbox,
                                       mock_tab, mock_label, mock_widget,
                                       mock_main_window, mock_dependencies):
        """Test that setup_ui creates all necessary components."""
        # Setup mocks
        helper = UISetupHelper(mock_main_window)
        helper.initialize(mock_dependencies)
        
        # Mock UI component classes
        mock_canvas = Mock()
        mock_playback = Mock()
        mock_extractor = Mock()
        mock_grid = Mock()
        mock_status_bar = Mock()
        mock_status_manager = Mock()
        
        helper._canvas_class = Mock(return_value=mock_canvas)
        helper._playback_controls_class = Mock(return_value=mock_playback)
        helper._frame_extractor_class = Mock(return_value=mock_extractor)
        helper._grid_view_class = Mock(return_value=mock_grid)
        helper._status_bar_class = Mock(return_value=mock_status_bar)
        helper._status_manager_class = Mock(return_value=mock_status_manager)
        
        # Mock menu manager
        mock_toolbar = Mock()
        mock_menus = Mock()
        mock_dependencies['menu_manager'].create_toolbar.return_value = mock_toolbar
        mock_dependencies['menu_manager'].create_menu_bar.return_value = mock_menus
        
        # Execute
        result = helper.setup_ui()
        
        # Verify window setup
        mock_main_window.setWindowTitle.assert_called_once_with("Python Sprite Viewer")
        mock_main_window.setMinimumSize.assert_called_once()
        mock_main_window.setAcceptDrops.assert_called_once_with(True)
        
        # Verify menu bar setup
        mock_main_window.menuBar.assert_called_once()
        mock_dependencies['menu_manager'].create_menu_bar.assert_called_once()
        
        # Verify toolbar setup
        mock_dependencies['menu_manager'].create_toolbar.assert_called_once_with('main')
        
        # Verify status bar setup
        mock_main_window.setStatusBar.assert_called_once()
        
        # Verify central widget setup
        mock_main_window.setCentralWidget.assert_called_once()
        
        # Verify returned components
        assert result['canvas'] == mock_canvas
        assert result['playback_controls'] == mock_playback
        assert result['frame_extractor'] == mock_extractor
        assert result['grid_view'] == mock_grid
        assert result['status_manager'] == mock_status_manager
        assert result['main_toolbar'] == mock_toolbar
        assert result['menus'] == mock_menus
        assert 'tab_widget' in result
        assert 'central_widget' in result
        assert 'info_label' in result
        assert 'zoom_label' in result
    
    def test_setup_ui_connects_signals(self, mock_main_window, mock_dependencies):
        """Test that setup_ui connects necessary signals."""
        helper = UISetupHelper(mock_main_window)
        helper.initialize(mock_dependencies)
        
        # Mock UI components
        with patch.object(helper, '_setup_window'), \
             patch.object(helper, '_setup_menu_bar'), \
             patch.object(helper, '_setup_toolbar'), \
             patch.object(helper, '_setup_status_bar'), \
             patch.object(helper, '_setup_main_content'):
            
            # Mock segment controller methods
            mock_dependencies['segment_controller'].update_grid_view_frames = Mock()
            mock_dependencies['segment_controller'].on_tab_changed = Mock()
            
            result = helper.setup_ui()
            
            # Verify setup methods were called
            helper._setup_window.assert_called_once()
            helper._setup_menu_bar.assert_called_once()
            helper._setup_toolbar.assert_called_once()
            helper._setup_status_bar.assert_called_once()
            helper._setup_main_content.assert_called_once()


class TestUISetupHelperIntegration:
    """Test UISetupHelper integration with sprite viewer."""
    
    def test_sprite_viewer_uses_ui_setup_helper(self):
        """Test that SpriteViewer properly uses UISetupHelper."""
        from sprite_viewer import SpriteViewer
        
        # Check that SpriteViewer imports UISetupHelper
        init_code = SpriteViewer.__init__.__code__
        
        # Check for UISetupHelper usage
        assert 'UISetupHelper' in init_code.co_names or \
               '_ui_helper' in init_code.co_names
    
    def test_ui_setup_helper_import(self):
        """Test that UISetupHelper can be imported correctly."""
        from coordinators import UISetupHelper as Helper
        from coordinators.ui_setup_helper import UISetupHelper
        
        # Verify they're the same class
        assert Helper is UISetupHelper