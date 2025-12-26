"""
Unit tests for controller initialization contracts.

Tests that controllers properly track initialization state via is_ready property,
ensuring fail-fast behavior when controllers are used before initialization.
"""

import pytest
from unittest.mock import Mock, MagicMock

from core.animation_segment_controller import AnimationSegmentController
from core.animation_controller import AnimationController
from core.auto_detection_controller import AutoDetectionController
from export.export_coordinator import ExportCoordinator
from managers import AnimationSegmentManager


class TestAnimationSegmentControllerInitialization:
    """Test AnimationSegmentController initialization contract."""

    def test_is_ready_false_before_setters(self):
        """Controller should report not ready before any setters called."""
        controller = AnimationSegmentController()
        assert not controller.is_ready

    def test_is_ready_false_with_partial_setters(self):
        """Controller should report not ready with only some setters called."""
        controller = AnimationSegmentController()
        controller.set_segment_manager(Mock())
        controller.set_grid_view(Mock())
        # Missing: set_sprite_model, set_tab_widget, set_segment_preview
        assert not controller.is_ready

    def test_is_ready_true_after_all_setters(self):
        """Controller should report ready after all setters called."""
        controller = AnimationSegmentController()
        controller.set_segment_manager(Mock())
        controller.set_grid_view(Mock())
        controller.set_sprite_model(Mock())
        controller.set_tab_widget(Mock())
        controller.set_segment_preview(Mock())
        assert controller.is_ready

    def test_required_deps_lists_all_dependencies(self):
        """_REQUIRED_DEPS should list all 5 required dependencies."""
        assert len(AnimationSegmentController._REQUIRED_DEPS) == 5
        expected = {'_segment_manager', '_grid_view', '_sprite_model',
                    '_tab_widget', '_segment_preview'}
        assert set(AnimationSegmentController._REQUIRED_DEPS) == expected


class TestAnimationControllerInitialization:
    """Test AnimationController initialization contract."""

    def test_is_ready_false_before_initialize(self):
        """Controller should report not ready before initialize() called."""
        controller = AnimationController()
        assert not controller.is_ready

    def test_is_ready_reflects_initialized_flag(self):
        """is_ready property should reflect _initialized flag state."""
        controller = AnimationController()

        # Initially False
        assert controller._initialized is False
        assert controller.is_ready is False

        # Manually set flag (simulates successful initialize)
        controller._initialized = True
        assert controller.is_ready is True

        # Reset
        controller._initialized = False
        assert controller.is_ready is False


class TestAutoDetectionControllerInitialization:
    """Test AutoDetectionController initialization contract."""

    def test_is_ready_false_before_initialize(self):
        """Controller should report not ready before initialize() called."""
        controller = AutoDetectionController()
        assert not controller.is_ready

    def test_is_ready_true_after_initialize(self):
        """Controller should report ready after initialize() called."""
        controller = AutoDetectionController()
        mock_model = Mock()
        mock_extractor = Mock()

        controller.initialize(mock_model, mock_extractor)

        assert controller.is_ready


class TestExportCoordinatorInitialization:
    """Test ExportCoordinator initialization contract."""

    def test_is_ready_false_before_initialize(self):
        """Coordinator should report not ready before initialize() called."""
        mock_window = Mock()
        coordinator = ExportCoordinator(mock_window)
        assert not coordinator.is_ready

    def test_is_ready_true_after_initialize(self):
        """Coordinator should report ready after initialize() called."""
        mock_window = Mock()
        coordinator = ExportCoordinator(mock_window)

        dependencies = {
            'sprite_model': Mock(),
            'segment_manager': Mock(),
        }
        coordinator.initialize(dependencies)

        assert coordinator.is_ready
