"""
Unit tests for coordinator infrastructure.
Tests the base coordinator classes without requiring full application.
"""

import pytest
from coordinators import CoordinatorBase


class MockCoordinator(CoordinatorBase):
    """Mock coordinator for testing."""
    
    def initialize(self, dependencies):
        self.initialized_deps = dependencies
        self.cleanup_called = False
    
    def cleanup(self):
        self.cleanup_called = True


class TestCoordinatorBase:
    """Test CoordinatorBase functionality."""
    
    def test_coordinator_initialization(self):
        """Test basic coordinator initialization."""
        main_window = object()
        coordinator = MockCoordinator(main_window)
        
        assert coordinator.main_window == main_window
        assert not coordinator.is_initialized
        assert not coordinator._initialized
    
    def test_coordinator_initialize(self):
        """Test coordinator initialize method."""
        coordinator = MockCoordinator(None)
        deps = {"key": "value", "number": 42}
        
        coordinator.initialize(deps)
        
        assert coordinator.initialized_deps == deps
        assert not coordinator.is_initialized  # Not set by initialize itself
        
        # Simulate registry setting initialized
        coordinator._initialized = True
        assert coordinator.is_initialized
    
    def test_coordinator_cleanup(self):
        """Test coordinator cleanup method."""
        coordinator = MockCoordinator(None)
        coordinator.cleanup()
        
        assert coordinator.cleanup_called


class TestCoordinatorIntegration:
    """Test coordinator system integration with sprite viewer."""

    def test_sprite_viewer_has_coordinators(self):
        """Test that SpriteViewer includes coordinators."""
        from sprite_viewer import SpriteViewer

        # Verify the class references coordinator attributes
        init_code = SpriteViewer.__init__.__code__

        # Check that __init__ references coordinators
        assert '_animation_coordinator' in init_code.co_names or \
               'AnimationCoordinator' in init_code.co_names

    def test_coordinator_imports(self):
        """Test that coordinator imports work correctly."""
        from coordinators import CoordinatorBase
        from coordinators.base import CoordinatorBase as Base

        # Verify they're the same classes
        assert CoordinatorBase is Base