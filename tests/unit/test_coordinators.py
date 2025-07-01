"""
Unit tests for coordinator infrastructure (Phase 1 refactoring).
Tests the base coordinator classes and registry without requiring full application.
"""

import pytest
from coordinators import CoordinatorBase, CoordinatorRegistry


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


class TestCoordinatorRegistry:
    """Test CoordinatorRegistry functionality."""
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = CoordinatorRegistry()
        
        assert registry._coordinators == {}
        assert registry.list_coordinators() == []
    
    def test_registry_register_and_get(self):
        """Test registering and retrieving coordinators."""
        registry = CoordinatorRegistry()
        coord1 = MockCoordinator(None)
        coord2 = MockCoordinator(None)
        
        registry.register("test1", coord1)
        registry.register("test2", coord2)
        
        assert registry.get("test1") == coord1
        assert registry.get("test2") == coord2
        assert registry.get("nonexistent") is None
    
    def test_registry_register_replacement(self):
        """Test replacing an existing coordinator."""
        registry = CoordinatorRegistry()
        coord1 = MockCoordinator(None)
        coord2 = MockCoordinator(None)
        
        registry.register("test", coord1)
        registry.register("test", coord2)  # Replace
        
        assert coord1.cleanup_called  # Old coordinator cleaned up
        assert registry.get("test") == coord2
    
    def test_registry_remove(self):
        """Test removing coordinators."""
        registry = CoordinatorRegistry()
        coord = MockCoordinator(None)
        
        registry.register("test", coord)
        assert registry.remove("test")
        assert coord.cleanup_called
        assert registry.get("test") is None
        
        # Remove non-existent
        assert not registry.remove("nonexistent")
    
    def test_registry_list_coordinators(self):
        """Test listing coordinator names."""
        registry = CoordinatorRegistry()
        
        registry.register("coord1", MockCoordinator(None))
        registry.register("coord2", MockCoordinator(None))
        registry.register("coord3", MockCoordinator(None))
        
        names = registry.list_coordinators()
        assert len(names) == 3
        assert "coord1" in names
        assert "coord2" in names
        assert "coord3" in names
    
    def test_registry_initialize_all(self):
        """Test initializing all coordinators."""
        registry = CoordinatorRegistry()
        coord1 = MockCoordinator(None)
        coord2 = MockCoordinator(None)
        
        registry.register("test1", coord1)
        registry.register("test2", coord2)
        
        deps = {"shared": "data"}
        registry.initialize_all(deps)
        
        assert coord1.initialized_deps == deps
        assert coord2.initialized_deps == deps
        assert coord1.is_initialized
        assert coord2.is_initialized
    
    def test_registry_initialize_all_with_error(self, capsys):
        """Test initialize_all handles errors gracefully."""
        registry = CoordinatorRegistry()
        
        class ErrorCoordinator(CoordinatorBase):
            def initialize(self, dependencies):
                raise ValueError("Test error")
            
            def cleanup(self):
                pass
        
        error_coord = ErrorCoordinator(None)
        good_coord = MockCoordinator(None)
        
        registry.register("error", error_coord)
        registry.register("good", good_coord)
        
        deps = {"test": "data"}
        registry.initialize_all(deps)
        
        # Good coordinator should still be initialized
        assert good_coord.initialized_deps == deps
        
        # Check error message was printed
        captured = capsys.readouterr()
        assert "Failed to initialize coordinator 'error'" in captured.out
        assert "Test error" in captured.out
    
    def test_registry_cleanup_all(self):
        """Test cleaning up all coordinators."""
        registry = CoordinatorRegistry()
        coord1 = MockCoordinator(None)
        coord2 = MockCoordinator(None)
        
        registry.register("test1", coord1)
        registry.register("test2", coord2)
        
        registry.cleanup_all()
        
        assert coord1.cleanup_called
        assert coord2.cleanup_called
        assert registry.list_coordinators() == []
        assert registry._coordinators == {}
    
    def test_registry_cleanup_all_with_error(self, capsys):
        """Test cleanup_all handles errors gracefully."""
        registry = CoordinatorRegistry()
        
        class ErrorCoordinator(CoordinatorBase):
            def initialize(self, dependencies):
                pass
            
            def cleanup(self):
                raise ValueError("Cleanup error")
        
        error_coord = ErrorCoordinator(None)
        good_coord = MockCoordinator(None)
        
        registry.register("error", error_coord)
        registry.register("good", good_coord)
        
        registry.cleanup_all()
        
        # Good coordinator should still be cleaned up
        assert good_coord.cleanup_called
        
        # Check error message was printed
        captured = capsys.readouterr()
        assert "Error during coordinator cleanup" in captured.out
        assert "Cleanup error" in captured.out
        
        # Registry should still be cleared
        assert registry.list_coordinators() == []


class TestCoordinatorIntegration:
    """Test coordinator system integration with sprite viewer."""
    
    def test_sprite_viewer_has_coordinator_registry(self):
        """Test that SpriteViewer includes coordinator registry."""
        # This is a minimal integration test that doesn't require Qt display
        from sprite_viewer import SpriteViewer
        
        # Verify the class has the expected attribute at class level
        # (We can't instantiate without Qt)
        init_code = SpriteViewer.__init__.__code__
        
        # Check that __init__ references _coordinator_registry
        assert '_coordinator_registry' in init_code.co_names or \
               'CoordinatorRegistry' in init_code.co_names
    
    def test_coordinator_imports(self):
        """Test that coordinator imports work correctly."""
        # These should not raise ImportError
        from coordinators import CoordinatorBase, CoordinatorRegistry
        from coordinators.base import CoordinatorBase as Base
        
        # Verify they're the same classes
        assert CoordinatorBase is Base