"""
Unit tests for ExportCoordinator (Phase 4 refactoring).
Tests the export coordinator that handles export dialog and operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from export import ExportCoordinator


class TestExportCoordinator:
    """Test ExportCoordinator functionality."""
    
    @pytest.fixture
    def mock_main_window(self):
        """Create mock main window."""
        return Mock()
    
    @pytest.fixture
    def mock_sprite_model(self):
        """Create mock sprite model."""
        model = Mock()
        model.sprite_frames = [Mock() for _ in range(5)]  # 5 mock frames
        model.current_frame = 2
        return model
    
    @pytest.fixture
    def mock_segment_manager(self):
        """Create mock segment manager."""
        return Mock()

    def test_initialize_with_dependencies(self, mock_main_window, mock_sprite_model,
                                          mock_segment_manager):
        """Test initialization with dependencies."""
        coordinator = ExportCoordinator(mock_main_window)

        dependencies = {
            'sprite_model': mock_sprite_model,
            'segment_manager': mock_segment_manager
        }

        coordinator.initialize(dependencies)

        assert coordinator.sprite_model == mock_sprite_model
        assert coordinator.segment_manager == mock_segment_manager
        # Note: _initialized is a private attribute, not a public property
    
    def test_cleanup(self, mock_main_window):
        """Test cleanup method."""
        coordinator = ExportCoordinator(mock_main_window)
        
        # Should not raise any errors
        coordinator.cleanup()
    
    @patch('export.export_coordinator.ExportDialog')
    @patch('export.export_coordinator.QMessageBox')
    def test_export_frames(self, mock_messagebox, mock_dialog_class, mock_main_window,
                          mock_sprite_model, mock_segment_manager):
        """Test export_frames method."""
        coordinator = ExportCoordinator(mock_main_window)
        coordinator.sprite_model = mock_sprite_model
        coordinator.segment_manager = mock_segment_manager
        
        # Create mock dialog instance
        mock_dialog = Mock()
        mock_dialog.set_sprites = Mock()
        mock_dialog.exportRequested = MagicMock()  # Signal mock
        mock_dialog.exec = Mock()
        mock_dialog_class.return_value = mock_dialog
        
        # Call export_frames
        coordinator.export_frames()
        
        # Verify dialog creation
        mock_dialog_class.assert_called_once_with(
            mock_main_window,
            frame_count=5,
            current_frame=2,
            segment_manager=mock_segment_manager
        )
        
        # Verify sprites were set
        mock_dialog.set_sprites.assert_called_once_with(mock_sprite_model.sprite_frames)
        
        # Verify signal connection
        mock_dialog.exportRequested.connect.assert_called_once()
        
        # Verify dialog was shown
        mock_dialog.exec.assert_called_once()
        
        # Verify no warning was shown
        mock_messagebox.warning.assert_not_called()
    
    @patch('export.export_coordinator.QMessageBox')
    def test_export_frames_no_frames(self, mock_messagebox, mock_main_window):
        """Test export_frames when no frames are available."""
        coordinator = ExportCoordinator(mock_main_window)
        
        # Set up sprite model with no frames
        mock_sprite_model = Mock()
        mock_sprite_model.sprite_frames = []
        coordinator.sprite_model = mock_sprite_model
        
        # Call export_frames
        coordinator.export_frames()
        
        # Verify warning was shown
        mock_messagebox.warning.assert_called_once_with(
            mock_main_window,
            "No Frames",
            "No frames to export."
        )
    
    @patch('export.export_coordinator.ExportDialog')
    def test_export_current_frame(self, mock_dialog_class, mock_main_window,
                                 mock_sprite_model, mock_segment_manager):
        """Test export_current_frame method."""
        coordinator = ExportCoordinator(mock_main_window)
        coordinator.sprite_model = mock_sprite_model
        coordinator.segment_manager = mock_segment_manager

        # Create mock dialog instance
        mock_dialog = Mock()
        mock_dialog.set_sprites = Mock()
        mock_dialog.exportRequested = MagicMock()  # Signal mock
        mock_dialog.exec = Mock()
        mock_dialog_class.return_value = mock_dialog

        # Call export_current_frame
        coordinator.export_current_frame()

        # Verify dialog creation (same as export_frames)
        mock_dialog_class.assert_called_once_with(
            mock_main_window,
            frame_count=5,
            current_frame=2,
            segment_manager=mock_segment_manager
        )

        # Verify dialog was configured and shown
        mock_dialog.set_sprites.assert_called_once_with(mock_sprite_model.sprite_frames)
        mock_dialog.exec.assert_called_once()

    def test_handle_export_request(self, mock_main_window, mock_sprite_model,
                                  mock_segment_manager):
        """Test _handle_export_request method with valid settings."""
        coordinator = ExportCoordinator(mock_main_window)
        coordinator.sprite_model = mock_sprite_model
        coordinator.segment_manager = mock_segment_manager

        # Mock the exporter to prevent actual export
        coordinator._exporter = Mock()
        coordinator._exporter.export_frames = Mock(return_value=True)

        # Test export settings with all required keys
        settings = {
            'output_dir': '/tmp/test',
            'base_name': 'test_sprite',
            'format': 'png',
            'mode': 'individual',
            'scale_factor': 1.0
        }

        # Call handler
        coordinator._handle_export_request(settings)

        # Verify exporter was called
        coordinator._exporter.export_frames.assert_called_once()
    
    def test_validate_export_with_frames(self, mock_main_window, mock_sprite_model):
        """Test _validate_export returns True when frames exist."""
        coordinator = ExportCoordinator(mock_main_window)
        coordinator.sprite_model = mock_sprite_model
        
        assert coordinator._validate_export() is True
    
    def test_validate_export_no_model(self, mock_main_window):
        """Test _validate_export returns False when no sprite model."""
        coordinator = ExportCoordinator(mock_main_window)

        with patch('export.export_coordinator.QMessageBox') as mock_messagebox:
            assert coordinator._validate_export() is False
            mock_messagebox.warning.assert_called_once()
    
    def test_validate_export_no_frames(self, mock_main_window):
        """Test _validate_export returns False when no frames."""
        coordinator = ExportCoordinator(mock_main_window)

        # Set up sprite model with no frames
        mock_sprite_model = Mock()
        mock_sprite_model.sprite_frames = []
        coordinator.sprite_model = mock_sprite_model

        with patch('export.export_coordinator.QMessageBox') as mock_messagebox:
            assert coordinator._validate_export() is False
            mock_messagebox.warning.assert_called_once()
    
    def test_has_frames(self, mock_main_window, mock_sprite_model):
        """Test has_frames method."""
        coordinator = ExportCoordinator(mock_main_window)
        
        # No sprite model
        assert coordinator.has_frames() is False
        
        # With sprite model and frames
        coordinator.sprite_model = mock_sprite_model
        assert coordinator.has_frames() is True
        
        # With sprite model but no frames
        mock_sprite_model.sprite_frames = []
        assert coordinator.has_frames() is False
    
    def test_get_frame_count(self, mock_main_window, mock_sprite_model):
        """Test get_frame_count method."""
        coordinator = ExportCoordinator(mock_main_window)
        
        # No sprite model
        assert coordinator.get_frame_count() == 0
        
        # With sprite model and frames
        coordinator.sprite_model = mock_sprite_model
        assert coordinator.get_frame_count() == 5
        
        # With sprite model but no frames
        mock_sprite_model.sprite_frames = []
        assert coordinator.get_frame_count() == 0
    
    def test_get_current_frame_index(self, mock_main_window, mock_sprite_model):
        """Test get_current_frame_index method."""
        coordinator = ExportCoordinator(mock_main_window)
        
        # No sprite model
        assert coordinator.get_current_frame_index() == 0
        
        # With sprite model
        coordinator.sprite_model = mock_sprite_model
        assert coordinator.get_current_frame_index() == 2


class TestExportCoordinatorIntegration:
    """Test ExportCoordinator integration with sprite viewer."""
    
    def test_sprite_viewer_uses_export_coordinator(self):
        """Test that SpriteViewer properly uses ExportCoordinator."""
        from sprite_viewer import SpriteViewer
        
        # Check that SpriteViewer imports ExportCoordinator
        init_code = SpriteViewer.__init__.__code__
        
        # Check for ExportCoordinator usage
        assert 'ExportCoordinator' in init_code.co_names or \
               '_export_coordinator' in init_code.co_names
    
    def test_export_coordinator_import(self):
        """Test that ExportCoordinator can be imported correctly."""
        from export import ExportCoordinator as Coordinator
        from export.export_coordinator import ExportCoordinator

        # Verify they're the same class
        assert Coordinator is ExportCoordinator
    
    def test_export_methods_removed_from_sprite_viewer(self):
        """Test that export methods have been removed from SpriteViewer."""
        from sprite_viewer import SpriteViewer
        
        # These methods should no longer exist in SpriteViewer
        assert not hasattr(SpriteViewer, '_export_frames')
        assert not hasattr(SpriteViewer, '_export_current_frame')
        assert not hasattr(SpriteViewer, '_handle_unified_export_request')