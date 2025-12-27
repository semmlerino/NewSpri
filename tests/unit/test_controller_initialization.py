"""
Unit tests for controller initialization contracts.

Tests that controllers are properly initialized via constructor dependency injection.
All dependencies must be provided at construction time.
"""

import pytest
from unittest.mock import Mock, MagicMock

from core.animation_segment_controller import AnimationSegmentController
from core.animation_controller import AnimationController
from core.auto_detection_controller import AutoDetectionController
from managers import AnimationSegmentManager


class TestAnimationSegmentControllerInitialization:
    """Test AnimationSegmentController initialization contract (constructor DI)."""

    def test_constructor_requires_all_dependencies(self):
        """Controller constructor requires all dependencies."""
        # Should work with all required arguments
        controller = AnimationSegmentController(
            segment_manager=Mock(),
            grid_view=Mock(),
            sprite_model=Mock(),
            tab_widget=Mock(),
            segment_preview=Mock(),
        )
        assert controller is not None
        assert controller._segment_manager is not None
        assert controller._grid_view is not None

    def test_constructor_accepts_none_for_optional_widgets(self):
        """Controller can accept None for widgets used only in some operations."""
        controller = AnimationSegmentController(
            segment_manager=Mock(),
            grid_view=Mock(),
            sprite_model=Mock(),
            tab_widget=None,  # Some operations don't need this
            segment_preview=None,  # Some operations don't need this
        )
        assert controller is not None


class TestAnimationControllerInitialization:
    """Test AnimationController initialization contract (constructor DI)."""

    def test_constructor_requires_dependencies(self):
        """Controller constructor requires sprite_model and sprite_viewer."""
        mock_model = Mock()
        mock_model.fps = 10
        mock_model.loop_enabled = True
        mock_model.dataLoaded = Mock()
        mock_model.extractionCompleted = Mock()
        mock_model.frameChanged = Mock()
        mock_model.errorOccurred = Mock()

        mock_viewer = Mock()
        mock_viewer.aboutToClose = Mock()

        controller = AnimationController(
            sprite_model=mock_model,
            sprite_viewer=mock_viewer,
        )

        assert controller is not None
        assert controller._sprite_model is mock_model
        assert controller._sprite_viewer is mock_viewer
        assert controller._is_active is True

    def test_controller_connects_model_signals_at_construction(self):
        """Controller connects to model signals during construction."""
        mock_model = Mock()
        mock_model.fps = 10
        mock_model.loop_enabled = True
        mock_model.dataLoaded = Mock()
        mock_model.extractionCompleted = Mock()
        mock_model.frameChanged = Mock()
        mock_model.errorOccurred = Mock()

        mock_viewer = Mock()
        mock_viewer.aboutToClose = Mock()

        controller = AnimationController(
            sprite_model=mock_model,
            sprite_viewer=mock_viewer,
        )

        # Verify model signals were connected
        mock_model.dataLoaded.connect.assert_called()
        mock_model.extractionCompleted.connect.assert_called()
        mock_model.frameChanged.connect.assert_called()
        mock_model.errorOccurred.connect.assert_called()


class TestAutoDetectionControllerInitialization:
    """Test AutoDetectionController initialization contract (constructor DI)."""

    def test_constructor_requires_dependencies(self):
        """Controller constructor requires sprite_model and frame_extractor."""
        mock_model = Mock()
        mock_extractor = Mock()

        controller = AutoDetectionController(
            sprite_model=mock_model,
            frame_extractor=mock_extractor,
        )

        assert controller is not None
        assert controller._sprite_model is mock_model
        assert controller._frame_extractor is mock_extractor

    def test_controller_stores_dependencies(self):
        """Controller properly stores dependencies at construction."""
        mock_model = Mock()
        mock_extractor = Mock()

        controller = AutoDetectionController(
            sprite_model=mock_model,
            frame_extractor=mock_extractor,
        )

        # Dependencies should be accessible via private attributes
        assert controller._sprite_model is mock_model
        assert controller._frame_extractor is mock_extractor
