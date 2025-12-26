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
