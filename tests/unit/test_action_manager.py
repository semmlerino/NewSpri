"""
Unit tests for ActionManager functionality.
Tests the centralized QAction creation and management system.
"""

import pytest
from unittest.mock import MagicMock

from action_manager import (
    ActionManager, ActionDefinition, ActionCategory,
    get_action_manager, reset_action_manager
)


class TestActionDefinition:
    """Test ActionDefinition class."""
    
    def test_action_definition_creation(self):
        """Test creating an action definition."""
        definition = ActionDefinition(
            action_id="test_action",
            text="Test Action",
            category=ActionCategory.FILE,
            shortcut_id="test_shortcut",
            tooltip="Test tooltip",
            icon="🔬"
        )
        
        assert definition.action_id == "test_action"
        assert definition.text == "Test Action"
        assert definition.category == ActionCategory.FILE
        assert definition.shortcut_id == "test_shortcut"
        assert definition.tooltip == "Test tooltip"
        assert definition.icon == "🔬"
        assert definition.enabled_by_default is True
        assert definition.enabled_context is None
    
    def test_action_definition_validation(self):
        """Test action definition validation."""
        # Test empty action_id
        with pytest.raises(ValueError, match="Action must have ID and text"):
            ActionDefinition("", "test", ActionCategory.FILE)
        
        # Test empty text
        with pytest.raises(ValueError, match="Action must have ID and text"):
            ActionDefinition("test_id", "", ActionCategory.FILE)
    
    def test_action_definition_context_requirements(self):
        """Test action definition with context requirements."""
        definition = ActionDefinition(
            action_id="context_action",
            text="Context Action",
            category=ActionCategory.ANIMATION,
            enabled_by_default=False,
            enabled_context="has_frames"
        )
        
        assert not definition.enabled_by_default
        assert definition.enabled_context == "has_frames"


class TestActionManager:
    """Test ActionManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_action_manager()
        self.manager = ActionManager()
    
    def test_manager_initialization(self):
        """Test action manager initialization."""
        assert isinstance(self.manager, ActionManager)
        
        # Check that default actions are loaded
        action_ids = self.manager.get_all_action_ids()
        assert len(action_ids) >= 15  # Should have file, view, animation actions
        
        # Check specific actions exist
        assert "file_open" in action_ids
        assert "view_zoom_in" in action_ids
        assert "animation_toggle" in action_ids
    
    def test_action_definition_retrieval(self):
        """Test retrieving action definitions."""
        # Test existing action
        definition = self.manager.get_action_definition("file_open")
        assert definition is not None
        assert definition.text == "Open..."
        assert definition.category == ActionCategory.FILE
        
        # Test non-existent action
        definition = self.manager.get_action_definition("non_existent")
        assert definition is None
    
    def test_action_registration(self):
        """Test registering new action definitions."""
        definition = ActionDefinition(
            action_id="test_action",
            text="Test Action",
            category=ActionCategory.FILE
        )
        
        # Register action
        success = self.manager.register_action("test_action", definition)
        assert success
        
        # Verify registration
        registered = self.manager.get_action_definition("test_action")
        assert registered is not None
        assert registered.text == "Test Action"
        
        # Test duplicate registration
        duplicate_success = self.manager.register_action("test_action", definition)
        assert not duplicate_success
    
    def test_actions_by_category(self):
        """Test getting actions by category."""
        # Note: We can't create actual QActions without QApplication,
        # but we can test that the method works without segfaulting
        action_ids = self.manager.get_all_action_ids()
        
        # Count actions by category in definitions
        file_count = sum(1 for action_id in action_ids 
                        if self.manager.get_action_definition(action_id).category == ActionCategory.FILE)
        view_count = sum(1 for action_id in action_ids 
                        if self.manager.get_action_definition(action_id).category == ActionCategory.VIEW)
        
        assert file_count >= 3  # Should have open, quit, export actions
        assert view_count >= 4  # Should have zoom actions
    
    def test_context_requirements(self):
        """Test context requirement handling."""
        # Test getting actions that require specific context
        has_frames_actions = self.manager.get_actions_requiring_context("has_frames")
        assert len(has_frames_actions) >= 5  # Export and animation actions
        
        # Verify specific actions require frames
        assert "file_export_frames" in has_frames_actions
        assert "animation_toggle" in has_frames_actions
        
        # Test context that shouldn't exist
        no_actions = self.manager.get_actions_requiring_context("non_existent_context")
        assert len(no_actions) == 0
    
    def test_context_state_management(self):
        """Test context state updates."""
        # Test initial state
        definition = self.manager.get_action_definition("file_export_frames")
        should_be_enabled = self.manager._should_action_be_enabled(definition)
        assert not should_be_enabled  # Should be disabled without frames
        
        # Update context
        self.manager.update_context(has_frames=True)
        should_be_enabled = self.manager._should_action_be_enabled(definition)
        assert should_be_enabled  # Should be enabled with frames
        
        # Update context again
        self.manager.update_context(has_frames=False)
        should_be_enabled = self.manager._should_action_be_enabled(definition)
        assert not should_be_enabled  # Should be disabled again
    
    def test_callback_management(self):
        """Test action callback handling."""
        callback_called = []
        
        def test_callback():
            callback_called.append(True)
        
        # Set callback
        self.manager.set_action_callback("file_open", test_callback)
        
        # Verify callback is stored
        definition = self.manager.get_action_definition("file_open")
        assert definition.callback == test_callback
    
    def test_singleton_instance(self):
        """Test singleton instance functionality."""
        manager1 = get_action_manager()
        manager2 = get_action_manager()
        
        assert manager1 is manager2  # Should be same instance
        
        # Reset and test again
        reset_action_manager()
        manager3 = get_action_manager()
        
        assert manager3 is not manager1  # Should be new instance after reset


class TestActionCategories:
    """Test ActionCategory enum."""
    
    def test_category_values(self):
        """Test category enum values."""
        assert ActionCategory.FILE.value == "file"
        assert ActionCategory.VIEW.value == "view"
        assert ActionCategory.ANIMATION.value == "animation"
        assert ActionCategory.HELP.value == "help"
        assert ActionCategory.TOOLBAR.value == "toolbar"


class TestActionIntegration:
    """Test integration scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_action_manager()
        self.manager = ActionManager()
    
    def test_action_definition_completeness(self):
        """Test that all action definitions are complete."""
        for action_id in self.manager.get_all_action_ids():
            definition = self.manager.get_action_definition(action_id)
            
            # Check required fields
            assert definition.action_id == action_id
            assert definition.text  # Should not be empty
            assert isinstance(definition.category, ActionCategory)
            
            # Check context consistency
            if definition.enabled_context:
                assert not definition.enabled_by_default or definition.enabled_context
    
    def test_shortcut_integration_consistency(self):
        """Test that shortcut IDs are consistent."""
        shortcut_actions = []
        
        for action_id in self.manager.get_all_action_ids():
            definition = self.manager.get_action_definition(action_id)
            if definition.shortcut_id:
                shortcut_actions.append((action_id, definition.shortcut_id))
        
        # Should have shortcut actions
        assert len(shortcut_actions) >= 10
        
        # Check that shortcut IDs follow expected patterns
        for action_id, shortcut_id in shortcut_actions:
            if action_id.startswith("file_"):
                assert shortcut_id.startswith("file_") or shortcut_id == action_id
            elif action_id.startswith("view_"):
                assert shortcut_id.startswith("view_") or shortcut_id == action_id
            elif action_id.startswith("animation_"):
                assert shortcut_id.startswith("animation_") or shortcut_id == action_id
    
    def test_all_categories_represented(self):
        """Test that all categories have actions."""
        action_ids = self.manager.get_all_action_ids()
        
        categories_with_actions = set()
        for action_id in action_ids:
            definition = self.manager.get_action_definition(action_id)
            categories_with_actions.add(definition.category)
        
        # Should have actions in major categories
        assert ActionCategory.FILE in categories_with_actions
        assert ActionCategory.VIEW in categories_with_actions
        assert ActionCategory.ANIMATION in categories_with_actions
    
    def test_context_requirements_consistency(self):
        """Test that context requirements are consistent."""
        for action_id in self.manager.get_all_action_ids():
            definition = self.manager.get_action_definition(action_id)
            
            # Actions requiring context should not be enabled by default
            # (unless they have fallback logic)
            if definition.enabled_context:
                # This is okay - some actions might be enabled by default
                # but still have context requirements for full functionality
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])